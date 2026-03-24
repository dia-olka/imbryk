/**
 * Template data file for translated-article.njk.
 *
 * Provides eleventyComputed values that require JavaScript (arrays/objects)
 * rather than Nunjucks string templates, which always stringify to strings.
 */
export default {
  eleventyComputed: {
    hreflangAlternates: (data) => data.tap?.availableLangs ?? null,
    hreflangDefault: (data) => {
      const tap = data.tap;
      if (!tap) return null;
      return `/edition/${tap.editionDate}/${tap.newspaperId}/${tap.slug}/`;
    },
    pageUi: (data) => data.tap?.ui ?? {},
  },
};
