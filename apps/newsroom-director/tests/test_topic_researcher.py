"""Tests for the topic researcher module."""

import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from newsroom_director.db import (
    Base,
    PromptRecord,
    PromptResearchLogRow,
    PromptRow,
    count_prompt_research_attempts,
    save_prompt_research_log,
)
from newsroom_director.generation import StubGenerationStrategy
from newsroom_director.news_scout.searcher import (
    RateLimitExceeded,
    SearchResult,
    StubSearcher,
)
from newsroom_director.topic_researcher import (
    ResearchedPrompt,
    _generate_queries_for_prompt,
    _generate_whisper,
    research_prompts,
)


def _make_prompt(
    prompt_id: str = "p1",
    text: str = "AI regulation in Europe",
    payment_amount: float = 3.0,
    category_ids: list[str] | None = None,
) -> PromptRecord:
    return PromptRecord(
        prompt_id=prompt_id,
        text=text,
        payment_amount=payment_amount,
        category_ids=category_ids or ["artificial-intelligence"],
    )


def _make_stub_gen(queries: list[str]) -> StubGenerationStrategy:
    response = json.dumps({"queries": queries})
    return StubGenerationStrategy(responses={"flash": response})


class SequentialGen(StubGenerationStrategy):
    """Returns different responses for sequential flash calls."""

    def __init__(self, responses_seq: list[str]) -> None:
        super().__init__()
        self._responses_seq = responses_seq
        self._seq_idx = 0

    def generate(self, system_prompt, model_tier, user_content="", response_schema=None):
        self._calls.append(
            {"system_prompt": system_prompt, "model_tier": model_tier, "user_content": user_content}
        )
        if self._seq_idx < len(self._responses_seq):
            resp = self._responses_seq[self._seq_idx]
            self._seq_idx += 1
            return resp
        return "{}"


def _make_gen_with_whisper(queries: list[str], whisper: str | None = "Public interest in AI regulation is growing."):
    """Gen that returns queries first, then a whisper."""
    responses = [json.dumps({"queries": queries})]
    if whisper is not None:
        responses.append(json.dumps({"whisper": whisper}))
    else:
        responses.append(json.dumps({"whisper": None}))
    return SequentialGen(responses)


def _make_search_results(n: int = 2) -> list[SearchResult]:
    return [
        SearchResult(
            title=f"Article {i}",
            snippet=f"Content about topic {i}",
            url=f"https://example.com/{i}",
            score=0.9 - i * 0.1,
        )
        for i in range(n)
    ]


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    # Insert a prompt row so FK constraints are satisfied
    session.add(PromptRow(id="p1", text="AI regulation", status="accepted"))
    session.add(PromptRow(id="p2", text="Climate change", status="accepted"))
    session.commit()
    yield session
    session.close()


# --- Query generation tests ---


class TestGenerateQueriesForPrompt:
    def test_generates_queries(self):
        gen = _make_stub_gen(["EU AI Act enforcement 2026", "AI safety regulation"])
        prompt = _make_prompt()
        queries = _generate_queries_for_prompt(prompt, gen, max_queries=3)
        assert queries == ["EU AI Act enforcement 2026", "AI safety regulation"]

    def test_respects_max_queries(self):
        gen = _make_stub_gen(["q1", "q2", "q3", "q4"])
        prompt = _make_prompt()
        queries = _generate_queries_for_prompt(prompt, gen, max_queries=2)
        assert len(queries) == 2

    def test_returns_empty_on_bad_json(self):
        gen = StubGenerationStrategy(responses={"flash": "not json"})
        prompt = _make_prompt()
        queries = _generate_queries_for_prompt(prompt, gen, max_queries=3)
        assert queries == []

    def test_returns_empty_on_empty_queries(self):
        gen = _make_stub_gen([])
        prompt = _make_prompt()
        queries = _generate_queries_for_prompt(prompt, gen, max_queries=3)
        assert queries == []

    def test_strips_whitespace(self):
        gen = _make_stub_gen(["  query with spaces  ", ""])
        prompt = _make_prompt()
        queries = _generate_queries_for_prompt(prompt, gen, max_queries=3)
        assert queries == ["query with spaces"]

    def test_uses_flash_model(self):
        gen = _make_stub_gen(["test query"])
        prompt = _make_prompt()
        _generate_queries_for_prompt(prompt, gen, max_queries=3)
        assert gen.calls[0]["model_tier"] == "flash"

    def test_retries_on_failure(self):
        call_count = [0]

        class CountingGen(StubGenerationStrategy):
            def generate(self, *args, **kwargs):
                call_count[0] += 1
                return "bad json"

        gen = CountingGen()
        prompt = _make_prompt()
        result = _generate_queries_for_prompt(prompt, gen, max_queries=3)
        assert result == []
        assert call_count[0] == 2  # MAX_RETRIES


