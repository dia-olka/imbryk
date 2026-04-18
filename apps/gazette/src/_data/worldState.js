/**
 * English world-state for the timeline page.
 *
 * At build time we prefer the live ledger the newsroom-director mirrored to
 * R2 at `_meta/world-ledger.json` after each daily run. Falls back to the
 * compile-time INITIAL_WORLD_LEDGER when R2 is unavailable (local dev, first
 * run before the pipeline has written anything, or R2 fetch error), so the
 * site still builds cleanly in every environment.
 */

import {
  INITIAL_WORLD_LEDGER,
  WorldLedgerSchema,
  serializeLedgerToSynopsis,
} from '@org/world-state';

const R2_PUBLIC_URL = process.env.R2_PUBLIC_URL || '';

async function fetchLiveLedger() {
  if (!R2_PUBLIC_URL) return null;
  try {
    const resp = await fetch(`${R2_PUBLIC_URL}/_meta/world-ledger.json`);
    if (!resp.ok) return null;
    const data = await resp.json();
    const parsed = WorldLedgerSchema.safeParse(data);
    if (!parsed.success) {
      console.warn(
        '[worldState] Live ledger failed schema validation, falling back to INITIAL_WORLD_LEDGER:',
        parsed.error.issues
      );
      return null;
    }
    return parsed.data;
  } catch {
    return null;
  }
}

export default async function () {
  const ledger = (await fetchLiveLedger()) || INITIAL_WORLD_LEDGER;
  return {
    epoch: ledger.epoch,
    synopsis: ledger.synopsis,
    serializedSynopsis: serializeLedgerToSynopsis(ledger),
    geopolitics: ledger.geopolitics,
    economics: ledger.economics,
    technology: ledger.technology,
    culture: ledger.culture,
    military: ledger.military,
    environment: ledger.environment,
    history: [...(ledger.history || [])].reverse(),
  };
}
