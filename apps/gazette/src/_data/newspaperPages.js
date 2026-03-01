import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));

export default function () {
  const fixturePath = join(__dirname, 'fixtures', 'sample-edition.json');
  const raw = readFileSync(fixturePath, 'utf-8');
  const edition = JSON.parse(raw);

  const pages = [];
  for (const newspaper of edition.newspapers) {
    pages.push({
      editionId: edition.edition_id,
      editionDate: edition.date,
      newspaperId: newspaper.newspaper_id,
      newspaperName: newspaper.newspaper_name,
      articles: newspaper.articles,
      inBrief: newspaper.in_brief,
      editorsNote: newspaper.editors_note,
      metadata: newspaper.metadata,
    });
  }
  return pages;
}
