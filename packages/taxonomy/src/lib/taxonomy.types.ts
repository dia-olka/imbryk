/** Category within a group. */
export interface Category {
  id: string;
  label: string;
  group: string;
}

/** Named group of categories. */
export interface CategoryGroup {
  name: string;
  categories: Category[];
}

/** Valid category ID string (branded for intent-clarity, accepts any string at runtime). */
export type CategoryId = string & { readonly __brand?: 'CategoryId' };

/** Newspaper-to-category subscription mapping. */
export interface NewspaperSubscription {
  newspaperId: string;
  categoryIds: CategoryId[];
}

/** Result of routing a prompt to newspapers. */
export interface RoutingResult {
  newspaperId: string;
  matchedCategories: CategoryId[];
}
