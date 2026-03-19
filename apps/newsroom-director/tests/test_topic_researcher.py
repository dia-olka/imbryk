"""Tests for the topic researcher module."""

import json

import pytest

from newsroom_director.db import PromptRecord
from newsroom_director.generation import StubGenerationStrategy
from newsroom_director.news_scout.searcher import (
    RateLimitExceeded,
    SearchResult,
    StubSearcher,
)
from newsroom_director.topic_researcher import (
    ResearchedPrompt,
    _generate_queries_for_prompt,
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


# --- Research prompts tests ---


class TestResearchPrompts:
    def test_basic_research(self):
        gen = _make_stub_gen(["AI regulation EU 2026"])
        searcher = StubSearcher(results=_make_search_results(2))
        prompts = [_make_prompt(payment_amount=4.0)]

        result = research_prompts(prompts, searcher, gen)

        assert len(result) == 2
        assert all(isinstance(r, ResearchedPrompt) for r in result)
        # Weight distributed: 4.0 / 2 = 2.0 each
        assert result[0].payment_amount == pytest.approx(2.0)
        assert result[1].payment_amount == pytest.approx(2.0)

    def test_inherits_category_ids(self):
        gen = _make_stub_gen(["test query"])
        searcher = StubSearcher(results=_make_search_results(1))
        prompts = [_make_prompt(category_ids=["ai", "climate-and-ecology"])]

        result = research_prompts(prompts, searcher, gen)

        assert len(result) == 1
        assert result[0].category_ids == ["ai", "climate-and-ecology"]

    def test_inherits_prompt_id(self):
        gen = _make_stub_gen(["test query"])
        searcher = StubSearcher(results=_make_search_results(1))
        prompts = [_make_prompt(prompt_id="my-prompt-42")]

        result = research_prompts(prompts, searcher, gen)

        assert result[0].prompt_id == "my-prompt-42"

    def test_source_url_set(self):
        gen = _make_stub_gen(["test query"])
        searcher = StubSearcher(results=_make_search_results(1))
        prompts = [_make_prompt()]

        result = research_prompts(prompts, searcher, gen)

        assert result[0].source_url == "https://example.com/0"

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

        assert result[0].text == "Big News\nSomething happened today."

    def test_weight_preservation(self):
        """Sum of research result weights equals original payment."""
        gen = _make_stub_gen(["q1"])
        searcher = StubSearcher(results=_make_search_results(3))
        prompts = [_make_prompt(payment_amount=6.0)]

        result = research_prompts(prompts, searcher, gen)

        total_weight = sum(r.payment_amount for r in result)
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

        # First prompt gets both URLs (a, b). Second prompt gets none (both seen).
        # So second prompt is dropped.
        assert len(result) == 2
        assert all(r.prompt_id == "p1" for r in result)
        # Weight: 2.0 / 2 = 1.0 each
        assert result[0].payment_amount == pytest.approx(1.0)

    def test_deduplicates_urls_across_queries(self):
        gen = _make_stub_gen(["q1", "q2"])
        same_result = SearchResult("A", "S", "https://example.com/same", 0.9)
        searcher = StubSearcher(results=[same_result])
        prompts = [_make_prompt()]

        result = research_prompts(prompts, searcher, gen)

        # Same URL from both queries → only one result
        assert len(result) == 1

    def test_empty_prompts_returns_empty(self):
        gen = _make_stub_gen(["q1"])
        searcher = StubSearcher(results=_make_search_results(1))

        result = research_prompts([], searcher, gen)

        assert result == []

    def test_no_search_results_drops_prompt(self):
        gen = _make_stub_gen(["q1"])
        searcher = StubSearcher(results=[])
        prompts = [_make_prompt()]

        result = research_prompts(prompts, searcher, gen)

        assert result == []

    def test_query_generation_failure_drops_prompt(self):
        gen = StubGenerationStrategy(responses={"flash": "bad json"})
        searcher = StubSearcher(results=_make_search_results(1))
        prompts = [_make_prompt()]

        result = research_prompts(prompts, searcher, gen)

        assert result == []

    def test_search_failure_skips_query(self):
        gen = _make_stub_gen(["q1", "q2"])

        class FailingSearcher(StubSearcher):
            def __init__(self):
                super().__init__(results=[])
                self._call_count = 0

            def search(self, query, max_results=5):
                self._call_count += 1
                if self._call_count == 1:
                    raise RateLimitExceeded("limit hit")
                return [SearchResult("OK", "Content", "https://ok.com", 0.9)]

        searcher = FailingSearcher()
        prompts = [_make_prompt()]

        result = research_prompts(prompts, searcher, gen)

        # First query failed, second succeeded
        assert len(result) == 1
        assert result[0].source_url == "https://ok.com"

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
        assert len(result) == 2
