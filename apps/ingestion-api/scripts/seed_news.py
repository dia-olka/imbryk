"""Seed real-world 2026 news events into the Imbryk database.

Usage:
    cd apps/ingestion-api
    DATABASE_URL=postgresql://... python scripts/seed_news.py data/seed-2026-news.json

The script is idempotent: events whose prompt text already exists in the
database are silently skipped.
"""

import json
import os
import sys
from pathlib import Path

# Allow running from the repo root or from apps/ingestion-api
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from ingestion_api.models import Base, CategorisedPrompt, Prompt


def main(seed_file: str) -> None:
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./imbryk.db")
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)

    with open(seed_file, encoding="utf-8") as f:
        data = json.load(f)

    events = data.get("events", [])
    if not events:
        print("No events found in seed file.")
        return

    inserted = 0
    skipped = 0

    with Session(engine) as session:
        for event in events:
            prompt_text: str = event["prompt"]
            categories: list[str] = event.get("categories", [])

            existing = session.query(Prompt).filter_by(text=prompt_text).first()
            if existing is not None:
                skipped += 1
                continue

            prompt = Prompt(
                text=prompt_text,
                payment_ref=None,
                status="accepted",
            )
            session.add(prompt)
            session.flush()

            for cat_id in categories:
                session.add(
                    CategorisedPrompt(
                        prompt_id=prompt.id,
                        category_id=cat_id,
                    )
                )

            inserted += 1

        session.commit()

    print(f"Seed complete: {inserted} event(s) inserted, {skipped} skipped.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <seed-json-file>", file=sys.stderr)
        sys.exit(1)

    main(sys.argv[1])
