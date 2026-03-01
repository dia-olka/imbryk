export type {
  Category,
  CategoryGroup,
  CategoryId,
  NewspaperSubscription,
  RoutingResult,
} from './lib/taxonomy.types.js';
export { CATEGORIES, CATEGORY_GROUPS, CATEGORY_IDS } from './lib/categories.js';
export {
  SOVEREIGN_SUBSCRIPTION,
  ASPIRANT_SUBSCRIPTION,
  OWNER_SUBSCRIPTION,
  MORALIST_SUBSCRIPTION,
  RADICAL_SUBSCRIPTION,
  HEDONIST_SUBSCRIPTION,
  NEWSPAPER_SUBSCRIPTIONS,
} from './lib/subscriptions.js';
export { routePrompt, countNewspapersReached } from './lib/router.js';
