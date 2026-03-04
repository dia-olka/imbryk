import slugify from '@sindresorhus/slugify';
import { getDesignTokens, toCSSCustomProperties } from './designTokens.js';
import loadEditions from './lib/loadEditions.js';

export default async function () {
  const editions = await loadEditions();
  const pages = [];

  for (const edition of editions) {
    const allNewspaperIds = edition.newspapers.map((n) => n.newspaper_id);

    for (const newspaper of edition.newspapers) {
      // Generate slugs for article preview links
      const slugCounts = {};
      const articlesWithSlugs = newspaper.articles.map((article) => {
        let slug = slugify(article.headline);
        if (slugCounts[slug]) {
          slugCounts[slug]++;
          slug = `${slug}-${slugCounts[slug]}`;
        } else {
          slugCounts[slug] = 1;
        }
        return { ...article, slug };
      });

      const tokens = getDesignTokens(newspaper.newspaper_id);
      pages.push({
        editionDate: edition.date,
        newspaperId: newspaper.newspaper_id,
        newspaperName: newspaper.newspaper_name,
        articles: articlesWithSlugs,
        inBrief: newspaper.in_brief,
        editorsNote: newspaper.editors_note,
        frontPageImagePrompt: newspaper.frontPageImagePrompt || null,
        heroImageUrl: newspaper.heroImageUrl || null,
        metadata: newspaper.metadata,
        allNewspaperIds,
        designTokens: tokens,
        cssVars: toCSSCustomProperties(tokens),
      });
    }
  }
  return pages;
}
