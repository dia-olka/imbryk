import { describe, it, expect, vi, beforeEach } from 'vitest';
import { transformR2Edition } from './loadEditions.js';

// ─── transformR2Edition ────────────────────────────────────────────────────

describe('transformR2Edition', () => {
  it('transforms R2 shape into gazette template shape', async () => {
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

    const result = await transformR2Edition(r2Edition, 'https://r2.example.com/editions/2026-03-01/test.json');

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

  it('handles multiple newspapers', async () => {
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

    const result = await transformR2Edition(r2Edition, 'https://r2.example.com/editions/2026-03-01/test.json');

    expect(result.newspapers).toHaveLength(2);
    const ids = result.newspapers.map((n) => n.newspaper_id);
    expect(ids).toContain('sovereign');
    expect(ids).toContain('owner');
  });

  it('sets newspaper_id if not present in parsed content', async () => {
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

    const result = await transformR2Edition(r2Edition, 'fixture');

    expect(result.newspapers[0].newspaper_id).toBe('radical');
  });

  it('skips malformed JSON content', async () => {
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

    const result = await transformR2Edition(r2Edition, 'https://r2.example.com/editions/2026-03-01/test.json');

    expect(result.newspapers).toHaveLength(1);
    expect(result.newspapers[0].newspaper_id).toBe('owner');
  });

  it('handles empty articles object', async () => {
    const r2Edition = {
      edition_id: '2026-03-01',
      date: '2026-03-01',
      articles: {},
    };

    const result = await transformR2Edition(r2Edition, 'fixture');

    expect(result.newspapers).toHaveLength(0);
    expect(result.curator_synthesis).toBeNull();
  });

  it('handles missing articles key', async () => {
    const r2Edition = {
      edition_id: '2026-03-01',
      date: '2026-03-01',
    };

    const result = await transformR2Edition(r2Edition, 'fixture');

    expect(result.newspapers).toHaveLength(0);
    expect(result.curator_synthesis).toBeNull();
  });

  it('handles fullArticles key (LLM field name variant)', async () => {
    const r2Edition = {
      edition_id: '2026-03-01',
      date: '2026-03-01',
      articles: {
        aspirant: {
          newspaper_name: 'The Aspirant',
          fullArticles: [
            { title: 'Headline via title', content: 'Body via content' },
          ],
          inBrief: [],
        },
      },
    };

    const result = await transformR2Edition(r2Edition, 'fixture');

    expect(result.newspapers[0].articles[0].headline).toBe('Headline via title');
    expect(result.newspapers[0].articles[0].body).toBe('Body via content');
  });

  it('normalises in_brief plain strings into headline+summary objects', async () => {
    const r2Edition = {
      edition_id: '2026-03-01',
      date: '2026-03-01',
      articles: {
        sovereign: {
          newspaper_name: 'The Sovereign',
          articles: [],
          inBrief: [
            'Bulgaria joined the eurozone. More details follow.',
            'Strait of Hormuz shipping alert issued by insurers.',
          ],
        },
      },
    };

    const result = await transformR2Edition(r2Edition, 'fixture');
    const inBrief = result.newspapers[0].in_brief;

    expect(inBrief).toHaveLength(2);
    expect(inBrief[0].headline).toBe('Bulgaria joined the eurozone');
    expect(inBrief[0].summary).toBe('Bulgaria joined the eurozone. More details follow.');
  });

  it('derives in_brief headline from content when headline field is missing', async () => {
    const r2Edition = {
      edition_id: '2026-03-01',
      date: '2026-03-01',
      articles: {
        moralist: {
          newspaper_name: 'The Moralist',
          articles: [],
          in_brief: [
            { clusterId: '-1', content: 'Wales captain Dewi Lake expressed confidence. More follows.' },
          ],
        },
      },
    };

    const result = await transformR2Edition(r2Edition, 'fixture');
    const item = result.newspapers[0].in_brief[0];

    expect(item.headline).toBe('Wales captain Dewi Lake expressed confidence');
    expect(item.summary).toBe('Wales captain Dewi Lake expressed confidence. More follows.');
  });

  it('handles curator as plain text (not JSON)', async () => {
    const r2Edition = {
      edition_id: '2026-03-01',
      date: '2026-03-01',
      articles: {
        curator: 'Welcome to The Curator. Today\'s themes are cost and crisis.',
      },
    };

    const result = await transformR2Edition(r2Edition, 'fixture');

    expect(result.curator_synthesis).toEqual({
      text: "Welcome to The Curator. Today's themes are cost and crisis.",
    });
  });

  it('handles already-parsed objects (not JSON strings)', async () => {
    const r2Edition = {
      edition_id: '2026-03-01',
      date: '2026-03-01',
      articles: {
        sovereign: {
          newspaper_name: 'The Sovereign',
          articles: [{ headline: 'Direct', body: 'Body' }],
          in_brief: [],
        },
      },
    };

    const result = await transformR2Edition(r2Edition, 'fixture');

    expect(result.newspapers).toHaveLength(1);
    expect(result.newspapers[0].articles[0].headline).toBe('Direct');
  });
});

// ─── Zod schema validation ─────────────────────────────────────────────────

describe('Zod schema validation', () => {
  it('R2IndexEntrySchema accepts a valid entry', async () => {
    const { R2IndexEntrySchema } = await import('./schemas.js');
    const result = R2IndexEntrySchema.safeParse({
      edition_id: 'abc-001',
      date: '2026-03-01',
    });
    expect(result.success).toBe(true);
  });

  it('R2IndexEntrySchema rejects an entry with bad date format', async () => {
    const { R2IndexEntrySchema } = await import('./schemas.js');
    const result = R2IndexEntrySchema.safeParse({
      edition_id: 'abc-001',
      date: '01-03-2026', // wrong format
    });
    expect(result.success).toBe(false);
  });

  it('R2IndexEntrySchema rejects an entry with missing edition_id', async () => {
    const { R2IndexEntrySchema } = await import('./schemas.js');
    const result = R2IndexEntrySchema.safeParse({ date: '2026-03-01' });
    expect(result.success).toBe(false);
  });

  it('ArticleSchema accepts a valid article', async () => {
    const { ArticleSchema } = await import('./schemas.js');
    const result = ArticleSchema.safeParse({
      headline: 'Test Headline',
      body: 'Article body text.',
    });
    expect(result.success).toBe(true);
  });

  it('ArticleSchema rejects an article missing headline', async () => {
    const { ArticleSchema } = await import('./schemas.js');
    const result = ArticleSchema.safeParse({ body: 'No headline here.' });
    expect(result.success).toBe(false);
  });

  it('ArticleSchema rejects an article with empty headline', async () => {
    const { ArticleSchema } = await import('./schemas.js');
    const result = ArticleSchema.safeParse({ headline: '', body: 'Body.' });
    expect(result.success).toBe(false);
  });

  it('EditionSchema accepts a valid gazette edition', async () => {
    const { EditionSchema } = await import('./schemas.js');
    const result = EditionSchema.safeParse({
      edition_id: 'yz-d2-001',
      date: '2026-03-01',
      newspapers: [
        {
          newspaper_id: 'sovereign',
          newspaper_name: 'The Sovereign',
          articles: [{ headline: 'Test', body: 'Body' }],
        },
      ],
      curator_synthesis: null,
    });
    expect(result.success).toBe(true);
  });

  it('EditionSchema rejects an edition with a newspaper missing newspaper_id', async () => {
    const { EditionSchema } = await import('./schemas.js');
    const result = EditionSchema.safeParse({
      edition_id: 'yz-d2-001',
      date: '2026-03-01',
      newspapers: [
        {
          newspaper_name: 'The Sovereign',
          articles: [],
        },
      ],
    });
    expect(result.success).toBe(false);
  });

  it('transformR2Edition includes newspapers with invalid articles (filtered later)', async () => {
    // A newspaper with an article missing `headline` should still appear in the
    // transformed output — it is the responsibility of articlePages.js and
    // newspaperPages.js to filter invalid articles before calling slugify.
    const r2Edition = {
      edition_id: '2026-03-01',
      date: '2026-03-01',
      articles: {
        sovereign: JSON.stringify({
          newspaper_name: 'The Sovereign',
          articles: [
            { headline: 'Good article', body: 'Body' },
            { body: 'Missing headline — LLM omitted it' }, // invalid
          ],
          in_brief: [],
        }),
      },
    };

    const result = await transformR2Edition(
      r2Edition,
      'https://r2.example.com/editions/2026-03-01/test.json'
    );

    expect(result.newspapers).toHaveLength(1);
    // Both articles are present in the raw transform — filtering happens downstream
    expect(result.newspapers[0].articles).toHaveLength(2);
  });
});

// ─── captureValidationError ────────────────────────────────────────────────

describe('captureValidationError', () => {
  it('logs to console.warn with sourceUrl and label', async () => {
    const { captureValidationError } = await import('./sentry.js');
    const { z } = await import('zod');

    const schema = z.object({ headline: z.string().min(1) });
    const result = schema.safeParse({ headline: '' });
    expect(result.success).toBe(false);

    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => { /* empty */ });
    await captureValidationError(
      {
        sourceUrl: 'https://r2.example.com/editions/2026-03-01/abc.json',
        label: 'article in newspaper "sovereign"',
        offendingData: { headline: '' },
      },
      result.error
    );

    expect(warnSpy).toHaveBeenCalledWith(
      expect.stringContaining(
        'https://r2.example.com/editions/2026-03-01/abc.json'
      )
    );
    expect(warnSpy).toHaveBeenCalledWith(
      expect.stringContaining('article in newspaper "sovereign"')
    );
    warnSpy.mockRestore();
  });
});
