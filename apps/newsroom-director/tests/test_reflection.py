"""Tests for editorial self-reflection module."""


import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from newsroom_director.db import (
    Base,
    JournalEntry,
    load_recent_journal,
    save_journal_entry,
)
from newsroom_director.generation import StubGenerationStrategy
from newsroom_director.personas import SOVEREIGN
from newsroom_director.reflection import (
    format_journal_for_generation,
    run_persona_reflection,
    run_pipeline_observation,
)


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# --- DB layer tests ---


class TestSaveJournalEntry:
    def test_insert(self, db_session):
        save_journal_entry(
            db_session, "sovereign", "2026-03-14", "reflection",
            "## What Worked\n- Good coverage of Iran crisis",
        )
        db_session.commit()

        entries = load_recent_journal(
            db_session, "sovereign", lookback_days=7,
            current_date="2026-03-15",
        )
        assert len(entries) == 1
        assert entries[0].persona_id == "sovereign"
        assert entries[0].entry_type == "reflection"
        assert "Iran crisis" in entries[0].content

    def test_upsert_replaces_content(self, db_session):
        save_journal_entry(
            db_session, "sovereign", "2026-03-14", "reflection", "V1",
        )
        db_session.commit()
        save_journal_entry(
            db_session, "sovereign", "2026-03-14", "reflection", "V2",
        )
        db_session.commit()

        entries = load_recent_journal(
            db_session, "sovereign", lookback_days=7,
            current_date="2026-03-15",
        )
        assert len(entries) == 1
        assert entries[0].content == "V2"

    def test_different_types_coexist(self, db_session):
        save_journal_entry(
            db_session, "sovereign", "2026-03-14",
            "reflection", "Reflection text",
        )
        save_journal_entry(
            db_session, "sovereign", "2026-03-14",
            "intention", "Intention text",
        )
        db_session.commit()

        entries = load_recent_journal(
            db_session, "sovereign", lookback_days=7,
            current_date="2026-03-15",
        )
        assert len(entries) == 2
        types = {e.entry_type for e in entries}
        assert types == {"reflection", "intention"}


class TestLoadRecentJournal:
    def test_respects_lookback_window(self, db_session):
        # Entry within window
        save_journal_entry(
            db_session, "sovereign", "2026-03-13", "reflection", "Recent",
        )
        # Entry outside window (8 days ago)
        save_journal_entry(
            db_session, "sovereign", "2026-03-06", "reflection", "Old",
        )
        db_session.commit()

        entries = load_recent_journal(
            db_session, "sovereign", lookback_days=7,
            current_date="2026-03-15",
        )
        assert len(entries) == 1
        assert entries[0].content == "Recent"

    def test_excludes_current_date(self, db_session):
        save_journal_entry(
            db_session, "sovereign", "2026-03-15", "reflection", "Today",
        )
        db_session.commit()

        entries = load_recent_journal(
            db_session, "sovereign", lookback_days=7,
            current_date="2026-03-15",
        )
        assert len(entries) == 0

    def test_includes_pipeline_observations(self, db_session):
        save_journal_entry(
            db_session, "sovereign", "2026-03-14", "reflection", "My reflection",
        )
        save_journal_entry(
            db_session, "_pipeline", "2026-03-14", "observation", "Pipeline obs",
        )
        db_session.commit()

        entries = load_recent_journal(
            db_session, "sovereign", lookback_days=7,
            current_date="2026-03-15",
        )
        assert len(entries) == 2
        persona_ids = {e.persona_id for e in entries}
        assert persona_ids == {"sovereign", "_pipeline"}

    def test_empty_when_no_entries(self, db_session):
        entries = load_recent_journal(
            db_session, "sovereign", lookback_days=7,
            current_date="2026-03-15",
        )
        assert entries == []

    def test_ordered_by_date_ascending(self, db_session):
        save_journal_entry(
            db_session, "sovereign", "2026-03-14", "reflection", "Day 2",
        )
        save_journal_entry(
            db_session, "sovereign", "2026-03-13", "reflection", "Day 1",
        )
        db_session.commit()

        entries = load_recent_journal(
            db_session, "sovereign", lookback_days=7,
            current_date="2026-03-15",
        )
        assert entries[0].content == "Day 1"
        assert entries[1].content == "Day 2"


