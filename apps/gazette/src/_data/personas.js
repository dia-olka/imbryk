import {
  NEWSPAPER_PERSONAS,
  CURATOR_PERSONA,
  ALL_PERSONAS,
} from '@org/ai-personas';
import { getDesignTokens, toCSSCustomProperties } from './designTokens.js';

export default function () {
  return {
    newspapers: NEWSPAPER_PERSONAS.map((p) => {
      const tokens = getDesignTokens(p.id);
      return {
        id: p.id,
        paperName: p.paperName,
        tagline: p.tagline,
        ideology: p.ideology,
        politicalLeaning: p.politicalLeaning,
        writingStyle: p.writingStyle,
        biases: p.biases,
        blindspots: p.blindspots,
        regionalBias: p.regionalBias,
        toneAdjustment: p.toneAdjustment,
        subscribedCategories: p.subscribedCategories,
        modelTier: p.modelTier,
        designTokens: tokens,
        cssVars: toCSSCustomProperties(tokens),
      };
    }),
    curator: (() => {
      const tokens = getDesignTokens(CURATOR_PERSONA.id);
      return {
        id: CURATOR_PERSONA.id,
        paperName: CURATOR_PERSONA.paperName,
        tagline: CURATOR_PERSONA.tagline,
        ideology: CURATOR_PERSONA.ideology,
        politicalLeaning: CURATOR_PERSONA.politicalLeaning,
        writingStyle: CURATOR_PERSONA.writingStyle,
        biases: CURATOR_PERSONA.biases,
        blindspots: CURATOR_PERSONA.blindspots,
        designTokens: tokens,
        cssVars: toCSSCustomProperties(tokens),
      };
    })(),
    all: ALL_PERSONAS.map((p) => {
      const tokens = getDesignTokens(p.id);
      return {
        id: p.id,
        paperName: p.paperName,
        tagline: p.tagline,
        designTokens: tokens,
        cssVars: toCSSCustomProperties(tokens),
      };
    }),
  };
}
