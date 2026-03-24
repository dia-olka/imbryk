export default {
  eleventyComputed: {
    switcherLangs: (data) => {
      const langs = data.ap?.availableLangs;
      return langs && langs.length > 1 ? langs : null;
    },
    switcherCurrentLang: () => 'en',
  },
};
