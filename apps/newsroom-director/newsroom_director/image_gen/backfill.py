"""Backfill image generation for articles from previous editions.

After the daily pipeline completes, this step finds articles in past editions
that have an imagePrompt but no image_url (i.e. Imagen previously failed for
them), generates the missing images, and overwrites the R2 edition JSON.

All failures are caught and logged — this step must never raise or affect
today's edition.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..db import fetch_editions_needing_image_backfill, update_article_content_json
from ..storage import EditionStorage
from ..validation import sanitize_prompt_text
from .client import ImageGenerationStrategy

logger = logging.getLogger(__name__)


@dataclass
class BackfillResult:
    """Summary of a single backfill run."""

    editions_scanned: int = 0
    editions_updated: int = 0
    images_generated: int = 0
    images_failed: int = 0


def _backfill_newspaper(
    edition_date: str,
    newspaper_id: str,
    parsed: dict,
    imagen_client: ImageGenerationStrategy,
    storage: EditionStorage,
    budget: list[int],
) -> tuple[int, int]:
    """Generate missing images for one newspaper's parsed content dict.

    Mutates *parsed* in-place by embedding ``image_url`` into articles that
    receive a successfully generated image.

    *budget* is a single-element mutable list ``[remaining]`` shared across
    newspapers in a run so the global cap is enforced correctly.

    Returns:
        ``(images_generated, images_failed)`` counts for this newspaper.
    """
    generated = 0
    failed = 0

    for idx, article in enumerate(parsed.get("articles", [])):
        if not isinstance(article, dict):
            continue
        if not article.get("imagePrompt") or article.get("image_url"):
            continue
        if budget[0] <= 0:
            logger.info(
                "Backfill budget exhausted",
                extra={"newspaper_id": newspaper_id},
            )
            break

        prompt = sanitize_prompt_text(article["imagePrompt"])
        logger.info(
            "Backfilling article image",
            extra={
                "newspaper_id": newspaper_id,
                "article_index": idx,
                "prompt": prompt[:80],
            },
        )

        image_bytes = imagen_client.generate(prompt)
        budget[0] -= 1

        if image_bytes is None:
            logger.warning(
                "Backfill image generation failed for article %d of %s",
                idx,
                newspaper_id,
            )
            failed += 1
            continue

        # Use edition_date (not edition UUID) as the storage path prefix —
        # this matches the convention from the main pipeline.
        url = storage.write_image(edition_date, newspaper_id, f"{idx}.webp", image_bytes)
        article["image_url"] = url
        generated += 1
        logger.info(
            "Backfill image uploaded",
            extra={"newspaper_id": newspaper_id, "article_index": idx, "url": url},
        )

    return generated, failed


def run_image_backfill(
    session: Session,
    today_date: str,
    imagen_client: ImageGenerationStrategy,
    storage: EditionStorage,
    max_editions: int = 7,
    max_images_per_run: int = 20,
) -> BackfillResult:
    """Backfill missing article images for previous editions.

    Finds articles from the last *max_editions* editions (excluding today)
    that have an ``imagePrompt`` but no ``image_url``, generates the missing
    images via Imagen, and overwrites the R2 edition JSON with the updated
    content.

    This function never raises — all exceptions are caught and logged.

    Args:
        session: Active DB session (read-only for this step).
        today_date: Today's YYYY-MM-DD date, excluded from the scan.
        imagen_client: Image generation backend.
        storage: Edition storage backend.
        max_editions: Maximum number of past editions to scan.
        max_images_per_run: Global cap on images generated per run.

    Returns:
        BackfillResult summary.
    """
    result = BackfillResult()
    budget = [max_images_per_run]

    try:
        targets = fetch_editions_needing_image_backfill(
            session=session,
            exclude_date=today_date,
            max_editions=max_editions,
        )
    except Exception:
        logger.warning("Backfill: failed to fetch editions from DB", exc_info=True)
        return result

    result.editions_scanned = len(targets)
    if not targets:
        return result

    logger.info(
        "Image backfill: %d edition(s) need attention",
        len(targets),
        extra={"step": "backfill", "edition_count": len(targets)},
    )

    for target in targets:
        if budget[0] <= 0:
            logger.info("Backfill budget exhausted, skipping remaining editions")
            break

        edition_generated = 0
        edition_failed = 0
        updated_articles: dict[str, str] = dict(target.newspaper_articles)

        for newspaper_id in target.newspapers_to_backfill:
            if budget[0] <= 0:
                break
            try:
                parsed = json.loads(target.newspaper_articles[newspaper_id])
            except (json.JSONDecodeError, TypeError, KeyError):
                logger.warning(
                    "Backfill: could not parse content for %s/%s",
                    target.edition_id,
                    newspaper_id,
                )
                continue

            try:
                gen, fail = _backfill_newspaper(
                    edition_date=target.edition_date,
                    newspaper_id=newspaper_id,
                    parsed=parsed,
                    imagen_client=imagen_client,
                    storage=storage,
                    budget=budget,
                )
                edition_generated += gen
                edition_failed += fail

                if gen > 0:
                    updated_articles[newspaper_id] = json.dumps(
                        parsed, ensure_ascii=False
                    )
            except Exception:
                logger.warning(
                    "Backfill: failed for newspaper %s in edition %s",
                    newspaper_id,
                    target.edition_id,
                    exc_info=True,
                )

        result.images_generated += edition_generated
        result.images_failed += edition_failed

        if edition_generated > 0:
            try:
                storage.write_edition(
                    target.edition_id,
                    target.edition_date,
                    updated_articles,
                )
                result.editions_updated += 1
                logger.info(
                    "Backfill: updated edition in storage",
                    extra={
                        "step": "backfill",
                        "edition_id": target.edition_id,
                        "images_generated": edition_generated,
                    },
                )
                # Persist the updated content_json to the DB so the next run
                # does not re-detect the same articles as needing backfill.
                for newspaper_id in target.newspapers_to_backfill:
                    if newspaper_id in updated_articles:
                        update_article_content_json(
                            session,
                            target.edition_id,
                            newspaper_id,
                            updated_articles[newspaper_id],
                        )
                session.commit()
            except Exception:
                logger.warning(
                    "Backfill: failed to write updated edition %s to storage",
                    target.edition_id,
                    exc_info=True,
                )

    logger.info(
        "Image backfill complete",
        extra={
            "step": "backfill_complete",
            "editions_scanned": result.editions_scanned,
            "editions_updated": result.editions_updated,
            "images_generated": result.images_generated,
            "images_failed": result.images_failed,
        },
    )
    return result
