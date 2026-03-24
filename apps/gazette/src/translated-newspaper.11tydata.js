/**
 * Template data file for translated-newspaper.njk.
 *
 * Provides eleventyComputed values that require JavaScript (arrays/objects)
 * rather than Nunjucks string templates, which always stringify to strings.
 */
export default {
  eleventyComputed: {
    hreflangAlternates: (data) => data.tnp?.availableLangs ?? null,
    hreflangDefault: (data) => {
      const tnp = data.tnp;
      if (!tnp) return null;
      return `/edition/${tnp.editionDate}/${tnp.newspaperId}/`;
    },
    pageUi: (data) => data.tnp?.ui ?? {},
    switcherLangs: (data) => data.tnp?.availableLangs ?? null,
    switcherCurrentLang: (data) => data.tnp?.lang ?? 'en',
  },
};
