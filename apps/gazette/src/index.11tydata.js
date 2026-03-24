import loadLanguages from './_data/lib/loadLanguages.js';
import loadTranslations from './_data/translations.js';
import loadEditions from './_data/lib/loadEditions.js';

export default {
  eleventyComputed: {
    switcherLangs: async () => {
      const editions = await loadEditions();
      if (!editions.length) return null;

      const latest = editions[0];
      const translations = await loadTranslations();
      const editionTranslations = translations[latest.edition_id];
      if (!editionTranslations) return null;

      const { system } = loadLanguages();
      const langs = [
        { code: 'en', nativeName: 'English', dir: 'ltr', url: '/' },
      ];
      for (const lang of system) {
        if (editionTranslations[lang.code]) {
          langs.push({
            code: lang.code,
            nativeName: lang.nativeName,
            dir: lang.dir,
            url: `/${lang.code}/`,
          });
        }
      }
      return langs.length > 1 ? langs : null;
    },
    switcherCurrentLang: () => 'en',
  },
};
