/**
 * Generates translated edition overview pages for all system languages.
 *
 * For each (edition, language) pair where translations exist, creates
 * a page showing front-page cards with translated lead headlines.
 *
 * Permalink: /edition/{date}/{lang}/
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

  const pages = [];

  for (const edition of editions) {
    const editionTranslations = translations[edition.edition_id];
    if (!editionTranslations) continue;

    for (const lang of systemLangs) {
      const langTranslation = editionTranslations[lang.code];
      if (!langTranslation) continue;

      // Merge translated lead headlines into newspaper data
      const translatedNewspapers = edition.newspapers.map((newspaper) => {
        const npTranslations =
          langTranslation.articles?.[newspaper.newspaper_id];
        if (!npTranslations) return newspaper;

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

      // Available languages for switcher
      const availableLangs = [
        {
          code: 'en',
          nativeName: 'English',
          dir: 'ltr',
          url: `/edition/${edition.date}/`,
        },
      ];
      for (const l of systemLangs) {
        if (editionTranslations[l.code]) {
          availableLangs.push({
            code: l.code,
            nativeName: l.nativeName,
            dir: l.dir,
            url: `/edition/${edition.date}/${l.code}/`,
          });
        }
      }

      pages.push({
        editionDate: edition.date,
        lang: lang.code,
        langName: lang.nativeName,
        langDir: lang.dir,
        langLocale: lang.locale,
        ui: uiStrings[lang.code] || {},
        newspapers: translatedNewspapers,
        curatorSynthesis: edition.curator_synthesis,
        availableLangs,
      });
    }
  }

  return pages;
}
