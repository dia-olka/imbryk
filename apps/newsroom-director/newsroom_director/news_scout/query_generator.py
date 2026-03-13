"""Generate search queries from the WorldLedger via Gemini Flash.

The LLM reasons about the current world state and produces targeted
search queries for each taxonomy category — what a journalist in this
world would find editorially interesting right now.
"""

from __future__ import annotations

import logging

from ..generation import GenerationStrategy
from .schemas import (
    QueryGenerationOutput,
    is_valid_query_output,
    parse_query_output,
)

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a news editor for a fictional newspaper simulation. You have access \
to the current state of the world (provided below) and a list of 30 editorial \
categories.

Your task: for each category, generate 2-3 targeted web search queries that \
would find current real-world news stories relevant to that category. Think \
about what developments would be most editorially interesting given the world \
state — not what is most popular or trending, but what a thoughtful journalist \
would want to investigate.

Guidelines:
- Queries should be specific enough to return focused results (not generic \
like "latest news").
- Include date/time references where useful (e.g. "March 2026", "this week").
- For categories where the world state suggests active developments, generate \
3 queries. For quieter domains, 1-2 is fine.
- Each query should be a natural search engine query string.

You MUST respond with a JSON object matching this exact schema:
{
  "categories": [
    {
      "category_id": "<taxonomy-category-slug>",
      "queries": ["query 1", "query 2"]
    }
  ]
}

Include ALL provided category IDs in the output, each with at least 1 query."""

MAX_RETRIES = 3


def generate_queries(
    synopsis: str,
    category_ids: list[str],
    generation_strategy: GenerationStrategy,
) -> dict[str, list[str]]:
    """Generate search queries for each category based on the WorldLedger.

    Args:
        synopsis: Serialized WorldLedger synopsis text.
        category_ids: All 30 taxonomy category slugs.
        generation_strategy: LLM backend (Gemini Flash).

    Returns:
        Dict mapping category_id to list of search query strings.
        May be empty if all attempts fail.
    """
    category_list = "\n".join(f"- {cid}" for cid in category_ids)
    user_content = (
        f"WORLD STATE SYNOPSIS:\n{synopsis}\n\n"
        f"CATEGORIES:\n{category_list}\n\n"
        "Generate search queries for each category."
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            raw = generation_strategy.generate(
                _SYSTEM_PROMPT,
                "flash",
                user_content,
                response_schema=QueryGenerationOutput,
            )

            if not is_valid_query_output(raw):
                logger.warning(
                    "Invalid query generation output (attempt %d/%d)",
                    attempt,
                    MAX_RETRIES,
                )
                continue

            queries = parse_query_output(raw)
            total = sum(len(qs) for qs in queries.values())
            logger.info(
                "Query generation complete",
                extra={
                    "step": "news_scout_queries",
                    "categories_covered": len(queries),
                    "total_queries": total,
                },
            )
            return queries

        except Exception:
            logger.exception(
                "Query generation failed (attempt %d/%d)",
                attempt,
                MAX_RETRIES,
            )

    logger.error("All %d query generation attempts failed", MAX_RETRIES)
    return {}
