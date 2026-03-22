import { describe, it, expect } from 'vitest';
import { interpolateTemplate } from './interpolate.js';
import { buildNewspaperPrompt, buildCuratorPrompt } from './prompt-builder.js';
import {
  NEWSPAPER_PERSONAS,
  CURATOR_PERSONA,
} from '@org/ai-personas';
import { INITIAL_WORLD_LEDGER } from '@org/world-state';
import { serializeLedgerToSynopsis } from '@org/world-state';

describe('interpolateTemplate', () => {
  it('should replace a single placeholder', () => {
    const result = interpolateTemplate('Hello {{NAME}}!', { NAME: 'World' });
    expect(result).toBe('Hello World!');
  });

  it('should replace multiple placeholders', () => {
    const result = interpolateTemplate('{{GREETING}} {{NAME}}!', {
      GREETING: 'Hello',
      NAME: 'World',
    });
    expect(result).toBe('Hello World!');
  });

  it('should throw on missing value for template placeholder', () => {
    expect(() =>
      interpolateTemplate('Hello {{NAME}} from {{PLACE}}!', { NAME: 'World' })
    ).toThrow('Missing values for template placeholders: PLACE');
  });

  it('should report all missing placeholders at once', () => {
    expect(() =>
      interpolateTemplate('{{A}} and {{B}}', {})
    ).toThrow('Missing values for template placeholders: A, B');
  });

  it('should ignore extra values not in the template', () => {
    const result = interpolateTemplate('Hello {{NAME}}!', {
      NAME: 'World',
      EXTRA: 'unused',
    });
    expect(result).toBe('Hello World!');
  });

  it('should handle templates with no placeholders', () => {
    const result = interpolateTemplate('No placeholders here.', {
      EXTRA: 'unused',
    });
    expect(result).toBe('No placeholders here.');
  });

  it('should replace duplicate placeholders', () => {
    const result = interpolateTemplate('{{X}} and {{X}}', { X: 'same' });
    expect(result).toBe('same and same');
  });
});

describe('buildNewspaperPrompt', () => {
  const worldSynopsis = serializeLedgerToSynopsis(INITIAL_WORLD_LEDGER);
  const clusterDigests = 'Cluster 1: Test digest content';

  it('should return systemInstruction and userContent for each persona', () => {
    for (const persona of NEWSPAPER_PERSONAS) {
      const result = buildNewspaperPrompt({
        persona,
        worldSynopsis,
        clusterDigests,
      });

      // System instruction contains persona identity but no context data
      expect(result.systemInstruction).toContain(persona.paperName);
      expect(result.systemInstruction).not.toContain('{{WORLD_LEDGER_SYNOPSIS}}');
      expect(result.systemInstruction).not.toContain('{{CLUSTER_DIGESTS}}');

      // User content contains context data (WorldLedger first for cache)
      expect(result.userContent).toContain(worldSynopsis);
      expect(result.userContent).toContain(clusterDigests);
      expect(result.userContent).toContain('<task>');
    }
  });

  it('should include editorial journal in userContent when provided', () => {
    const persona = NEWSPAPER_PERSONAS[0];
    const journal = 'Previous edition covered water wars extensively.';
    const result = buildNewspaperPrompt({
      persona,
      worldSynopsis,
      clusterDigests,
      editorialJournal: journal,
    });

    expect(result.userContent).toContain(journal);
  });

  it('should omit editorial journal section when not provided', () => {
    const persona = NEWSPAPER_PERSONAS[0];
    const result = buildNewspaperPrompt({
      persona,
      worldSynopsis,
      clusterDigests,
    });

    expect(result.userContent).not.toContain('EDITORIAL JOURNAL');
  });
});

describe('buildCuratorPrompt', () => {
  it('should produce a valid prompt for Curator', () => {
    const allArticles = 'Article 1: Test article content';
    const result = buildCuratorPrompt({
      persona: CURATOR_PERSONA,
      allArticles,
    });

    expect(result).toContain('The Curator');
    expect(result).toContain(allArticles);
    expect(result).not.toContain('{{ALL_ARTICLES}}');
  });
});

describe('every persona template can be built without error', () => {
  const worldSynopsis = 'Test world synopsis';
  const clusterDigests = 'Test cluster digests';

  it('should build all newspaper persona prompts', () => {
    for (const persona of NEWSPAPER_PERSONAS) {
      expect(() =>
        buildNewspaperPrompt({ persona, worldSynopsis, clusterDigests })
      ).not.toThrow();
    }
  });

  it('should build the Curator prompt', () => {
    expect(() =>
      buildCuratorPrompt({ persona: CURATOR_PERSONA, allArticles: 'test' })
    ).not.toThrow();
  });
});
