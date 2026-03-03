import type { NewsroomPersona } from '@org/ai-personas';
import { interpolateTemplate } from './interpolate.js';

export interface PromptBuildInput {
  persona: NewsroomPersona;
  worldSynopsis: string;
  clusterDigests: string;
}

export interface CuratorBuildInput {
  persona: NewsroomPersona;
  allArticles: string;
}

export function buildNewspaperPrompt(input: PromptBuildInput): string {
  return interpolateTemplate(input.persona.systemPromptTemplate, {
    WORLD_LEDGER_SYNOPSIS: input.worldSynopsis,
    CLUSTER_DIGESTS: input.clusterDigests,
  });
}

export function buildCuratorPrompt(input: CuratorBuildInput): string {
  return interpolateTemplate(input.persona.systemPromptTemplate, {
    ALL_ARTICLES: input.allArticles,
  });
}
