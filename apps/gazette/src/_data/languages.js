import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));

/**
 * Load language configuration from data/languages.json.
 * Returns { system: [...], ui: {...} } for use in templates.
 */
export default function () {
  const langPath = join(__dirname, '..', '..', '..', '..', 'data', 'languages.json');
  try {
    const raw = readFileSync(langPath, 'utf-8');
    return JSON.parse(raw);
  } catch (err) {
    console.warn('Failed to load data/languages.json:', err.message);
    return { system: [], ui: {} };
  }
}
