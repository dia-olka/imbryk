/**
 * Loads edition data from R2 (production) or local fixture (local dev).
 *
 * In production (R2_PUBLIC_URL is set), fetches editions/index.json from R2,
 * then fetches each edition JSON and transforms it from the R2 shape to the
 * gazette's template shape.
 *
 * In local development (no R2_PUBLIC_URL), reads the fixture file.
 */

import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

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
 */
export function transformR2Edition(r2Edition) {
  const newspapers = [];
  let curatorSynthesis = null;

  for (const [newspaperId, rawContent] of Object.entries(
    r2Edition.articles || {}
  )) {
    let parsed;
    try {
      parsed =
        typeof rawContent === 'string' ? JSON.parse(rawContent) : rawContent;
    } catch {
      // Skip malformed newspaper content
      continue;
    }

    if (newspaperId === 'curator') {
      curatorSynthesis = parsed;
    } else {
      // Ensure newspaper_id is set (may already be in the parsed content)
      if (!parsed.newspaper_id) {
        parsed.newspaper_id = newspaperId;
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
  const indexResp = await fetch(indexUrl);
  if (!indexResp.ok) {
    console.warn(
      `Failed to fetch edition index from R2 (${indexResp.status}), falling back to fixture`
    );
    return loadFromFixture();
  }

  const index = await indexResp.json();

  const editions = [];
  for (const entry of index) {
    const editionUrl = `${R2_PUBLIC_URL}/editions/${entry.date}/${entry.edition_id}.json`;
    try {
      const resp = await fetch(editionUrl);
      if (!resp.ok) {
        console.warn(
          `Failed to fetch edition ${entry.edition_id} (${resp.status}), skipping`
        );
        continue;
      }
      const r2Edition = await resp.json();
      editions.push(transformR2Edition(r2Edition));
    } catch (err) {
      console.warn(`Error fetching edition ${entry.edition_id}:`, err.message);
    }
  }

  // Sort newest first
  editions.sort((a, b) => b.date.localeCompare(a.date));
  return editions;
}

function loadFromFixture() {
  const fixturePath = join(__dirname, '..', 'fixtures', 'sample-edition.json');
  const raw = readFileSync(fixturePath, 'utf-8');
  const edition = JSON.parse(raw);
  return [edition];
}
