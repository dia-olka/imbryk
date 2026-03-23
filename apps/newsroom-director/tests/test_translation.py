"""Tests for the translation pipeline."""

import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from newsroom_director.db import Base, save_edition
from newsroom_director.storage import StubEditionStorage
from newsroom_director.translation.budget import TranslationBudget
from newsroom_director.translation.client import StubTranslationClient
from newsroom_director.translation.main import (
    _batch_texts_for_article,
    _extract_articles,
    _translate_all,
    run_translation,
)


@pytest.fixture()
def db_url(tmp_path):
    """Create a temporary SQLite database with schema."""
    db_path = tmp_path / "test.db"
    url = f"sqlite:///{db_path}"
    engine = create_engine(url)
    Base.metadata.create_all(bind=engine)
    return url


@pytest.fixture()
def db_session(db_url):
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _seed_edition(session, date="2026-03-23"):
    """Insert a minimal edition with articles."""
    sovereign_content = json.dumps({
        "newspaper_name": "The Sovereign",
        "articles": [
            {
                "headline": "Global Summit Reaches Agreement",
                "body": "World leaders gathered to sign a historic accord.",
                "imageAlt": "Leaders shaking hands",
            },
            {
                "headline": "Defence Spending Rises",
                "body": "Military budgets increase across NATO.",
                "imageAlt": "Soldiers in formation",
            },
            {
                "headline": "Third Article Filler",
                "body": "Not a lead.",
            },
        ],
    })
    aspirant_content = json.dumps({
        "newspaper_name": "The Aspirant",
        "articles": [
            {
                "headline": "Startup Boom Continues",
                "body": "Venture capital flows at record pace.",
                "imageAlt": "Silicon Valley office",
            },
        ],
    })
    curator_content = json.dumps({
        "text": "## CONSENSUS\nAll agree.",
    })
    articles = {
        "sovereign": sovereign_content,
        "aspirant": aspirant_content,
        "curator": curator_content,
    }
    return save_edition(session, date, articles)


# --- Unit tests ---


class TestExtractArticles:
    def test_extracts_all_articles(self):
        content = json.dumps({
            "articles": [
                {"headline": "A", "body": "Body A"},
                {"headline": "B", "body": "Body B"},
                {"headline": "C", "body": "Body C"},
            ],
        })
        articles = _extract_articles(content)
        assert len(articles) == 3
        assert articles[0]["headline"] == "A"
        assert articles[0]["original_index"] == 0
        assert articles[2]["headline"] == "C"
        assert articles[2]["original_index"] == 2

    def test_skips_empty_articles(self):
        content = json.dumps({
            "articles": [
                {"headline": "", "body": ""},
                {"headline": "Real", "body": "Content"},
            ],
        })
        articles = _extract_articles(content)
        assert len(articles) == 1
        assert articles[0]["headline"] == "Real"

    def test_handles_malformed_json(self):
        assert _extract_articles("not json") == []

    def test_includes_image_alt(self):
        content = json.dumps({
            "articles": [
                {"headline": "A", "body": "B", "imageAlt": "Alt text"},
            ],
        })
        articles = _extract_articles(content)
        assert articles[0]["imageAlt"] == "Alt text"

    def test_missing_image_alt(self):
        content = json.dumps({
            "articles": [{"headline": "A", "body": "B"}],
        })
        articles = _extract_articles(content)
        assert articles[0]["imageAlt"] == ""


class TestBatchTextsForArticle:
    def test_all_fields(self):
        article = {"headline": "H", "body": "B", "imageAlt": "I", "original_index": 0}
        pairs = _batch_texts_for_article(article)
        assert len(pairs) == 3
        assert pairs[0] == ("headline", "H")
        assert pairs[1] == ("body", "B")
        assert pairs[2] == ("imageAlt", "I")

    def test_skips_empty_fields(self):
        article = {"headline": "H", "body": "", "imageAlt": "", "original_index": 0}
        pairs = _batch_texts_for_article(article)
        assert len(pairs) == 1
        assert pairs[0] == ("headline", "H")


