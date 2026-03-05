import { describe, it, expect } from 'vitest';
import { CATEGORIES, CATEGORY_IDS } from './categories.js';
import { NEWSPAPER_SUBSCRIPTIONS } from './subscriptions.js';
import { routePrompt, countNewspapersReached } from './router.js';
import type { CategoryId } from './taxonomy.types.js';

describe('Categories', () => {
  it('should have exactly 30 categories', () => {
    expect(CATEGORIES).toHaveLength(30);
  });

  it('should have exactly 30 category IDs', () => {
    expect(CATEGORY_IDS).toHaveLength(30);
  });

  it('should have unique category IDs', () => {
    const ids = CATEGORIES.map((c) => c.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('should have every category ID in the CATEGORY_IDS array', () => {
    for (const category of CATEGORIES) {
      expect(CATEGORY_IDS).toContain(category.id);
    }
  });
});

describe('Subscriptions', () => {
  it('should have 6 newspaper subscriptions', () => {
    expect(NEWSPAPER_SUBSCRIPTIONS).toHaveLength(6);
  });

  it('should have each newspaper subscribe to 9-10 categories', () => {
    for (const sub of NEWSPAPER_SUBSCRIPTIONS) {
      expect(sub.categoryIds.length).toBeGreaterThanOrEqual(9);
      expect(sub.categoryIds.length).toBeLessThanOrEqual(10);
    }
  });

  it('should have every category subscribed to by at least 1 newspaper', () => {
    const subscribedCategories = new Set(
      NEWSPAPER_SUBSCRIPTIONS.flatMap((sub) => sub.categoryIds),
    );
    for (const id of CATEGORY_IDS) {
      expect(subscribedCategories.has(id)).toBe(true);
    }
  });

  it('should only reference valid category IDs', () => {
    const validIds = new Set<string>(CATEGORY_IDS);
    for (const sub of NEWSPAPER_SUBSCRIPTIONS) {
      for (const id of sub.categoryIds) {
        expect(validIds.has(id)).toBe(true);
      }
    }
  });
});

describe('Router', () => {
  it('should return no newspapers for empty categories', () => {
    const result = routePrompt([] as CategoryId[]);
    expect(result).toHaveLength(0);
  });

  it('should route a single category to the correct newspapers', () => {
    const result = routePrompt(['markets-and-macroeconomics']);
    const newspaperIds = result.map((r) => r.newspaperId);
    expect(newspaperIds).toContain('owner');
    expect(newspaperIds).not.toContain('hedonist');
  });

  it('should include matched categories in the result', () => {
    const result = routePrompt(['markets-and-macroeconomics']);
    const ownerResult = result.find((r) => r.newspaperId === 'owner');
    expect(ownerResult?.matchedCategories).toContain(
      'markets-and-macroeconomics',
    );
  });

  it('should route multiple categories to the union of newspapers', () => {
    const result = routePrompt([
      'markets-and-macroeconomics',
      'entertainment-and-hollywood',
    ]);
    const newspaperIds = result.map((r) => r.newspaperId);
    expect(newspaperIds).toContain('owner');
    expect(newspaperIds).toContain('hedonist');
    expect(newspaperIds).toContain('moralist');
  });

  it('should route geopolitics-and-diplomacy to Sovereign and Aspirant', () => {
    const result = routePrompt(['geopolitics-and-diplomacy']);
    const newspaperIds = result.map((r) => r.newspaperId);
    expect(newspaperIds).toContain('sovereign');
    expect(newspaperIds).toContain('aspirant');
  });
});

describe('Pricing', () => {
  it('should count newspapers reached matching routing result length', () => {
    const categories: CategoryId[] = [
      'markets-and-macroeconomics',
      'entertainment-and-hollywood',
    ];
    const routed = routePrompt(categories);
    const count = countNewspapersReached(categories);
    expect(count).toBe(routed.length);
  });

  it('should return 0 for empty categories', () => {
    expect(countNewspapersReached([] as CategoryId[])).toBe(0);
  });
});