# --- Whisper generation tests ---


class TestGenerateWhisper:
    def test_generates_whisper(self):
        gen = StubGenerationStrategy(
            responses={"flash": json.dumps({"whisper": "Public interest is growing."})}
        )
        prompt = _make_prompt()
        whisper = _generate_whisper(prompt, gen)
        assert whisper == "Public interest is growing."

    def test_returns_none_on_null_whisper(self):
        gen = StubGenerationStrategy(
            responses={"flash": json.dumps({"whisper": None})}
        )
        prompt = _make_prompt()
        assert _generate_whisper(prompt, gen) is None

    def test_returns_none_on_bad_json(self):
        gen = StubGenerationStrategy(responses={"flash": "not json"})
        prompt = _make_prompt()
        assert _generate_whisper(prompt, gen) is None

    def test_strips_whitespace(self):
        gen = StubGenerationStrategy(
            responses={"flash": json.dumps({"whisper": "  Observers note interest.  "})}
        )
        prompt = _make_prompt()
        assert _generate_whisper(prompt, gen) == "Observers note interest."

    def test_returns_none_on_empty_whisper(self):
        gen = StubGenerationStrategy(
            responses={"flash": json.dumps({"whisper": "  "})}
        )
        prompt = _make_prompt()
        assert _generate_whisper(prompt, gen) is None


# --- Research prompts tests ---


