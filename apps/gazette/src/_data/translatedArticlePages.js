/**
 * Generates translated article pages for all system languages.
 *
 * For each (article, language) pair where a translation exists, creates
 * a page object with the translated headline/body merged with the original
 * article metadata (images, persona, design tokens).
 *
 * Permalink: /edition/{date}/{newspaper}/{slug}/{lang}/
 */

import slugify from '@sindresorhus/slugify';
import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

import { getDesignTokens, toCSSCustomProperties } from './designTokens.js';
import loadEditions from './lib/loadEditions.js';
import { ArticleSchema } from './lib/schemas.js';
import loadTranslations from './translations.js';

const __dirname = dirname(fileURLToPath(import.meta.url));

function loadLanguages() {
  const langPath = join(__dirname, '..', '..', '..', '..', 'data', 'languages.json');
  try {
    return JSON.parse(readFileSync(langPath, 'utf-8'));
  } catch {
    return { system: [], ui: {} };
  }
}

export default async function () {
  const translations = await loadTranslations();
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
      // Build slugs for original articles (same logic as articlePages.js)
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

      const tokens = getDesignTokens(newspaper.newspaper_id);
      const cssVars = toCSSCustomProperties(tokens);

      for (const lang of systemLangs) {
        const langTranslation = editionTranslations[lang.code];
        if (!langTranslation) continue;

        const newspaperTranslations =
          langTranslation.articles?.[newspaper.newspaper_id];
        if (!newspaperTranslations) continue;

        // Build a lookup: original_index -> translated fields
        const translatedByIndex = {};
        for (const t of newspaperTranslations) {
          translatedByIndex[t.original_index] = t;
        }

        for (let i = 0; i < articlesWithSlugs.length; i++) {
          const original = articlesWithSlugs[i];
          const translated = translatedByIndex[i];
          if (!translated) continue;

          // Merge translated fields with original metadata
          const translatedArticle = {
            ...original,
            headline: translated.headline || original.headline,
            body: translated.body || original.body,
            // Keep original image_url, use translated alt if available
            imageAlt: translated.imageAlt || original.imagePrompt,
          };

          // Build available languages for language switcher
          const availableLangs = systemLangs
            .filter((l) => editionTranslations[l.code]?.articles?.[newspaper.newspaper_id])
            .map((l) => ({
              code: l.code,
              nativeName: l.nativeName,
              dir: l.dir,
              url: `/edition/${edition.date}/${newspaper.newspaper_id}/${original.slug}/${l.code}/`,
            }));

          // Add English as default
          availableLangs.unshift({
            code: 'en',
            nativeName: 'English',
            dir: 'ltr',
            url: `/edition/${edition.date}/${newspaper.newspaper_id}/${original.slug}/`,
          });

          pages.push({
            editionDate: edition.date,
            newspaperId: newspaper.newspaper_id,
            newspaperName: newspaper.newspaper_name,
            slug: original.slug,
            lang: lang.code,
            langName: lang.nativeName,
            langDir: lang.dir,
            langLocale: lang.locale,
            ui: uiStrings[lang.code] || {},
            article: translatedArticle,
            originalArticle: original,
            prevArticle: i > 0 ? articlesWithSlugs[i - 1] : null,
            nextArticle:
              i < articlesWithSlugs.length - 1
                ? articlesWithSlugs[i + 1]
                : null,
            editorsNote: newspaper.editors_note,
            heroImageUrl: newspaper.heroImageUrl || null,
            allNewspaperIds,
            availableLangs,
            designTokens: tokens,
            cssVars,
            googleFontsUrl: tokens?.googleFontsUrl || null,
          });
        }
      }
    }
  }

  return pages;
}
