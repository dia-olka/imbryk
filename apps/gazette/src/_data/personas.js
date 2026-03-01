import {
  NEWSPAPER_PERSONAS,
  CURATOR_PERSONA,
  ALL_PERSONAS,
} from '@org/ai-personas';

export default function () {
  return {
    newspapers: NEWSPAPER_PERSONAS.map((p) => ({
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
    })),
    curator: {
      id: CURATOR_PERSONA.id,
      paperName: CURATOR_PERSONA.paperName,
      tagline: CURATOR_PERSONA.tagline,
      ideology: CURATOR_PERSONA.ideology,
      politicalLeaning: CURATOR_PERSONA.politicalLeaning,
      writingStyle: CURATOR_PERSONA.writingStyle,
      biases: CURATOR_PERSONA.biases,
      blindspots: CURATOR_PERSONA.blindspots,
    },
    all: ALL_PERSONAS.map((p) => ({
      id: p.id,
      paperName: p.paperName,
      tagline: p.tagline,
    })),
  };
}
