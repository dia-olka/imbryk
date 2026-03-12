"""Tests for the News Scout module."""

import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from newsroom_director.db import (
    Base,
    NewsItemRow,
    fetch_pending_news_items,
    mark_news_items_processed,
    save_news_item,
)
from newsroom_director.generation import StubGenerationStrategy
from newsroom_director.news_scout.main import run_news_scout
from newsroom_director.news_scout.query_generator import generate_queries
from newsroom_director.news_scout.schemas import (
    is_valid_query_output,
    parse_query_output,
)
from newsroom_director.news_scout.searcher import (
    RateLimitExceeded,
    SearchResult,
    StubSearcher,
    _RateLimiter,
)

# --- Schema validation tests ---


class TestQueryOutputSchemas:
    def test_valid_output(self):
        raw = json.dumps({
            "categories": [
                {
                    "category_id": "artificial-intelligence",
                    "queries": ["AI regulation EU 2026"],
                },
            ]
        })
        assert is_valid_query_output(raw) is True

    def test_empty_categories_invalid(self):
        raw = json.dumps({"categories": []})
        assert is_valid_query_output(raw) is False

    def test_no_queries_invalid(self):
        raw = json.dumps({
            "categories": [
                {"category_id": "ai", "queries": []},
            ]
        })
        assert is_valid_query_output(raw) is False

    def test_blank_queries_invalid(self):
        raw = json.dumps({
            "categories": [
                {"category_id": "ai", "queries": ["", "  "]},
            ]
        })
        assert is_valid_query_output(raw) is False

    def test_non_json_invalid(self):
        assert is_valid_query_output("not json") is False

    def test_parse_output(self):
        raw = json.dumps({
            "categories": [
                {
                    "category_id": "geopolitics-and-diplomacy",
                    "queries": ["NATO summit 2026", "US-China trade"],
                },
                {
                    "category_id": "markets-and-macroeconomics",
                    "queries": ["Fed rate decision"],
                },
            ]
        })
        result = parse_query_output(raw)
        assert len(result) == 2
        assert result["geopolitics-and-diplomacy"] == [
            "NATO summit 2026",
            "US-China trade",
        ]
        assert result["markets-and-macroeconomics"] == ["Fed rate decision"]

    def test_parse_skips_empty_category_id(self):
        raw = json.dumps({
            "categories": [
                {"category_id": "", "queries": ["some query"]},
                {"category_id": "ai", "queries": ["real query"]},
            ]
        })
        result = parse_query_output(raw)
        assert "" not in result
        assert "ai" in result


# --- Query generator tests ---


class TestQueryGenerator:
    def _make_stub_gen(self, response: str) -> StubGenerationStrategy:
        return StubGenerationStrategy(responses={"flash": response})

    def test_generates_queries_from_valid_response(self):
        response = json.dumps({
            "categories": [
                {
                    "category_id": "artificial-intelligence",
                    "queries": ["AI safety regulation 2026"],
                },
            ]
        })
        gen = self._make_stub_gen(response)
        result = generate_queries("synopsis", ["artificial-intelligence"], gen)
        assert "artificial-intelligence" in result
        assert len(result["artificial-intelligence"]) == 1

    def test_returns_empty_on_invalid_response(self):
        gen = self._make_stub_gen("not json")
        result = generate_queries("synopsis", ["ai"], gen)
        assert result == {}

    def test_retries_on_invalid_output(self):
        call_count = [0]

        class CountingGen(StubGenerationStrategy):
            def generate(self, *args, **kwargs):
                call_count[0] += 1
                return "bad json"

        gen = CountingGen()
        result = generate_queries("synopsis", ["ai"], gen)
        assert result == {}
        assert call_count[0] == 3  # MAX_RETRIES

    def test_uses_flash_model_tier(self):
        response = json.dumps({
            "categories": [
                {"category_id": "ai", "queries": ["test query"]},
            ]
        })
        gen = self._make_stub_gen(response)
        generate_queries("synopsis", ["ai"], gen)
        assert gen.calls[0]["model_tier"] == "flash"


# --- Searcher tests ---


class TestStubSearcher:
    def test_returns_canned_results(self):
        results = [
            SearchResult(
                title="Test Article",
                snippet="Test content",
                url="https://example.com/1",
                score=0.9,
            )
        ]
        searcher = StubSearcher(results=results)
        found = searcher.search("test query")
        assert len(found) == 1
        assert found[0].title == "Test Article"
        assert searcher.calls == ["test query"]

    def test_empty_searcher(self):
        searcher = StubSearcher()
        assert searcher.search("anything") == []


