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
  if (urlOrPath.startsWith('http://') || urlOrPath.startsWith('https://'))
    return urlOrPath;
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
    r2Edition.articles || {},
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
          err,
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
        const alt =
          parsed.editorsNote ?? parsed.editorNote ?? parsed.editor_note;
        if (typeof alt === 'string') {
          parsed.editors_note = alt;
        }
      }

      if (Array.isArray(parsed.in_brief)) {
        parsed.in_brief = parsed.in_brief.map((item) => {
          if (typeof item === 'string') {
            // Plain string — derive headline from first sentence
            const headline =
              item.split(/[.!?]/)[0].trim().slice(0, 80) || item.slice(0, 80);
            return { headline, summary: item };
          }
          const headline = item.headline ?? item.title ?? undefined;
          const summary =
            item.summary ?? item.content ?? item.text ?? undefined;
          // Derive headline from summary when the LLM omitted it entirely
          const resolvedHeadline =
            headline ??
            (summary
              ? summary.split(/[.!?]/)[0].trim().slice(0, 80)
              : undefined);
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
          npResult.error,
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
 * Result is memoised at module scope. 11ty data files (editions.js,
 * translations.js, articlePages.js, newspaperPages.js, edition.11tydata.js)
 * all call this during a single build; without the cache each caller would
 * refetch every edition from R2 — the main reason builds took 15 minutes.
 *
 * @returns {Promise<Array>} Array of edition objects in gazette template shape,
 *                           sorted newest-first.
 */
let memoised;

export default function loadEditions() {
  if (!memoised)
    memoised = R2_PUBLIC_URL
      ? loadFromR2()
      : Promise.resolve(loadFromFixture());
  return memoised;
}

async function loadFromR2() {
  const indexUrl = `${R2_PUBLIC_URL}/editions/index.json`;

  let index;
  try {
    const indexResp = await fetch(indexUrl);
    if (!indexResp.ok) {
      // 404 just means no editions have been published yet (first deploy) —
      // not a real failure, so skip Sentry and log a single calm line.
      if (indexResp.status === 404) {
        console.info(`Editions index not found at ${indexUrl}, using fixture`);
      } else {
        await captureLoadError(
          indexUrl,
          'fetch editions index',
          new Error(`HTTP ${indexResp.status} ${indexResp.statusText}`),
        );
        console.warn(
          `Failed to fetch edition index from R2 (${indexResp.status}), falling back to fixture`,
        );
      }
      return loadFromFixture();
    }
    index = await indexResp.json();
  } catch (err) {
    await captureLoadError(indexUrl, 'fetch editions index', err);
    console.warn(
      'Error fetching edition index, falling back to fixture:',
      err.message,
    );
    return loadFromFixture();
  }

  if (!Array.isArray(index)) {
    await captureLoadError(
      indexUrl,
      'editions index shape',
      new Error(`Expected array, got ${typeof index}`),
    );
    console.warn('Edition index is not an array, falling back to fixture');
    return loadFromFixture();
  }

  // Fan out all edition fetches in parallel — previously this was serial
  // and dominated build time. Per-entry errors still skip only that entry.
  const fetchJobs = index.map(async (entry) => {
    const entryResult = R2IndexEntrySchema.safeParse(entry);
    if (!entryResult.success) {
      await captureValidationError(
        {
          sourceUrl: indexUrl,
          label: `index entry (edition_id: ${entry?.edition_id ?? 'unknown'})`,
          offendingData: entry,
        },
        entryResult.error,
      );
      return null;
    }

    const { edition_id, date } = entryResult.data;
    const editionUrl = `${R2_PUBLIC_URL}/editions/${date}/${edition_id}.json`;

    let r2Edition;
    try {
      const resp = await fetch(editionUrl);
      if (!resp.ok) {
        // 404 means the index is out of sync with the bucket (edition was
        // deleted or index contains a stale entry). Skip without Sentry —
        // the next pipeline run rewrites the index.
        if (resp.status === 404) {
          console.info(
            `Edition ${edition_id} not found at ${editionUrl}, skipping`,
          );
        } else {
          await captureLoadError(
            editionUrl,
            `fetch edition ${edition_id}`,
            new Error(`HTTP ${resp.status} ${resp.statusText}`),
          );
          console.warn(
            `Failed to fetch edition ${edition_id} from ${editionUrl} (${resp.status}), skipping`,
          );
        }
        return null;
      }
      r2Edition = await resp.json();
    } catch (err) {
      await captureLoadError(editionUrl, `fetch edition ${edition_id}`, err);
      console.warn(
        `Error fetching edition ${edition_id} from ${editionUrl}:`,
        err.message,
      );
      return null;
    }

    const editionResult = R2EditionSchema.safeParse(r2Edition);
    if (!editionResult.success) {
      await captureValidationError(
        {
          sourceUrl: editionUrl,
          label: `R2 edition ${edition_id}`,
          offendingData: r2Edition,
        },
        editionResult.error,
      );
      return null;
    }

    const transformed = await transformR2Edition(
      editionResult.data,
      editionUrl,
    );

    const transformedResult = EditionSchema.safeParse(transformed);
    if (!transformedResult.success) {
      await captureValidationError(
        {
          sourceUrl: editionUrl,
          label: `transformed edition ${edition_id}`,
          offendingData: transformed,
        },
        transformedResult.error,
      );
      // Still include the edition — individual invalid articles are filtered
      // in articlePages.js / newspaperPages.js before slugify is called.
    }

    return transformed;
  });

  const editions = (await Promise.all(fetchJobs)).filter((e) => e !== null);

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
    throw new Error(
      `Failed to load gazette fixture from ${fixturePath}: ${err.message}`,
    );
  }

  // Validate fixture — fail fast in development so schema drift is caught early.
  const result = EditionSchema.safeParse(edition);
  if (!result.success) {
    console.error(
      `Gazette fixture at ${sourceUrl} does not match EditionSchema:`,
      JSON.stringify(result.error.flatten(), null, 2),
    );
    throw new Error(
      `Gazette fixture validation failed — run the build to see details. Fix ${sourceUrl} or update the schema.`,
    );
  }

  // Return 3 editions with different dates (today, minus 1 day, minus 2 days)
  const editions = [];
  const baseDate = new Date(result.data.date);
  for (let i = 0; i < 3; i++) {
    const newEdition = JSON.parse(JSON.stringify(result.data));
    const newDate = new Date(baseDate);
    newDate.setDate(baseDate.getDate() - i);
    // Format as YYYY-MM-DD
    const yyyy = newDate.getFullYear();
    const mm = String(newDate.getMonth() + 1).padStart(2, '0');
    const dd = String(newDate.getDate()).padStart(2, '0');
    newEdition.date = `${yyyy}-${mm}-${dd}`;

    // First edition gets V2 curator synthesis so both template paths are exercised.
    if (
      i === 0 &&
      newEdition.curator_synthesis &&
      !newEdition.curator_synthesis.version
    ) {
      const npIds = newEdition.newspapers.map((n) => n.newspaper_id);
      newEdition.curator_synthesis = {
        version: 2,
        consensus: [
          {
            text: 'All outlets agree that new autonomous drone deployments mark a strategic escalation in the Gulf region.',
            voices: npIds,
          },
          {
            text: 'The diplomatic process for the Northern Shield conflict has been frozen to redirect military resources.',
            voices: npIds,
          },
          {
            text: 'AI data-centre expansion has triggered federal mandates to fast-track nuclear energy deployment.',
            voices: ['sovereign', 'owner', 'radical', 'moralist'],
          },
        ],
        fault_lines: [
          {
            topic: 'Suspension of Northern Shield peace talks',
            label_left: 'Necessary strategic triage',
            label_right: 'Imperial abandonment',
            stances: [
              { newspaper_id: 'sovereign', score: 12 },
              { newspaper_id: 'aspirant', score: 88 },
              { newspaper_id: 'owner', score: 22 },
              { newspaper_id: 'moralist', score: 70 },
              { newspaper_id: 'radical', score: 94 },
              { newspaper_id: 'hedonist', score: 46 },
            ],
            summary:
              'Sharp divide between security-first and humanitarian perspectives.',
          },
          {
            topic: 'AI safety guardrails for autonomous weapons',
            label_left: 'Sovereign survival necessity',
            label_right: 'Unacceptable risk to civilians',
            stances: [
              { newspaper_id: 'sovereign', score: 10 },
              { newspaper_id: 'aspirant', score: 84 },
              { newspaper_id: 'owner', score: 20 },
              { newspaper_id: 'moralist', score: 86 },
              { newspaper_id: 'radical', score: 92 },
              { newspaper_id: 'hedonist', score: 52 },
            ],
            summary:
              'Pentagon rejection of guardrails splits outlets along security vs ethics lines.',
          },
        ],
        gaps: [
          {
            topic: 'Accountability gap',
            description:
              'No outlet addressed civilian casualty data from the drone deployment or any independent oversight mechanisms.',
          },
          {
            topic: 'Coverage gap',
            description:
              'The Meridian currency story received no coverage from two outlets, despite direct commodity market implications.',
          },
        ],
        what_to_watch: [
          'Follow the Fracture Accords council response to the drone deployment.',
          'Track whether the nuclear fast-track mandate faces legal challenges from environmental groups.',
        ],
      };
    }

    editions.push(newEdition);
  }
  return editions;
}
