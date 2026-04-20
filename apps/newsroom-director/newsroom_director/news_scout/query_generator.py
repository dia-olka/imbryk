"""Generate search queries from the World History via Gemini Flash.

The LLM reasons about the current state of world affairs and produces
targeted search queries for each taxonomy category — what a journalist
would find editorially interesting right now.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..config import TAVILY_MAX_QUERIES_PER_CATEGORY
from ..generation import GenerationStrategy
from .schemas import (
    QueryGenerationOutput,
    is_valid_query_output,
    parse_query_output,
)

if TYPE_CHECKING:
    from ..personas import PersonaConfig

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are the chief intelligence officer for a newspaper group. Commission \
search queries that will surface the most editorially consequential real-\
world news for today's editions across all newspapers in the group.

Inputs you may receive: a world history record, a list of editorial \
categories, newspaper personas (ideology and focus), optional editorial \
context (director observations, newspaper intentions, reader engagement \
data), and recent headlines.

Query standards:
- Prefer named actors, specific regions, concrete events, verifiable \
timelines. Avoid generic "latest X news" queries.
- Include temporal anchors (month, quarter) when recency matters.
- Do not re-scout stories already covered in the recent-headlines block.
- Tailor to the readership: a conservative-leaning paper and a progressive \
one covering the same category want different framings.
- At most {max_queries} queries per category. Prioritise quality — one \
razor-sharp query beats three vague ones.

Include ALL provided category IDs; every category must have at least one \
query."""

MAX_RETRIES = 3


def _format_personas(personas: list[PersonaConfig]) -> str:
    """Format persona definitions as a compact editorial roster."""
    lines = []
    for p in personas:
        lines.append(
            f"- {p.paper_name} ({p.id}): {p.ideology} | {p.political_leaning} | "
            f"categories: {', '.join(p.subscribed_categories)}"
        )
    return "\n".join(lines)


def generate_queries(
    synopsis: str,
    category_ids: list[str],
    generation_strategy: GenerationStrategy,
    personas: list[PersonaConfig] | None = None,
    editorial_context: str = "",
    today_date: str = "",
) -> dict[str, list[str]]:
    """Generate search queries for each category based on World History.

    Args:
        synopsis: Serialized world history synopsis — a factual record
            of recent real-world events and ongoing story threads.
        category_ids: All 30 taxonomy category slugs.
        generation_strategy: LLM backend (Gemini Flash).
        personas: Newspaper persona configs so the model knows which
            editorial identities will consume each category's articles.
        editorial_context: Formatted editorial context — journal entries,
            previous headlines, and reader metrics from prior editions.

    Returns:
        Dict mapping category_id to list of search query strings.
        May be empty if all attempts fail.
    """
    category_list = "\n".join(f"- {cid}" for cid in category_ids)
    personas_section = (
        f"\nNEWSPAPER PERSONAS:\n{_format_personas(personas)}\n"
        if personas
        else ""
    )
    context_section = (
        f"\nEDITORIAL CONTEXT:\n{editorial_context}\n"
        if editorial_context
        else ""
    )
    today_section = (
        f"TODAY'S DATE: {today_date}\nSearch for real-world developments "
        f"that happened ON or IMMEDIATELY BEFORE {today_date}. Prefer "
        f"queries with explicit date anchors for this month.\n\n"
        if today_date
        else ""
    )

    user_content = (
        f"{today_section}"
        f"WORLD HISTORY:\n{synopsis}\n"
        f"{personas_section}"
        f"{context_section}\n"
        f"CATEGORIES:\n{category_list}\n\n"
        "Generate search queries for each category."
    )

    max_q = TAVILY_MAX_QUERIES_PER_CATEGORY
    system_prompt = _SYSTEM_PROMPT.replace("{max_queries}", str(max_q))

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            raw = generation_strategy.generate(
                system_prompt,
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
            # Enforce hard cap in case LLM exceeds the requested limit
            if max_q:
                queries = {
                    cat: qs[:max_q] for cat, qs in queries.items()
                }
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
