import type {
  WorldLedger,
  Nation,
  Alliance,
  Conflict,
  Currency,
  Scarcity,
  EnvironmentalCrisis,
  HistoricalEvent,
  StoryThread,
  TechDomain,
  CulturalMovement,
  TradingBloc,
  MilitaryForce,
} from './world-ledger.types.js';

export interface LedgerMutation {
  epoch?: string;
  synopsis?: string;

  // Geopolitics
  addNations?: Nation[];
  updateNations?: (Partial<Nation> & { name: string })[];
  addAlliances?: Alliance[];
  addConflicts?: Conflict[];
  updateConflicts?: (Partial<Conflict> & { name: string })[];

  // Economics
  addCurrencies?: Currency[];
  addTradingBlocs?: TradingBloc[];
  addScarcities?: Scarcity[];
  updateGlobalGdpTrend?: string;

  // Technology
  updateAi?: Partial<TechDomain>;
  updateEnergy?: Partial<TechDomain>;
  updateBiotech?: Partial<TechDomain>;
  addTechDomains?: TechDomain[];

  // Culture
  addDominantNarratives?: string[];
  addMovements?: CulturalMovement[];
  updateMediaLandscape?: string;

  // Military
  addForces?: MilitaryForce[];
  updateForces?: (Partial<MilitaryForce> & { entity: string })[];
  addArmsRaces?: string[];
  addDoctrineShifts?: string[];

  // Environment
  updateTemperatureAnomaly?: number;
  addCrises?: EnvironmentalCrisis[];
  addMitigationEfforts?: string[];

  // Story Threads
  addStoryThreads?: StoryThread[];
  updateStoryThreads?: (Partial<StoryThread> & { name: string })[];

  // History
  addHistoricalEvents?: HistoricalEvent[];
}

export function applyMutation(
  ledger: WorldLedger,
  mutation: LedgerMutation,
): WorldLedger {
  return {
    epoch: mutation.epoch ?? ledger.epoch,
    synopsis: mutation.synopsis ?? ledger.synopsis,

    geopolitics: {
      nations: mergeByKey(
        ledger.geopolitics.nations,
        mutation.addNations,
        mutation.updateNations,
        'name',
      ),
      alliances: append(ledger.geopolitics.alliances, mutation.addAlliances),
      conflicts: mergeByKey(
        ledger.geopolitics.conflicts,
        mutation.addConflicts,
        mutation.updateConflicts,
        'name',
      ),
    },

    economics: {
      currencies: append(ledger.economics.currencies, mutation.addCurrencies),
      tradingBlocs: append(
        ledger.economics.tradingBlocs,
        mutation.addTradingBlocs,
      ),
      scarcities: append(ledger.economics.scarcities, mutation.addScarcities),
      globalGdpTrend:
        mutation.updateGlobalGdpTrend ?? ledger.economics.globalGdpTrend,
    },

    technology: {
      ai: mergeTechDomain(ledger.technology.ai, mutation.updateAi),
      energy: mergeTechDomain(ledger.technology.energy, mutation.updateEnergy),
      biotech: mergeTechDomain(
        ledger.technology.biotech,
        mutation.updateBiotech,
      ),
      other: append(ledger.technology.other, mutation.addTechDomains),
    },

    culture: {
      dominantNarratives: append(
        ledger.culture.dominantNarratives,
        mutation.addDominantNarratives,
      ),
      movements: append(ledger.culture.movements, mutation.addMovements),
      mediaLandscape:
        mutation.updateMediaLandscape ?? ledger.culture.mediaLandscape,
    },

    military: {
      forces: mergeByKey(
        ledger.military.forces,
        mutation.addForces,
        mutation.updateForces,
        'entity',
      ),
      armsRaces: append(ledger.military.armsRaces, mutation.addArmsRaces),
      doctrineShifts: append(
        ledger.military.doctrineShifts,
        mutation.addDoctrineShifts,
      ),
    },

    environment: {
      globalTemperatureAnomaly:
        mutation.updateTemperatureAnomaly ??
        ledger.environment.globalTemperatureAnomaly,
      crises: append(ledger.environment.crises, mutation.addCrises),
      mitigationEfforts: append(
        ledger.environment.mitigationEfforts,
        mutation.addMitigationEfforts,
      ),
    },

    storyThreads: mergeByKey(
      ledger.storyThreads,
      mutation.addStoryThreads,
      mutation.updateStoryThreads,
      'name',
    ),

    history: append(ledger.history, mutation.addHistoricalEvents),
  };
}

function append<T>(existing: T[], additions?: T[]): T[] {
  if (!additions || additions.length === 0) return [...existing];
  return [...existing, ...additions];
}

function mergeByKey<T, K extends keyof T>(
  existing: T[],
  additions: T[] | undefined,
  updates: (Partial<T> & Pick<T, K>)[] | undefined,
  key: K,
): T[] {
  let result = [...existing];

  if (additions && additions.length > 0) {
    result = [...result, ...additions];
  }

  if (updates && updates.length > 0) {
    result = result.map((item) => {
      const update = updates.find((u) => u[key] === item[key]);
      if (update) {
        return { ...item, ...update };
      }
      return item;
    });
  }

  return result;
}

function mergeTechDomain(
  existing: TechDomain,
  update?: Partial<TechDomain>,
): TechDomain {
  if (!update) return { ...existing };
  return { ...existing, ...update };
}
