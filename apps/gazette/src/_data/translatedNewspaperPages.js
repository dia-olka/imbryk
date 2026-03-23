/**
 * Generates translated newspaper pages for all system languages.
 *
 * For each (newspaper, language) pair where translations exist, creates
 * a page object with translated article headlines/bodies merged with
 * original newspaper metadata.
 *
 * Permalink: /edition/{date}/{newspaper}/{lang}/
 */

import slugify from '@sindresorhus/slugify';
import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

import { getDesignTokens, toCSSCustomProperties } from './designTokens.js';
import loadEditions from './lib/loadEditions.js';
import { ArticleSchema } from './lib/schemas.js';

const __dirname = dirname(fileURLToPath(import.meta.url));

function loadLanguages() {
  const langPath = join(__dirname, '..', '..', '..', '..', 'data', 'languages.json');
  try {
    return JSON.parse(readFileSync(langPath, 'utf-8'));
  } catch {
    return { system: [], ui: {} };
  }
}

export default async function (data) {
  const translations = data?.translations || {};
  const langConfig = loadLanguages();
  const systemLangs = langConfig.system || [];
  const uiStrings = langConfig.ui || {};

  if (!systemLangs.length || !Object.keys(translations).length) return [];

  const editions = await loadEditions();
  const pages = [];

  for (const edition of editions) {
    const editionTranslations = translations[edition.edition_id];
    if (!editionTranslations) continue;

    const allNewspaperIds = edition.newspapers.map((n) => n.newspaper_id);

    for (const newspaper of edition.newspapers) {
      // Validate and slug articles (same as newspaperPages.js)
      const validArticles = [];
      for (const article of newspaper.articles ?? []) {
        const result = ArticleSchema.safeParse(article);
        if (!result.success) continue;
        validArticles.push(result.data);
      }

      const slugCounts = {};
      const articlesWithSlugs = validArticles.map((article) => {
        let slug = slugify(article.headline);
        if (slugCounts[slug]) {
          slugCounts[slug]++;
          slug = `${slug}-${slugCounts[slug]}`;
        } else {
          slugCounts[slug] = 1;
        }
        return { ...article, slug };
      });

      for (const lang of systemLangs) {
        const langTranslation = editionTranslations[lang.code];
        if (!langTranslation) continue;

        const newspaperTranslations =
          langTranslation.articles?.[newspaper.newspaper_id];
        if (!newspaperTranslations) continue;

        // Build lookup
        const translatedByIndex = {};
        for (const t of newspaperTranslations) {
          translatedByIndex[t.original_index] = t;
        }

        // Merge translations into articles
        const translatedArticles = articlesWithSlugs.map((original, i) => {
          const translated = translatedByIndex[i];
          if (!translated) return original;
          return {
            ...original,
            headline: translated.headline || original.headline,
            body: translated.body || original.body,
            imageAlt: translated.imageAlt || original.imagePrompt,
          };
        });

        // Available languages for switcher
        const availableLangs = systemLangs
          .filter((l) => editionTranslations[l.code]?.articles?.[newspaper.newspaper_id])
          .map((l) => ({
            code: l.code,
            nativeName: l.nativeName,
            dir: l.dir,
            url: `/edition/${edition.date}/${newspaper.newspaper_id}/${l.code}/`,
          }));

        availableLangs.unshift({
          code: 'en',
          nativeName: 'English',
          dir: 'ltr',
          url: `/edition/${edition.date}/${newspaper.newspaper_id}/`,
        });

        const tokens = getDesignTokens(newspaper.newspaper_id);
        pages.push({
          editionDate: edition.date,
          newspaperId: newspaper.newspaper_id,
          newspaperName: newspaper.newspaper_name,
          lang: lang.code,
          langName: lang.nativeName,
          langDir: lang.dir,
          langLocale: lang.locale,
          ui: uiStrings[lang.code] || {},
          articles: translatedArticles,
          inBrief: newspaper.in_brief,
          editorsNote: newspaper.editors_note,
          heroImageUrl: newspaper.heroImageUrl || null,
          frontPageImagePrompt: newspaper.frontPageImagePrompt || null,
          allNewspaperIds,
          availableLangs,
          designTokens: tokens,
          cssVars: toCSSCustomProperties(tokens),
          googleFontsUrl: tokens?.googleFontsUrl || null,
        });
      }
    }
  }

  return pages;
}
