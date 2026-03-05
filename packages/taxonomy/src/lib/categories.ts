import { TAXONOMY_DATA } from './_generated_data.js';
import type { Category, CategoryGroup, CategoryId } from './taxonomy.types.js';

/** Flat list of all valid category ID strings, derived from the shared JSON. */
export const CATEGORY_IDS: CategoryId[] = TAXONOMY_DATA.groups.flatMap((g) =>
  g.categories.map((c) => c.id as CategoryId),
);

/** All categories with their group name attached. */
export const CATEGORIES: Category[] = TAXONOMY_DATA.groups.flatMap((g) =>
  g.categories.map((c) => ({ id: c.id, label: c.label, group: g.name })),
);

/** Grouped view of the taxonomy. */
export const CATEGORY_GROUPS: CategoryGroup[] = TAXONOMY_DATA.groups.map(
  (g) => ({
    name: g.name,
    categories: g.categories.map((c) => ({
      id: c.id,
      label: c.label,
      group: g.name,
    })),
  }),
);

/** Set for O(1) membership checks. */
export const CATEGORY_ID_SET: ReadonlySet<string> = new Set(CATEGORY_IDS);
