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
  metadata: z.record(z.unknown()).optional(),
});

export const R2EditionSchema = z.object({
  edition_id: z.string().min(1),
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Must be YYYY-MM-DD'),
  articles: z.record(z.union([z.string(), z.record(z.unknown())])).optional(),
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
  metadata: z.record(z.unknown()).optional(),
});

export const EditionSchema = z.object({
  edition_id: z.string().min(1),
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Must be YYYY-MM-DD'),
  newspapers: z.array(NewspaperSchema),
  curator_synthesis: z.record(z.unknown()).nullable().optional(),
});

// ─── Inferred types ────────────────────────────────────────────────────────

export type R2IndexEntry = z.infer<typeof R2IndexEntrySchema>;
export type R2Article = z.infer<typeof R2ArticleSchema>;
export type R2NewspaperContent = z.infer<typeof R2NewspaperContentSchema>;
export type R2Edition = z.infer<typeof R2EditionSchema>;
export type Article = z.infer<typeof ArticleSchema>;
export type Newspaper = z.infer<typeof NewspaperSchema>;
export type Edition = z.infer<typeof EditionSchema>;
