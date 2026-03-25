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
You are the chief intelligence officer for a newspaper group. \
Your job is to commission search queries that will surface the most \
editorially consequential real-world news for today's editions across \
all newspapers in the group.

You have up to six inputs:
1. A world history record — a factual summary of recent real-world events, \
ongoing story threads, geopolitical developments, economic trends, \
technological shifts, and environmental crises tracked over time.
2. A set of editorial categories that the newspapers collectively cover.
3. The editorial identities of the newspapers — their ideologies, political \
leanings, and areas of focus — so you can tailor queries to what each \
readership finds most compelling.
4. (Optional) The editorial director's observations and each newspaper's \
editorial intentions — what the team noticed about coverage quality and \
what they plan to focus on next.
5. (Optional) Headlines from the previous edition — so you avoid \
commissioning duplicate stories and instead advance the narrative.
6. (Optional) Reader engagement data — which articles readers actually \
engaged with, so you can prioritise topics that resonate.

Your reasoning process:
- Review the world history to understand ongoing story threads, recent \
developments, and evolving situations that may have new developments today.
- For each category, consider which newspapers subscribe to it and what \
angle their readership would find most valuable — a geopolitical category \
read by a conservative-leaning paper demands different query framing than \
the same category read by a progressive one.
- If editorial context is provided, use it to steer your queries: address \
coverage gaps the editorial director flagged, support newspapers' stated \
intentions, avoid re-scouting stories that were already published, and \
lean into topics that readers engaged with.
- Decide which specific real-world developments a discerning editor would \
find most valuable RIGHT NOW — not trending stories, but stories with \
genuine narrative depth and geopolitical weight.
- Formulate queries that cut through noise: prefer named actors, specific \
regions, concrete events, and verifiable timelines over broad topic searches.
- Generate at most {max_queries} query per category. Make each one count — \
choose the single most editorially valuable angle.
- Include temporal anchors (e.g. "March 2026", "Q1 2026", "this month") \
where recency matters.
- Avoid: generic news queries ("latest X news"), celebrity/entertainment \
unless the category demands it, queries duplicating each other across \
categories, and queries that would retrieve stories already covered in \
the previous edition.

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
    user_content = (
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
