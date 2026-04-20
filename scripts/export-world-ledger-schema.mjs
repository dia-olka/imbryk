#!/usr/bin/env node
/*
 * Exports the zod WorldLedgerSchema to a JSON Schema file that serves as the
 * cross-language wire contract. Consumed by:
 *   - packages/world-state (TS side — validates R2 reads)
 *   - apps/newsroom-director (Python side — regenerates pydantic models from it)
 *
 * Invoked by nx target `world-state:export-schema`. The generated JSON Schema
 * is checked in; CI re-runs this script and fails if the output drifts.
 */

import { writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { z } from 'zod';
import { WorldLedgerSchema, WORLD_LEDGER_SCHEMA_VERSION } from '../packages/world-state/src/lib/world-ledger.schemas.ts';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, '..');
const OUT = join(
  ROOT,
  'packages/world-state/src/schema/world-ledger.schema.json',
);

const jsonSchema = z.toJSONSchema(WorldLedgerSchema, {
  target: 'draft-2020-12',
});
jsonSchema.title = 'WorldLedger';
jsonSchema['x-schema-version'] = WORLD_LEDGER_SCHEMA_VERSION;

writeFileSync(OUT, JSON.stringify(jsonSchema, null, 2) + '\n', 'utf-8');

console.log(`✓ ${OUT}`);
