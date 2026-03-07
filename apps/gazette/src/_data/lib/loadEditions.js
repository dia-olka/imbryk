/**
 * Loads edition data from R2 (production) or local fixture (local dev).
 *
 * In production (R2_PUBLIC_URL is set), fetches editions/index.json from R2,
 * then fetches each edition JSON and transforms it from the R2 shape to the
 * gazette's template shape.
 *
 * In local development (no R2_PUBLIC_URL), reads the fixture file.
 *
 * All data is validated with Zod schemas. Invalid entries are skipped and
 * reported to Sentry (with the full source URL) so operators can locate the
 * offending file in R2. The build never crashes on bad data.
 */

import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  R2IndexEntrySchema,
  R2EditionSchema,
  R2NewspaperContentSchema,
  EditionSchema,
} from './schemas.js';
import { captureValidationError, captureLoadError } from './sentry.js';

const __dirname = dirname(fileURLToPath(import.meta.url));

const R2_PUBLIC_URL = process.env.R2_PUBLIC_URL || '';

/**
 * Transform an R2 edition JSON into the gazette template shape.
 *
 * R2 shape:
 *   { edition_id, date, articles: { sovereign: "<json-string>", curator: "<json-string>", ... } }
 *
 * Each newspaper value is a JSON-encoded string containing:
 *   { newspaper_id, newspaper_name, articles: [...], in_brief: [...], editors_note, metadata, ... }
 *
 * Gazette shape:
 *   { edition_id, date, newspapers: [{...parsed}], curator_synthesis: {...parsed} }
 *
 * @param {object} r2Edition  - Raw R2 edition object (already validated with R2EditionSchema).
 * @param {string} sourceUrl  - Full R2 URL of the edition file (used in Sentry reports).
 */
export async function transformR2Edition(r2Edition, sourceUrl) {
  const newspapers = [];
  let curatorSynthesis = null;

  for (const [newspaperId, rawContent] of Object.entries(
    r2Edition.articles || {}
  )) {
    let parsed;
    try {
      parsed =
        typeof rawContent === 'string' ? JSON.parse(rawContent) : rawContent;
    } catch (err) {
      await captureLoadError(
        sourceUrl,
        `JSON.parse newspaper "${newspaperId}"`,
        err
      );
      continue;
    }

    if (newspaperId === 'curator') {
      curatorSynthesis = parsed;
    } else {
      // Ensure newspaper_id is set (may already be in the parsed content)
      if (!parsed.newspaper_id) {
        parsed.newspaper_id = newspaperId;
      }

      // Validate the parsed newspaper content
      const npResult = R2NewspaperContentSchema.safeParse(parsed);
      if (!npResult.success) {
        await captureValidationError(
          {
            sourceUrl,
            label: `newspaper "${newspaperId}"`,
            offendingData: parsed,
          },
          npResult.error
        );
        // Use the raw parsed data anyway — only articles missing `headline`
        // will be filtered out later when building article/newspaper pages.
      }

      newspapers.push(parsed);
    }
  }

  return {
    edition_id: r2Edition.edition_id,
    date: r2Edition.date,
    newspapers,
    curator_synthesis: curatorSynthesis,
  };
}

/**
 * Load all editions — from R2 in production, from fixture in local dev.
 *
 * @returns {Promise<Array>} Array of edition objects in gazette template shape,
 *                           sorted newest-first.
 */
export default async function loadEditions() {
  if (R2_PUBLIC_URL) {
    return await loadFromR2();
  }
  return loadFromFixture();
}

async function loadFromR2() {
  const indexUrl = `${R2_PUBLIC_URL}/editions/index.json`;

  let index;
  try {
    const indexResp = await fetch(indexUrl);
    if (!indexResp.ok) {
      await captureLoadError(
        indexUrl,
        'fetch editions index',
        new Error(`HTTP ${indexResp.status} ${indexResp.statusText}`)
      );
      console.warn(
        `Failed to fetch edition index from R2 (${indexResp.status}), falling back to fixture`
      );
      return loadFromFixture();
    }
    index = await indexResp.json();
  } catch (err) {
    await captureLoadError(indexUrl, 'fetch editions index', err);
    console.warn('Error fetching edition index, falling back to fixture:', err.message);
    return loadFromFixture();
  }

  if (!Array.isArray(index)) {
    await captureLoadError(
      indexUrl,
      'editions index shape',
      new Error(`Expected array, got ${typeof index}`)
    );
    console.warn('Edition index is not an array, falling back to fixture');
    return loadFromFixture();
  }

  const editions = [];

  for (const entry of index) {
    // Validate the index entry before using it to build the URL
    const entryResult = R2IndexEntrySchema.safeParse(entry);
    if (!entryResult.success) {
      await captureValidationError(
        {
          sourceUrl: indexUrl,
          label: `index entry (edition_id: ${entry?.edition_id ?? 'unknown'})`,
          offendingData: entry,
        },
        entryResult.error
      );
      continue;
    }

    const { edition_id, date } = entryResult.data;
    const editionUrl = `${R2_PUBLIC_URL}/editions/${date}/${edition_id}.json`;

    let r2Edition;
    try {
      const resp = await fetch(editionUrl);
      if (!resp.ok) {
        await captureLoadError(
          editionUrl,
          `fetch edition ${edition_id}`,
          new Error(`HTTP ${resp.status} ${resp.statusText}`)
        );
        console.warn(
          `Failed to fetch edition ${edition_id} from ${editionUrl} (${resp.status}), skipping`
        );
        continue;
      }
      r2Edition = await resp.json();
    } catch (err) {
      await captureLoadError(editionUrl, `fetch edition ${edition_id}`, err);
      console.warn(`Error fetching edition ${edition_id} from ${editionUrl}:`, err.message);
      continue;
    }

    // Validate the raw R2 edition shape
    const editionResult = R2EditionSchema.safeParse(r2Edition);
    if (!editionResult.success) {
      await captureValidationError(
        {
          sourceUrl: editionUrl,
          label: `R2 edition ${edition_id}`,
          offendingData: r2Edition,
        },
        editionResult.error
      );
      continue;
    }

    const transformed = await transformR2Edition(editionResult.data, editionUrl);

    // Validate the transformed gazette shape
    const transformedResult = EditionSchema.safeParse(transformed);
    if (!transformedResult.success) {
      await captureValidationError(
        {
          sourceUrl: editionUrl,
          label: `transformed edition ${edition_id}`,
          offendingData: transformed,
        },
        transformedResult.error
      );
      // Still include the edition — individual invalid articles are filtered
      // in articlePages.js / newspaperPages.js before slugify is called.
    }

    editions.push(transformed);
  }

  // Sort newest first
  editions.sort((a, b) => b.date.localeCompare(a.date));
  return editions;
}

function loadFromFixture() {
  const fixturePath = join(__dirname, '..', 'fixtures', 'sample-edition.json');
  const sourceUrl = fixturePath;

  let edition;
  try {
    const raw = readFileSync(fixturePath, 'utf-8');
    edition = JSON.parse(raw);
  } catch (err) {
    throw new Error(`Failed to load gazette fixture from ${fixturePath}: ${err.message}`);
  }

  // Validate fixture — fail fast in development so schema drift is caught early.
  const result = EditionSchema.safeParse(edition);
  if (!result.success) {
    console.error(
      `Gazette fixture at ${sourceUrl} does not match EditionSchema:`,
      JSON.stringify(result.error.flatten(), null, 2)
    );
    throw new Error(
      `Gazette fixture validation failed — run the build to see details. Fix ${sourceUrl} or update the schema.`
    );
  }

  return [result.data];
}