class TestResearchPrompts:
    def test_basic_research(self):
        gen = _make_stub_gen(["AI regulation EU 2026"])
        searcher = StubSearcher(results=_make_search_results(2))
        prompts = [_make_prompt(payment_amount=4.0)]

        result = research_prompts(prompts, searcher, gen)

        assert len(result.researched) == 2
        assert all(isinstance(r, ResearchedPrompt) for r in result.researched)
        # Weight distributed: 4.0 / 2 = 2.0 each
        assert result.researched[0].payment_amount == pytest.approx(2.0)
        assert result.researched[1].payment_amount == pytest.approx(2.0)

    def test_inherits_category_ids(self):
        gen = _make_stub_gen(["test query"])
        searcher = StubSearcher(results=_make_search_results(1))
        prompts = [_make_prompt(category_ids=["ai", "climate-and-ecology"])]

        result = research_prompts(prompts, searcher, gen)

        assert len(result.researched) == 1
        assert result.researched[0].category_ids == ["ai", "climate-and-ecology"]

    def test_inherits_prompt_id(self):
        gen = _make_stub_gen(["test query"])
        searcher = StubSearcher(results=_make_search_results(1))
        prompts = [_make_prompt(prompt_id="my-prompt-42")]

        result = research_prompts(prompts, searcher, gen)

        assert result.researched[0].prompt_id == "my-prompt-42"

    def test_source_url_set(self):
        gen = _make_stub_gen(["test query"])
        searcher = StubSearcher(results=_make_search_results(1))
        prompts = [_make_prompt()]

        result = research_prompts(prompts, searcher, gen)

        assert result.researched[0].source_url == "https://example.com/0"

    def test_text_is_title_plus_snippet(self):
        gen = _make_stub_gen(["test query"])
        results = [
            SearchResult(
                title="Big News",
                snippet="Something happened today.",
                url="https://example.com/1",
                score=0.95,
            )
        ]
        searcher = StubSearcher(results=results)
        prompts = [_make_prompt()]

        result = research_prompts(prompts, searcher, gen)

        assert result.researched[0].text == "Big News\nSomething happened today."

    def test_weight_preservation(self):
        """Sum of research result weights equals original payment."""
        gen = _make_stub_gen(["q1"])
        searcher = StubSearcher(results=_make_search_results(3))
        prompts = [_make_prompt(payment_amount=6.0)]

        result = research_prompts(prompts, searcher, gen)

        total_weight = sum(r.payment_amount for r in result.researched)
        assert total_weight == pytest.approx(6.0)

    def test_multiple_prompts(self):
        gen = _make_stub_gen(["test query"])
        # Each prompt gets the same search results, but URLs deduplicate
        searcher = StubSearcher(
            results=[
                SearchResult("A1", "S1", "https://example.com/a", 0.9),
                SearchResult("A2", "S2", "https://example.com/b", 0.8),
            ]
        )
        prompts = [
            _make_prompt(prompt_id="p1", payment_amount=2.0),
            _make_prompt(prompt_id="p2", payment_amount=4.0),
        ]

        result = research_prompts(prompts, searcher, gen)

        # First prompt gets both URLs (a, b). Second prompt gets none (both
        # seen), so it falls back to whisper. The stub gen returns queries
        # JSON for the whisper call too, which won't parse as valid whisper,
        # so p2 ends up in failed_prompt_ids.
        p1_results = [r for r in result.researched if r.prompt_id == "p1"]
        assert len(p1_results) == 2
        # Weight: 2.0 / 2 = 1.0 each
        assert p1_results[0].payment_amount == pytest.approx(1.0)

    def test_deduplicates_urls_across_queries(self):
        gen = _make_stub_gen(["q1", "q2"])
        same_result = SearchResult("A", "S", "https://example.com/same", 0.9)
        searcher = StubSearcher(results=[same_result])
        prompts = [_make_prompt()]

        result = research_prompts(prompts, searcher, gen)

        # Same URL from both queries → only one result
        assert len(result.researched) == 1

    def test_empty_prompts_returns_empty(self):
        gen = _make_stub_gen(["q1"])
        searcher = StubSearcher(results=_make_search_results(1))

        result = research_prompts([], searcher, gen)

        assert result.researched == []
        assert result.failed_prompt_ids == []

    def test_no_results_whisper_fallback(self):
        """When Tavily returns nothing, a whisper is generated."""
        gen = _make_gen_with_whisper(["q1"], whisper="Observers note growing interest in AI.")
        searcher = StubSearcher(results=[])
        prompts = [_make_prompt()]

        result = research_prompts(prompts, searcher, gen)

        assert len(result.researched) == 1
        assert result.researched[0].text == "Observers note growing interest in AI."
        assert result.researched[0].source_url == ""
        assert result.researched[0].prompt_id == "p1"
        assert result.failed_prompt_ids == []

    def test_no_results_whisper_null_returns_failed(self):
        """When whisper is null (unsafe), prompt is deferred."""
        gen = _make_gen_with_whisper(["q1"], whisper=None)
        searcher = StubSearcher(results=[])
        prompts = [_make_prompt()]

        result = research_prompts(prompts, searcher, gen)

        assert result.researched == []
        assert result.failed_prompt_ids == ["p1"]

    def test_query_generation_failure_returns_failed_id(self):
        gen = StubGenerationStrategy(responses={"flash": "bad json"})
        searcher = StubSearcher(results=_make_search_results(1))
        prompts = [_make_prompt()]

        result = research_prompts(prompts, searcher, gen)

        assert result.researched == []
        assert result.failed_prompt_ids == ["p1"]

    def test_search_failure_skips_query(self):
        gen = _make_stub_gen(["q1", "q2"])

        class FailingSearcher(StubSearcher):
            def __init__(self):
                super().__init__(results=[])
                self._call_count = 0

            def search(self, query, max_results=5):
                self._call_count += 1
                if self._call_count == 1:
                    raise ConnectionError("network error")
                return [SearchResult("OK", "Content", "https://ok.com", 0.9)]

        searcher = FailingSearcher()
        prompts = [_make_prompt()]

        result = research_prompts(prompts, searcher, gen)

        # First query failed (network error), second succeeded
        assert len(result.researched) == 1
        assert result.researched[0].source_url == "https://ok.com"

    def test_exclude_urls_skips_known_urls(self):
        """URLs already in pipeline (e.g. News Scout) are excluded."""
        gen = _make_stub_gen(["q1"])
        searcher = StubSearcher(results=[
            SearchResult("A", "S", "https://example.com/already-known", 0.9),
            SearchResult("B", "S", "https://example.com/new", 0.8),
        ])
        prompts = [_make_prompt()]

        result = research_prompts(
            prompts, searcher, gen,
            exclude_urls={"https://example.com/already-known"},
        )

        assert len(result.researched) == 1
        assert result.researched[0].source_url == "https://example.com/new"

    def test_rate_limit_stops_all_searches(self):
        """RateLimitExceeded aborts remaining queries and prompts."""
        gen = _make_stub_gen(["q1", "q2"])

        class RateLimitSearcher(StubSearcher):
            def __init__(self):
                super().__init__(results=[])
                self._call_count = 0

            def search(self, query, max_results=5):
                self._call_count += 1
                if self._call_count == 1:
                    return [SearchResult("OK", "C", "https://ok.com", 0.9)]
                raise RateLimitExceeded("monthly limit")

        searcher = RateLimitSearcher()
        prompts = [
            _make_prompt(prompt_id="p1"),
            _make_prompt(prompt_id="p2"),
        ]

        result = research_prompts(prompts, searcher, gen)

        # First query of first prompt succeeded, second hit rate limit.
        # Second prompt skipped entirely.
        assert len(result.researched) == 1
        assert result.researched[0].prompt_id == "p1"
        # Second prompt deferred for retry
        assert "p2" in result.failed_prompt_ids
        # Searcher was only called twice (once success, once rate limit)
        assert searcher._call_count == 2

    def test_rate_limit_preserves_results_before_limit(self):
        """Results gathered before rate limit are kept."""
        gen = _make_stub_gen(["q1"])

        class LateRateLimitSearcher(StubSearcher):
            def __init__(self):
                super().__init__(results=[])
                self._call_count = 0

            def search(self, query, max_results=5):
                self._call_count += 1
                raise RateLimitExceeded("limit")

        searcher = LateRateLimitSearcher()
        prompts = [_make_prompt()]

        result = research_prompts(prompts, searcher, gen)

        # Rate limit on first query — no results, prompt deferred
        assert len(result.researched) == 0
        assert "p1" in result.failed_prompt_ids

    def test_custom_max_queries_and_results(self):
        gen = _make_stub_gen(["q1", "q2", "q3"])
        searcher = StubSearcher(results=_make_search_results(10))
        prompts = [_make_prompt()]

        result = research_prompts(
            prompts, searcher, gen,
            max_queries=1,
            max_results_per_query=2,
        )

        # Only 1 query executed, max 2 results
        assert len(searcher.calls) == 1
        # Searcher returns min(max_results, available) — StubSearcher
        # returns results[:max_results], so 2
        assert len(result.researched) == 2

    def test_whisper_preserves_weight(self):
        """Whisper fallback preserves the full payment amount."""
        gen = _make_gen_with_whisper(["q1"], whisper="People are discussing AI.")
        searcher = StubSearcher(results=[])
        prompts = [_make_prompt(payment_amount=5.0)]

        result = research_prompts(prompts, searcher, gen)

        assert len(result.researched) == 1
        assert result.researched[0].payment_amount == pytest.approx(5.0)

    def test_whisper_inherits_categories(self):
        gen = _make_gen_with_whisper(["q1"], whisper="Interest in climate policy.")
        searcher = StubSearcher(results=[])
        prompts = [_make_prompt(category_ids=["climate-and-ecology", "geopolitics"])]

        result = research_prompts(prompts, searcher, gen)

        assert result.researched[0].category_ids == ["climate-and-ecology", "geopolitics"]