# --- Rate limiter tests ---


class TestRateLimiter:
    def test_monthly_limit_raises(self):
        limiter = _RateLimiter(rpm=100, monthly_limit=3)
        limiter._monthly_count = 3  # Already at limit
        with pytest.raises(RateLimitExceeded, match="monthly limit"):
            limiter.acquire()

    def test_monthly_remaining(self):
        limiter = _RateLimiter(rpm=100, monthly_limit=10)
        limiter._monthly_count = 0
        assert limiter.monthly_remaining == 10
        limiter._monthly_count = 7
        assert limiter.monthly_remaining == 3

    def test_rpm_allows_burst(self):
        limiter = _RateLimiter(rpm=5, monthly_limit=999)
        limiter._monthly_count = 0
        # Should not raise for 5 quick calls
        for _ in range(5):
            limiter.acquire()

    def test_monthly_limit_zero_blocks_immediately(self):
        limiter = _RateLimiter(rpm=100, monthly_limit=0)
        with pytest.raises(RateLimitExceeded):
            limiter.acquire()


class TestRateLimitInScout:
    def test_monthly_limit_stops_searches(self, tmp_path):
        """When monthly limit is hit, scout stores whatever it got and exits cleanly."""
        db_path = tmp_path / "scout_rl.db"
        url = f"sqlite:///{db_path}"
        engine = create_engine(url)
        Base.metadata.create_all(bind=engine)

        query_response = json.dumps({
            "categories": [
                {"category_id": "ai", "queries": ["q1", "q2", "q3"]},
                {"category_id": "climate", "queries": ["q4", "q5"]},
            ]
        })
        gen = StubGenerationStrategy(responses={"flash": query_response})

        call_count = [0]

        class LimitedSearcher(StubSearcher):
            def search(self, query, max_results=5):
                call_count[0] += 1
                if call_count[0] >= 2:
                    raise RateLimitExceeded("Monthly limit reached")
                return [SearchResult(
                    title="Article",
                    snippet="Content",
                    url=f"https://example.com/{call_count[0]}",
                    score=0.9,
                )]

        result = run_news_scout(
            database_url=url,
            generation_strategy=gen,
            searcher=LimitedSearcher(),
            edition_date="2026-03-12",
        )

        # First query succeeded, second hit limit — should store 1 item
        assert result["items_stored"] == 1
        assert result["queries_executed"] == 2  # Attempted 2, second failed


# --- DB integration tests ---


class TestNewsItemDB:
    @pytest.fixture()
    def db_session(self, tmp_path):
        db_path = tmp_path / "test.db"
        url = f"sqlite:///{db_path}"
        engine = create_engine(url)
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    def test_save_and_fetch(self, db_session):
        saved = save_news_item(
            session=db_session,
            edition_date="2026-03-12",
            category_id="artificial-intelligence",
            query="AI regulation EU",
            headline="EU Enforces AI Act",
            snippet="The European Union began enforcement...",
            source_url="https://example.com/ai-act",
            relevance_score=0.95,
        )
        assert saved is True
        db_session.commit()

        items = fetch_pending_news_items(db_session, "2026-03-12")
        assert len(items) == 1
        assert items[0].headline == "EU Enforces AI Act"
        assert items[0].category_id == "artificial-intelligence"

    def test_duplicate_url_rejected(self, db_session):
        save_news_item(
            session=db_session,
            edition_date="2026-03-12",
            category_id="ai",
            query="q1",
            headline="Title",
            snippet="Content",
            source_url="https://example.com/dup",
            relevance_score=0.9,
        )
        db_session.commit()

        saved = save_news_item(
            session=db_session,
            edition_date="2026-03-12",
            category_id="ai",
            query="q2",
            headline="Title 2",
            snippet="Content 2",
            source_url="https://example.com/dup",
            relevance_score=0.8,
        )
        assert saved is False

    def test_same_url_different_dates_ok(self, db_session):
        save_news_item(
            session=db_session,
            edition_date="2026-03-12",
            category_id="ai",
            query="q1",
            headline="Title",
            snippet="Content",
            source_url="https://example.com/same",
            relevance_score=0.9,
        )
        db_session.commit()

        saved = save_news_item(
            session=db_session,
            edition_date="2026-03-13",
            category_id="ai",
            query="q1",
            headline="Title",
            snippet="Content",
            source_url="https://example.com/same",
            relevance_score=0.9,
        )
        assert saved is True

    def test_mark_processed(self, db_session):
        save_news_item(
            session=db_session,
            edition_date="2026-03-12",
            category_id="ai",
            query="q1",
            headline="Title",
            snippet="Content",
            source_url="https://example.com/1",
            relevance_score=0.9,
        )
        db_session.commit()

        mark_news_items_processed(db_session, "2026-03-12")
        db_session.commit()

        # Should return empty since all are processed
        items = fetch_pending_news_items(db_session, "2026-03-12")
        assert len(items) == 0

    def test_fetch_only_pending(self, db_session):
        save_news_item(
            session=db_session,
            edition_date="2026-03-12",
            category_id="ai",
            query="q1",
            headline="Pending",
            snippet="Content",
            source_url="https://example.com/pending",
            relevance_score=0.9,
        )
        db_session.commit()

        # Manually mark one as processed
        row = db_session.query(NewsItemRow).first()
        row.status = "processed"
        db_session.commit()

        items = fetch_pending_news_items(db_session, "2026-03-12")
        assert len(items) == 0

    def test_fetch_filters_by_date(self, db_session):
        save_news_item(
            session=db_session,
            edition_date="2026-03-12",
            category_id="ai",
            query="q1",
            headline="Today",
            snippet="Content",
            source_url="https://example.com/today",
            relevance_score=0.9,
        )
        save_news_item(
            session=db_session,
            edition_date="2026-03-11",
            category_id="ai",
            query="q1",
            headline="Yesterday",
            snippet="Content",
            source_url="https://example.com/yesterday",
            relevance_score=0.9,
        )
        db_session.commit()

        items = fetch_pending_news_items(db_session, "2026-03-12")
        assert len(items) == 1
        assert items[0].headline == "Today"


