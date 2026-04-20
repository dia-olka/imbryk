export interface Nation {
  name: string;
  governmentType: string;
  leader: string;
  stability: number;
  description: string;
}

export interface Alliance {
  name: string;
  members: string[];
  purpose: string;
}

export interface Conflict {
  name: string;
  parties: string[];
  status: 'active' | 'frozen' | 'resolved';
  description: string;
}

export interface GeopoliticsState {
  nations: Nation[];
  alliances: Alliance[];
  conflicts: Conflict[];
}

export interface Currency {
  name: string;
  issuingEntity: string;
  strength: number;
  description: string;
}

export interface TradingBloc {
  name: string;
  members: string[];
  focus: string;
}

export interface Scarcity {
  resource: string;
  severity: 'low' | 'moderate' | 'critical';
  affectedRegions: string[];
  description: string;
}

export interface EconomicsState {
  currencies: Currency[];
  tradingBlocs: TradingBloc[];
  scarcities: Scarcity[];
  globalGdpTrend: string;
}

export interface TechDomain {
  name: string;
  maturityLevel: 'emerging' | 'growth' | 'mature' | 'declining';
  keyPlayers: string[];
  description: string;
}

export interface TechnologyState {
  ai: TechDomain;
  energy: TechDomain;
  biotech: TechDomain;
  other: TechDomain[];
}

export interface CulturalMovement {
  name: string;
  reach: 'local' | 'regional' | 'global';
  description: string;
}

export interface CultureState {
  dominantNarratives: string[];
  movements: CulturalMovement[];
  mediaLandscape: string;
}

export interface MilitaryForce {
  entity: string;
  conventionalStrength: number;
  nuclearCapable: boolean;
  specialCapabilities: string[];
}

export interface MilitaryState {
  forces: MilitaryForce[];
  armsRaces: string[];
  doctrineShifts: string[];
}

export interface EnvironmentalCrisis {
  name: string;
  severity: 'low' | 'moderate' | 'severe' | 'catastrophic';
  affectedRegions: string[];
  description: string;
}

export interface EnvironmentState {
  globalTemperatureAnomaly: number;
  crises: EnvironmentalCrisis[];
  mitigationEfforts: string[];
}

export interface HistoricalEvent {
  date: string;
  headline: string;
  description: string;
  impact: string;
  sectors: string[];
}

export interface StoryThread {
  name: string;
  status: 'developing' | 'ongoing' | 'resolved';
  started: string;
  lastCovered: string;
  summary: string;
  relatedNations: string[];
  sectors: string[];
}

export interface WorldLedger {
  schemaVersion: '1.0.0';
  epoch: string;
  synopsis: string;
  geopolitics: GeopoliticsState;
  economics: EconomicsState;
  technology: TechnologyState;
  culture: CultureState;
  military: MilitaryState;
  environment: EnvironmentState;
  storyThreads: StoryThread[];
  history: HistoricalEvent[];
}
