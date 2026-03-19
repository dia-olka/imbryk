"""Topic research — transform user prompts into real-world news via Tavily.

Each paid prompt is used to generate targeted search queries (Gemini Flash),
which are executed via Tavily. The resulting news articles enter the
distillation pipeline in place of the raw user text.

Weight inheritance: a prompt's payment weight is distributed evenly across
its research results, preserving the economic signal.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from .config import TAVILY_MAX_RESULTS_PER_QUERY, TOPIC_RESEARCH_MAX_QUERIES
from .db import PromptRecord
from .generation import GenerationStrategy
from .news_scout.searcher import SearchResult, SearchStrategy

logger = logging.getLogger(__name__)

MAX_RETRIES = 2

_SYSTEM_PROMPT = """\
You are a news research assistant. Given a user's topic request, generate \
{max_queries} targeted search queries that will surface the most relevant \
and recent real-world news articles about this topic.

Rules:
- Each query should target a different angle or aspect of the topic.
- Include temporal anchors (e.g. "March 2026", "this week") where recency \
matters.
- Prefer named actors, specific regions, concrete events, and verifiable \
timelines over broad topic searches.
- Avoid generic queries like "latest news about X".

Respond with ONLY a JSON object:
{{"queries": ["query 1", "query 2", ...]}}"""


@dataclass
class TopicQueryOutput:
    """Schema for the topic query generation LLM call."""

    queries: list[str]


@dataclass
class ResearchedPrompt:
    """A research result that can be routed like a PromptRecord.

    Has the same interface as PromptRecord (prompt_id, text,
    payment_amount, category_ids) so the routing and conversion
    code works unchanged, plus source_url for citation.
    """

    prompt_id: str
    text: str
    payment_amount: float
    category_ids: list[str]
    source_url: str


def _generate_queries_for_prompt(
    prompt: PromptRecord,
    generation_strategy: GenerationStrategy,
    max_queries: int,
) -> list[str]:
    """Generate search queries for a single user prompt via Gemini Flash."""
    system_prompt = _SYSTEM_PROMPT.replace(
        "{max_queries}", str(max_queries)
    )
    user_content = f"TOPIC REQUEST:\n{prompt.text}"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            raw = generation_strategy.generate(
                system_prompt,
                "flash",
                user_content,
                response_schema=TopicQueryOutput,
            )
            parsed = json.loads(raw)
            queries = [
                q.strip()
                for q in parsed.get("queries", [])
                if isinstance(q, str) and q.strip()
            ]
            if queries:
                return queries[:max_queries]

            logger.warning(
                "Empty queries for prompt %s (attempt %d/%d)",
                prompt.prompt_id,
                attempt,
                MAX_RETRIES,
            )
        except (json.JSONDecodeError, TypeError, AttributeError):
            logger.warning(
                "Failed to parse query response for prompt %s (attempt %d/%d)",
                prompt.prompt_id,
                attempt,
                MAX_RETRIES,
                exc_info=True,
            )

    logger.error(
        "All query generation attempts failed for prompt %s",
        prompt.prompt_id,
    )
    return []


def research_prompts(
    prompts: list[PromptRecord],
    searcher: SearchStrategy,
    generation_strategy: GenerationStrategy,
    max_queries: int | None = None,
    max_results_per_query: int | None = None,
) -> list[ResearchedPrompt]:
    """Research all prompts and return ResearchedPrompts with inherited weights.

    Each prompt is transformed into 0-N ResearchedPrompts derived from
    Tavily search results. The prompt's payment_amount is distributed
    evenly across its results. Each result inherits the original prompt's
    category_ids for routing.

    Prompts that yield no research results are dropped from the pipeline.

    Args:
        prompts: Paid user prompts to research.
        searcher: Tavily search backend.
        generation_strategy: LLM backend for query generation.
        max_queries: Max queries per prompt (default: TOPIC_RESEARCH_MAX_QUERIES).
        max_results_per_query: Max Tavily results per query
            (default: TAVILY_MAX_RESULTS_PER_QUERY).

    Returns:
        List of ResearchedPrompts that can be routed like PromptRecords.
    """
    if not prompts:
        return []

    mq = max_queries if max_queries is not None else TOPIC_RESEARCH_MAX_QUERIES
    mr = (
        max_results_per_query
        if max_results_per_query is not None
        else TAVILY_MAX_RESULTS_PER_QUERY
    )

    researched: list[ResearchedPrompt] = []
    seen_urls: set[str] = set()
    total_queries = 0

    for prompt in prompts:
        queries = _generate_queries_for_prompt(
            prompt, generation_strategy, mq
        )
        if not queries:
            logger.info(
                "No queries generated for prompt %s, dropping",
                prompt.prompt_id,
            )
            continue

        # Collect all search results for this prompt
        prompt_results: list[SearchResult] = []
        for query in queries:
            total_queries += 1
            try:
                results = searcher.search(query, max_results=mr)
                for r in results:
                    if r.url not in seen_urls:
                        seen_urls.add(r.url)
                        prompt_results.append(r)
            except Exception:
                logger.warning(
                    "Search failed for query %r (prompt %s), skipping",
                    query,
                    prompt.prompt_id,
                    exc_info=True,
                )

        if not prompt_results:
            logger.info(
                "No search results for prompt %s, dropping",
                prompt.prompt_id,
            )
            continue

        # Distribute weight evenly across results
        weight_per_result = prompt.payment_amount / len(prompt_results)

        for sr in prompt_results:
            researched.append(
                ResearchedPrompt(
                    prompt_id=prompt.prompt_id,
                    text=f"{sr.title}\n{sr.snippet}",
                    payment_amount=weight_per_result,
                    category_ids=prompt.category_ids,
                    source_url=sr.url,
                )
            )

    logger.info(
        "Topic research complete",
        extra={
            "step": "topic_research",
            "prompts_input": len(prompts),
            "queries_generated": total_queries,
            "results_output": len(researched),
            "unique_urls": len(seen_urls),
        },
    )

    return researched
