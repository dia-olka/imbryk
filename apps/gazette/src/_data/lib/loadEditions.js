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
 * Resolve an image URL/path to an absolute URL.
 * - Absolute URLs (legacy data with baked-in domain) are returned as-is.
 * - Relative R2 keys are prefixed with R2_PUBLIC_URL.
 * - Falsy values pass through unchanged.
 */
function resolveImageUrl(urlOrPath) {
  if (!urlOrPath) return urlOrPath;
  if (urlOrPath.startsWith('http://') || urlOrPath.startsWith('https://')) return urlOrPath;
  if (R2_PUBLIC_URL) return `${R2_PUBLIC_URL}/${urlOrPath}`;
  return urlOrPath;
}

/**
 * Static mapping from newspaper ID to display name.
 * Derived from data/personas.json — update if personas change.
 */
const NEWSPAPER_NAMES = {
  sovereign: 'The Sovereign',
  aspirant: 'The Aspirant',
  owner: 'The Owner',
  moralist: 'The Moralist',
  radical: 'The Radical',
  hedonist: 'The Hedonist',
  curator: 'The Curator',
};

/**
 * Strip markdown code fences from a string, if present.
 * Handles ```json ... ``` or ``` ... ``` wrappers that LLMs occasionally emit.
 */
function stripMarkdownFences(text) {
  const trimmed = text.trim();
  if (!trimmed.startsWith('```')) return trimmed;
  const lines = trimmed.split('\n');
  const inner = lines.slice(1); // remove opening fence line (```json or ```)
  if (inner.length > 0 && inner[inner.length - 1].trim() === '```') {
    inner.pop(); // remove closing fence
  }
  return inner.join('\n');
}

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
    if (typeof rawContent === 'string') {
      const cleaned = stripMarkdownFences(rawContent);
      try {
        parsed = JSON.parse(cleaned);
      } catch (err) {
        if (newspaperId === 'curator') {
          // Curator returned as plain text/markdown — store it as-is
          curatorSynthesis = { text: cleaned };
          continue;
        }
        await captureLoadError(
          sourceUrl,
          `JSON.parse newspaper "${newspaperId}"`,
          err
        );
        continue;
      }
    } else {
      parsed = rawContent;
    }

    if (newspaperId === 'curator') {
      curatorSynthesis = parsed;
    } else {
      // Ensure newspaper_id is set (may already be in the parsed content)
      if (!parsed.newspaper_id) {
        parsed.newspaper_id = newspaperId;
      }

      // Inject newspaper_name from the static mapping when the LLM omits it.
      if (!parsed.newspaper_name && NEWSPAPER_NAMES[newspaperId]) {
        parsed.newspaper_name = NEWSPAPER_NAMES[newspaperId];
      }

      // Normalise field name variants produced by LLMs that deviate from the schema.
      // The LLM prompt specifies exact names, but flash-tier models occasionally use
      // alternatives (e.g. "title"/"content" instead of "headline"/"body",
      // "inBrief"/"inBriefs" instead of "in_brief", "editorsNote"/"editorNote"
      // instead of "editors_note", "fullArticles" instead of "articles").

      // Normalise articles key variants (fullArticles, etc.)
      if (!Array.isArray(parsed.articles)) {
        parsed.articles = parsed.fullArticles ?? parsed.article_list;
      }

      if (Array.isArray(parsed.articles)) {
        parsed.articles = parsed.articles.map((a) => ({
          ...a,
          headline: a.headline ?? a.title ?? undefined,
          body: a.body ?? a.content ?? a.text ?? undefined,
          image_url: resolveImageUrl(a.image_url),
        }));
      }

      // Normalise in_brief key variants
      if (!parsed.in_brief) {
        parsed.in_brief = parsed.inBrief ?? parsed.inBriefs;
      }

      // Normalise editors_note key variants
      if (!parsed.editors_note) {
        const alt = parsed.editorsNote ?? parsed.editorNote ?? parsed.editor_note;
        if (typeof alt === 'string') {
          parsed.editors_note = alt;
        }
      }

      if (Array.isArray(parsed.in_brief)) {
        parsed.in_brief = parsed.in_brief.map((item) => {
          if (typeof item === 'string') {
            // Plain string — derive headline from first sentence
            const headline = item.split(/[.!?]/)[0].trim().slice(0, 80) || item.slice(0, 80);
            return { headline, summary: item };
          }
          const headline = item.headline ?? item.title ?? undefined;
          const summary = item.summary ?? item.content ?? item.text ?? undefined;
          // Derive headline from summary when the LLM omitted it entirely
          const resolvedHeadline =
            headline ?? (summary ? summary.split(/[.!?]/)[0].trim().slice(0, 80) : undefined);
          return { ...item, headline: resolvedHeadline, summary };
        });
      }

      // Resolve heroImageUrl (relative key → absolute URL)
      if (parsed.heroImageUrl) {
        parsed.heroImageUrl = resolveImageUrl(parsed.heroImageUrl);
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

  // Deduplicate by date (URL structure uses date as the unique key).
  // Later entries overwrite earlier ones, so the last edition_id for a date wins.
  const byDate = new Map();
  for (const ed of editions) {
    byDate.set(ed.date, ed);
  }

  // Sort newest first
  return [...byDate.values()].sort((a, b) => b.date.localeCompare(a.date));
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