# --- Formatting tests ---


class TestFormatJournalForGeneration:
    def test_empty_entries(self):
        result = format_journal_for_generation([], "sovereign")
        assert "No editorial journal" in result

    def test_includes_latest_intention(self):
        entries = [
            JournalEntry("sovereign", "2026-03-13", "intention", "Focus on energy"),
            JournalEntry("sovereign", "2026-03-14", "intention", "Cover Iran"),
        ]
        result = format_journal_for_generation(entries, "sovereign")
        assert "Cover Iran" in result
        assert "LATEST EDITORIAL INTENTION" in result

    def test_includes_recent_reflections(self):
        entries = [
            JournalEntry("sovereign", "2026-03-12", "reflection", "Reflection A"),
            JournalEntry("sovereign", "2026-03-13", "reflection", "Reflection B"),
            JournalEntry("sovereign", "2026-03-14", "reflection", "Reflection C"),
        ]
        result = format_journal_for_generation(entries, "sovereign")
        assert "Reflection A" in result
        assert "Reflection B" in result
        assert "Reflection C" in result

    def test_includes_pipeline_observation(self):
        entries = [
            JournalEntry("sovereign", "2026-03-14", "reflection", "My stuff"),
            JournalEntry("_pipeline", "2026-03-14", "observation", "Cross-pub note"),
        ]
        result = format_journal_for_generation(entries, "sovereign")
        assert "Cross-pub note" in result
        assert "EDITORIAL DIRECTOR" in result

    def test_caps_at_3_reflections(self):
        entries = [
            JournalEntry("sovereign", f"2026-03-{10+i:02d}", "reflection", f"R{i}")
            for i in range(5)
        ]
        result = format_journal_for_generation(entries, "sovereign")
        # Should only include last 3
        assert "R2" in result
        assert "R3" in result
        assert "R4" in result
        assert "R0" not in result
        assert "R1" not in result


# --- Reflection execution tests ---


class TestRunPersonaReflection:
    def test_returns_reflection_text(self):
        gen = StubGenerationStrategy()
        result = run_persona_reflection(
            persona=SOVEREIGN,
            edition_date="2026-03-14",
            persona_articles_json='{"articles": [{"headline": "Test", "body": "Test body."}]}',
            curator_text="## CONSENSUS\nTest consensus.",
            previous_entries=[],
            generation_strategy=gen,
        )
        # Stub returns plain text for non-schema calls
        assert result is not None
        assert len(result) > 0

    def test_records_call_to_pro_tier(self):
        gen = StubGenerationStrategy()
        run_persona_reflection(
            persona=SOVEREIGN,
            edition_date="2026-03-14",
            persona_articles_json="{}",
            curator_text="",
            previous_entries=[],
            generation_strategy=gen,
        )
        # Reflection should use pro tier
        assert any(c["model_tier"] == "pro" for c in gen.calls)


class TestRunPipelineObservation:
    def test_returns_observation_text(self):
        gen = StubGenerationStrategy()
        result = run_pipeline_observation(
            edition_date="2026-03-14",
            all_articles_text="=== SOVEREIGN ===\nTest articles",
            previous_entries=[],
            generation_strategy=gen,
        )
        assert result is not None

    def test_records_call_to_pro_tier(self):
        gen = StubGenerationStrategy()
        run_pipeline_observation(
            edition_date="2026-03-14",
            all_articles_text="test",
            previous_entries=[],
            generation_strategy=gen,
        )
        # Pipeline observation should use pro tier
        assert any(c["model_tier"] == "pro" for c in gen.calls)
