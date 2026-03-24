export default {
  eleventyComputed: {
    pageUi: (data) => data.tep?.ui ?? {},
    switcherLangs: (data) => data.tep?.availableLangs ?? null,
    switcherCurrentLang: (data) => data.tep?.lang ?? 'en',
  },
};
