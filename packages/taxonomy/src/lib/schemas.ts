import { z } from 'zod';

// ── Taxonomy JSON schema ────────────────────────────────────────────
const CategorySchema = z.object({
  id: z.string(),
  label: z.string(),
});

const CategoryGroupSchema = z.object({
  name: z.string(),
  categories: z.array(CategorySchema),
});

const TaxonomySchema = z.object({
  groups: z.array(CategoryGroupSchema),
  subscriptions: z.record(z.string(), z.array(z.string())),
});

// ── Persona JSON schema ─────────────────────────────────────────────
const PersonaSchema = z.object({
  id: z.string(),
  paperName: z.string(),
  tagline: z.string(),
  ideology: z.string(),
  politicalLeaning: z.string(),
  writingStyle: z.string(),
  biases: z.array(z.string()),
  blindspots: z.array(z.string()),
  regionalBias: z.string(),
  toneAdjustment: z.string(),
  modelTier: z.enum(['pro', 'flash']),
  promptSuffix: z.string().nullable(),
  curatorPrompt: z.string().optional(),
});

const PersonasFileSchema = z.object({
  preamble: z.string(),
  personas: z.array(PersonaSchema),
});

export {
  TaxonomySchema,
  PersonasFileSchema,
  PersonaSchema,
  CategorySchema,
  CategoryGroupSchema,
};

export type TaxonomyData = z.infer<typeof TaxonomySchema>;
export type PersonasData = z.infer<typeof PersonasFileSchema>;
export type RawPersona = z.infer<typeof PersonaSchema>;
