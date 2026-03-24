import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));

/**
 * Load language configuration from data/languages.json.
 * Returns { system: [...], ui: {...} }.
 */
export default function loadLanguages() {
  const langPath = join(
    __dirname,
    '..',
    '..',
    '..',
    '..',
    '..',
    'data',
    'languages.json',
  );
  try {
    return JSON.parse(readFileSync(langPath, 'utf-8'));
  } catch {
    return { system: [], ui: {} };
  }
}
