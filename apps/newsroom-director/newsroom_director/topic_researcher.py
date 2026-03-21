"""Topic research — transform user prompts into real-world news via Tavily.

Each paid prompt is used to generate targeted search queries (Gemini Flash),
which are executed via Tavily. The resulting news articles enter the
distillation pipeline in place of the raw user text.

Weight inheritance: a prompt's payment weight is distributed evenly across
its research results, preserving the economic signal.

All research attempts (success or failure) are persisted to the
``prompt_research_log`` table so every step from prompt to search query to
Tavily result is auditable.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from .config import (
    TAVILY_MAX_RESULTS_PER_QUERY,
    TOPIC_RESEARCH_MAX_QUERIES,
    TOPIC_RESEARCH_MAX_RETRIES,
)
from .db import (
    PromptRecord,
    count_prompt_research_attempts,
    save_prompt_research_log,
)
from .generation import GenerationStrategy
from .news_scout.searcher import RateLimitExceeded, SearchResult, SearchStrategy

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
{"queries": ["query 1", "query 2", ...]}"""

_WHISPER_PROMPT = """\
You are a safety filter for an AI newspaper generation system. A reader \
submitted a topic suggestion. No matching news articles were found, but \
the editorial team still wants to acknowledge public interest in this topic.

Rephrase the reader's suggestion as a brief, neutral, third-person \
observation about public discourse — a "whisper" reflecting what people \
are talking about. Do NOT repeat the raw user text. Instead, capture the \
essence of the topic in a safe, editorial voice.

Rules:
- Write 1-2 sentences maximum.
- Use phrases like "Public attention has turned to…", "Observers note \
growing interest in…", "Conversations are circulating about…".
- Strip any offensive, harmful, or manipulative content — keep only the \
legitimate topical interest.
- If the input is nonsensical, abusive, or cannot be safely rephrased, \
respond with exactly: {"whisper": null}
- Do NOT include URLs, user handles, or personally identifiable information.

Respond with ONLY a JSON object:
{"whisper": "Your rephrased whisper here"}"""


@dataclass
class TopicQueryOutput:
    """Schema for the topic query generation LLM call."""

    queries: list[str]


@dataclass
class WhisperOutput:
    """Schema for the whisper generation LLM call."""

    whisper: str | None


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


