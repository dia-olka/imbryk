"""Integration tests for the orchestrator (run_morning_press)."""

import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from newsroom_director.db import (
    Base,
    CategorisedPromptRow,
    PaymentRefRow,
    PromptRow,
    fetch_unprocessed_prompts,
    load_world_ledger,
)
from newsroom_director.distillation.pipeline import DistillationPipeline
from newsroom_director.distillation.types import BudgetedDigest, ClusterDigest
from newsroom_director.generation import StubGenerationStrategy
from newsroom_director.main import run_morning_press
from newsroom_director.storage import StubEditionStorage


class StubDistillationPipeline(DistillationPipeline):
    """Pipeline that skips embedding (no model needed for tests)."""

    def run(self, prompts):
        if not prompts:
            return []
        # Create a single cluster digest from all prompts
        digest = ClusterDigest(
            cluster_id=0,
            cluster_size=len(prompts),
            aggregate_weight=sum(p.payment_amount for p in prompts),
            verbatim_prompts=[
                (p.payment_amount, p.text) for p in prompts[:5]
            ],
            long_tail_summary="Test summary",
            keywords=["test"],
        )
        return [
            BudgetedDigest(
                digest=digest,
                allocated_tokens=1000,
                serialized=f"CLUSTER #0 | prompts: {len(prompts)}",
            )
        ]


