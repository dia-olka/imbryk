"""Backfill image generation for articles from previous editions.

After the daily pipeline completes, this step finds articles in past editions
that have missing images (article images without image_url or missing hero
images), generates the missing images, and overwrites the R2 edition JSON.

When an image prompt fails (likely permanently due to safety filters), the
backfill uses a Flash-tier LLM to rewrite the prompt before retrying.  For
newspapers missing a hero image prompt entirely, Flash generates one from the
article headlines.

All failures are caught and logged — this step must never raise or affect
today's edition.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..db import fetch_editions_needing_image_backfill, update_article_content_json
from ..generation import GenerationStrategy
from ..storage import EditionStorage
from ..validation import sanitize_prompt_text
from .client import ImageGenerationStrategy

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Flash LLM prompts for rewriting / generating image prompts
# ---------------------------------------------------------------------------

_REWRITE_PROMPT_SYSTEM = """\
You are an image prompt rewriter for Google Imagen. The original prompt was \
rejected by Imagen's safety filters or content policy. Rewrite it into a \
prompt that will succeed while preserving the visual intent.

RULES:
- Remove all references to specific people by name.
- Remove explicit violence, gore, or distressing imagery.
- Replace political figures with generic descriptions ("a diplomat", "a leader").
- Keep the scene, setting, mood, and composition.
- Structure as: Subject + Setting/Context + Style + Quality modifiers.
- Always include: "4K", "HDR", and "professional photography" or "editorial illustration".
- Do NOT include any text or lettering in the image description.
- Be specific about lighting, materials, colours, and composition.

Respond with ONLY the rewritten prompt text, nothing else."""

_HERO_PROMPT_SYSTEM = """\
You are a visual editor for a newspaper. Given the headlines of today's top \
stories, create a single compelling image prompt for the newspaper's front \
page hero image. The image should capture the dominant theme or mood of the \
day's coverage.

RULES:
- Structure as: Subject + Setting/Context + Style + Quality modifiers.
- Always include: "4K", "HDR", and "professional photography" or "editorial illustration".
- Do NOT include text, lettering, or newspaper mastheads.
- Do NOT reference specific people by name.
- Be specific about lighting, materials, colours, and composition.
- The image should work as a dramatic, eye-catching front page visual.