@dataclass
class ResearchResult:
    """Return value from research_prompts with audit data."""

    researched: list[ResearchedPrompt]
    failed_prompt_ids: list[str] = field(default_factory=list)


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
        except Exception:
            logger.warning(
                "Failed to generate queries for prompt %s (attempt %d/%d)",
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


def _generate_whisper(
    prompt: PromptRecord,
    generation_strategy: GenerationStrategy,
) -> str | None:
    """Sanitize a user prompt into a safe editorial whisper via Gemini Flash.

    Returns the whisper text, or None if the prompt cannot be safely rephrased.
    """
    user_content = f"READER SUGGESTION:\n{prompt.text}"

    try:
        raw = generation_strategy.generate(
            _WHISPER_PROMPT,
            "flash",
            user_content,
            response_schema=WhisperOutput,
        )
        parsed = json.loads(raw)
        whisper = parsed.get("whisper")
        if isinstance(whisper, str) and whisper.strip():
            return whisper.strip()
        logger.info(
            "Whisper generation returned null for prompt %s (unsafe content filtered)",
            prompt.prompt_id,
        )
        return None
    except Exception:
        logger.warning(
            "Failed to generate whisper for prompt %s",
            prompt.prompt_id,
            exc_info=True,
        )
        return None


def research_prompts(
    prompts: list[PromptRecord],
    searcher: SearchStrategy,
    generation_strategy: GenerationStrategy,
    max_queries: int | None = None,
    max_results_per_query: int | None = None,
    exclude_urls: set[str] | None = None,
    session: Session | None = None,
    edition_date: str = "",
    max_research_retries: int | None = None,
) -> ResearchResult:
    """Research all prompts and return ResearchedPrompts with inherited weights.

    Each prompt is transformed into 0-N ResearchedPrompts derived from
    Tavily search results. The prompt's payment_amount is distributed
    evenly across its results. Each result inherits the original prompt's
    category_ids for routing.

    Prompts that yield no research results are tracked as failed.  If the
    prompt has not exceeded ``max_research_retries`` attempts, its ID is
    returned in ``failed_prompt_ids`` so the caller can leave it as
    ``accepted`` for retry on the next pipeline run.

    All attempts (success and failure) are persisted to
    ``prompt_research_log`` when a DB session is provided.

    Args:
        prompts: Paid user prompts to research.
        searcher: Tavily search backend.
        generation_strategy: LLM backend for query generation.
        max_queries: Max queries per prompt (default: TOPIC_RESEARCH_MAX_QUERIES).
        max_results_per_query: Max Tavily results per query
            (default: TAVILY_MAX_RESULTS_PER_QUERY).
        exclude_urls: URLs to skip (e.g. News Scout items already in pipeline).
        session: DB session for persisting research logs. Optional for
            backward compatibility with tests.
        edition_date: Current edition date (YYYY-MM-DD).
        max_research_retries: Max research attempts before giving up on a
            prompt (default: TOPIC_RESEARCH_MAX_RETRIES).

    Returns:
        ResearchResult with researched prompts and failed prompt IDs.
    """
    if not prompts:
        return ResearchResult(researched=[])

    mq = max_queries if max_queries is not None else TOPIC_RESEARCH_MAX_QUERIES
    mr = (
        max_results_per_query
        if max_results_per_query is not None
        else TAVILY_MAX_RESULTS_PER_QUERY
    )
    max_retries = (
        max_research_retries
        if max_research_retries is not None
        else TOPIC_RESEARCH_MAX_RETRIES
    )

    researched: list[ResearchedPrompt] = []
    failed_prompt_ids: list[str] = []
    seen_urls: set[str] = set(exclude_urls) if exclude_urls else set()
    total_queries = 0
    rate_limited = False

    for prompt in prompts:
        # Check retry count before attempting research
        if session is not None:
            prior_attempts = count_prompt_research_attempts(
                session, prompt.prompt_id
            )
            if prior_attempts >= max_retries:
                # Last chance — generate a whisper before giving up
                whisper = _generate_whisper(prompt, generation_strategy)
                if whisper:
                    logger.info(
                        "Prompt %s exhausted retries (%d), using whisper",
                        prompt.prompt_id,
                        max_retries,
                    )
                    researched.append(
                        ResearchedPrompt(
                            prompt_id=prompt.prompt_id,
                            text=whisper,
                            payment_amount=prompt.payment_amount,
                            category_ids=prompt.category_ids,
                            source_url="",
                        )
                    )
                    save_prompt_research_log(
                        session,
                        prompt_id=prompt.prompt_id,
                        edition_date=edition_date,
                        queries=[],
                        results=[{"whisper": whisper}],
                        status="exhausted_whisper",
                    )
                else:
                    logger.warning(
                        "Prompt %s exhausted retries (%d) and whisper failed, "
                        "marking as exhausted",
                        prompt.prompt_id,
                        max_retries,
                    )
                    save_prompt_research_log(
                        session,
                        prompt_id=prompt.prompt_id,
                        edition_date=edition_date,
                        queries=[],
                        results=[],
                        status="exhausted",
                    )
                # Don't add to failed_prompt_ids — let it be marked processed
                # so it stops being retried.
                continue

        if rate_limited:
            logger.info(
                "Skipping prompt %s — Tavily rate limit reached",
                prompt.prompt_id,
            )
            failed_prompt_ids.append(prompt.prompt_id)
            if session is not None:
                save_prompt_research_log(
                    session,
                    prompt_id=prompt.prompt_id,
                    edition_date=edition_date,
                    queries=[],
                    results=[],
                    status="rate_limited",
                )
            continue

        queries = _generate_queries_for_prompt(
            prompt, generation_strategy, mq
        )
        if not queries:
            logger.info(
                "No queries generated for prompt %s, will retry",
                prompt.prompt_id,
            )
            failed_prompt_ids.append(prompt.prompt_id)
            if session is not None:
                save_prompt_research_log(
                    session,
                    prompt_id=prompt.prompt_id,
                    edition_date=edition_date,
                    queries=[],
                    results=[],
                    status="query_generation_failed",
                )
            continue

        # Collect all search results for this prompt
        prompt_results: list[SearchResult] = []
        prompt_status = "success"
        for query in queries:
            if rate_limited:
                break
            total_queries += 1
            try:
                results = searcher.search(query, max_results=mr)
                for r in results:
                    if r.url not in seen_urls:
                        seen_urls.add(r.url)
                        prompt_results.append(r)
            except RateLimitExceeded:
                logger.warning(
                    "Tavily rate limit reached during query %r (prompt %s), "
                    "stopping all further searches",
                    query,
                    prompt.prompt_id,
                )
                rate_limited = True
                prompt_status = "rate_limited"
            except Exception:
                logger.warning(
                    "Search failed for query %r (prompt %s), skipping",
                    query,
                    prompt.prompt_id,
                    exc_info=True,
                )

        # Serialize results for the research log
        results_data = [
            {"title": r.title, "snippet": r.snippet, "url": r.url}
            for r in prompt_results
        ]

        if not prompt_results:
            if prompt_status == "success":
                prompt_status = "no_results"
            # No news found — try to generate a sanitized whisper so the
            # prompt still influences the edition without exposing raw text.
            whisper = _generate_whisper(prompt, generation_strategy)
            if whisper:
                logger.info(
                    "No search results for prompt %s, using whisper fallback",
                    prompt.prompt_id,
                )
                researched.append(
                    ResearchedPrompt(
                        prompt_id=prompt.prompt_id,
                        text=whisper,
                        payment_amount=prompt.payment_amount,
                        category_ids=prompt.category_ids,
                        source_url="",
                    )
                )
                prompt_status = "whisper"
                if session is not None:
                    save_prompt_research_log(
                        session,
                        prompt_id=prompt.prompt_id,
                        edition_date=edition_date,
                        queries=queries,
                        results=[{"whisper": whisper}],
                        status=prompt_status,
                    )
                continue

            # Whisper generation also failed — defer for retry
            logger.info(
                "No search results and whisper failed for prompt %s, "
                "will retry next run",
                prompt.prompt_id,
            )
            failed_prompt_ids.append(prompt.prompt_id)
            if session is not None:
                save_prompt_research_log(
                    session,
                    prompt_id=prompt.prompt_id,
                    edition_date=edition_date,
                    queries=queries,
                    results=[],
                    status=prompt_status,
                )
            continue

        # Persist successful research log
        if session is not None:
            save_prompt_research_log(
                session,
                prompt_id=prompt.prompt_id,
                edition_date=edition_date,
                queries=queries,
                results=results_data,
                status="success",
            )

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
            "searches_executed": total_queries,
            "results_output": len(researched),
            "failed_prompts": len(failed_prompt_ids),
            "unique_urls": len(seen_urls),
            "rate_limited": rate_limited,
        },
    )

    return ResearchResult(
        researched=researched,
        failed_prompt_ids=failed_prompt_ids,
    )
