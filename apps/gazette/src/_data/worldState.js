import {
  INITIAL_WORLD_LEDGER,
  serializeLedgerToSynopsis,
} from '@org/world-state';

export default function () {
  const ledger = INITIAL_WORLD_LEDGER;
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
    history: [...ledger.history].reverse(),
  };
}
