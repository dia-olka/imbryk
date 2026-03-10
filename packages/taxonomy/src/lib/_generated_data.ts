/* Auto-generated from data/taxonomy.json
 * DO NOT EDIT — run `npx nx run taxonomy:generate-data` to regenerate. */

 

export const TAXONOMY_DATA = {
  groups: [
    {
      name: 'Power & Governance',
      categories: [
        {
          id: 'geopolitics-and-diplomacy',
          label: 'Geopolitics & Diplomacy',
        },
        {
          id: 'domestic-politics-and-policy',
          label: 'Domestic Politics & Policy',
        },
        {
          id: 'military-and-defence',
          label: 'Military & Defence',
        },
        {
          id: 'law-and-justice',
          label: 'Law & Justice',
        },
        {
          id: 'immigration-and-borders',
          label: 'Immigration & Borders',
        },
      ],
    },
    {
      name: 'Wealth & Economy',
      categories: [
        {
          id: 'markets-and-macroeconomics',
          label: 'Markets & Macroeconomics',
        },
        {
          id: 'trade-and-supply-chains',
          label: 'Trade & Supply Chains',
        },
        {
          id: 'real-estate-and-urbanism',
          label: 'Real Estate & Urbanism',
        },
        {
          id: 'crypto-and-decentralization',
          label: 'Crypto & Decentralization',
        },
        {
          id: 'labor-and-automation',
          label: 'Labor & Automation',
        },
      ],
    },
    {
      name: 'Science & The Frontier',
      categories: [
        {
          id: 'artificial-intelligence',
          label: 'Artificial Intelligence',
        },
        {
          id: 'space-and-aerospace',
          label: 'Space & Aerospace',
        },
        {
          id: 'energy-and-transition',
          label: 'Energy & Transition',
        },
        {
          id: 'science-and-biohacking',
          label: 'Science & Bio-hacking',
        },
        {
          id: 'fringe-and-the-unexplained',
          label: 'Fringe & The Unexplained',
        },
      ],
    },
    {
      name: 'Society & Information',
      categories: [
        {
          id: 'digital-culture-and-creators',
          label: 'Digital Culture & Creators',
        },
        {
          id: 'media-and-propaganda',
          label: 'Media & Propaganda',
        },
        {
          id: 'social-movements-and-rights',
          label: 'Social Movements & Rights',
        },
        {
          id: 'religion-and-heritage',
          label: 'Religion & Heritage',
        },
        {
          id: 'crime-and-security',
          label: 'Crime & Security',
        },
      ],
    },
    {
      name: 'Environment & Resources',
      categories: [
        {
          id: 'climate-and-ecology',
          label: 'Climate & Ecology',
        },
        {
          id: 'disasters-and-extremes',
          label: 'Disasters & Extremes',
        },
        {
          id: 'agriculture-and-water',
          label: 'Agriculture & Water',
        },
        {
          id: 'global-health-and-pandemics',
          label: 'Global Health & Pandemics',
        },
      ],
    },
    {
      name: 'Culture & Spectacle',
      categories: [
        {
          id: 'entertainment-and-hollywood',
          label: 'Entertainment & Hollywood',
        },
        {
          id: 'sports-and-nationalism',
          label: 'Sports & Nationalism',
        },
        {
          id: 'gaming-and-virtual-worlds',
          label: 'Gaming & Virtual Worlds',
        },
        {
          id: 'arts-and-counter-culture',
          label: 'Arts & Counter-Culture',
        },
        {
          id: 'fashion-and-lifestyle',
          label: 'Fashion & Lifestyle',
        },
        {
          id: 'corruption-and-scandal',
          label: 'Corruption & Scandal',
        },
      ],
    },
  ],
  subscriptions: {
    sovereign: [
      'geopolitics-and-diplomacy',
      'domestic-politics-and-policy',
      'military-and-defence',
      'law-and-justice',
      'trade-and-supply-chains',
      'artificial-intelligence',
      'space-and-aerospace',
      'energy-and-transition',
      'media-and-propaganda',
      'disasters-and-extremes',
    ],
    aspirant: [
      'geopolitics-and-diplomacy',
      'immigration-and-borders',
      'artificial-intelligence',
      'science-and-biohacking',
      'social-movements-and-rights',
      'climate-and-ecology',
      'disasters-and-extremes',
      'agriculture-and-water',
      'global-health-and-pandemics',
      'arts-and-counter-culture',
    ],
    owner: [
      'domestic-politics-and-policy',
      'markets-and-macroeconomics',
      'trade-and-supply-chains',
      'real-estate-and-urbanism',
      'crypto-and-decentralization',
      'labor-and-automation',
      'artificial-intelligence',
      'energy-and-transition',
      'agriculture-and-water',
      'gaming-and-virtual-worlds',
    ],
    moralist: [
      'domestic-politics-and-policy',
      'law-and-justice',
      'immigration-and-borders',
      'religion-and-heritage',
      'crime-and-security',
      'agriculture-and-water',
      'global-health-and-pandemics',
      'sports-and-nationalism',
      'entertainment-and-hollywood',
    ],
    radical: [
      'domestic-politics-and-policy',
      'immigration-and-borders',
      'crypto-and-decentralization',
      'labor-and-automation',
      'fringe-and-the-unexplained',
      'digital-culture-and-creators',
      'media-and-propaganda',
      'crime-and-security',
      'corruption-and-scandal',
    ],
    hedonist: [
      'digital-culture-and-creators',
      'media-and-propaganda',
      'crime-and-security',
      'entertainment-and-hollywood',
      'sports-and-nationalism',
      'gaming-and-virtual-worlds',
      'arts-and-counter-culture',
      'fashion-and-lifestyle',
      'corruption-and-scandal',
    ],
  },
} as const;
