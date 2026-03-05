import slugify from '@sindresorhus/slugify';
import { getDesignTokens, toCSSCustomProperties } from './designTokens.js';
import loadEditions from './lib/loadEditions.js';

export default async function () {
  const editions = await loadEditions();
  const pages = [];

  for (const edition of editions) {
    const allNewspaperIds = edition.newspapers.map((n) => n.newspaper_id);

    for (const newspaper of edition.newspapers) {
      // Generate slugs, ensuring uniqueness within a newspaper
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
      const cssVars = toCSSCustomProperties(tokens);

      for (let i = 0; i < articlesWithSlugs.length; i++) {
        const article = articlesWithSlugs[i];
        pages.push({
          editionDate: edition.date,
          newspaperId: newspaper.newspaper_id,
          newspaperName: newspaper.newspaper_name,
          slug: article.slug,
          article,
          prevArticle: i > 0 ? articlesWithSlugs[i - 1] : null,
          nextArticle:
            i < articlesWithSlugs.length - 1 ? articlesWithSlugs[i + 1] : null,
          editorsNote: newspaper.editors_note,
          heroImageUrl: newspaper.heroImageUrl || null,
          allNewspaperIds,
          designTokens: tokens,
          cssVars,
        });
      }
    }
  }

  return pages;
}
