import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

/**
 * WCAG 2.2 AA automated accessibility tests for the Gazette static site.
 *
 * Tests navigate by following actual links so they work identically against:
 *  - local Eleventy dev server (fixture data)
 *  - deployed Cloudflare Pages (real data)
 *
 * Audit checklist coverage:
 *  1. ARIA landmarks     — header, main, footer on every page
 *  2. Skip link          — present and targets #main-content
 *  3. Colour contrast    — axe "color-contrast" rule
 *  4. Navigation         — primary nav links work
 *  5. Touch targets      — axe "target-size" rule
 *  6. Full axe scan      — wcag2a, wcag2aa, wcag22aa per route
 */

// ── Helpers ──────────────────────────────────────────────────────────────────

async function assertLandmarks(page: Parameters<typeof test>[1]['page']) {
  await expect(page.locator('header[role="banner"]')).toHaveCount(1);
  await expect(page.locator('main#main-content')).toHaveCount(1);
  await expect(page.locator('footer[role="contentinfo"]')).toHaveCount(1);
}

async function assertSkipLink(page: Parameters<typeof test>[1]['page']) {
  const skipLink = page.locator('a[href="#main-content"]');
  await expect(skipLink).toHaveCount(1);
}

async function axeScan(page: Parameters<typeof test>[1]['page']) {
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();
  expect(results.violations).toEqual([]);
}

// ── Home page ─────────────────────────────────────────────────────────────────

test.describe('Home page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('has correct ARIA landmarks', async ({ page }) => {
    await assertLandmarks(page);
  });

  test('has skip link targeting #main-content', async ({ page }) => {
    await assertSkipLink(page);
  });

  test('has page title', async ({ page }) => {
    await expect(page).toHaveTitle(/.+/);
  });

  test('primary nav links are present', async ({ page }) => {
    const nav = page.locator('nav[aria-label="Primary navigation"]');
    await expect(nav).toHaveCount(1);
    await expect(nav.getByRole('link', { name: 'Today' })).toBeVisible();
    await expect(nav.getByRole('link', { name: 'World' })).toBeVisible();
    await expect(nav.getByRole('link', { name: 'Archive' })).toBeVisible();
  });

  test('shows front-page grid or empty state', async ({ page }) => {
    const hasEdition =
      (await page.locator('.front-page-grid').count()) > 0;
    const hasEmpty =
      (await page.locator('text=No editions published yet').count()) > 0;
    expect(hasEdition || hasEmpty).toBe(true);
  });

  test('no axe violations', async ({ page }) => {
    await axeScan(page);
  });
});

// ── Archive page ──────────────────────────────────────────────────────────────

test.describe('Archive page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/archive/');
  });

  test('has correct ARIA landmarks', async ({ page }) => {
    await assertLandmarks(page);
  });

  test('has skip link', async ({ page }) => {
    await assertSkipLink(page);
  });

  test('has page title containing "Archive"', async ({ page }) => {
    await expect(page).toHaveTitle(/Archive/i);
  });

  test('shows archive grid or empty state', async ({ page }) => {
    const hasGrid = (await page.locator('.archive-grid').count()) > 0;
    const hasEmpty =
      (await page.locator('text=No editions published yet').count()) > 0;
    expect(hasGrid || hasEmpty).toBe(true);
  });

  test('no axe violations', async ({ page }) => {
    await axeScan(page);
  });
});

// ── Newspaper directory page ──────────────────────────────────────────────────

test.describe('Newspaper directory page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/newspapers/');
  });

  test('has correct ARIA landmarks', async ({ page }) => {
    await assertLandmarks(page);
  });

  test('has skip link', async ({ page }) => {
    await assertSkipLink(page);
  });

  test('has page title', async ({ page }) => {
    await expect(page).toHaveTitle(/.+/);
  });

  test('no axe violations', async ({ page }) => {
    await axeScan(page);
  });
});

// ── World history page ────────────────────────────────────────────────────────

test.describe('Timeline page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/timeline/');
  });

  test('has correct ARIA landmarks', async ({ page }) => {
    await assertLandmarks(page);
  });

  test('has skip link', async ({ page }) => {
    await assertSkipLink(page);
  });

  test('has page title containing "Timeline" or "World"', async ({ page }) => {
    await expect(page).toHaveTitle(/Timeline|World/i);
  });

  test('no axe violations', async ({ page }) => {
    await axeScan(page);
  });
});

// ── Edition and newspaper pages (followed from home) ─────────────────────────