# --- News Scout orchestrator tests ---


class TestRunNewsScout:
    def test_full_pipeline(self, tmp_path):
        db_path = tmp_path / "scout.db"
        url = f"sqlite:///{db_path}"
        engine = create_engine(url)
        Base.metadata.create_all(bind=engine)

        query_response = json.dumps({
            "categories": [
                {
                    "category_id": "artificial-intelligence",
                    "queries": ["AI regulation 2026"],
                },
            ]
        })
        gen = StubGenerationStrategy(responses={"flash": query_response})

        search_results = [
            SearchResult(
                title="EU AI Act Enforcement Begins",
                snippet="The European Union started enforcing the AI Act...",
                url="https://example.com/ai-act",
                score=0.95,
            ),
            SearchResult(
                title="OpenAI Releases GPT-5",
                snippet="OpenAI announced the release of GPT-5...",
                url="https://example.com/gpt5",
                score=0.88,
            ),
        ]
        searcher = StubSearcher(results=search_results)

        result = run_news_scout(
            database_url=url,
            generation_strategy=gen,
            searcher=searcher,
            edition_date="2026-03-12",
        )

        assert result["queries_executed"] == 1
        assert result["items_stored"] == 2
        assert result["categories_covered"] == 1

        # Verify items are in DB
        Session = sessionmaker(bind=engine)
        session = Session()
        items = fetch_pending_news_items(session, "2026-03-12")
        assert len(items) == 2
        session.close()

    def test_empty_queries_returns_zero(self, tmp_path):
        db_path = tmp_path / "scout_empty.db"
        url = f"sqlite:///{db_path}"
        engine = create_engine(url)
        Base.metadata.create_all(bind=engine)

        gen = StubGenerationStrategy(responses={"flash": "bad json"})
        searcher = StubSearcher()

        result = run_news_scout(
            database_url=url,
            generation_strategy=gen,
            searcher=searcher,
            edition_date="2026-03-12",
        )

        assert result["queries_executed"] == 0
        assert result["items_stored"] == 0

    def test_deduplicates_urls(self, tmp_path):
        db_path = tmp_path / "scout_dedup.db"
        url = f"sqlite:///{db_path}"
        engine = create_engine(url)
        Base.metadata.create_all(bind=engine)

        query_response = json.dumps({
            "categories": [
                {
                    "category_id": "ai",
                    "queries": ["query 1", "query 2"],
                },
            ]
        })
        gen = StubGenerationStrategy(responses={"flash": query_response})

        # Same URL returned by both queries
        search_results = [
            SearchResult(
                title="Same Article",
                snippet="Same content",
                url="https://example.com/same",
                score=0.9,
            ),
        ]
        searcher = StubSearcher(results=search_results)

        result = run_news_scout(
            database_url=url,
            generation_strategy=gen,
            searcher=searcher,
            edition_date="2026-03-12",
        )

        assert result["queries_executed"] == 2
        assert result["items_stored"] == 1  # Deduplicated
