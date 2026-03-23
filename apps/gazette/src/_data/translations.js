/**
 * Loads translation data from R2 for each edition + system language.
 *
 * Returns a Map-like object: { [editionId]: { [langCode]: translationData } }
 *
 * In local dev (no R2_PUBLIC_URL), returns an empty object so the site
 * builds without translations — English-only.
 */

import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { z } from 'zod';

import loadEditions from './lib/loadEditions.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const R2_PUBLIC_URL = process.env.R2_PUBLIC_URL || '';

// Zod schema for translation JSON validation
const TranslatedArticleSchema = z.object({
  original_index: z.number(),
  headline: z.string().optional(),
  body: z.string().optional(),
  imageAlt: z.string().optional(),
});

const TranslationSchema = z.object({
  edition_id: z.string().min(1),
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  lang: z.string().min(2),
  provider: z.string().min(1),
  translated_at: z.string(),
  articles: z.record(z.string(), z.array(TranslatedArticleSchema)),
});

/**
 * Load language config from data/languages.json.
 */
function loadLanguages() {
  const langPath = join(__dirname, '..', '..', '..', '..', 'data', 'languages.json');
  try {
    const raw = readFileSync(langPath, 'utf-8');
    return JSON.parse(raw);
  } catch {
    return { system: [], ui: {} };
  }
}

export default async function () {
  if (!R2_PUBLIC_URL) {
    // Local dev — load fixture translations
    return loadFixtureTranslations();
  }

  const editions = await loadEditions();
  const langConfig = loadLanguages();
  const systemLangs = langConfig.system || [];

  if (!systemLangs.length) return {};

  // { editionId: { langCode: translationData } }
  const translations = {};

  for (const edition of editions) {
    const editionTranslations = {};

    for (const lang of systemLangs) {
      const url = `${R2_PUBLIC_URL}/editions/${edition.date}/translations/${lang.code}/${edition.edition_id}.json`;

      try {
        const resp = await fetch(url);
        if (!resp.ok) continue; // translation not available yet — normal

        const data = await resp.json();
        const result = TranslationSchema.safeParse(data);
        if (!result.success) {
          console.warn(
            `Invalid translation JSON for ${edition.edition_id}/${lang.code}:`,
            result.error.flatten()
          );
          continue;
        }

        editionTranslations[lang.code] = result.data;
      } catch {
        // Fetch failed — skip silently, English pages still build
        continue;
      }
    }

    if (Object.keys(editionTranslations).length > 0) {
      translations[edition.edition_id] = editionTranslations;
    }
  }

  return translations;
}

/**
 * Load fixture translations for local development.
 * Reads translation-{lang}.json files from the fixtures directory.
 */
function loadFixtureTranslations() {
  const langConfig = loadLanguages();
  const systemLangs = langConfig.system || [];
  if (!systemLangs.length) return {};

  const fixtureDir = join(__dirname, 'fixtures');
  const translations = {};

  for (const lang of systemLangs) {
    const filePath = join(fixtureDir, `translation-${lang.code}.json`);
    try {
      const raw = readFileSync(filePath, 'utf-8');
      const data = JSON.parse(raw);
      const result = TranslationSchema.safeParse(data);
      if (!result.success) {
        console.warn(`Invalid fixture translation for ${lang.code}:`, result.error.flatten());
        continue;
      }
      // The fixture has a single edition_id — replicate it for all 3 dev editions
      // (loadEditions creates 3 editions with different dates from the same fixture)
      const editionId = result.data.edition_id;
      if (!translations[editionId]) {
        translations[editionId] = {};
      }
      translations[editionId][lang.code] = result.data;
    } catch {
      continue;
    }
  }

  return translations;
}
