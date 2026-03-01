import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));

export default function () {
  const fixturePath = join(__dirname, 'fixtures', 'sample-edition.json');
  const raw = readFileSync(fixturePath, 'utf-8');
  const edition = JSON.parse(raw);
  return [edition];
}
