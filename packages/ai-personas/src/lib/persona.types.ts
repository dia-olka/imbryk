import type { CategoryId } from '@org/taxonomy';

export interface NewsroomPersona {
  id: string;
  paperName: string;
  tagline: string;
  ideology: string;
  politicalLeaning: string;
  writingStyle: string;
  biases: string[];
  blindspots: string[];
  regionalBias: string;
  toneAdjustment: string;
  subscribedCategories: CategoryId[];
  modelTier: 'pro' | 'flash';
  systemPromptTemplate: string;
}
