export default {
  eleventyComputed: {
    pageUi: (data) => data.tip?.ui ?? {},
    switcherLangs: (data) => data.tip?.availableLangs ?? null,
    switcherCurrentLang: (data) => data.tip?.lang ?? 'en',
  },
};
