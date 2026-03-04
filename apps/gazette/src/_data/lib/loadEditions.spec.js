import { describe, it, expect } from 'vitest';
import { transformR2Edition } from './loadEditions.js';

describe('transformR2Edition', () => {
  it('transforms R2 shape into gazette template shape', () => {
    const r2Edition = {
      edition_id: '2026-03-01',
      date: '2026-03-01',
      articles: {
        sovereign: JSON.stringify({
          newspaper_id: 'sovereign',
          newspaper_name: 'The Sovereign',
          articles: [{ headline: 'Test', body: 'Body' }],
          in_brief: [],
          editors_note: 'Note',
          metadata: {},
        }),
        curator: JSON.stringify({
          synthesis: 'Meta-analysis text',
          themes: ['theme1'],
        }),
      },
    };

    const result = transformR2Edition(r2Edition);

    expect(result.edition_id).toBe('2026-03-01');
    expect(result.date).toBe('2026-03-01');
    expect(result.newspapers).toHaveLength(1);
    expect(result.newspapers[0].newspaper_id).toBe('sovereign');
    expect(result.newspapers[0].articles[0].headline).toBe('Test');
    expect(result.curator_synthesis).toEqual({
      synthesis: 'Meta-analysis text',
      themes: ['theme1'],
    });
  });

  it('handles multiple newspapers', () => {
    const r2Edition = {
      edition_id: '2026-03-01',
      date: '2026-03-01',
      articles: {
        sovereign: JSON.stringify({
          newspaper_name: 'The Sovereign',
          articles: [],
          in_brief: [],
          editors_note: '',
          metadata: {},
        }),
        owner: JSON.stringify({
          newspaper_name: 'The Owner',
          articles: [],
          in_brief: [],
          editors_note: '',
          metadata: {},
        }),
      },
    };

    const result = transformR2Edition(r2Edition);

    expect(result.newspapers).toHaveLength(2);
    const ids = result.newspapers.map((n) => n.newspaper_id);
    expect(ids).toContain('sovereign');
    expect(ids).toContain('owner');
  });

  it('sets newspaper_id if not present in parsed content', () => {
    const r2Edition = {
      edition_id: '2026-03-01',
      date: '2026-03-01',
      articles: {
        radical: JSON.stringify({
          newspaper_name: 'The Radical',
          articles: [],
          in_brief: [],
        }),
      },
    };

    const result = transformR2Edition(r2Edition);

    expect(result.newspapers[0].newspaper_id).toBe('radical');
  });

  it('skips malformed JSON content', () => {
    const r2Edition = {
      edition_id: '2026-03-01',
      date: '2026-03-01',
      articles: {
        sovereign: 'not valid json {{{',
        owner: JSON.stringify({
          newspaper_name: 'The Owner',
          articles: [],
        }),
      },
    };

    const result = transformR2Edition(r2Edition);

    expect(result.newspapers).toHaveLength(1);
    expect(result.newspapers[0].newspaper_id).toBe('owner');
  });

  it('handles empty articles object', () => {
    const r2Edition = {
      edition_id: '2026-03-01',
      date: '2026-03-01',
      articles: {},
    };

    const result = transformR2Edition(r2Edition);

    expect(result.newspapers).toHaveLength(0);
    expect(result.curator_synthesis).toBeNull();
  });

  it('handles missing articles key', () => {
    const r2Edition = {
      edition_id: '2026-03-01',
      date: '2026-03-01',
    };

    const result = transformR2Edition(r2Edition);

    expect(result.newspapers).toHaveLength(0);
    expect(result.curator_synthesis).toBeNull();
  });

  it('handles already-parsed objects (not JSON strings)', () => {
    const r2Edition = {
      edition_id: '2026-03-01',
      date: '2026-03-01',
      articles: {
        sovereign: {
          newspaper_name: 'The Sovereign',
          articles: [{ headline: 'Direct' }],
          in_brief: [],
        },
      },
    };

    const result = transformR2Edition(r2Edition);

    expect(result.newspapers).toHaveLength(1);
    expect(result.newspapers[0].articles[0].headline).toBe('Direct');
  });
});