test.describe('Edition navigation', () => {
  test('home → newspaper front page: landmarks and axe clean', async ({
    page,
  }) => {
    await page.goto('/');

    // Try to find any newspaper card link from the front-page grid.
    const firstCard = page.locator('.front-page-grid a').first();
    const cardCount = await page.locator('.front-page-grid a').count();

    // If no editions are published, skip the navigation tests gracefully.
    test.skip(cardCount === 0, 'No editions on home page — skipping');

    const href = await firstCard.getAttribute('href');
    await page.goto(href!);

    await assertLandmarks(page);
    await assertSkipLink(page);
    await axeScan(page);
  });

  test('home → newspaper → article: landmarks and axe clean', async ({
    page,
  }) => {
    await page.goto('/');

    const cardCount = await page.locator('.front-page-grid a').count();
    test.skip(cardCount === 0, 'No editions on home page — skipping');

    // Navigate to the first newspaper page
    const firstCard = page.locator('.front-page-grid a').first();
    const npHref = await firstCard.getAttribute('href');
    await page.goto(npHref!);

    // Navigate to the first article from the newspaper page
    const firstArticleLink = page
      .locator('.newspaper-articles a')
      .first();
    const articleCount = await page
      .locator('.newspaper-articles a')
      .count();
    test.skip(articleCount === 0, 'No articles on newspaper page — skipping');

    const articleHref = await firstArticleLink.getAttribute('href');
    await page.goto(articleHref!);

    await assertLandmarks(page);
    await assertSkipLink(page);
    await axeScan(page);
  });

  test('breadcrumb navigation returns to edition overview', async ({ page }) => {
    await page.goto('/');

    const cardCount = await page.locator('.front-page-grid a').count();
    test.skip(cardCount === 0, 'No editions on home page — skipping');

    // Navigate to first newspaper page
    const npHref = await page
      .locator('.front-page-grid a')
      .first()
      .getAttribute('href');
    await page.goto(npHref!);

    // Breadcrumb should include a link back to home
    const breadcrumb = page.locator('nav[aria-label="Breadcrumb"]');
    await expect(breadcrumb).toHaveCount(1);
    await expect(breadcrumb.getByRole('link', { name: 'Home' })).toBeVisible();
  });

  test('back link on newspaper page navigates to edition overview', async ({
    page,
  }) => {
    await page.goto('/');

    const cardCount = await page.locator('.front-page-grid a').count();
    test.skip(cardCount === 0, 'No editions on home page — skipping');

    const npHref = await page
      .locator('.front-page-grid a')
      .first()
      .getAttribute('href');
    await page.goto(npHref!);

    const backLink = page.locator('a.back-link');
    await expect(backLink).toBeVisible();
    await backLink.click();

    // Should land on an edition overview page
    await expect(page).toHaveURL(/\/edition\/.+\/$/);
  });
});

// ── Navigation bar ────────────────────────────────────────────────────────────

test.describe('Global navigation', () => {
  test('Today nav link leads to home page', async ({ page }) => {
    await page.goto('/archive/');
    await page.getByRole('navigation', { name: 'Primary navigation' }).getByRole('link', { name: 'Today' }).click();
    await expect(page).toHaveURL('/');
  });

  test('Archive nav link leads to /archive/', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('navigation', { name: 'Primary navigation' }).getByRole('link', { name: 'Archive' }).click();
    await expect(page).toHaveURL('/archive/');
  });

  test('World nav link leads to /timeline/', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('navigation', { name: 'Primary navigation' }).getByRole('link', { name: 'World' }).click();
    await expect(page).toHaveURL('/timeline/');
  });

  test('aria-current="page" set on active nav item', async ({ page }) => {
    await page.goto('/archive/');
    const activeLink = page.locator('nav[aria-label="Primary navigation"] a[aria-current="page"]');
    await expect(activeLink).toHaveCount(1);
    await expect(activeLink).toHaveText('Archive');
  });
});

// ── Curator synthesis page ────────────────────────────────────────────────────

test.describe('Curator page', () => {
  test('V2 curator page: landmarks, accessibility, and structure', async ({ page }) => {
    // Navigate to the latest edition (first in the list → V2 fixture data)
    await page.goto('/');
    const editionLinks = page.locator('.front-page-grid a');
    const count = await editionLinks.count();
    test.skip(count === 0, 'No editions on home page — skipping');

    // Go to the edition overview first
    const firstHref = await editionLinks.first().getAttribute('href');
    // Extract edition date from href like /edition/2026-03-01/sovereign/
    const dateMatch = firstHref!.match(/\/edition\/(\d{4}-\d{2}-\d{2})\//);
    test.skip(!dateMatch, 'Could not extract edition date from URL');

    // Navigate directly to the curator page for that edition
    await page.goto(`/edition/${dateMatch![1]}/curator/`);

    await assertLandmarks(page);
    await assertSkipLink(page);

    // V2: should have metrics, legend, consensus, fault lines, gaps
    await expect(page.locator('.curator-metrics')).toHaveCount(1);
    await expect(page.locator('.curator-legend')).toHaveCount(1);
    await expect(page.locator('.voice-chip').first()).toBeVisible();
    await expect(page.locator('.spectrum__dot').first()).toBeVisible();
    await expect(page.locator('.gap-icon').first()).toBeVisible();

    await axeScan(page);
  });

  test('V1 curator page: landmarks and axe clean', async ({ page }) => {
    // Navigate to the latest edition then go one edition back (V1 data)
    await page.goto('/');
    const editionLinks = page.locator('.front-page-grid a');
    const count = await editionLinks.count();
    test.skip(count === 0, 'No editions on home page — skipping');

    const firstHref = await editionLinks.first().getAttribute('href');
    const dateMatch = firstHref!.match(/\/edition\/(\d{4}-\d{2}-\d{2})\//);
    test.skip(!dateMatch, 'Could not extract edition date from URL');

    // Go to the V2 curator page and follow the "Previous edition" link
    await page.goto(`/edition/${dateMatch![1]}/curator/`);
    const prevLink = page.locator('.edition-nav__link').first();
    const prevCount = await prevLink.count();
    test.skip(prevCount === 0, 'No previous edition link — skipping');

    await prevLink.click();
    await expect(page).toHaveURL(/\/curator\//);

    await assertLandmarks(page);
    await assertSkipLink(page);

    // V1: should NOT have V2-specific elements but should have synthesis-section
    await expect(page.locator('.curator-metrics')).toHaveCount(0);
    await expect(page.locator('.synthesis-section')).not.toHaveCount(0);

    await axeScan(page);
  });
});
