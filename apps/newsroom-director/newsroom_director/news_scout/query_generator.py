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
You are the chief intelligence officer for a fictional world newspaper. \
Your job is to commission search queries that will surface the most \
editorially consequential real-world news for today's edition.

You have two inputs:
1. A synopsis of the fictional world's current state — nations, conflicts, \
alliances, economic trends, technological developments, cultural movements, \
and environmental crises.
2. A set of editorial categories that the newspaper covers.

Your reasoning process:
- Identify which fictional world threads have real-world analogues or \
parallels that could enrich the narrative (e.g. a fictional energy scarcity \
crisis maps to real-world energy market disruptions).
- For each category, decide which specific real-world developments a \
discerning editor would find most valuable RIGHT NOW — not trending stories, \
but stories with genuine narrative depth and geopolitical weight.
- Formulate queries that cut through noise: prefer named actors, specific \
regions, concrete events, and verifiable timelines over broad topic searches.
- Where the world synopsis signals active tension or change in a domain, \
generate 3 precise queries. For stable domains, 1-2 well-targeted queries \
are enough.
- Include temporal anchors (e.g. "March 2026", "Q1 2026", "this month") \
where recency matters.
- Avoid: generic news queries ("latest X news"), celebrity/entertainment \
unless the category demands it, queries duplicating each other across \
categories.

You MUST respond with a JSON object matching this exact schema:
{
  "categories": [
    {
      "category_id": "<taxonomy-category-slug>",
      "queries": ["query 1", "query 2"]
    }
  ]
}

Include ALL provided category IDs. Every category must have at least 1 query. \
Prioritise quality over quantity — a single razor-sharp query beats three \
vague ones."""

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
                "pro",
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
