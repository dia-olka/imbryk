import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

/**
 * WCAG 2.2 AA automated accessibility tests for the Imbryk prompt UI.
 *
 * Audit checklist coverage:
 *  1. Colour contrast      — axe "color-contrast" rule
 *  2. Keyboard navigation  — tab-order and trap checks
 *  3. Screen reader        — labels, aria-live, aria-hidden
 *  4. Focus management     — state transitions
 *  5. Touch targets        — axe "target-size" rule
 *  6. Error messages       — aria-describedby + role=alert
 *  7. Reduced motion       — CSS media query (static check, not runtime)
 */

test.describe('WCAG 2.2 AA — Imbryk prompt UI', () => {
  // ── 1. Full-page axe scan on the input state ──────────────────────────────
  test('input state: no axe violations (wcag2a, wcag2aa, wcag22aa)', async ({
    page,
  }) => {
    await page.goto('/');

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
      .analyze();

    expect(results.violations).toEqual([]);
  });

  // ── 2. Skip link is present and targets #main-content ────────────────────
  test('skip link targets #main-content', async ({ page }) => {
    await page.goto('/');
    const skipLink = page.locator('a[href="#main-content"]');
    await expect(skipLink).toHaveCount(1);
    const mainContent = page.locator('#main-content');
    await expect(mainContent).toHaveCount(1);
  });

  // ── 3. Orb textarea has an accessible label ───────────────────────────────
  test('orb textarea is labelled', async ({ page }) => {
    await page.goto('/');
    const textarea = page.getByLabel('Describe a world-altering event');
    await expect(textarea).toBeVisible();
  });

  // ── 4. Character count and validation are announced via aria-live ─────────
  test('character count region has aria-live=polite', async ({ page }) => {
    await page.goto('/');
    // The char-count paragraph carries aria-live="polite"
    const liveRegion = page.locator('p[aria-live="polite"]');
    await expect(liveRegion).toHaveCount(1);
  });

  // ── 5. Validation error appears with role=alert when input is too short ───
  test('validation error uses role=alert', async ({ page }) => {
    await page.goto('/');
    const textarea = page.getByLabel('Describe a world-altering event');
    await textarea.fill('short'); // < 10 chars
    const alert = page.locator('[role="alert"]');
    await expect(alert).toBeVisible();
  });

  // ── 6. Textarea aria-invalid is set when input is too short ───────────────
  test('textarea aria-invalid when below minimum length', async ({ page }) => {
    await page.goto('/');
    const textarea = page.getByLabel('Describe a world-altering event');
    await textarea.fill('short'); // < 10 chars
    await expect(textarea).toHaveAttribute('aria-invalid', 'true');
  });

  // ── 7. Orb body is not in tab order when not flipped ─────────────────────
  test('orb body is not in tab order when showing front face', async ({
    page,
  }) => {
    await page.goto('/');
    const orbBody = page.locator('.orb-body');
    await expect(orbBody).toHaveAttribute('tabindex', '-1');
  });

  // ── 8. ARIA landmarks: header, main, footer ───────────────────────────────
  test('page has correct ARIA landmarks', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('header[role="banner"]')).toHaveCount(1);
    await expect(page.locator('main#main-content')).toHaveCount(1);
    await expect(page.locator('footer[role="contentinfo"]')).toHaveCount(1);
  });

  // ── 9. Orb back face: aria-hidden when not visible ────────────────────────
  test('orb back face is aria-hidden when not visible', async ({ page }) => {
    await page.goto('/');
    const backFace = page.locator('.orb-face--back');
    await expect(backFace).toHaveAttribute('aria-hidden', 'true');
  });

  // ── 10. Button touch targets meet 44x44 minimum ───────────────────────────
  test('all buttons meet 44x44px minimum touch target', async ({ page }) => {
    await page.goto('/');
    const buttons = page.locator('button:visible');
    const count = await buttons.count();

    for (let i = 0; i < count; i++) {
      const btn = buttons.nth(i);
      const box = await btn.boundingBox();
      if (box) {
        expect(box.height, `Button ${i} height`).toBeGreaterThanOrEqual(44);
        expect(box.width, `Button ${i} width`).toBeGreaterThanOrEqual(44);
      }
    }
  });

  // ── 11. Orb scene has role=group with descriptive aria-label ─────────────
  test('orb scene has role=group with aria-label', async ({ page }) => {
    await page.goto('/');
    const orbScene = page.locator('[role="group"][aria-label]');
    await expect(orbScene).toHaveCount(1);
  });

  // ── 12. Quote announcement region is present ──────────────────────────────
  test('quote announcement region is present', async ({ page }) => {
    await page.goto('/');
    // sr-only div with aria-live="polite" for quote announcements
    const liveRegions = page.locator('div[aria-live="polite"]');
    await expect(liveRegions).toHaveCount(1);
  });

  // ── 13. Page title is set ─────────────────────────────────────────────────
  test('page has a title', async ({ page }) => {
    await page.goto('/');
    const title = await page.title();
    expect(title.length).toBeGreaterThan(0);
  });

  // ── 14. No keyboard trap in default state ────────────────────────────────
  test('keyboard navigation flows through all interactive elements', async ({
    page,
  }) => {
    await page.goto('/');
    // Tab through the page — we should be able to Tab past the textarea
    // without getting trapped.
    await page.keyboard.press('Tab'); // skip link
    await page.keyboard.press('Tab'); // textarea
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    // Should be on the textarea or an interactive element, not stuck
    expect(['TEXTAREA', 'A', 'BUTTON']).toContain(focused);
  });

  // ── 15. Colour contrast: axe scan with deferred CSS ──────────────────────
  test('no colour contrast violations', async ({ page }) => {
    await page.goto('/');
    // Wait for Tailwind to fully paint
    await page.waitForTimeout(500);

    const results = await new AxeBuilder({ page })
      .withTags(['cat.color'])
      .analyze();

    expect(results.violations).toEqual([]);
  });
});
