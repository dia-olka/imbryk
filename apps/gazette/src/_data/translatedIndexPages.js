/**
 * Generates translated index (home) pages for all system languages.
 *
 * For each language where translations exist for the latest edition,
 * creates a page showing front-page cards with translated lead headlines.
 *
 * Permalink: /{lang}/
 */

import loadEditions from './lib/loadEditions.js';
import loadLanguages from './lib/loadLanguages.js';
import loadTranslations from './translations.js';

export default async function () {
  const editions = await loadEditions();
  const translations = await loadTranslations();
  const langConfig = loadLanguages();
  const systemLangs = langConfig.system || [];
  const uiStrings = langConfig.ui || {};

  if (!editions.length || !systemLangs.length) return [];

  // Latest edition (editions are sorted newest-first)
  const latest = editions[0];
  const editionTranslations = translations[latest.edition_id];
  if (!editionTranslations) return [];

  const pages = [];

  for (const lang of systemLangs) {
    const langTranslation = editionTranslations[lang.code];
    if (!langTranslation) continue;

    // Merge translated lead headlines into newspaper data
    const translatedNewspapers = latest.newspapers.map((newspaper) => {
      const npTranslations =
        langTranslation.articles?.[newspaper.newspaper_id];
      if (!npTranslations) return newspaper;

      // Translate article headlines for card display
      const translatedArticles = (newspaper.articles ?? []).map(
        (article, i) => {
          const translated = npTranslations.find(
            (t) => t.original_index === i,
          );
          if (!translated) return article;
          return {
            ...article,
            headline: translated.headline || article.headline,
          };
        },
      );

      // Translated frontPageImagePrompt
      const npMeta =
        langTranslation.newspapers?.[newspaper.newspaper_id];

      return {
        ...newspaper,
        articles: translatedArticles,
        frontPageImagePrompt:
          npMeta?.frontPageImagePrompt ||
          newspaper.frontPageImagePrompt,
      };
    });

    // Available languages for switcher (based on which langs have translations for latest)
    const availableLangs = [
      { code: 'en', nativeName: 'English', dir: 'ltr', url: '/' },
    ];
    for (const l of systemLangs) {
      if (editionTranslations[l.code]) {
        availableLangs.push({
          code: l.code,
          nativeName: l.nativeName,
          dir: l.dir,
          url: `/${l.code}/`,
        });
      }
    }

    pages.push({
      lang: lang.code,
      langName: lang.nativeName,
      langDir: lang.dir,
      langLocale: lang.locale,
      ui: uiStrings[lang.code] || {},
      edition: {
        ...latest,
        newspapers: translatedNewspapers,
      },
      availableLangs,
      allEditions: editions,
    });
  }

  return pages;
}