Respond with ONLY the image prompt text, nothing else."""


@dataclass
class BackfillResult:
    """Summary of a single backfill run."""

    editions_scanned: int = 0
    editions_updated: int = 0
    images_generated: int = 0
    images_failed: int = 0
    prompts_rewritten: int = 0


# ---------------------------------------------------------------------------
# LLM helpers
# ---------------------------------------------------------------------------


def _rewrite_image_prompt(
    original_prompt: str,
    headline: str,
    llm: GenerationStrategy,
) -> str | None:
    """Ask Flash to rewrite a rejected Imagen prompt."""
    try:
        user_content = (
            f"ORIGINAL REJECTED PROMPT:\n{original_prompt}\n\n"
            f"ARTICLE HEADLINE:\n{headline}"
        )
        result = llm.generate(_REWRITE_PROMPT_SYSTEM, "flash", user_content)
        rewritten = result.strip()
        return sanitize_prompt_text(rewritten) if rewritten else None
    except Exception:
        logger.warning("Failed to rewrite image prompt via LLM", exc_info=True)
        return None


def _generate_hero_prompt(
    articles: list[dict],
    newspaper_id: str,
    llm: GenerationStrategy,
) -> str | None:
    """Ask Flash to generate a hero image prompt from article headlines."""
    try:
        headlines = [
            f"- {a['headline']}"
            for a in articles
            if isinstance(a, dict) and a.get("headline")
        ]
        if not headlines:
            return None

        user_content = (
            f"NEWSPAPER: {newspaper_id}\n\n"
            f"TODAY'S HEADLINES:\n" + "\n".join(headlines[:10])
        )
        result = llm.generate(_HERO_PROMPT_SYSTEM, "flash", user_content)
        hero_prompt = result.strip()
        return sanitize_prompt_text(hero_prompt) if hero_prompt else None
    except Exception:
        logger.warning("Failed to generate hero prompt via LLM", exc_info=True)
        return None


# ---------------------------------------------------------------------------
# Core backfill logic
# ---------------------------------------------------------------------------


def _generate_with_rewrite(
    prompt: str,
    headline: str,
    imagen_client: ImageGenerationStrategy,
    llm: GenerationStrategy | None,
    budget: list[int],
) -> tuple[bytes | None, bool]:
    """Try to generate an image; on failure rewrite the prompt via Flash.

    Returns ``(image_bytes_or_none, was_rewritten)``.
    """
    image_bytes = imagen_client.generate(prompt)
    budget[0] -= 1

    if image_bytes is not None:
        return image_bytes, False

    # Original prompt failed — rewrite via Flash and retry
    if llm is not None and budget[0] > 0:
        rewritten = _rewrite_image_prompt(prompt, headline, llm)
        if rewritten:
            logger.info(
                "Retrying with rewritten prompt: %.120s",
                rewritten,
            )
            image_bytes = imagen_client.generate(rewritten)
            budget[0] -= 1
            if image_bytes is not None:
                return image_bytes, True

    return None, False


def _backfill_newspaper(
    edition_date: str,
    newspaper_id: str,
    parsed: dict,
    imagen_client: ImageGenerationStrategy,
    storage: EditionStorage,
    budget: list[int],
    llm: GenerationStrategy | None = None,
) -> tuple[int, int, int]:
    """Generate missing images for one newspaper's parsed content dict.

    Mutates *parsed* in-place by embedding ``image_url`` / ``heroImageUrl``
    into the content dict.

    *budget* is a single-element mutable list ``[remaining]`` shared across
    newspapers in a run so the global cap is enforced correctly.

    Returns:
        ``(images_generated, images_failed, prompts_rewritten)`` counts.
    """
    generated = 0
    failed = 0
    rewritten_count = 0

    # --- Article images ---
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

        headline = article.get("headline", "<no headline>")
        prompt = sanitize_prompt_text(article["imagePrompt"])
        logger.info(
            "Backfilling article image for %s/%s article %d: %s",
            edition_date,
            newspaper_id,
            idx,
            headline,
            extra={
                "edition_date": edition_date,
                "newspaper_id": newspaper_id,
                "article_index": idx,
                "headline": headline,
                "prompt": prompt,
            },
        )

        image_bytes, was_rewritten = _generate_with_rewrite(
            prompt, headline, imagen_client, llm, budget,
        )

        if image_bytes is None:
            logger.warning(
                "Backfill image generation returned None for %s/%s "
                "article %d (%s) | prompt: %s",
                edition_date,
                newspaper_id,
                idx,
                headline,
                prompt,
                extra={
                    "edition_date": edition_date,
                    "newspaper_id": newspaper_id,
                    "article_index": idx,
                    "headline": headline,
                    "prompt": prompt,
                },
            )
            failed += 1
            continue

        if was_rewritten:
            rewritten_count += 1

        # Use edition_date (not edition UUID) as the storage path prefix —
        # this matches the convention from the main pipeline.
        url = storage.write_image(edition_date, newspaper_id, f"{idx}.png", image_bytes)
        article["image_url"] = url
        generated += 1
        logger.info(
            "Backfill image uploaded: %s/%s article %d -> %s",
            edition_date,
            newspaper_id,
            idx,
            url,
            extra={
                "edition_date": edition_date,
                "newspaper_id": newspaper_id,
                "article_index": idx,
                "headline": headline,
                "url": url,
            },
        )

    # --- Hero image ---
    if not parsed.get("heroImageUrl") and budget[0] > 0:
        hero_prompt = parsed.get("frontPageImagePrompt")

        # Generate a hero prompt from article headlines if missing
        if not hero_prompt and llm is not None:
            logger.info(
                "Generating hero prompt from articles for %s",
                newspaper_id,
                extra={
                    "edition_date": edition_date,
                    "newspaper_id": newspaper_id,
                },
            )
            hero_prompt = _generate_hero_prompt(
                parsed.get("articles", []), newspaper_id, llm,
            )
            if hero_prompt:
                parsed["frontPageImagePrompt"] = hero_prompt

        if hero_prompt:
            sanitized = sanitize_prompt_text(hero_prompt)
            logger.info(
                "Backfilling hero image for %s/%s",
                edition_date,
                newspaper_id,
                extra={
                    "edition_date": edition_date,
                    "newspaper_id": newspaper_id,
                    "prompt": sanitized,
                },
            )

            # Derive a headline for the rewrite context
            top_headline = ""
            for a in parsed.get("articles", []):
                if isinstance(a, dict) and a.get("headline"):
                    top_headline = a["headline"]
                    break

            image_bytes, was_rewritten = _generate_with_rewrite(
                sanitized, top_headline, imagen_client, llm, budget,
            )

            if image_bytes is not None:
                url = storage.write_image(
                    edition_date, newspaper_id, "hero.png", image_bytes,
                )
                parsed["heroImageUrl"] = url
                generated += 1
                if was_rewritten:
                    rewritten_count += 1
                logger.info(
                    "Backfill hero image uploaded: %s/%s -> %s",
                    edition_date,
                    newspaper_id,
                    url,
                    extra={
                        "edition_date": edition_date,
                        "newspaper_id": newspaper_id,
                        "url": url,
                    },
                )
            else:
                failed += 1
                logger.warning(
                    "Backfill hero image generation failed for %s/%s",
                    edition_date,
                    newspaper_id,
                    extra={
                        "edition_date": edition_date,
                        "newspaper_id": newspaper_id,
                    },
                )
        else:
            logger.warning(
                "No hero prompt available for %s/%s — skipping hero backfill",
                edition_date,
                newspaper_id,
                extra={
                    "edition_date": edition_date,
                    "newspaper_id": newspaper_id,
                },
            )

    return generated, failed, rewritten_count


def run_image_backfill(
    session: Session,
    today_date: str,
    imagen_client: ImageGenerationStrategy,
    storage: EditionStorage,
    max_editions: int = 7,
    max_images_per_run: int = 20,
    llm: GenerationStrategy | None = None,
) -> BackfillResult:
    """Backfill missing images for previous editions.

    Finds newspapers from the last *max_editions* editions (excluding today)
    that have articles with ``imagePrompt`` but no ``image_url``, or that are
    missing a hero image, generates the missing images via Imagen, and
    overwrites the R2 edition JSON with the updated content.

    When Imagen rejects a prompt, Flash rewrites it before retrying.  When a
    hero image prompt is missing entirely, Flash generates one from article
    headlines.

    This function never raises — all exceptions are caught and logged.

    Args:
        session: Active DB session.
        today_date: Today's YYYY-MM-DD date, excluded from the scan.
        imagen_client: Image generation backend.
        storage: Edition storage backend.
        max_editions: Maximum number of past editions to scan.
        max_images_per_run: Global cap on Imagen calls per run.
        llm: LLM generation backend for prompt rewriting (Flash tier).

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
                gen, fail, rewritten = _backfill_newspaper(
                    edition_date=target.edition_date,
                    newspaper_id=newspaper_id,
                    parsed=parsed,
                    imagen_client=imagen_client,
                    storage=storage,
                    budget=budget,
                    llm=llm,
                )
                edition_generated += gen
                edition_failed += fail
                result.prompts_rewritten += rewritten

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
            "prompts_rewritten": result.prompts_rewritten,
        },
    )
    return result
