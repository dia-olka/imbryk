import type { WorldLedger } from './world-ledger.types.js';
import { WORLD_LEDGER_SCHEMA_VERSION } from './world-ledger.schemas.js';

export const WORLD_LEDGER_TEMPLATE: WorldLedger = {
  schemaVersion: WORLD_LEDGER_SCHEMA_VERSION,
  epoch: '',
  synopsis: '',
  geopolitics: {
    nations: [],
    alliances: [],
    conflicts: [],
  },
  economics: {
    currencies: [],
    tradingBlocs: [],
    scarcities: [],
    globalGdpTrend: '',
  },
  technology: {
    ai: {
      name: 'Artificial Intelligence',
      maturityLevel: 'emerging',
      keyPlayers: [],
      description: '',
    },
    energy: {
      name: 'Energy',
      maturityLevel: 'emerging',
      keyPlayers: [],
      description: '',
    },
    biotech: {
      name: 'Biotechnology',
      maturityLevel: 'emerging',
      keyPlayers: [],
      description: '',
    },
    other: [],
  },
  culture: {
    dominantNarratives: [],
    movements: [],
    mediaLandscape: '',
  },
  military: {
    forces: [],
    armsRaces: [],
    doctrineShifts: [],
  },
  environment: {
    globalTemperatureAnomaly: 0,
    crises: [],
    mitigationEfforts: [],
  },
  storyThreads: [],
  history: [],
};
