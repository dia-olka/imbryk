import type { CATEGORY_IDS } from './categories.js';

export interface CategoryGroup {
  name: string;
  categories: Category[];
}

export interface Category {
  id: string;
  label: string;
  group: string;
}

export type CategoryId = (typeof CATEGORY_IDS)[number];

export interface NewspaperSubscription {
  newspaperId: string;
  categoryIds: CategoryId[];
}

export interface RoutingResult {
  newspaperId: string;
  matchedCategories: CategoryId[];
}
