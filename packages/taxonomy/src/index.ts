export type {
  Category,
  CategoryGroup,
  CategoryId,
  NewspaperSubscription,
  RoutingResult,
} from './lib/taxonomy.types.ts';
export {
  CATEGORIES,
  CATEGORY_GROUPS,
  CATEGORY_IDS,
  CATEGORY_ID_SET,
} from './lib/categories.ts';
export {
  SOVEREIGN_SUBSCRIPTION,
  ASPIRANT_SUBSCRIPTION,
  OWNER_SUBSCRIPTION,
  MORALIST_SUBSCRIPTION,
  RADICAL_SUBSCRIPTION,
  HEDONIST_SUBSCRIPTION,
  NEWSPAPER_SUBSCRIPTIONS,
} from './lib/subscriptions.ts';
export { routePrompt, countNewspapersReached } from './lib/router.ts';
export { TaxonomySchema, PersonasFileSchema } from './lib/schemas.ts';
export type { TaxonomyData, PersonasData, RawPersona } from './lib/schemas.ts';
