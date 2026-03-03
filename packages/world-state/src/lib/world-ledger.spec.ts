import { describe, it, expect } from 'vitest';
import { WORLD_LEDGER_TEMPLATE } from './world-ledger.template.js';
import { INITIAL_WORLD_LEDGER } from './world-ledger.initial.js';
import { serializeLedgerToSynopsis } from './world-ledger.serialiser.js';
import { applyMutation } from './world-ledger.mutator.js';
import type { WorldLedger } from './world-ledger.types.js';

describe('WorldLedger template', () => {
  it('should have an empty template', () => {
    expect(WORLD_LEDGER_TEMPLATE.epoch).toBe('');
    expect(WORLD_LEDGER_TEMPLATE.history).toEqual([]);
  });
});

describe('INITIAL_WORLD_LEDGER', () => {
  it('should have an epoch set', () => {
    expect(INITIAL_WORLD_LEDGER.epoch).toBe('Year Zero — The Morning After');
  });

  it('should have a non-empty synopsis', () => {
    expect(INITIAL_WORLD_LEDGER.synopsis.length).toBeGreaterThan(100);
  });

  it('should have 6 nations', () => {
    expect(INITIAL_WORLD_LEDGER.geopolitics.nations).toHaveLength(6);
  });

  it('should include the Atlantic Republic', () => {
    const names = INITIAL_WORLD_LEDGER.geopolitics.nations.map((n: { name: string }) => n.name);
    expect(names).toContain('Atlantic Republic');
  });

  it('should have alliances', () => {
    expect(INITIAL_WORLD_LEDGER.geopolitics.alliances.length).toBeGreaterThan(
      0
    );
  });

  it('should have conflicts', () => {
    expect(INITIAL_WORLD_LEDGER.geopolitics.conflicts.length).toBeGreaterThan(
      0
    );
  });

  it('should have currencies', () => {
    expect(INITIAL_WORLD_LEDGER.economics.currencies.length).toBeGreaterThan(0);
  });

  it('should have seed history events', () => {
    expect(INITIAL_WORLD_LEDGER.history.length).toBeGreaterThanOrEqual(3);
  });

  it('should have technology domains populated', () => {
    expect(INITIAL_WORLD_LEDGER.technology.ai.keyPlayers.length).toBeGreaterThan(
      0
    );
    expect(
      INITIAL_WORLD_LEDGER.technology.energy.keyPlayers.length
    ).toBeGreaterThan(0);
  });

  it('should have environment data', () => {
    expect(INITIAL_WORLD_LEDGER.environment.globalTemperatureAnomaly).toBe(1.8);
    expect(INITIAL_WORLD_LEDGER.environment.crises.length).toBeGreaterThan(0);
  });
});

describe('serializeLedgerToSynopsis', () => {
  it('should produce a non-empty string from the initial ledger', () => {
    const result = serializeLedgerToSynopsis(INITIAL_WORLD_LEDGER);
    expect(result.length).toBeGreaterThan(500);
  });

  it('should contain expected section headers', () => {
    const result = serializeLedgerToSynopsis(INITIAL_WORLD_LEDGER);
    expect(result).toContain('--- GEOPOLITICS ---');
    expect(result).toContain('--- ECONOMICS ---');
    expect(result).toContain('--- TECHNOLOGY ---');
    expect(result).toContain('--- CULTURE ---');
    expect(result).toContain('--- MILITARY ---');
    expect(result).toContain('--- ENVIRONMENT ---');
    expect(result).toContain('--- RECENT HISTORY ---');
  });

  it('should contain nation names', () => {
    const result = serializeLedgerToSynopsis(INITIAL_WORLD_LEDGER);
    expect(result).toContain('Atlantic Republic');
    expect(result).toContain('Eastern Compact');
  });

  it('should contain the epoch', () => {
    const result = serializeLedgerToSynopsis(INITIAL_WORLD_LEDGER);
    expect(result).toContain('EPOCH: Year Zero');
  });

  it('should handle an empty ledger gracefully', () => {
    const result = serializeLedgerToSynopsis(WORLD_LEDGER_TEMPLATE);
    expect(result).toContain('EPOCH:');
    expect(result).not.toContain('--- RECENT HISTORY ---');
  });
});

describe('applyMutation', () => {
  it('should add new nations without modifying the original', () => {
    const original = structuredClone(INITIAL_WORLD_LEDGER);
    const originalNationCount = original.geopolitics.nations.length;

    const mutated = applyMutation(original, {
      addNations: [
        {
          name: 'Island Federation',
          governmentType: 'Direct democracy',
          leader: 'Speaker Kai Manu',
          stability: 70,
          description: 'A newly independent island state.',
        },
      ],
    });

    expect(mutated.geopolitics.nations).toHaveLength(originalNationCount + 1);
    expect(original.geopolitics.nations).toHaveLength(originalNationCount);
  });

  it('should update existing conflicts by name', () => {
    const mutated = applyMutation(INITIAL_WORLD_LEDGER, {
      updateConflicts: [
        {
          name: 'Caspian Basin Standoff',
          status: 'active',
          description: 'Hostilities have resumed along the corridor.',
        },
      ],
    });

    const updated = mutated.geopolitics.conflicts.find(
      (c: { name: string }) => c.name === 'Caspian Basin Standoff'
    );
    expect(updated?.status).toBe('active');
    expect(updated?.description).toContain('Hostilities have resumed');
  });

  it('should append history events', () => {
    const originalCount = INITIAL_WORLD_LEDGER.history.length;
    const mutated = applyMutation(INITIAL_WORLD_LEDGER, {
      addHistoricalEvents: [
        {
          date: 'Year Zero, Day 30',
          headline: 'Trade summit collapses',
          description: 'The first multilateral trade summit ended without agreement.',
          impact: 'Trade tensions increased across all blocs.',
          sectors: ['trade-and-commerce', 'geopolitics'],
        },
      ],
    });

    expect(mutated.history).toHaveLength(originalCount + 1);
    expect(mutated.history[mutated.history.length - 1].headline).toBe(
      'Trade summit collapses'
    );
  });

  it('should update synopsis when provided', () => {
    const mutated = applyMutation(INITIAL_WORLD_LEDGER, {
      synopsis: 'The world has changed.',
    });
    expect(mutated.synopsis).toBe('The world has changed.');
  });

  it('should update temperature anomaly', () => {
    const mutated = applyMutation(INITIAL_WORLD_LEDGER, {
      updateTemperatureAnomaly: 2.1,
    });
    expect(mutated.environment.globalTemperatureAnomaly).toBe(2.1);
  });

  it('should update GDP trend', () => {
    const mutated = applyMutation(INITIAL_WORLD_LEDGER, {
      updateGlobalGdpTrend: 'Recession imminent.',
    });
    expect(mutated.economics.globalGdpTrend).toBe('Recession imminent.');
  });

  it('should not modify the original ledger', () => {
    const original: WorldLedger = structuredClone(INITIAL_WORLD_LEDGER);
    const snapshot = JSON.stringify(original);

    applyMutation(original, {
      addNations: [
        {
          name: 'Test Nation',
          governmentType: 'Test',
          leader: 'Test',
          stability: 50,
          description: 'Test',
        },
      ],
      addHistoricalEvents: [
        {
          date: 'Test',
          headline: 'Test',
          description: 'Test',
          impact: 'Test',
          sectors: ['geopolitics'],
        },
      ],
      updateTemperatureAnomaly: 99,
      synopsis: 'Changed',
    });

    expect(JSON.stringify(original)).toBe(snapshot);
  });
});
