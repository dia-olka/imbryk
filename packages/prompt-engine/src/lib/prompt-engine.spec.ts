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

  it('should produce a valid prompt for each newspaper persona', () => {
    for (const persona of NEWSPAPER_PERSONAS) {
      const result = buildNewspaperPrompt({
        persona,
        worldSynopsis,
        clusterDigests,
      });

      expect(result).toContain(persona.paperName);
      expect(result).toContain(worldSynopsis);
      expect(result).toContain(clusterDigests);
      expect(result).not.toContain('{{WORLD_LEDGER_SYNOPSIS}}');
      expect(result).not.toContain('{{CLUSTER_DIGESTS}}');
    }
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

describe('every persona template can be interpolated without error', () => {
  const worldSynopsis = 'Test world synopsis';
  const clusterDigests = 'Test cluster digests';

  it('should interpolate all newspaper persona templates', () => {
    for (const persona of NEWSPAPER_PERSONAS) {
      expect(() =>
        buildNewspaperPrompt({ persona, worldSynopsis, clusterDigests })
      ).not.toThrow();
    }
  });

  it('should interpolate the Curator template', () => {
    expect(() =>
      buildCuratorPrompt({ persona: CURATOR_PERSONA, allArticles: 'test' })
    ).not.toThrow();
  });
});
