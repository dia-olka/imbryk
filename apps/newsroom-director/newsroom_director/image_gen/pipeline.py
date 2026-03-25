"""Image generation pipeline step — generates images for a newspaper edition."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..storage import EditionStorage
from ..validation import sanitize_prompt_text
from .backfill import _rewrite_image_prompt
from .client import ImageGenerationStrategy

if TYPE_CHECKING:
    from ..generation import GenerationStrategy

logger = logging.getLogger(__name__)

# Maximum number of article images per newspaper (excluding hero).
MAX_ARTICLE_IMAGES = 2


@dataclass
class ImageResult:
    """Mapping of generated image URLs for a single newspaper."""

    article_image_urls: dict[int, str]  # article index -> image URL
    hero_image_url: str | None


def generate_images_for_newspaper(
    newspaper_id: str,
    articles: list[dict],
    front_page_image_prompt: str | None,
    imagen_client: ImageGenerationStrategy,
    storage: EditionStorage,
    edition_id: str,
    max_article_images: int = MAX_ARTICLE_IMAGES,
    negative_prompt: str = "",
    llm: GenerationStrategy | None = None,
) -> ImageResult:
    """Generate images for a newspaper's articles and hero.

    Selects the top articles (by weight) that have a non-null imagePrompt,
    generates images via Imagen, and uploads them to storage.

    When *llm* is provided and a prompt is rejected by Imagen (safety filter),
    the prompt is rewritten via Flash and retried once before giving up.

    Args:
        newspaper_id: The newspaper identifier (e.g., "sovereign").
        articles: List of article dicts from Gemini output.
        front_page_image_prompt: Nullable hero image prompt.
        imagen_client: Image generation backend.
        storage: Edition storage backend for uploading images.
        edition_id: The edition identifier for storage paths.
        max_article_images: Max article images to generate.
        negative_prompt: Per-persona negative prompt for Imagen.
        llm: Optional LLM backend for rewriting rejected prompts.

    Returns:
        ImageResult with URLs for generated images.
    """
    article_image_urls: dict[int, str] = {}
    hero_image_url: str | None = None

    # Select articles with imagePrompt, sorted by weight descending
    candidates = [
        (i, a)
        for i, a in enumerate(articles)
        if a.get("imagePrompt")
    ]
    candidates.sort(key=lambda x: x[1].get("weight", 0), reverse=True)
    candidates = candidates[:max_article_images]

    # Generate article images
    for idx, article in candidates:
        headline = article.get("headline", "<no headline>")
        image_prompt = sanitize_prompt_text(article["imagePrompt"])
        logger.info(
            "Generating article image for %s article %d: %s",
            newspaper_id,
            idx,
            headline,
            extra={
                "newspaper_id": newspaper_id,
                "article_index": idx,
                "headline": headline,
                "prompt": image_prompt,
            },
        )

        image_bytes = imagen_client.generate(
            image_prompt,
            negative_prompt=negative_prompt,
            aspect_ratio="4:3",
        )
        if image_bytes is None and llm is not None:
            rewritten = _rewrite_image_prompt(image_prompt, headline, llm)
            if rewritten:
                logger.info(
                    "Retrying article image with rewritten prompt for %s article %d",
                    newspaper_id,
                    idx,
                    extra={"newspaper_id": newspaper_id, "article_index": idx,
                           "rewritten_prompt": rewritten},
                )
                image_bytes = imagen_client.generate(
                    rewritten, negative_prompt=negative_prompt, aspect_ratio="4:3",
                )
        if image_bytes is None:
            logger.warning(
                "Image generation returned None for %s article %d (%s) "
                "| prompt: %s",
                newspaper_id,
                idx,
                headline,
                image_prompt,
                extra={
                    "newspaper_id": newspaper_id,
                    "article_index": idx,
                    "headline": headline,
                    "prompt": image_prompt,
                },
            )
            continue

        filename = f"{idx}.png"
        url = storage.write_image(
            edition_id, newspaper_id, filename, image_bytes
        )
        article_image_urls[idx] = url

        logger.info(
            "Article image uploaded: %s article %d -> %s",
            newspaper_id,
            idx,
            url,
            extra={
                "newspaper_id": newspaper_id,
                "article_index": idx,
                "headline": headline,
                "url": url,
            },
        )

    # Generate hero image
    if not front_page_image_prompt:
        logger.warning(
            "No hero image prompt provided for %s — skipping hero image generation",
            newspaper_id,
            extra={"newspaper_id": newspaper_id},
        )
    else:
        sanitized_hero_prompt = sanitize_prompt_text(front_page_image_prompt)
        logger.info(
            "Generating hero image for %s",
            newspaper_id,
            extra={
                "newspaper_id": newspaper_id,
                "prompt": sanitized_hero_prompt,
            },
        )

        hero_bytes = imagen_client.generate(
            sanitized_hero_prompt,
            negative_prompt=negative_prompt,
            aspect_ratio="16:9",
        )
        if hero_bytes is None and llm is not None:
            top_headline = next(
                (a.get("headline", "") for a in articles if a.get("headline")),
                "",
            )
            rewritten = _rewrite_image_prompt(sanitized_hero_prompt, top_headline, llm)
            if rewritten:
                logger.info(
                    "Retrying hero image with rewritten prompt for %s",
                    newspaper_id,
                    extra={"newspaper_id": newspaper_id,
                           "rewritten_prompt": rewritten},
                )
                hero_bytes = imagen_client.generate(
                    rewritten, negative_prompt=negative_prompt, aspect_ratio="16:9",
                )
        if hero_bytes is not None:
            hero_image_url = storage.write_image(
                edition_id, newspaper_id, "hero.png", hero_bytes
            )
            logger.info(
                "Hero image uploaded: %s -> %s",
                newspaper_id,
                hero_image_url,
                extra={
                    "newspaper_id": newspaper_id,
                    "url": hero_image_url,
                },
            )
        else:
            logger.warning(
                "Hero image generation returned None for %s | prompt: %s",
                newspaper_id,
                sanitized_hero_prompt,
                extra={
                    "newspaper_id": newspaper_id,
                    "prompt": sanitized_hero_prompt,
                },
            )

    return ImageResult(
        article_image_urls=article_image_urls,
        hero_image_url=hero_image_url,
    )
