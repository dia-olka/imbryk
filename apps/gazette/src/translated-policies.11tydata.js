import loadLanguages from './_data/lib/loadLanguages.js';

function buildSwitcherLangs(basePath) {
  const { system } = loadLanguages();
  const langs = [
    { code: 'en', nativeName: 'English', dir: 'ltr', url: `${basePath}` },
  ];
  for (const lang of system) {
    langs.push({
      code: lang.code,
      nativeName: lang.nativeName,
      dir: lang.dir,
      url: `${basePath}${lang.code}/`,
    });
  }
  return langs;
}

export default {
  eleventyComputed: {
    pageUi: (data) => data.sp?.ui ?? {},
    switcherLangs: () => buildSwitcherLangs('/policies/'),
    switcherCurrentLang: (data) => data.sp?.lang ?? 'en',
  },
};
