"""Tests for the database access layer."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from newsroom_director.db import (
    Base,
    CategorisedPromptRow,
    PaymentRefRow,
    PromptRow,
    WorldLedgerHistoryRow,
    fetch_unprocessed_prompts,
    load_world_ledger,
    mark_prompts_processed,
    save_edition,
    save_world_ledger,
)


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture()
def seeded_session(db_session):
    """Session with sample prompts, categories, and payments."""
    # Payment ref
    pay = PaymentRefRow(
        id="pay-1",
        provider_transaction_id="tx-100",
        amount=5.0,
        currency="USD",
        status="settled",
    )
    db_session.add(pay)

    # Prompt 1 — accepted, with payment
    p1 = PromptRow(
        id="p-1",
        text="What about the Caspian crisis?",
        payment_ref="tx-100",
        status="accepted",
    )
    db_session.add(p1)
    db_session.add(
        CategorisedPromptRow(
            id="cp-1", prompt_id="p-1", category_id="geopolitics"
        )
    )
    db_session.add(
        CategorisedPromptRow(
            id="cp-2", prompt_id="p-1", category_id="energy"
        )
    )

    # Prompt 2 — accepted, no payment
    p2 = PromptRow(
        id="p-2",
        text="Celebrity scandal update",
        payment_ref=None,
        status="accepted",
    )
    db_session.add(p2)
    db_session.add(
        CategorisedPromptRow(
            id="cp-3", prompt_id="p-2", category_id="entertainment"
        )
    )

    # Prompt 3 — already processed
    p3 = PromptRow(
        id="p-3",
        text="Old prompt",
        payment_ref=None,
        status="processed",
    )
    db_session.add(p3)

    db_session.commit()
    return db_session


class TestFetchUnprocessedPrompts:
    def test_returns_accepted_prompts(self, seeded_session):
        results = fetch_unprocessed_prompts(seeded_session)
        ids = {r.prompt_id for r in results}
        assert ids == {"p-1", "p-2"}

    def test_excludes_processed(self, seeded_session):
        results = fetch_unprocessed_prompts(seeded_session)
        ids = {r.prompt_id for r in results}
        assert "p-3" not in ids

    def test_includes_payment_amount(self, seeded_session):
        results = fetch_unprocessed_prompts(seeded_session)
        p1 = next(r for r in results if r.prompt_id == "p-1")
        assert p1.payment_amount == 5.0

    def test_no_payment_has_zero_amount(self, seeded_session):
        results = fetch_unprocessed_prompts(seeded_session)
        p2 = next(r for r in results if r.prompt_id == "p-2")
        assert p2.payment_amount == 0.0

    def test_includes_categories(self, seeded_session):
        results = fetch_unprocessed_prompts(seeded_session)
        p1 = next(r for r in results if r.prompt_id == "p-1")
        assert set(p1.category_ids) == {"geopolitics", "energy"}


class TestMarkPromptsProcessed:
    def test_updates_status(self, seeded_session):
        mark_prompts_processed(seeded_session, ["p-1", "p-2"])
        seeded_session.commit()
        results = fetch_unprocessed_prompts(seeded_session)
        assert len(results) == 0

    def test_empty_list_no_error(self, seeded_session):
        mark_prompts_processed(seeded_session, [])


class TestWorldLedger:
    def test_load_returns_none_when_empty(self, db_session):
        assert load_world_ledger(db_session) is None

    def test_save_and_load_roundtrip(self, db_session):
        ledger = {"epoch": "Test", "nations": []}
        save_world_ledger(db_session, ledger)
        db_session.commit()

        loaded = load_world_ledger(db_session)
        assert loaded == ledger

    def test_save_upserts(self, db_session):
        save_world_ledger(db_session, {"epoch": "V1"})
        db_session.commit()
        save_world_ledger(db_session, {"epoch": "V2"})
        db_session.commit()

        loaded = load_world_ledger(db_session)
        assert loaded["epoch"] == "V2"

    def test_save_records_history(self, db_session):
        save_world_ledger(db_session, {"epoch": "V1"}, edition_date="2026-03-20")
        db_session.commit()
        save_world_ledger(db_session, {"epoch": "V2"}, edition_date="2026-03-21")
        db_session.commit()

        history = (
            db_session.query(WorldLedgerHistoryRow)
            .order_by(WorldLedgerHistoryRow.created_at.asc())
            .all()
        )
        assert len(history) == 2
        assert history[0].edition_date == "2026-03-20"
        assert history[1].edition_date == "2026-03-21"


class TestSaveEdition:
    def test_creates_edition_and_articles(self, db_session):
        articles = {
            "sovereign": "Article content 1",
            "aspirant": "Article content 2",
        }
        edition_id = save_edition(db_session, "2026-03-01", articles)
        db_session.commit()

        assert edition_id is not None
        assert len(edition_id) == 36  # UUID format