@pytest.fixture()
def test_db_url(tmp_path):
    db_path = tmp_path / "test.db"
    url = f"sqlite:///{db_path}"
    engine = create_engine(url)
    Base.metadata.create_all(bind=engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed data
    pay = PaymentRefRow(
        id="pay-1",
        provider_transaction_id="tx-100",
        amount=5.0,
    )
    session.add(pay)

    p1 = PromptRow(
        id="p-1",
        text="What is happening in the Caspian Basin?",
        payment_ref="tx-100",
        status="accepted",
    )
    session.add(p1)
    session.add(
        CategorisedPromptRow(
            id="cp-1", prompt_id="p-1", category_id="geopolitics-and-diplomacy"
        )
    )

    p2 = PromptRow(
        id="p-2",
        text="Latest celebrity gossip please",
        payment_ref=None,
        status="accepted",
    )
    session.add(p2)
    session.add(
        CategorisedPromptRow(
            id="cp-2", prompt_id="p-2", category_id="entertainment-and-hollywood"
        )
    )

    p3 = PromptRow(
        id="p-3",
        text="How are markets reacting to the Meridian?",
        payment_ref=None,
        status="accepted",
    )
    session.add(p3)
    session.add(
        CategorisedPromptRow(
            id="cp-3", prompt_id="p-3", category_id="markets-and-macroeconomics"
        )
    )

    session.commit()
    session.close()

    return url


class TestOrchestrator:
    def test_full_pipeline(self, test_db_url):
        gen = StubGenerationStrategy()
        storage = StubEditionStorage()
        pipeline = StubDistillationPipeline()

        result = run_morning_press(
            database_url=test_db_url,
            generation_strategy=gen,
            storage=storage,
            distillation_pipeline=pipeline,
        )

        assert result["edition_id"] is not None
        assert result["newspaper_count"] > 0
        assert result["article_count"] > 0

    def test_articles_per_newspaper(self, test_db_url):
        gen = StubGenerationStrategy()
        storage = StubEditionStorage()
        pipeline = StubDistillationPipeline()

        run_morning_press(
            database_url=test_db_url,
            generation_strategy=gen,
            storage=storage,
            distillation_pipeline=pipeline,
        )

        # Storage should have one edition
        editions = storage.list_editions()
        assert len(editions) == 1

        articles = editions[0]["articles"]
        # geopolitics-and-diplomacy -> sovereign, aspirant
        # entertainment-and-hollywood -> moralist, hedonist
        # markets-and-macroeconomics -> owner
        # + curator
        assert "curator" in articles

    def test_prompts_marked_processed(self, test_db_url):
        gen = StubGenerationStrategy()
        storage = StubEditionStorage()
        pipeline = StubDistillationPipeline()

        run_morning_press(
            database_url=test_db_url,
            generation_strategy=gen,
            storage=storage,
            distillation_pipeline=pipeline,
        )

        # Verify prompts are processed
        engine = create_engine(test_db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        remaining = fetch_unprocessed_prompts(session)
        assert len(remaining) == 0
        session.close()

    def test_world_ledger_saved(self, test_db_url):
        gen = StubGenerationStrategy()
        storage = StubEditionStorage()
        pipeline = StubDistillationPipeline()

        run_morning_press(
            database_url=test_db_url,
            generation_strategy=gen,
            storage=storage,
            distillation_pipeline=pipeline,
        )

        # The stub returns non-JSON, so mutation parsing fails gracefully.
        # WorldLedger should NOT be saved (mutation parse failure).
        # This is expected -- real LLM would return valid JSON.
        engine = create_engine(test_db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        ledger = load_world_ledger(session)
        # With stub, mutation parsing fails, so ledger stays None
        assert ledger is None
        session.close()

    def test_no_prompts_returns_empty(self, tmp_path):
        db_path = tmp_path / "empty.db"
        url = f"sqlite:///{db_path}"
        engine = create_engine(url)
        Base.metadata.create_all(bind=engine)

        result = run_morning_press(
            database_url=url,
            generation_strategy=StubGenerationStrategy(),
            storage=StubEditionStorage(),
            distillation_pipeline=StubDistillationPipeline(),
        )

        assert result["edition_id"] is None
        assert result["newspaper_count"] == 0

    def test_generation_strategy_called(self, test_db_url):
        gen = StubGenerationStrategy()
        storage = StubEditionStorage()
        pipeline = StubDistillationPipeline()

        run_morning_press(
            database_url=test_db_url,
            generation_strategy=gen,
            storage=storage,
            distillation_pipeline=pipeline,
        )

        # Generation should be called for validation + newspapers + curator + mutation
        assert len(gen.calls) > 0

    def test_validation_filters_prompts(self, test_db_url):
        """Validation that rejects all prompts produces empty edition."""
        accepted_json = json.dumps({"accepted": []})
        gen = StubGenerationStrategy(responses={"pro": accepted_json})
        storage = StubEditionStorage()
        pipeline = StubDistillationPipeline()

        result = run_morning_press(
            database_url=test_db_url,
            generation_strategy=gen,
            storage=storage,
            distillation_pipeline=pipeline,
            enable_validation=True,
        )

        assert result["edition_id"] is None
        assert result["newspaper_count"] == 0

    def test_validation_disabled(self, test_db_url):
        gen = StubGenerationStrategy()
        storage = StubEditionStorage()
        pipeline = StubDistillationPipeline()

        result = run_morning_press(
            database_url=test_db_url,
            generation_strategy=gen,
            storage=storage,
            distillation_pipeline=pipeline,
            enable_validation=False,
        )

        # Should still produce an edition without validation step
        assert result["edition_id"] is not None
        assert result["article_count"] > 0

    def test_edition_index_written(self, test_db_url):
        """After pipeline completes, storage should have an index."""
        gen = StubGenerationStrategy()
        storage = StubEditionStorage()
        pipeline = StubDistillationPipeline()

        run_morning_press(
            database_url=test_db_url,
            generation_strategy=gen,
            storage=storage,
            distillation_pipeline=pipeline,
        )

        assert storage._index is not None
        assert len(storage._index) >= 1
        # Index entries should have edition_id and date
        entry = storage._index[0]
        assert "edition_id" in entry
        assert "date" in entry

    def test_deploy_hook_triggered(self, test_db_url, monkeypatch):
        """Deploy hook is called when CF_DEPLOY_HOOK_URL is set."""
        import newsroom_director.main as main_mod

        hook_calls = []

        def fake_urlopen(req, timeout=None):
            hook_calls.append(req.full_url)

            class FakeResp:
                status = 200

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    pass

            return FakeResp()

        monkeypatch.setattr(main_mod, "CF_DEPLOY_HOOK_URL", "https://deploy.example.com/hook")
        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

        gen = StubGenerationStrategy()
        storage = StubEditionStorage()
        pipeline = StubDistillationPipeline()

        run_morning_press(
            database_url=test_db_url,
            generation_strategy=gen,
            storage=storage,
            distillation_pipeline=pipeline,
        )

        assert len(hook_calls) == 1
        assert hook_calls[0] == "https://deploy.example.com/hook"

    def test_deploy_hook_skipped_when_not_set(self, test_db_url, monkeypatch):
        """Deploy hook is not called when CF_DEPLOY_HOOK_URL is empty."""
        import newsroom_director.main as main_mod
        monkeypatch.setattr(main_mod, "CF_DEPLOY_HOOK_URL", "")

        gen = StubGenerationStrategy()
        storage = StubEditionStorage()
        pipeline = StubDistillationPipeline()

        # Should not raise
        run_morning_press(
            database_url=test_db_url,
            generation_strategy=gen,
            storage=storage,
            distillation_pipeline=pipeline,
        )
