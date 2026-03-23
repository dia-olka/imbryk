/**
 * Generates translated timeline pages for each system language.
 *
 * Timeline content (world history events) is translated via the translation
 * API as part of the daily translation job. The translations are stored in
 * R2 at: translations/_meta/timeline-{lang}.json
 *
 * If no R2 translations exist, pages are not generated (English-only).
 */

import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const R2_PUBLIC_URL = process.env.R2_PUBLIC_URL || '';

function loadLanguages() {
  const langPath = join(__dirname, '..', '..', '..', '..', 'data', 'languages.json');
  try {
    return JSON.parse(readFileSync(langPath, 'utf-8'));
  } catch {
    return { system: [], ui: {} };
  }
}

export default async function () {
  const langConfig = loadLanguages();
  const systemLangs = langConfig.system || [];
  const uiStrings = langConfig.ui || {};

  if (!systemLangs.length || !R2_PUBLIC_URL) return [];

  const pages = [];

  for (const lang of systemLangs) {
    const url = `${R2_PUBLIC_URL}/translations/_meta/timeline-${lang.code}.json`;

    try {
      const resp = await fetch(url);
      if (!resp.ok) continue;

      const data = await resp.json();
      if (!data.history || !Array.isArray(data.history)) continue;

      pages.push({
        lang: lang.code,
        langDir: lang.dir,
        langLocale: lang.locale,
        langName: lang.nativeName,
        ui: uiStrings[lang.code] || {},
        title: data.title || 'World History',
        synopsis: data.synopsis || '',
        epoch: data.epoch || '',
        history: data.history,
      });
    } catch {
      continue;
    }
  }

  return pages;
}
