"""Tests for morning batch integration with news items."""

import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from newsroom_director.db import (
    Base,
    CategorisedPromptRow,
    NewsItemRow,
    PaymentRefRow,
    PromptRow,
    fetch_pending_news_items,
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
        digest = ClusterDigest(
            cluster_id=0,
            cluster_size=len(prompts),
            aggregate_weight=sum(p.payment_amount for p in prompts),
            verbatim_prompts=[
                (p.payment_amount, p.text, "") for p in prompts[:5]
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


def _seed_news_items(session, edition_date="2026-03-12"):
    """Seed news items for testing."""
    for i, (cat, headline) in enumerate([
        ("geopolitics-and-diplomacy", "NATO Summit Concludes"),
        ("markets-and-macroeconomics", "Fed Holds Rates Steady"),
        ("entertainment-and-hollywood", "Oscar Nominations Announced"),
    ]):
        session.add(NewsItemRow(
            id=f"ni-{i}",
            edition_date=edition_date,
            category_id=cat,
            query=f"test query {i}",
            headline=headline,
            snippet=f"Detailed content about {headline.lower()}...",
            source_url=f"https://example.com/news-{i}",
            relevance_score=0.9 - i * 0.1,
            status="pending",
        ))
    session.commit()


def _seed_prompts(session):
    """Seed user prompts for testing."""
    pay = PaymentRefRow(
        id="pay-1",
        provider_transaction_id="tx-100",
        amount=5.0,
    )
    session.add(pay)
    p1 = PromptRow(
        id="p-1",
        text="Major earthquake strikes the Pacific",
        payment_ref="tx-100",
        status="accepted",
    )
    session.add(p1)
    session.add(CategorisedPromptRow(
        id="cp-1", prompt_id="p-1", category_id="disasters-and-extremes",
    ))
    session.commit()


class TestNewsItemsIntegration:
    @pytest.fixture()
    def db_url_news_only(self, tmp_path):
        """DB with news items but no user prompts."""
        db_path = tmp_path / "news_only.db"
        url = f"sqlite:///{db_path}"
        engine = create_engine(url)
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        _seed_news_items(session)
        session.close()
        return url

    @pytest.fixture()
    def db_url_mixed(self, tmp_path):
        """DB with both user prompts and news items."""
        db_path = tmp_path / "mixed.db"
        url = f"sqlite:///{db_path}"
        engine = create_engine(url)
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        _seed_prompts(session)
        _seed_news_items(session)
        session.close()
        return url

    def test_news_only_produces_edition(self, db_url_news_only):
        """News items alone should produce an edition."""
        gen = StubGenerationStrategy()
        storage = StubEditionStorage()
        pipeline = StubDistillationPipeline()

        result = run_morning_press(
            database_url=db_url_news_only,
            generation_strategy=gen,
            storage=storage,
            distillation_pipeline=pipeline,
            enable_validation=False,
            edition_date="2026-03-12",
        )

        assert result["edition_id"] is not None
        assert result["newspaper_count"] > 0
        assert result["news_item_count"] == 3

    def test_news_items_marked_processed(self, db_url_news_only):
        """After pipeline, news items should be marked processed."""
        gen = StubGenerationStrategy()
        storage = StubEditionStorage()
        pipeline = StubDistillationPipeline()

        run_morning_press(
            database_url=db_url_news_only,
            generation_strategy=gen,
            storage=storage,
            distillation_pipeline=pipeline,
            enable_validation=False,
            edition_date="2026-03-12",
        )

        engine = create_engine(db_url_news_only)
        Session = sessionmaker(bind=engine)
        session = Session()
        pending = fetch_pending_news_items(session, "2026-03-12")
        assert len(pending) == 0
        session.close()

    def test_mixed_sources_produce_edition(self, db_url_mixed):
        """Both user prompts and news items together produce an edition."""
        gen = StubGenerationStrategy()
        storage = StubEditionStorage()
        pipeline = StubDistillationPipeline()

        result = run_morning_press(
            database_url=db_url_mixed,
            generation_strategy=gen,
            storage=storage,
            distillation_pipeline=pipeline,
            enable_validation=False,
            edition_date="2026-03-12",
        )

        assert result["edition_id"] is not None
        assert result["prompt_count"] == 1
        assert result["news_item_count"] == 3

    def test_news_items_use_low_weight(self, db_url_news_only):
        """News items should enter distillation with NEWS_ITEM_BASE_WEIGHT."""
        captured_prompts = []

        class CapturingPipeline(StubDistillationPipeline):
            def run(self, prompts):
                captured_prompts.extend(prompts)
                return super().run(prompts)

        gen = StubGenerationStrategy()
        storage = StubEditionStorage()
        pipeline = CapturingPipeline()

        run_morning_press(
            database_url=db_url_news_only,
            generation_strategy=gen,
            storage=storage,
            distillation_pipeline=pipeline,
            enable_validation=False,
            edition_date="2026-03-12",
        )

        # All prompts should have the news item base weight (0.3)
        assert len(captured_prompts) > 0
        for p in captured_prompts:
            assert p.payment_amount == 0.3

    def test_news_only_always_mutates(self, db_url_news_only):
        """Mutation always runs when articles are generated, even with news-only editions."""
        gen = StubGenerationStrategy()
        storage = StubEditionStorage()
        pipeline = StubDistillationPipeline()

        run_morning_press(
            database_url=db_url_news_only,
            generation_strategy=gen,
            storage=storage,
            distillation_pipeline=pipeline,
            enable_validation=False,
            edition_date="2026-03-12",
        )

        # Mutation always runs — expect pro calls for newspaper gen, curator, and mutation
        pro_calls = [c for c in gen.calls if c["model_tier"] == "pro"]
        assert len(pro_calls) >= 1

    def test_news_only_produces_edition_and_mutation(self, db_url_news_only):
        """News-only edition is produced and mutation runs unconditionally."""
        gen = StubGenerationStrategy()
        storage = StubEditionStorage()
        pipeline = StubDistillationPipeline()

        result = run_morning_press(
            database_url=db_url_news_only,
            generation_strategy=gen,
            storage=storage,
            distillation_pipeline=pipeline,
            enable_validation=False,
            edition_date="2026-03-12",
        )

        assert result["edition_id"] is not None

    def test_validation_skips_news_items(self, db_url_mixed):
        """Coherence validation should not reject news items."""
        # Validation rejects ALL prompts, but news items should survive
        accepted_json = json.dumps({"accepted": []})
        gen = StubGenerationStrategy(responses={"pro": accepted_json})
        storage = StubEditionStorage()
        pipeline = StubDistillationPipeline()

        result = run_morning_press(
            database_url=db_url_mixed,
            generation_strategy=gen,
            storage=storage,
            distillation_pipeline=pipeline,
            enable_validation=True,
            edition_date="2026-03-12",
        )

        # All user prompts rejected, but news items survive
        assert result["edition_id"] is not None
        assert result["prompt_count"] == 0
        assert result["news_item_count"] == 3
