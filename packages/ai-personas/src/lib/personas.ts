import { PERSONAS_DATA, SUBSCRIPTIONS_DATA } from './_generated_data.js';
import type { CategoryId } from '@org/taxonomy';
import type { NewsroomPersona } from './persona.types.js';

type RawPersona = (typeof PERSONAS_DATA.personas)[number];

/** Build the full system prompt from preamble + persona suffix. */
function buildPrompt(raw: RawPersona, preamble: string): string {
  if (raw.curatorPrompt) return raw.curatorPrompt;
  if (!raw.promptSuffix) return '';
  return `${preamble}\n\n${raw.promptSuffix}`;
}

/** Resolve a persona's subscribed categories from the taxonomy data. */
function getSubscribedCategories(personaId: string): CategoryId[] {
  const subs = (SUBSCRIPTIONS_DATA as Record<string, readonly string[]>)[
    personaId
  ];
  return (subs ?? []) as CategoryId[];
}

function toPersona(raw: RawPersona): NewsroomPersona {
  return {
    id: raw.id,
    paperName: raw.paperName,
    tagline: raw.tagline,
    ideology: raw.ideology,
    politicalLeaning: raw.politicalLeaning,
    writingStyle: raw.writingStyle,
    biases: [...raw.biases],
    blindspots: [...raw.blindspots],
    regionalBias: raw.regionalBias,
    toneAdjustment: raw.toneAdjustment,
    subscribedCategories: getSubscribedCategories(raw.id),
    modelTier: raw.modelTier,
    systemPromptTemplate: buildPrompt(raw, PERSONAS_DATA.preamble),
  };
}

const allPersonas = PERSONAS_DATA.personas.map(toPersona);

function findPersona(id: string): NewsroomPersona {
  const p = allPersonas.find((persona) => persona.id === id);
  if (!p) throw new Error(`Persona not found: ${id}`);
  return p;
}

export const SOVEREIGN: NewsroomPersona = findPersona('sovereign');
export const ASPIRANT: NewsroomPersona = findPersona('aspirant');
export const OWNER: NewsroomPersona = findPersona('owner');
export const MORALIST: NewsroomPersona = findPersona('moralist');
export const RADICAL: NewsroomPersona = findPersona('radical');
export const HEDONIST: NewsroomPersona = findPersona('hedonist');
export const CURATOR: NewsroomPersona = findPersona('curator');

export const NEWSPAPER_PERSONAS: NewsroomPersona[] = [
  SOVEREIGN,
  ASPIRANT,
  OWNER,
  MORALIST,
  RADICAL,
  HEDONIST,
];

export const CURATOR_PERSONA: NewsroomPersona = CURATOR;

export const ALL_PERSONAS: NewsroomPersona[] = [...NEWSPAPER_PERSONAS, CURATOR];
