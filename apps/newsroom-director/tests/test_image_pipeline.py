"""Tests for the image generation pipeline step."""

import pytest

from newsroom_director.image_gen.client import StubImageClient
from newsroom_director.image_gen.pipeline import (
    MAX_ARTICLE_IMAGES,
    ImageResult,
    generate_images_for_newspaper,
)
from newsroom_director.storage import StubEditionStorage


def _make_articles(count: int, with_prompt: bool = True) -> list[dict]:
    """Create a list of article dicts with optional imagePrompt."""
    articles = []
    for i in range(count):
        article = {
            "headline": f"Article {i}",
            "body": f"Body {i}",
            "slug": f"article-{i}",
            "weight": (count - i) * 10,  # Descending weight
            "imagePrompt": f"An image for article {i}" if with_prompt else None,
        }
        articles.append(article)
    return articles


class TestGenerateImagesForNewspaper:
    def test_generates_article_images_with_urls(self):
        client = StubImageClient()
        storage = StubEditionStorage()
        articles = _make_articles(2)

        result = generate_images_for_newspaper(
            newspaper_id="sovereign",
            articles=articles,
            front_page_image_prompt=None,
            imagen_client=client,
            storage=storage,
            edition_id="ed-001",
        )

        assert isinstance(result, ImageResult)
        assert len(result.article_image_urls) == 2
        assert 0 in result.article_image_urls
        assert 1 in result.article_image_urls
        assert result.hero_image_url is None
        # Verify images written to storage
        assert len(storage._images) == 2

    def test_respects_max_article_images(self):
        client = StubImageClient()
        storage = StubEditionStorage()
        articles = _make_articles(6)

        result = generate_images_for_newspaper(
            newspaper_id="sovereign",
            articles=articles,
            front_page_image_prompt=None,
            imagen_client=client,
            storage=storage,
            edition_id="ed-001",
        )

        assert len(result.article_image_urls) == MAX_ARTICLE_IMAGES
        assert len(client._calls) == MAX_ARTICLE_IMAGES

    def test_custom_max_images(self):
        client = StubImageClient()
        storage = StubEditionStorage()
        articles = _make_articles(5)

        result = generate_images_for_newspaper(
            newspaper_id="sovereign",
            articles=articles,
            front_page_image_prompt=None,
            imagen_client=client,
            storage=storage,
            edition_id="ed-001",
            max_article_images=1,
        )

        assert len(result.article_image_urls) == 1

    def test_selects_highest_weight_articles(self):
        client = StubImageClient()
        storage = StubEditionStorage()

        articles = [
            {"headline": "Low", "weight": 5, "imagePrompt": "low", "slug": "low"},
            {"headline": "High", "weight": 100, "imagePrompt": "high", "slug": "high"},
            {"headline": "Mid", "weight": 50, "imagePrompt": "mid", "slug": "mid"},
        ]

        result = generate_images_for_newspaper(
            newspaper_id="aspirant",
            articles=articles,
            front_page_image_prompt=None,
            imagen_client=client,
            storage=storage,
            edition_id="ed-002",
            max_article_images=2,
        )

        # Should pick index 1 (weight 100) and index 2 (weight 50)
        assert 1 in result.article_image_urls
        assert 2 in result.article_image_urls
        assert 0 not in result.article_image_urls

    def test_skips_articles_without_image_prompt(self):
        client = StubImageClient()
        storage = StubEditionStorage()

        articles = [
            {"headline": "A", "weight": 100, "imagePrompt": "gen me", "slug": "a"},
            {"headline": "B", "weight": 90, "imagePrompt": None, "slug": "b"},
            {"headline": "C", "weight": 80, "imagePrompt": "", "slug": "c"},
            {"headline": "D", "weight": 70, "imagePrompt": "gen me too", "slug": "d"},
        ]

        result = generate_images_for_newspaper(
            newspaper_id="owner",
            articles=articles,
            front_page_image_prompt=None,
            imagen_client=client,
            storage=storage,
            edition_id="ed-003",
        )

        # Only articles at index 0 and 3 have non-empty imagePrompt
        assert len(result.article_image_urls) == 2
        assert 0 in result.article_image_urls
        assert 3 in result.article_image_urls
        assert 1 not in result.article_image_urls
        assert 2 not in result.article_image_urls

    def test_generates_hero_image(self):
        client = StubImageClient()
        storage = StubEditionStorage()

        result = generate_images_for_newspaper(
            newspaper_id="sovereign",
            articles=[],
            front_page_image_prompt="A grand government building",
            imagen_client=client,
            storage=storage,
            edition_id="ed-001",
        )

        assert result.hero_image_url is not None
        assert "hero.webp" in result.hero_image_url
        assert "editions/ed-001/sovereign/hero.webp" in storage._images

    def test_no_hero_when_prompt_is_none(self):
        client = StubImageClient()
        storage = StubEditionStorage()

        result = generate_images_for_newspaper(
            newspaper_id="sovereign",
            articles=[],
            front_page_image_prompt=None,
            imagen_client=client,
            storage=storage,
            edition_id="ed-001",
        )

        assert result.hero_image_url is None
        assert len(storage._images) == 0

    def test_failure_non_blocking_articles(self):
        """When image generation fails for an article, the pipeline continues."""
        client = StubImageClient(should_fail=True)
        storage = StubEditionStorage()
        articles = _make_articles(2)

        result = generate_images_for_newspaper(
            newspaper_id="radical",
            articles=articles,
            front_page_image_prompt="Hero prompt",
            imagen_client=client,
            storage=storage,
            edition_id="ed-001",
        )

        # All generations failed but no exception raised
        assert len(result.article_image_urls) == 0
        assert result.hero_image_url is None
        assert len(storage._images) == 0
        # Client was still called for each candidate + hero
        assert len(client._calls) == 3  # 2 articles + 1 hero

    def test_partial_failure(self):
        """Some images fail, others succeed — only successful ones returned."""

        class PartialClient(StubImageClient):
            def generate(self, prompt: str) -> bytes | None:
                self._calls.append(prompt)
                # Fail for the first call only
                if len(self._calls) == 1:
                    return None
                return self.STUB_WEBP

        client = PartialClient()
        storage = StubEditionStorage()
        articles = _make_articles(2)

        result = generate_images_for_newspaper(
            newspaper_id="moralist",
            articles=articles,
            front_page_image_prompt=None,
            imagen_client=client,
            storage=storage,
            edition_id="ed-001",
        )

        # First article fails, second succeeds
        assert len(result.article_image_urls) == 1
        assert len(storage._images) == 1

    def test_storage_urls_contain_newspaper_id(self):
        client = StubImageClient()
        storage = StubEditionStorage()
        articles = _make_articles(1)

        result = generate_images_for_newspaper(
            newspaper_id="hedonist",
            articles=articles,
            front_page_image_prompt="Hero!",
            imagen_client=client,
            storage=storage,
            edition_id="ed-007",
        )

        for url in result.article_image_urls.values():
            assert "hedonist" in url
            assert "ed-007" in url

        assert "hedonist" in result.hero_image_url
        assert "ed-007" in result.hero_image_url

    def test_empty_articles_list(self):
        client = StubImageClient()
        storage = StubEditionStorage()

        result = generate_images_for_newspaper(
            newspaper_id="sovereign",
            articles=[],
            front_page_image_prompt=None,
            imagen_client=client,
            storage=storage,
            edition_id="ed-001",
        )

        assert result.article_image_urls == {}
        assert result.hero_image_url is None
        assert len(client._calls) == 0
