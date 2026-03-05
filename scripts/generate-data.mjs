#!/usr/bin/env node
/**
 * Generates data modules from data/taxonomy.json and data/personas.json.
 *
 * Targets:
 *   - Python:     apps/<app>/<pkg>/_generated_data.py
 *   - TypeScript: packages/<pkg>/src/lib/_generated_data.ts
 *
 * Usage:
 *   node scripts/generate-data.mjs                          # all targets
 *   node scripts/generate-data.mjs --target ingestion-api   # single target
 *   node scripts/generate-data.mjs --target taxonomy        # TS package
 */

import { readFileSync, writeFileSync } from 'node:fs';
import { execSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

const taxonomy = JSON.parse(
  readFileSync(join(ROOT, 'data', 'taxonomy.json'), 'utf-8'),
);
const personas = JSON.parse(
  readFileSync(join(ROOT, 'data', 'personas.json'), 'utf-8'),
);

// ── Python generation ───────────────────────────────────────────────

/** Pretty-print a JSON-serialisable value as a valid Python literal. */
function toPython(value, indent = 0) {
  const pad = ' '.repeat(indent);
  const pad1 = ' '.repeat(indent + 4);

  if (value === null || value === undefined) return 'None';
  if (typeof value === 'boolean') return value ? 'True' : 'False';
  if (typeof value === 'number') return String(value);
  if (typeof value === 'string') {
    if (value.includes('\n')) {
      const escaped = value.replace(/\\/g, '\\\\').replace(/"""/g, '\\"\\"\\"');
      return `"""${escaped}"""`;
    }
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    if (value.length === 0) return '[]';
    const items = value.map((v) => `${pad1}${toPython(v, indent + 4)},`);
    return `[\n${items.join('\n')}\n${pad}]`;
  }
  if (typeof value === 'object') {
    const entries = Object.entries(value);
    if (entries.length === 0) return '{}';
    const items = entries.map(
      ([k, v]) => `${pad1}${JSON.stringify(k)}: ${toPython(v, indent + 4)},`,
    );
    return `{\n${items.join('\n')}\n${pad}}`;
  }
  return String(value);
}

function generatePythonModule() {
  return [
    '"""Auto-generated from data/taxonomy.json and data/personas.json.',
    '',
    'DO NOT EDIT — run `npx nx run <project>:generate-data` to regenerate.',
    '"""',
    '',
    '# ruff: noqa: E501',
    '',
    `TAXONOMY_DATA: dict = ${toPython(taxonomy)}`,
    '',
    `PERSONAS_DATA: dict = ${toPython(personas)}`,
    '',
  ].join('\n');
}

// ── TypeScript generation ───────────────────────────────────────────

function generateTsTaxonomy() {
  return [
    '/* Auto-generated from data/taxonomy.json',
    ' * DO NOT EDIT — run `npx nx run taxonomy:generate-data` to regenerate. */',
    '',
    '/* eslint-disable */',
    '',
    `export const TAXONOMY_DATA = ${JSON.stringify(taxonomy, null, 2)} as const;`,
    '',
  ].join('\n');
}

function generateTsPersonas() {
  return [
    '/* Auto-generated from data/personas.json and data/taxonomy.json',
    ' * DO NOT EDIT — run `npx nx run ai-personas:generate-data` to regenerate. */',
    '',
    '/* eslint-disable */',
    '',
    `export const PERSONAS_DATA = ${JSON.stringify(personas, null, 2)} as const;`,
    '',
    `export const SUBSCRIPTIONS_DATA = ${JSON.stringify(taxonomy.subscriptions, null, 2)} as const;`,
    '',
  ].join('\n');
}

// ── Target registry ─────────────────────────────────────────────────

const ALL_TARGETS = [
  {
    name: 'ingestion-api',
    outPath: join(ROOT, 'apps/ingestion-api/ingestion_api/_generated_data.py'),
    generate: generatePythonModule,
  },
  {
    name: 'newsroom-director',
    outPath: join(
      ROOT,
      'apps/newsroom-director/newsroom_director/_generated_data.py',
    ),
    generate: generatePythonModule,
  },
  {
    name: 'taxonomy',
    outPath: join(ROOT, 'packages/taxonomy/src/lib/_generated_data.ts'),
    generate: generateTsTaxonomy,
  },
  {
    name: 'ai-personas',
    outPath: join(ROOT, 'packages/ai-personas/src/lib/_generated_data.ts'),
    generate: generateTsPersonas,
  },
];

// ── Formatting ──────────────────────────────────────────────────────

function formatFile(filePath) {
  if (filePath.endsWith('.ts')) {
    try {
      execSync(`npx prettier --write "${filePath}"`, {
        stdio: 'pipe',
        cwd: ROOT,
      });
    } catch {
      /* prettier not available — skip */
    }
  } else if (filePath.endsWith('.py')) {
    try {
      execSync(`ruff format "${filePath}"`, { stdio: 'pipe', cwd: ROOT });
    } catch {
      /* ruff not available — skip */
    }
  }
}

// ── CLI ─────────────────────────────────────────────────────────────

const args = process.argv.slice(2);
const targetFlagIdx = args.indexOf('--target');

let targets = ALL_TARGETS;
if (targetFlagIdx !== -1 && args[targetFlagIdx + 1]) {
  const name = args[targetFlagIdx + 1];
  targets = ALL_TARGETS.filter((t) => t.name === name);
  if (targets.length === 0) {
    // Backwards compat: --app flag
    const appName = name;
    targets = ALL_TARGETS.filter((t) => t.name === appName);
  }
  if (targets.length === 0) {
    console.error(`Unknown target: ${args[targetFlagIdx + 1]}`);
    process.exit(1);
  }
}
// Also support legacy --app flag
const appFlagIdx = args.indexOf('--app');
if (appFlagIdx !== -1 && args[appFlagIdx + 1]) {
  const name = args[appFlagIdx + 1];
  targets = ALL_TARGETS.filter((t) => t.name === name);
  if (targets.length === 0) {
    console.error(`Unknown target: ${name}`);
    process.exit(1);
  }
}

for (const target of targets) {
  writeFileSync(target.outPath, target.generate(), 'utf-8');
  formatFile(target.outPath);
  console.log(`✓ ${target.outPath}`);
}
