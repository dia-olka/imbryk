import { describe, it, expect } from 'vitest';
import {
  ALL_PERSONAS,
  NEWSPAPER_PERSONAS,
  CURATOR,
} from './personas.js';

describe('Personas', () => {
  it('should have 7 total personas', () => {
    expect(ALL_PERSONAS).toHaveLength(7);
  });

  it('should have 6 newspaper personas', () => {
    expect(NEWSPAPER_PERSONAS).toHaveLength(6);
  });

  it('should have a curator with no ideology', () => {
    expect(CURATOR.ideology).toContain('None');
  });

  it('should have unique IDs across all personas', () => {
    const ids = ALL_PERSONAS.map((p) => p.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('should have subscribedCategories on every persona', () => {
    for (const persona of ALL_PERSONAS) {
      expect(persona.subscribedCategories).toBeDefined();
      expect(Array.isArray(persona.subscribedCategories)).toBe(true);
    }
  });

  it('should have modelTier on every persona', () => {
    for (const persona of ALL_PERSONAS) {
      expect(['pro', 'flash']).toContain(persona.modelTier);
    }
  });

  it('should have regionalBias on every persona', () => {
    for (const persona of ALL_PERSONAS) {
      expect(persona.regionalBias).toBeTruthy();
    }
  });

  it('should have toneAdjustment on every persona', () => {
    for (const persona of ALL_PERSONAS) {
      expect(persona.toneAdjustment).toBeTruthy();
    }
  });

  it('should have newspaper personas use {{CLUSTER_DIGESTS}} in system prompts', () => {
    for (const persona of NEWSPAPER_PERSONAS) {
      expect(persona.systemPromptTemplate).toContain('{{CLUSTER_DIGESTS}}');
      expect(persona.systemPromptTemplate).not.toContain(
        '{{EVENT_DESCRIPTION}}',
      );
    }
  });

  it('should have Curator template use {{ALL_ARTICLES}}', () => {
    expect(CURATOR.systemPromptTemplate).toContain('{{ALL_ARTICLES}}');
  });

  it('should have Curator template not use {{SIX_ARTICLES}}', () => {
    expect(CURATOR.systemPromptTemplate).not.toContain('{{SIX_ARTICLES}}');
  });

  it('should have Sovereign and Owner as pro tier', () => {
    const sovereign = ALL_PERSONAS.find((p) => p.id === 'sovereign');
    const owner = ALL_PERSONAS.find((p) => p.id === 'owner');
    expect(sovereign?.modelTier).toBe('pro');
    expect(owner?.modelTier).toBe('pro');
  });

  it('should have Curator as pro tier', () => {
    expect(CURATOR.modelTier).toBe('flash');
  });
});
