"""Tests for the image backfill module."""

from __future__ import annotations

import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from newsroom_director.db import (
    Base,
    EditionArticleRow,
    EditionRow,
    fetch_editions_needing_image_backfill,
)
from newsroom_director.image_gen.backfill import BackfillResult, run_image_backfill
from newsroom_director.image_gen.client import StubImageClient
from newsroom_director.storage import StubEditionStorage


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TODAY = "2026-03-07"
YESTERDAY = "2026-03-06"
TWO_DAYS_AGO = "2026-03-05"


def _make_session(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _seed_edition(session, edition_id, date, newspapers: dict[str, list[dict]]):
    """Add an edition + article rows. newspapers maps newspaper_id -> articles list."""
    edition = EditionRow(id=edition_id, date=date, status="published")
    session.add(edition)
    session.flush()

    for newspaper_id, articles in newspapers.items():
        content = json.dumps({"newspaper_name": newspaper_id, "articles": articles})
        session.add(
            EditionArticleRow(
                id=f"{edition_id}-{newspaper_id}",
                edition_id=edition_id,
                newspaper_id=newspaper_id,
                content_json=content,
            )
        )
    session.commit()


def _article(headline="Test", image_prompt=None, image_url=None):
    a = {"headline": headline, "body": "body text"}
    if image_prompt is not None:
        a["imagePrompt"] = image_prompt
    if image_url is not None:
        a["image_url"] = image_url
    return a


# ---------------------------------------------------------------------------
# TestFetchEditionsNeedingImageBackfill
# ---------------------------------------------------------------------------


class TestFetchEditionsNeedingImageBackfill:
    def test_returns_empty_when_no_previous_editions(self, tmp_path):
        session = _make_session(tmp_path)
        # Only today's edition exists
        _seed_edition(
            session,
            "ed-today",
            TODAY,
            {"sovereign": [_article(image_prompt="a prompt")]},
        )
        result = fetch_editions_needing_image_backfill(session, exclude_date=TODAY)
        assert result == []

    def test_returns_target_for_edition_with_missing_images(self, tmp_path):
        session = _make_session(tmp_path)
        _seed_edition(
            session,
            "ed-yest",
            YESTERDAY,
            {"sovereign": [_article(image_prompt="a prompt")]},  # no image_url
        )
        result = fetch_editions_needing_image_backfill(session, exclude_date=TODAY)
        assert len(result) == 1
        assert result[0].edition_id == "ed-yest"
        assert "sovereign" in result[0].newspapers_to_backfill

    def test_excludes_today_edition(self, tmp_path):
        session = _make_session(tmp_path)
        _seed_edition(
            session,
            "ed-today",
            TODAY,
            {"sovereign": [_article(image_prompt="prompt")]},
        )
        _seed_edition(
            session,
            "ed-yest",
            YESTERDAY,
            {"sovereign": [_article(image_prompt="prompt")]},
        )
        result = fetch_editions_needing_image_backfill(session, exclude_date=TODAY)
        assert len(result) == 1
        assert result[0].edition_date == YESTERDAY

    def test_excludes_newspapers_where_all_images_present(self, tmp_path):
        session = _make_session(tmp_path)
        _seed_edition(
            session,
            "ed-yest",
            YESTERDAY,
            {
                "sovereign": [_article(image_prompt="p", image_url="https://done")],
                "aspirant": [_article(image_prompt="p")],  # missing
            },
        )
        result = fetch_editions_needing_image_backfill(session, exclude_date=TODAY)
        assert len(result) == 1
        assert result[0].newspapers_to_backfill == ["aspirant"]
        assert "sovereign" not in result[0].newspapers_to_backfill

    def test_excludes_articles_without_image_prompt(self, tmp_path):
        session = _make_session(tmp_path)
        _seed_edition(
            session,
            "ed-yest",
            YESTERDAY,
            {"sovereign": [_article()]},  # no imagePrompt at all
        )
        result = fetch_editions_needing_image_backfill(session, exclude_date=TODAY)
        assert result == []

    def test_newspaper_articles_includes_all_newspapers(self, tmp_path):
        session = _make_session(tmp_path)
        _seed_edition(
            session,
            "ed-yest",
            YESTERDAY,
            {
                "sovereign": [_article(image_prompt="p")],
                "curator": "synthesis text",  # curator stored as string
            },
        )
        result = fetch_editions_needing_image_backfill(session, exclude_date=TODAY)
        # curator should be in newspaper_articles (needed for write_edition envelope)
        assert "sovereign" in result[0].newspaper_articles
        assert "curator" in result[0].newspaper_articles

    def test_curator_never_in_newspapers_to_backfill(self, tmp_path):
        session = _make_session(tmp_path)
        # Curator content is not a dict with articles — just raw text
        edition = EditionRow(id="ed-yest", date=YESTERDAY, status="published")
        session.add(edition)
        session.flush()
        session.add(EditionArticleRow(
            id="ed-yest-curator",
            edition_id="ed-yest",
            newspaper_id="curator",
            content_json="curator synthesis text",
        ))
        session.add(EditionArticleRow(
            id="ed-yest-sovereign",
            edition_id="ed-yest",
            newspaper_id="sovereign",
            content_json=json.dumps({"articles": [_article(image_prompt="p")]}),
        ))
        session.commit()

        result = fetch_editions_needing_image_backfill(session, exclude_date=TODAY)
        assert "curator" not in result[0].newspapers_to_backfill

    def test_respects_max_editions_limit(self, tmp_path):
        session = _make_session(tmp_path)
        for i in range(10):
            date = f"2026-02-{i + 1:02d}"
            _seed_edition(
                session,
                f"ed-{i}",
                date,
                {"sovereign": [_article(image_prompt="p")]},
            )
        result = fetch_editions_needing_image_backfill(
            session, exclude_date=TODAY, max_editions=3
        )
        assert len(result) == 3

    def test_handles_malformed_content_json_gracefully(self, tmp_path):
        session = _make_session(tmp_path)
        edition = EditionRow(id="ed-bad", date=YESTERDAY, status="published")
        session.add(edition)
        session.flush()
        session.add(EditionArticleRow(
            id="ed-bad-sovereign",
            edition_id="ed-bad",
            newspaper_id="sovereign",
            content_json="NOT VALID JSON {{{{",
        ))
        session.commit()

        # Should not raise, and the malformed row is simply skipped
        result = fetch_editions_needing_image_backfill(session, exclude_date=TODAY)
        assert result == []


# ---------------------------------------------------------------------------
# TestRunImageBackfill
# ---------------------------------------------------------------------------


class TestRunImageBackfill:
    def test_no_previous_editions_returns_zero_result(self, tmp_path):
        session = _make_session(tmp_path)
        _seed_edition(session, "ed-today", TODAY, {"sovereign": [_article()]})

        result = run_image_backfill(
            session=session,
            today_date=TODAY,
            imagen_client=StubImageClient(),
            storage=StubEditionStorage(),
        )
        assert result.editions_scanned == 0
        assert result.images_generated == 0

    def test_generates_missing_images_and_updates_storage(self, tmp_path):
        session = _make_session(tmp_path)
        _seed_edition(
            session,
            "ed-yest",
            YESTERDAY,
            {"sovereign": [_article(image_prompt="a vivid scene")]},
        )
        storage = StubEditionStorage()

        result = run_image_backfill(
            session=session,
            today_date=TODAY,
            imagen_client=StubImageClient(),
            storage=storage,
        )

        assert result.images_generated == 1
        assert result.images_failed == 0
        assert result.editions_updated == 1
        # write_edition should have been called with the updated content
        assert len(storage._editions) == 1
        updated = json.loads(storage._editions[0]["articles"]["sovereign"])
        assert updated["articles"][0]["image_url"].startswith("https://")

    def test_image_url_uses_edition_date_not_uuid(self, tmp_path):
        """Images must be stored under the date path to match main pipeline convention."""
        session = _make_session(tmp_path)
        _seed_edition(
            session,
            "ed-yest-uuid",
            YESTERDAY,
            {"sovereign": [_article(image_prompt="scene")]},
        )
        storage = StubEditionStorage()

        run_image_backfill(
            session=session,
            today_date=TODAY,
            imagen_client=StubImageClient(),
            storage=storage,
        )

        # The image key in StubEditionStorage encodes the edition_id passed to write_image
        image_keys = list(storage._images.keys())
        assert len(image_keys) == 1
        assert YESTERDAY in image_keys[0]
        assert "ed-yest-uuid" not in image_keys[0]

    def test_skips_articles_that_already_have_image_url(self, tmp_path):
        session = _make_session(tmp_path)
        _seed_edition(
            session,
            "ed-yest",
            YESTERDAY,
            {"sovereign": [_article(image_prompt="p", image_url="https://already")]},
        )
        client = StubImageClient()

        result = run_image_backfill(
            session=session,
            today_date=TODAY,
            imagen_client=client,
            storage=StubEditionStorage(),
        )

        assert result.images_generated == 0
        assert client._calls == []

    def test_handles_imagen_failure_gracefully(self, tmp_path):
        session = _make_session(tmp_path)
        _seed_edition(
            session,
            "ed-yest",
            YESTERDAY,
            {"sovereign": [_article(image_prompt="p")]},
        )

        result = run_image_backfill(
            session=session,
            today_date=TODAY,
            imagen_client=StubImageClient(should_fail=True),
            storage=StubEditionStorage(),
        )

        assert result.images_failed == 1
        assert result.images_generated == 0
        assert result.editions_updated == 0  # no successful images → no write_edition

    def test_storage_write_failure_does_not_raise(self, tmp_path):
        session = _make_session(tmp_path)
        _seed_edition(
            session,
            "ed-yest",
            YESTERDAY,
            {"sovereign": [_article(image_prompt="p")]},
        )

        class FailingStorage(StubEditionStorage):
            def write_edition(self, *args, **kwargs):
                raise RuntimeError("R2 unavailable")

        # Should not raise
        result = run_image_backfill(
            session=session,
            today_date=TODAY,
            imagen_client=StubImageClient(),
            storage=FailingStorage(),
        )
        assert result.images_generated == 1
        assert result.editions_updated == 0  # write failed but no exception propagated

    def test_budget_cap_limits_total_images(self, tmp_path):
        session = _make_session(tmp_path)
        # Two editions, each with two articles needing images
        for edition_id, date in [("ed-1", YESTERDAY), ("ed-2", TWO_DAYS_AGO)]:
            _seed_edition(
                session,
                edition_id,
                date,
                {
                    "sovereign": [
                        _article(image_prompt="p1"),
                        _article(image_prompt="p2"),
                    ]
                },
            )

        result = run_image_backfill(
            session=session,
            today_date=TODAY,
            imagen_client=StubImageClient(),
            storage=StubEditionStorage(),
            max_images_per_run=1,
        )

        assert result.images_generated <= 1

    def test_write_edition_includes_all_newspapers(self, tmp_path):
        """write_edition must receive all newspapers, not just the backfilled one."""
        session = _make_session(tmp_path)
        _seed_edition(
            session,
            "ed-yest",
            YESTERDAY,
            {
                "sovereign": [_article(image_prompt="p")],  # needs backfill
                "owner": [_article(image_url="https://already")],  # already done
            },
        )
        storage = StubEditionStorage()

        run_image_backfill(
            session=session,
            today_date=TODAY,
            imagen_client=StubImageClient(),
            storage=storage,
        )

        written = storage._editions[0]["articles"]
        assert "sovereign" in written
        assert "owner" in written

    def test_multiple_newspapers_in_one_edition(self, tmp_path):
        session = _make_session(tmp_path)
        _seed_edition(
            session,
            "ed-yest",
            YESTERDAY,
            {
                "sovereign": [_article(image_prompt="p1")],
                "aspirant": [_article(image_prompt="p2")],
            },
        )
        storage = StubEditionStorage()

        result = run_image_backfill(
            session=session,
            today_date=TODAY,
            imagen_client=StubImageClient(),
            storage=storage,
        )

        assert result.images_generated == 2
        assert result.editions_updated == 1
        # Only one write_edition call (not one per newspaper)
        assert len(storage._editions) == 1
