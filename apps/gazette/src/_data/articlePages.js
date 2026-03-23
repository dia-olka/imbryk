import slugify from '@sindresorhus/slugify';
import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

import { getDesignTokens, toCSSCustomProperties } from './designTokens.js';
import loadEditions from './lib/loadEditions.js';
import { captureValidationError } from './lib/sentry.js';
import { ArticleSchema } from './lib/schemas.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const R2_PUBLIC_URL = process.env.R2_PUBLIC_URL || '';

function loadLanguages() {
  const langPath = join(__dirname, '..', '..', '..', '..', 'data', 'languages.json');
  try {
    return JSON.parse(readFileSync(langPath, 'utf-8'));
  } catch {
    return { system: [], ui: {} };
  }
}

export default async function (data) {
  const editions = await loadEditions();
  const translations = data?.translations || {};
  const langConfig = loadLanguages();
  const systemLangs = langConfig.system || [];
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

      // Generate slugs, ensuring uniqueness within a newspaper
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
      const cssVars = toCSSCustomProperties(tokens);

      // Build available languages for the language switcher
      const editionTranslations = translations[edition.edition_id] || {};
      const availableLangs = [
        { code: 'en', nativeName: 'English', dir: 'ltr' },
      ];
      for (const lang of systemLangs) {
        if (editionTranslations[lang.code]?.articles?.[newspaper.newspaper_id]) {
          availableLangs.push({
            code: lang.code,
            nativeName: lang.nativeName,
            dir: lang.dir,
          });
        }
      }

      for (let i = 0; i < articlesWithSlugs.length; i++) {
        const article = articlesWithSlugs[i];
        // Add URLs to available langs (needs slug)
        const langsWithUrls = availableLangs.map((l) => ({
          ...l,
          url: l.code === 'en'
            ? `/edition/${edition.date}/${newspaper.newspaper_id}/${article.slug}/`
            : `/edition/${edition.date}/${newspaper.newspaper_id}/${article.slug}/${l.code}/`,
        }));

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
          availableLangs: langsWithUrls,
          designTokens: tokens,
          cssVars,
          googleFontsUrl: tokens?.googleFontsUrl || null,
        });
      }
    }
  }

  return pages;
}
