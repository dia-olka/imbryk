import slugify from '@sindresorhus/slugify';
import { getDesignTokens, toCSSCustomProperties } from './designTokens.js';
import loadEditions from './lib/loadEditions.js';
import { captureValidationError } from './lib/sentry.js';
import { ArticleSchema } from './lib/schemas.js';

const R2_PUBLIC_URL = process.env.R2_PUBLIC_URL || '';

export default async function () {
  const editions = await loadEditions();
  const pages = [];

  for (const edition of editions) {
    const allNewspaperIds = edition.newspapers.map((n) => n.newspaper_id);

    for (const newspaper of edition.newspapers) {
      // Filter and validate articles before calling slugify.
      // Articles missing `headline` (or failing schema) are skipped and
      // reported to Sentry with the full R2 URL so operators can inspect the
      // offending file.
      const editionUrl = R2_PUBLIC_URL
        ? `${R2_PUBLIC_URL}/editions/${edition.date}/${edition.edition_id}.json`
        : `fixture:${edition.edition_id}`;

      const validArticles = [];
      for (const article of newspaper.articles ?? []) {
        const result = ArticleSchema.safeParse(article);
        if (!result.success) {
          await captureValidationError(
            {
              sourceUrl: editionUrl,
              label: `article in newspaper "${newspaper.newspaper_id}" (edition ${edition.edition_id})`,
              offendingData: article,
            },
            result.error
          );
          continue;
        }
        validArticles.push(result.data);
      }

      // Generate slugs for article preview links
      const slugCounts = {};
      const articlesWithSlugs = validArticles.map((article) => {
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
