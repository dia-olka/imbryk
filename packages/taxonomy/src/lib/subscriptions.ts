import { TAXONOMY_DATA } from './_generated_data.js';
import type { CategoryId, NewspaperSubscription } from './taxonomy.types.js';

function buildSubscriptions(): NewspaperSubscription[] {
  return Object.entries(TAXONOMY_DATA.subscriptions).map(
    ([newspaperId, categoryIds]) => ({
      newspaperId,
      categoryIds: categoryIds as unknown as CategoryId[],
    }),
  );
}

const allSubscriptions = buildSubscriptions();

function findSub(id: string): NewspaperSubscription {
  const sub = allSubscriptions.find((s) => s.newspaperId === id);
  if (!sub) throw new Error(`No subscription found for newspaper: ${id}`);
  return sub;
}

export const SOVEREIGN_SUBSCRIPTION: NewspaperSubscription =
  findSub('sovereign');
export const ASPIRANT_SUBSCRIPTION: NewspaperSubscription = findSub('aspirant');
export const OWNER_SUBSCRIPTION: NewspaperSubscription = findSub('owner');
export const MORALIST_SUBSCRIPTION: NewspaperSubscription = findSub('moralist');
export const RADICAL_SUBSCRIPTION: NewspaperSubscription = findSub('radical');
export const HEDONIST_SUBSCRIPTION: NewspaperSubscription = findSub('hedonist');

export const NEWSPAPER_SUBSCRIPTIONS: NewspaperSubscription[] =
  allSubscriptions;
