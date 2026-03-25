import { z } from 'zod';

// ─── R2 raw shapes ─────────────────────────────────────────────────────────

export const R2IndexEntrySchema = z.object({
  edition_id: z.string().min(1),
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Must be YYYY-MM-DD'),
});

export const R2ArticleSchema = z.object({
  headline: z.string().min(1),
  body: z.string(),
  length: z.number().optional(),
  clusters: z.array(z.number()).optional(),
  weight: z.number().optional(),
  word_count: z.number().optional(),
  imagePrompt: z.string().nullable().optional(),
  image_url: z.string().nullable().optional(),
});

export const R2InBriefSchema = z.object({
  headline: z.string().min(1),
  summary: z.string(),
  clusters: z.array(z.number()).optional(),
});

export const R2NewspaperContentSchema = z.object({
  newspaper_id: z.string().optional(),
  newspaper_name: z.string().min(1),
  frontPageImagePrompt: z.string().nullable().optional(),
  heroImageUrl: z.string().nullable().optional(),
  articles: z.array(R2ArticleSchema),
  in_brief: z.array(R2InBriefSchema).optional(),
  editors_note: z.string().optional(),
  metadata: z.record(z.string(), z.unknown()).optional(),
});

export const R2EditionSchema = z.object({
  edition_id: z.string().min(1),
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Must be YYYY-MM-DD'),
  articles: z.record(z.string(), z.union([z.string(), z.record(z.string(), z.unknown())])).optional(),
});

// ─── Gazette template shapes (post-transform) ──────────────────────────────

export const ArticleSchema = z.object({
  headline: z.string().min(1),
  body: z.string(),
  length: z.number().optional(),
  clusters: z.array(z.number()).optional(),
  weight: z.number().optional(),
  word_count: z.number().optional(),
  imagePrompt: z.string().nullable().optional(),
  image_url: z.string().nullable().optional(),
});

export const InBriefSchema = z.object({
  headline: z.string().min(1),
  summary: z.string(),
  clusters: z.array(z.number()).optional(),
});

export const NewspaperSchema = z.object({
  newspaper_id: z.string().min(1),
  newspaper_name: z.string().min(1),
  frontPageImagePrompt: z.string().nullable().optional(),
  heroImageUrl: z.string().nullable().optional(),
  articles: z.array(ArticleSchema),
  in_brief: z.array(InBriefSchema).optional(),
  editors_note: z.string().optional(),
  metadata: z.record(z.string(), z.unknown()).optional(),
});

// ─── Curator synthesis schemas (versioned) ─────────────────────────────────

/** V1: plain string lists (original format). */
export const CuratorSynthesisV1Schema = z.object({
  consensus: z.array(z.string()),
  fault_lines: z.array(z.string()),
  uncovered_angles: z.array(z.string()).optional(),
  what_to_watch: z.array(z.string()).optional(),
});

/** V2: structured analysis with spectrum stance scores. */
export const FaultLineStanceSchema = z.object({
  newspaper_id: z.string().min(1),
  score: z.number().min(0).max(100),
});

export const FaultLineItemSchema = z.object({
  topic: z.string().min(1),
  label_left: z.string().min(1),
  label_right: z.string().min(1),
  stances: z.array(FaultLineStanceSchema),
  summary: z.string(),
});

export const ConsensusItemSchema = z.object({
  text: z.string().min(1),
  voices: z.array(z.string()),
});

export const GapItemSchema = z.object({
  topic: z.string().min(1),
  description: z.string(),
});

export const CuratorSynthesisV2Schema = z.object({
  version: z.literal(2),
  consensus: z.array(ConsensusItemSchema),
  fault_lines: z.array(FaultLineItemSchema),
  gaps: z.array(GapItemSchema),
  what_to_watch: z.array(z.string()).optional(),
});

/** Legacy: free-form text (pre-structured format). */
export const CuratorSynthesisLegacySchema = z.object({
  text: z.string().optional(),
  analysis: z.string().optional(),
});

/** Union of all curator synthesis versions. */
export const CuratorSynthesisSchema = z.union([
  CuratorSynthesisV2Schema,
  CuratorSynthesisV1Schema,
  CuratorSynthesisLegacySchema,
  z.record(z.string(), z.unknown()),
]);

export const EditionSchema = z.object({
  edition_id: z.string().min(1),
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Must be YYYY-MM-DD'),
  newspapers: z.array(NewspaperSchema),
  curator_synthesis: CuratorSynthesisSchema.nullable().optional(),
});

// ─── Inferred types ────────────────────────────────────────────────────────

export type R2IndexEntry = z.infer<typeof R2IndexEntrySchema>;
export type R2Article = z.infer<typeof R2ArticleSchema>;
export type R2NewspaperContent = z.infer<typeof R2NewspaperContentSchema>;
export type R2Edition = z.infer<typeof R2EditionSchema>;
export type Article = z.infer<typeof ArticleSchema>;
export type Newspaper = z.infer<typeof NewspaperSchema>;
export type Edition = z.infer<typeof EditionSchema>;
export type CuratorSynthesisV1 = z.infer<typeof CuratorSynthesisV1Schema>;
export type CuratorSynthesisV2 = z.infer<typeof CuratorSynthesisV2Schema>;
export type CuratorSynthesis = z.infer<typeof CuratorSynthesisSchema>;
