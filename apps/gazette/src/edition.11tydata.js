import loadLanguages from './_data/lib/loadLanguages.js';
import loadTranslations from './_data/translations.js';

export default {
  eleventyComputed: {
    switcherLangs: async (data) => {
      const edition = data.edition;
      if (!edition) return null;

      const translations = await loadTranslations();
      const editionTranslations = translations[edition.edition_id];
      if (!editionTranslations) return null;

      const { system } = loadLanguages();
      const langs = [
        {
          code: 'en',
          nativeName: 'English',
          dir: 'ltr',
          url: `/edition/${edition.date}/`,
        },
      ];
      for (const lang of system) {
        if (editionTranslations[lang.code]) {
          langs.push({
            code: lang.code,
            nativeName: lang.nativeName,
            dir: lang.dir,
            url: `/edition/${edition.date}/${lang.code}/`,
          });
        }
      }
      return langs.length > 1 ? langs : null;
    },
    switcherCurrentLang: () => 'en',
  },
};