class TestTranslateAll:
    def test_respects_batch_size(self):
        client = StubTranslationClient()
        texts = [f"text {i}" for i in range(30)]
        results = _translate_all(client, texts, "es")
        assert len(results) == 30
        # StubTranslationClient has max_batch_size=25, so should be 2 calls
        assert len(client.calls) == 2
        assert len(client.calls[0]["texts"]) == 25
        assert len(client.calls[1]["texts"]) == 5

    def test_handles_empty(self):
        client = StubTranslationClient()
        results = _translate_all(client, [], "es")
        assert results == []

    def test_failed_client_returns_nones(self):
        client = StubTranslationClient(should_fail=True)
        results = _translate_all(client, ["hello", "world"], "es")
        assert results == [None, None]


class TestTranslationBudget:
    def test_initial_remaining_is_full_budget(self):
        store = StubEditionStorage()
        budget = TranslationBudget(store, "stub", monthly_limit=1000)
        assert budget.remaining() == 1000

    def test_record_usage_decrements(self):
        store = StubEditionStorage()
        budget = TranslationBudget(store, "stub", monthly_limit=1000)
        budget.record_usage(300)
        assert budget.remaining() == 700

    def test_would_exceed(self):
        store = StubEditionStorage()
        budget = TranslationBudget(store, "stub", monthly_limit=1000)
        budget.record_usage(800)
        assert budget.would_exceed(201) is True
        assert budget.would_exceed(200) is False

    def test_persists_to_storage(self):
        store = StubEditionStorage()
        budget = TranslationBudget(store, "azure", monthly_limit=5000)
        budget.record_usage(1234)

        # Check that the usage was written to _raw
        assert len(store._raw) == 1
        key = list(store._raw.keys())[0]
        assert "usage-azure-" in key
        data = json.loads(store._raw[key])
        assert data["chars_used"] == 1234
        assert data["provider"] == "azure"


# --- Integration tests ---


