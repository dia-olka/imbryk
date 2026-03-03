import type { CategoryId, RoutingResult } from './taxonomy.types.js';
import { NEWSPAPER_SUBSCRIPTIONS } from './subscriptions.js';

export function routePrompt(categoryIds: CategoryId[]): RoutingResult[] {
  if (categoryIds.length === 0) {
    return [];
  }

  const categorySet = new Set(categoryIds);
  const results: RoutingResult[] = [];

  for (const subscription of NEWSPAPER_SUBSCRIPTIONS) {
    const matched = subscription.categoryIds.filter((id) =>
      categorySet.has(id),
    );
    if (matched.length > 0) {
      results.push({
        newspaperId: subscription.newspaperId,
        matchedCategories: matched,
      });
    }
  }

  return results;
}

export function countNewspapersReached(categoryIds: CategoryId[]): number {
  return routePrompt(categoryIds).length;
}
