import type { CategoryId, NewspaperSubscription } from './taxonomy.types.js';

export const SOVEREIGN_SUBSCRIPTION: NewspaperSubscription = {
  newspaperId: 'sovereign',
  categoryIds: [
    'geopolitics',
    'domestic-politics',
    'military-and-defence',
    'law-and-justice',
    'immigration',
    'intelligence-and-surveillance',
    'trade-and-commerce',
    'energy',
    'technology-and-innovation',
  ] satisfies CategoryId[],
};

export const ASPIRANT_SUBSCRIPTION: NewspaperSubscription = {
  newspaperId: 'aspirant',
  categoryIds: [
    'geopolitics',
    'social-issues',
    'climate-and-environment',
    'health-and-medicine',
    'education',
    'immigration',
    'science-and-research',
    'food-and-agriculture',
    'culture-and-arts',
  ] satisfies CategoryId[],
};

export const OWNER_SUBSCRIPTION: NewspaperSubscription = {
  newspaperId: 'owner',
  categoryIds: [
    'finance-and-markets',
    'trade-and-commerce',
    'real-estate-and-property',
    'cryptocurrency',
    'labour-and-employment',
    'technology-and-innovation',
    'artificial-intelligence',
    'energy',
  ] satisfies CategoryId[],
};

export const MORALIST_SUBSCRIPTION: NewspaperSubscription = {
  newspaperId: 'moralist',
  categoryIds: [
    'domestic-politics',
    'religion-and-faith',
    'education',
    'crime-and-public-safety',
    'health-and-medicine',
    'immigration',
    'law-and-justice',
    'social-issues',
    'entertainment',
  ] satisfies CategoryId[],
};

export const RADICAL_SUBSCRIPTION: NewspaperSubscription = {
  newspaperId: 'radical',
  categoryIds: [
    'domestic-politics',
    'labour-and-employment',
    'corruption-and-scandal',
    'intelligence-and-surveillance',
    'cryptocurrency',
    'social-issues',
    'immigration',
    'geopolitics',
    'climate-and-environment',
  ] satisfies CategoryId[],
};

export const HEDONIST_SUBSCRIPTION: NewspaperSubscription = {
  newspaperId: 'hedonist',
  categoryIds: [
    'entertainment',
    'celebrity-and-personalities',
    'culture-and-arts',
    'sports',
    'fashion-and-style',
    'food-and-lifestyle',
    'travel',
    'corruption-and-scandal',
  ] satisfies CategoryId[],
};

export const NEWSPAPER_SUBSCRIPTIONS: NewspaperSubscription[] = [
  SOVEREIGN_SUBSCRIPTION,
  ASPIRANT_SUBSCRIPTION,
  OWNER_SUBSCRIPTION,
  MORALIST_SUBSCRIPTION,
  RADICAL_SUBSCRIPTION,
  HEDONIST_SUBSCRIPTION,
];