class TestRunTranslation:
    def test_translates_all_articles_for_all_languages(self, db_url, db_session, tmp_path):
        edition_id = _seed_edition(db_session)
        db_session.commit()

        store = StubEditionStorage()
        # Seed the R2 index so the orchestrator can find the edition_id
        index = json.dumps([{"edition_id": edition_id, "date": "2026-03-23", "newspaper_ids": ["sovereign", "aspirant"]}])
        store.write_raw("editions/index.json", index.encode("utf-8"), "application/json")

        client = StubTranslationClient()

        # Write a temporary languages.json
        languages_json = tmp_path / "data" / "languages.json"
        languages_json.parent.mkdir(parents=True)
        languages_json.write_text(json.dumps({
            "system": [
                {"code": "es", "locale": "es_ES", "name": "Spanish", "nativeName": "Español", "dir": "ltr", "dateLocale": "es-ES"},
                {"code": "fr", "locale": "fr_FR", "name": "French", "nativeName": "Français", "dir": "ltr", "dateLocale": "fr-FR"},
            ],
            "ui": {},
        }))

        # Patch _load_system_languages to use our test file
        import newsroom_director.translation.main as mod
        original = mod._load_system_languages

        def _patched():
            data = json.loads(languages_json.read_text())
            return data.get("system", [])

        mod._load_system_languages = _patched

        try:
            summary = run_translation(
                database_url=db_url,
                storage=store,
                translator=client,
                edition_date="2026-03-23",
            )
        finally:
            mod._load_system_languages = original

        # 2 article translations + 2 timeline translations = 4
        assert summary["translations_written"] == 4
        assert summary["languages_attempted"] == 2
        assert summary["total_chars"] > 0

        # Verify R2 files written
        es_key = f"editions/2026-03-23/translations/es/{edition_id}.json"
        fr_key = f"editions/2026-03-23/translations/fr/{edition_id}.json"
        es_data = store.read_json(es_key)
        fr_data = store.read_json(fr_key)
        assert es_data is not None
        assert fr_data is not None
        assert es_data["lang"] == "es"
        assert es_data["provider"] == "stub"
        assert "sovereign" in es_data["articles"]
        assert "aspirant" in es_data["articles"]
        # Curator should NOT be translated
        assert "curator" not in es_data["articles"]
        # All 3 sovereign articles should be translated (not just leads)
        assert len(es_data["articles"]["sovereign"]) == 3
        # 1 aspirant article
        assert len(es_data["articles"]["aspirant"]) == 1

        # Verify timeline translations written
        es_timeline = store.read_json("translations/_meta/timeline-es.json")
        fr_timeline = store.read_json("translations/_meta/timeline-fr.json")
        assert es_timeline is not None
        assert fr_timeline is not None
        assert es_timeline["lang"] == "es"
        assert len(es_timeline["history"]) > 0

    def test_idempotent_skip(self, db_url, db_session, tmp_path):
        """If translation already exists in R2, skip it."""
        edition_id = _seed_edition(db_session)
        db_session.commit()

        store = StubEditionStorage()
        index = json.dumps([{"edition_id": edition_id, "date": "2026-03-23"}])
        store.write_raw("editions/index.json", index.encode("utf-8"), "application/json")

        # Pre-seed the Spanish article translation
        es_key = f"editions/2026-03-23/translations/es/{edition_id}.json"
        store.write_raw(es_key, json.dumps({"existing": True}).encode("utf-8"), "application/json")
        # Pre-seed the Spanish timeline translation
        store.write_raw(
            "translations/_meta/timeline-es.json",
            json.dumps({"existing": True}).encode("utf-8"),
            "application/json",
        )

        client = StubTranslationClient()

        languages_json = tmp_path / "data" / "languages.json"
        languages_json.parent.mkdir(parents=True)
        languages_json.write_text(json.dumps({
            "system": [
                {"code": "es", "locale": "es_ES", "name": "Spanish", "nativeName": "Español", "dir": "ltr", "dateLocale": "es-ES"},
            ],
            "ui": {},
        }))

        import newsroom_director.translation.main as mod
        original = mod._load_system_languages

        def _patched():
            data = json.loads(languages_json.read_text())
            return data.get("system", [])

        mod._load_system_languages = _patched

        try:
            summary = run_translation(
                database_url=db_url,
                storage=store,
                translator=client,
                edition_date="2026-03-23",
            )
        finally:
            mod._load_system_languages = original

        # Should skip — no translations written
        assert summary["translations_written"] == 0
        # Client should not have been called
        assert len(client.calls) == 0

    def test_no_edition_returns_early(self, db_url, tmp_path):
        store = StubEditionStorage()
        client = StubTranslationClient()

        languages_json = tmp_path / "data" / "languages.json"
        languages_json.parent.mkdir(parents=True)
        languages_json.write_text(json.dumps({
            "system": [{"code": "es", "locale": "es_ES", "name": "Spanish", "nativeName": "Español", "dir": "ltr", "dateLocale": "es-ES"}],
            "ui": {},
        }))

        import newsroom_director.translation.main as mod
        original = mod._load_system_languages

        def _patched():
            data = json.loads(languages_json.read_text())
            return data.get("system", [])

        mod._load_system_languages = _patched

        try:
            summary = run_translation(
                database_url=db_url,
                storage=store,
                translator=client,
                edition_date="2026-03-23",
            )
        finally:
            mod._load_system_languages = original

        assert summary["reason"] == "no_edition"

    def test_budget_exceeded_skips_language(self, db_url, db_session, tmp_path):
        """When budget is exhausted, language is skipped."""
        edition_id = _seed_edition(db_session)
        db_session.commit()

        store = StubEditionStorage()
        index = json.dumps([{"edition_id": edition_id, "date": "2026-03-23"}])
        store.write_raw("editions/index.json", index.encode("utf-8"), "application/json")

        client = StubTranslationClient()

        languages_json = tmp_path / "data" / "languages.json"
        languages_json.parent.mkdir(parents=True)
        languages_json.write_text(json.dumps({
            "system": [
                {"code": "es", "locale": "es_ES", "name": "Spanish", "nativeName": "Español", "dir": "ltr", "dateLocale": "es-ES"},
            ],
            "ui": {},
        }))

        import newsroom_director.translation.main as mod
        original_load = mod._load_system_languages

        def _patched():
            data = json.loads(languages_json.read_text())
            return data.get("system", [])

        mod._load_system_languages = _patched

        # Patch TRANSLATION_CHAR_BUDGET to a tiny value (1 char)
        import newsroom_director.translation.main as tmod
        orig_budget = tmod.TRANSLATION_CHAR_BUDGET
        tmod.TRANSLATION_CHAR_BUDGET = "1"

        try:
            summary = run_translation(
                database_url=db_url,
                storage=store,
                translator=client,
                edition_date="2026-03-23",
            )
        finally:
            mod._load_system_languages = original_load
            tmod.TRANSLATION_CHAR_BUDGET = orig_budget

        assert summary["translations_written"] == 0
        assert len(client.calls) == 0