# --- Research logging tests ---


class TestResearchLogging:
    def test_success_persists_log(self, db_session):
        gen = _make_stub_gen(["EU AI Act 2026"])
        searcher = StubSearcher(results=_make_search_results(2))
        prompts = [_make_prompt(prompt_id="p1")]

        research_prompts(
            prompts, searcher, gen,
            session=db_session,
            edition_date="2026-03-21",
        )
        db_session.flush()

        logs = db_session.query(PromptResearchLogRow).all()
        assert len(logs) == 1
        assert logs[0].prompt_id == "p1"
        assert logs[0].edition_date == "2026-03-21"
        assert logs[0].status == "success"
        queries = json.loads(logs[0].queries_json)
        assert queries == ["EU AI Act 2026"]
        results = json.loads(logs[0].results_json)
        assert len(results) == 2
        assert results[0]["url"] == "https://example.com/0"

    def test_whisper_persists_log(self, db_session):
        gen = _make_gen_with_whisper(["q1"], whisper="Observers note interest in AI.")
        searcher = StubSearcher(results=[])
        prompts = [_make_prompt(prompt_id="p1")]

        research_prompts(
            prompts, searcher, gen,
            session=db_session,
            edition_date="2026-03-21",
        )
        db_session.flush()

        logs = db_session.query(PromptResearchLogRow).all()
        assert len(logs) == 1
        assert logs[0].status == "whisper"
        results = json.loads(logs[0].results_json)
        assert results == [{"whisper": "Observers note interest in AI."}]

    def test_no_results_no_whisper_persists_log(self, db_session):
        gen = _make_gen_with_whisper(["q1"], whisper=None)
        searcher = StubSearcher(results=[])
        prompts = [_make_prompt(prompt_id="p1")]

        result = research_prompts(
            prompts, searcher, gen,
            session=db_session,
            edition_date="2026-03-21",
        )
        db_session.flush()

        logs = db_session.query(PromptResearchLogRow).all()
        assert len(logs) == 1
        assert logs[0].status == "no_results"
        assert result.failed_prompt_ids == ["p1"]

    def test_query_gen_failure_persists_log(self, db_session):
        gen = StubGenerationStrategy(responses={"flash": "bad json"})
        searcher = StubSearcher(results=_make_search_results(1))
        prompts = [_make_prompt(prompt_id="p1")]

        result = research_prompts(
            prompts, searcher, gen,
            session=db_session,
            edition_date="2026-03-21",
        )
        db_session.flush()

        logs = db_session.query(PromptResearchLogRow).all()
        assert len(logs) == 1
        assert logs[0].status == "query_generation_failed"
        assert result.failed_prompt_ids == ["p1"]

    def test_rate_limited_persists_log(self, db_session):
        gen = _make_stub_gen(["q1"])

        class AlwaysRateLimited(StubSearcher):
            def search(self, query, max_results=5):
                raise RateLimitExceeded("limit")

        searcher = AlwaysRateLimited(results=[])
        prompts = [
            _make_prompt(prompt_id="p1"),
            _make_prompt(prompt_id="p2"),
        ]

        research_prompts(
            prompts, searcher, gen,
            session=db_session,
            edition_date="2026-03-21",
        )
        db_session.flush()

        logs = db_session.query(PromptResearchLogRow).order_by(
            PromptResearchLogRow.prompt_id
        ).all()
        # p1 got rate_limited during search, p2 skipped entirely
        assert len(logs) == 2
        assert logs[0].prompt_id == "p1"
        assert logs[1].prompt_id == "p2"
        assert logs[1].status == "rate_limited"


