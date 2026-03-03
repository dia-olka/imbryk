import type { Category, CategoryGroup } from './taxonomy.types.js';

export const CATEGORY_IDS = [
  // Power & Governance
  'geopolitics',
  'domestic-politics',
  'military-and-defence',
  'law-and-justice',
  'immigration',
  'intelligence-and-surveillance',
  // Finance & Economy
  'finance-and-markets',
  'trade-and-commerce',
  'real-estate-and-property',
  'cryptocurrency',
  'labour-and-employment',
  // Science & Technology
  'technology-and-innovation',
  'artificial-intelligence',
  'science-and-research',
  'energy',
  // Society & Values
  'social-issues',
  'education',
  'religion-and-faith',
  'crime-and-public-safety',
  'health-and-medicine',
  // Environment
  'climate-and-environment',
  'food-and-agriculture',
  // Culture & Entertainment
  'entertainment',
  'celebrity-and-personalities',
  'culture-and-arts',
  'sports',
  'fashion-and-style',
  'food-and-lifestyle',
  'travel',
  'corruption-and-scandal',
] as const;

const POWER_AND_GOVERNANCE: Category[] = [
  { id: 'geopolitics', label: 'Geopolitics', group: 'Power & Governance' },
  {
    id: 'domestic-politics',
    label: 'Domestic Politics',
    group: 'Power & Governance',
  },
  {
    id: 'military-and-defence',
    label: 'Military & Defence',
    group: 'Power & Governance',
  },
  {
    id: 'law-and-justice',
    label: 'Law & Justice',
    group: 'Power & Governance',
  },
  { id: 'immigration', label: 'Immigration', group: 'Power & Governance' },
  {
    id: 'intelligence-and-surveillance',
    label: 'Intelligence & Surveillance',
    group: 'Power & Governance',
  },
];

const FINANCE_AND_ECONOMY: Category[] = [
  {
    id: 'finance-and-markets',
    label: 'Finance & Markets',
    group: 'Finance & Economy',
  },
  {
    id: 'trade-and-commerce',
    label: 'Trade & Commerce',
    group: 'Finance & Economy',
  },
  {
    id: 'real-estate-and-property',
    label: 'Real Estate & Property',
    group: 'Finance & Economy',
  },
  {
    id: 'cryptocurrency',
    label: 'Cryptocurrency',
    group: 'Finance & Economy',
  },
  {
    id: 'labour-and-employment',
    label: 'Labour & Employment',
    group: 'Finance & Economy',
  },
];

const SCIENCE_AND_TECHNOLOGY: Category[] = [
  {
    id: 'technology-and-innovation',
    label: 'Technology & Innovation',
    group: 'Science & Technology',
  },
  {
    id: 'artificial-intelligence',
    label: 'Artificial Intelligence',
    group: 'Science & Technology',
  },
  {
    id: 'science-and-research',
    label: 'Science & Research',
    group: 'Science & Technology',
  },
  { id: 'energy', label: 'Energy', group: 'Science & Technology' },
];

const SOCIETY_AND_VALUES: Category[] = [
  {
    id: 'social-issues',
    label: 'Social Issues',
    group: 'Society & Values',
  },
  { id: 'education', label: 'Education', group: 'Society & Values' },
  {
    id: 'religion-and-faith',
    label: 'Religion & Faith',
    group: 'Society & Values',
  },
  {
    id: 'crime-and-public-safety',
    label: 'Crime & Public Safety',
    group: 'Society & Values',
  },
  {
    id: 'health-and-medicine',
    label: 'Health & Medicine',
    group: 'Society & Values',
  },
];

const ENVIRONMENT: Category[] = [
  {
    id: 'climate-and-environment',
    label: 'Climate & Environment',
    group: 'Environment',
  },
  {
    id: 'food-and-agriculture',
    label: 'Food & Agriculture',
    group: 'Environment',
  },
];

const CULTURE_AND_ENTERTAINMENT: Category[] = [
  {
    id: 'entertainment',
    label: 'Entertainment',
    group: 'Culture & Entertainment',
  },
  {
    id: 'celebrity-and-personalities',
    label: 'Celebrity & Personalities',
    group: 'Culture & Entertainment',
  },
  {
    id: 'culture-and-arts',
    label: 'Culture & Arts',
    group: 'Culture & Entertainment',
  },
  { id: 'sports', label: 'Sports', group: 'Culture & Entertainment' },
  {
    id: 'fashion-and-style',
    label: 'Fashion & Style',
    group: 'Culture & Entertainment',
  },
  {
    id: 'food-and-lifestyle',
    label: 'Food & Lifestyle',
    group: 'Culture & Entertainment',
  },
  { id: 'travel', label: 'Travel', group: 'Culture & Entertainment' },
  {
    id: 'corruption-and-scandal',
    label: 'Corruption & Scandal',
    group: 'Culture & Entertainment',
  },
];

export const CATEGORIES: Category[] = [
  ...POWER_AND_GOVERNANCE,
  ...FINANCE_AND_ECONOMY,
  ...SCIENCE_AND_TECHNOLOGY,
  ...SOCIETY_AND_VALUES,
  ...ENVIRONMENT,
  ...CULTURE_AND_ENTERTAINMENT,
];

export const CATEGORY_GROUPS: CategoryGroup[] = [
  { name: 'Power & Governance', categories: POWER_AND_GOVERNANCE },
  { name: 'Finance & Economy', categories: FINANCE_AND_ECONOMY },
  { name: 'Science & Technology', categories: SCIENCE_AND_TECHNOLOGY },
  { name: 'Society & Values', categories: SOCIETY_AND_VALUES },
  { name: 'Environment', categories: ENVIRONMENT },
  { name: 'Culture & Entertainment', categories: CULTURE_AND_ENTERTAINMENT },
];
