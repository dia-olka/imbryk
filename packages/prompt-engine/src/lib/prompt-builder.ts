import type { NewsroomPersona } from '@org/ai-personas';
import { interpolateTemplate } from './interpolate.js';

export interface PromptBuildInput {
  persona: NewsroomPersona;
  worldSynopsis: string;
  clusterDigests: string;
  editorialJournal?: string;
}

export interface NewspaperPromptOutput {
  /** Persona identity, voice, rules, exemplars — passed as system_instruction. */
  systemInstruction: string;
  /** World state + journal + clusters + task — passed as user content. */
  userContent: string;
}

export interface CuratorBuildInput {
  persona: NewsroomPersona;
  allArticles: string;
}

/**
 * Build the system instruction and user content for a newspaper generation call.
 *
 * System instruction = persona template (no context data, for caching).
 * User content = WorldLedger (first, for prefix cache) + journal + clusters + task.
 */
export function buildNewspaperPrompt(input: PromptBuildInput): NewspaperPromptOutput {
  const systemInstruction = input.persona.systemPromptTemplate;

  const userParts: string[] = [`WORLD HISTORY:\n${input.worldSynopsis}`];
  const journal = input.editorialJournal;
  if (journal) {
    userParts.push(
      'YOUR EDITORIAL JOURNAL (recent entries — use these to inform your ' +
        'editorial decisions today, but do not reference the journal itself ' +
        'in your articles):\n' +
        journal
    );
  }
  userParts.push(`CLUSTER DIGESTS:\n${input.clusterDigests}`);
  userParts.push(
    '<task>\nBased on the context and clusters above, produce ' +
      "today's edition. Follow all rules in your system instruction.\n</task>"
  );

  return {
    systemInstruction,
    userContent: userParts.join('\n\n'),
  };
}

export function buildCuratorPrompt(input: CuratorBuildInput): string {
  return interpolateTemplate(input.persona.systemPromptTemplate, {
    ALL_ARTICLES: input.allArticles,
  });
}