# --- Retry behaviour tests ---


class TestResearchRetries:
    def test_prompt_retried_within_max_retries(self, db_session):
        """Prompt with fewer attempts than max is retried (returned as failed)."""
        gen = _make_gen_with_whisper(["q1"], whisper=None)
        searcher = StubSearcher(results=[])
        prompts = [_make_prompt(prompt_id="p1")]

        result = research_prompts(
            prompts, searcher, gen,
            session=db_session,
            edition_date="2026-03-21",
            max_research_retries=3,
        )

        assert "p1" in result.failed_prompt_ids

    def test_exhausted_with_whisper(self, db_session):
        """Prompt that exhausted retries still gets a whisper if possible."""
        # Simulate a prior failed attempt
        save_prompt_research_log(
            db_session, "p1", "2026-03-20", ["old query"], [], "no_results"
        )
        db_session.flush()

        gen = StubGenerationStrategy(
            responses={"flash": json.dumps({"whisper": "People discuss AI."})}
        )
        searcher = StubSearcher(results=[])
        prompts = [_make_prompt(prompt_id="p1")]

        result = research_prompts(
            prompts, searcher, gen,
            session=db_session,
            edition_date="2026-03-21",
            max_research_retries=1,
        )

        # Got a whisper — not in failed_ids
        assert "p1" not in result.failed_prompt_ids
        assert len(result.researched) == 1
        assert result.researched[0].text == "People discuss AI."

        logs = (
            db_session.query(PromptResearchLogRow)
            .filter(PromptResearchLogRow.status == "exhausted_whisper")
            .all()
        )
        assert len(logs) == 1

    def test_exhausted_no_whisper(self, db_session):
        """Prompt that exhausted retries and whisper fails is fully dropped."""
        save_prompt_research_log(
            db_session, "p1", "2026-03-20", ["old query"], [], "no_results"
        )
        db_session.flush()

        gen = StubGenerationStrategy(
            responses={"flash": json.dumps({"whisper": None})}
        )
        searcher = StubSearcher(results=[])
        prompts = [_make_prompt(prompt_id="p1")]

        result = research_prompts(
            prompts, searcher, gen,
            session=db_session,
            edition_date="2026-03-21",
            max_research_retries=1,
        )

        assert "p1" not in result.failed_prompt_ids
        assert result.researched == []

        logs = (
            db_session.query(PromptResearchLogRow)
            .filter(PromptResearchLogRow.status == "exhausted")
            .all()
        )
        assert len(logs) == 1

    def test_count_prompt_research_attempts(self, db_session):
        assert count_prompt_research_attempts(db_session, "p1") == 0

        save_prompt_research_log(
            db_session, "p1", "2026-03-20", ["q1"], [], "no_results"
        )
        db_session.flush()
        assert count_prompt_research_attempts(db_session, "p1") == 1

        save_prompt_research_log(
            db_session, "p1", "2026-03-21", ["q2"], [], "no_results"
        )
        db_session.flush()
        assert count_prompt_research_attempts(db_session, "p1") == 2

        # Different prompt not counted
        assert count_prompt_research_attempts(db_session, "p2") == 0
