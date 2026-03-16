import { z } from 'zod';

// ── Geopolitics ─────────────────────────────────────────────────────

const NationSchema = z.object({
  name: z.string(),
  governmentType: z.string(),
  leader: z.string(),
  stability: z.number().int().min(0).max(100),
  description: z.string(),
});

const AllianceSchema = z.object({
  name: z.string(),
  members: z.array(z.string()),
  purpose: z.string(),
});

const ConflictSchema = z.object({
  name: z.string(),
  parties: z.array(z.string()),
  status: z.enum(['active', 'frozen', 'resolved']),
  description: z.string(),
});

const GeopoliticsStateSchema = z.object({
  nations: z.array(NationSchema),
  alliances: z.array(AllianceSchema),
  conflicts: z.array(ConflictSchema),
});

// ── Economics ────────────────────────────────────────────────────────

const CurrencySchema = z.object({
  name: z.string(),
  issuingEntity: z.string(),
  strength: z.number().int().min(0).max(100),
  description: z.string(),
});

const TradingBlocSchema = z.object({
  name: z.string(),
  members: z.array(z.string()),
  focus: z.string(),
});

const ScarcitySchema = z.object({
  resource: z.string(),
  severity: z.enum(['low', 'moderate', 'critical']),
  affectedRegions: z.array(z.string()),
  description: z.string(),
});

const EconomicsStateSchema = z.object({
  currencies: z.array(CurrencySchema),
  tradingBlocs: z.array(TradingBlocSchema),
  scarcities: z.array(ScarcitySchema),
  globalGdpTrend: z.string(),
});

// ── Technology ───────────────────────────────────────────────────────

const TechDomainSchema = z.object({
  name: z.string(),
  maturityLevel: z.enum(['emerging', 'growth', 'mature', 'declining']),
  keyPlayers: z.array(z.string()),
  description: z.string(),
});

const TechnologyStateSchema = z.object({
  ai: TechDomainSchema,
  energy: TechDomainSchema,
  biotech: TechDomainSchema,
  other: z.array(TechDomainSchema),
});

// ── Culture ──────────────────────────────────────────────────────────

const CulturalMovementSchema = z.object({
  name: z.string(),
  reach: z.enum(['local', 'regional', 'global']),
  description: z.string(),
});

const CultureStateSchema = z.object({
  dominantNarratives: z.array(z.string()),
  movements: z.array(CulturalMovementSchema),
  mediaLandscape: z.string(),
});

// ── Military ─────────────────────────────────────────────────────────

const MilitaryForceSchema = z.object({
  entity: z.string(),
  conventionalStrength: z.number().int().min(0).max(100),
  nuclearCapable: z.boolean(),
  specialCapabilities: z.array(z.string()),
});

const MilitaryStateSchema = z.object({
  forces: z.array(MilitaryForceSchema),
  armsRaces: z.array(z.string()),
  doctrineShifts: z.array(z.string()),
});

// ── Environment ──────────────────────────────────────────────────────

const EnvironmentalCrisisSchema = z.object({
  name: z.string(),
  severity: z.enum(['low', 'moderate', 'severe', 'catastrophic']),
  affectedRegions: z.array(z.string()),
  description: z.string(),
});

const EnvironmentStateSchema = z.object({
  globalTemperatureAnomaly: z.number(),
  crises: z.array(EnvironmentalCrisisSchema),
  mitigationEfforts: z.array(z.string()),
});

// ── Story Threads ────────────────────────────────────────────────────

const StoryThreadSchema = z.object({
  name: z.string(),
  status: z.enum(['developing', 'ongoing', 'resolved']),
  started: z.string(),
  lastCovered: z.string(),
  summary: z.string(),
  relatedNations: z.array(z.string()),
  sectors: z.array(z.string()),
});

// ── History ──────────────────────────────────────────────────────────

const HistoricalEventSchema = z.object({
  date: z.string(),
  headline: z.string(),
  description: z.string(),
  impact: z.string(),
  sectors: z.array(z.string()),
});

// ── WorldLedger ──────────────────────────────────────────────────────

const WorldLedgerSchema = z.object({
  epoch: z.string(),
  synopsis: z.string(),
  geopolitics: GeopoliticsStateSchema,
  economics: EconomicsStateSchema,
  technology: TechnologyStateSchema,
  culture: CultureStateSchema,
  military: MilitaryStateSchema,
  environment: EnvironmentStateSchema,
  storyThreads: z.array(StoryThreadSchema),
  history: z.array(HistoricalEventSchema),
});

export {
  NationSchema,
  AllianceSchema,
  ConflictSchema,
  GeopoliticsStateSchema,
  CurrencySchema,
  TradingBlocSchema,
  ScarcitySchema,
  EconomicsStateSchema,
  TechDomainSchema,
  TechnologyStateSchema,
  CulturalMovementSchema,
  CultureStateSchema,
  MilitaryForceSchema,
  MilitaryStateSchema,
  EnvironmentalCrisisSchema,
  EnvironmentStateSchema,
  StoryThreadSchema,
  HistoricalEventSchema,
  WorldLedgerSchema,
};
