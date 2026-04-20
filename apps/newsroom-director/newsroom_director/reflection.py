"""Editorial self-reflection — per-persona critique after each edition.

After all newspapers + curator are generated, each persona reviews its own
output and writes a journal entry. These entries are loaded into the
generation prompt on subsequent runs, giving the LLM persistent editorial
memory that evolves over time.
"""

from __future__ import annotations

import json
import logging

from .db import ArticleMetric, JournalEntry
from .generation import GenerationStrategy
from .personas import PersonaConfig

logger = logging.getLogger(__name__)


def _build_persona_reflection_prompt(
    persona: PersonaConfig,
    edition_date: str,
    persona_articles_json: str,
    curator_text: str,
    previous_entries: list[JournalEntry],
    metrics_text: str = "",
) -> tuple[str, str]:
    """Build system + user prompt for a persona's self-reflection."""

    metrics_instruction = ""
    if metrics_text:
        metrics_instruction = """
If reader metrics are provided below, factor them into your assessment. \
What topics resonated with readers? What fell flat? But do not chase clicks \
mindlessly — stay true to your editorial identity."""

    system = f"""\
You are the editor-in-chief of {persona.paper_name}, reviewing today's edition.

Your task is to write a brief editorial journal entry — an honest \
self-assessment that your future self will read before producing \
tomorrow's edition.
{metrics_instruction}
STRUCTURE YOUR RESPONSE AS:

## What Worked
1-3 bullet points on your strongest editorial decisions today.

## What Fell Short
1-3 bullet points on missed opportunities, weak coverage, or repetitive \
patterns.

## Tomorrow's Intentions
1-3 concrete editorial goals for the next edition.

## Running Notes
Any observations about long-term trends, recurring prompt themes, or \
editorial blind spots you are noticing across multiple days. Update or \
revise previous running notes if they are stale.

Be specific. Name articles, topics, and framing choices. Do not be generic.
Your future self needs actionable guidance, not platitudes.

Respond with ONLY the markdown text — no JSON wrapping, no code fences."""

    # Format previous journal entries
    journal_section = _format_journal_entries(previous_entries, persona.id)

    metrics_section = f"\n\n{metrics_text}" if metrics_text else ""

    user = f"""\
TODAY'S EDITION ({edition_date}):
{persona_articles_json}

{journal_section}
{metrics_section}
CURATOR'S ANALYSIS OF TODAY:
{curator_text}"""

    return system, user


def _build_pipeline_observation_prompt(
    edition_date: str,
    all_articles_text: str,
    previous_entries: list[JournalEntry],
    metrics_text: str = "",
) -> tuple[str, str]:
    """Build system + user prompt for pipeline-level observation."""

    metrics_instruction = ""
    if metrics_text:
        metrics_instruction = """
- Reader engagement: which newspapers and articles attracted the most \
readers? Are engagement patterns aligned with editorial quality?"""

    system = f"""\
You are the editorial director overseeing all 6 newspapers in this group.
Review today's cross-publication output and write observations for the \
pipeline.

Focus on:
- Coverage overlap: did multiple papers tell the same story the same way?
- Coverage gaps: what categories or angles got no meaningful coverage?
- Balance: is one ideological perspective dominating the day's output?
- Quality trends: compare to your previous observations if available.{metrics_instruction}

Be concise and specific. Name newspapers and articles.

Respond with ONLY the markdown text — no JSON wrapping, no code fences."""

    journal_section = _format_journal_entries(previous_entries, "_pipeline")

    metrics_section = f"\n\n{metrics_text}" if metrics_text else ""

    user = f"""\
TODAY'S EDITIONS ({edition_date}):
{all_articles_text}

{journal_section}{metrics_section}"""

    return system, user


def _format_journal_entries(
    entries: list[JournalEntry],
    persona_id: str,
) -> str:
    """Format journal entries for injection into a prompt."""
    persona_entries = [e for e in entries if e.persona_id == persona_id]
    pipeline_entries = [
        e for e in entries
        if e.persona_id == "_pipeline" and persona_id != "_pipeline"
    ]

    parts: list[str] = []

    if persona_entries:
        parts.append("YOUR PREVIOUS JOURNAL ENTRIES:")
        for entry in persona_entries:
            parts.append(
                f"\n--- {entry.entry_date} ({entry.entry_type}) ---\n"
                f"{entry.content}"
            )

    if pipeline_entries:
        parts.append("\nPIPELINE OBSERVATIONS (from editorial director):")
        for entry in pipeline_entries:
            parts.append(
                f"\n--- {entry.entry_date} ---\n{entry.content}"
            )

    if not parts:
        return "YOUR PREVIOUS JOURNAL ENTRIES:\n(No previous entries — this is your first edition.)"

    return "\n".join(parts)


def format_journal_for_generation(
    entries: list[JournalEntry],
    persona_id: str,
) -> str:
    """Format journal entries for the {{EDITORIAL_JOURNAL}} placeholder.

    Used during newspaper generation to inject recent reflections and
    intentions into the persona's system prompt.
    """
    if not entries:
        return "(No editorial journal entries yet.)"

    # For generation, show a condensed view: latest intention + last 3
    # reflections + last pipeline observation.
    persona_entries = [e for e in entries if e.persona_id == persona_id]
    pipeline_entries = [e for e in entries if e.persona_id == "_pipeline"]

    parts: list[str] = []

    # Most recent intention
    intentions = [e for e in persona_entries if e.entry_type == "intention"]
    if intentions:
        latest = intentions[-1]
        parts.append(
            f"YOUR LATEST EDITORIAL INTENTION ({latest.entry_date}):\n"
            f"{latest.content}"
        )

    # Last 3 reflections
    reflections = [e for e in persona_entries if e.entry_type == "reflection"]
    recent_reflections = reflections[-3:]
    if recent_reflections:
        parts.append("YOUR RECENT REFLECTIONS:")
        for entry in recent_reflections:
            parts.append(f"\n--- {entry.entry_date} ---\n{entry.content}")

    # Latest pipeline observation
    observations = [e for e in pipeline_entries if e.entry_type == "observation"]
    if observations:
        latest_obs = observations[-1]
        parts.append(
            f"\nEDITORIAL DIRECTOR'S OBSERVATION ({latest_obs.entry_date}):\n"
            f"{latest_obs.content}"
        )

    return "\n".join(parts) if parts else "(No editorial journal entries yet.)"


def format_previous_edition_summary(
    persona_id: str,
    edition_date: str,
    edition_content_json: str | None,
    metrics: list[ArticleMetric] | None = None,
    recent_headlines: list[tuple[str, str]] | None = None,
) -> str:
    """Format a compact summary of the persona's previous edition(s).

    Returns a short block listing headlines + view counts, suitable for
    appending to the editorial journal in generation prompts. If
    ``recent_headlines`` is supplied, a multi-day "RECENT HEADLINES TO
    AVOID" block is appended so the model can see stories it has already
    led the paper with this week.

    Returns empty string if no data is available.
    """
    lines: list[str] = []

    # Yesterday's headlines (with metrics when available)
    if edition_content_json:
        try:
            content = json.loads(edition_content_json)
        except (json.JSONDecodeError, TypeError):
            content = None

        if isinstance(content, list):
            article_list = content
        elif isinstance(content, dict):
            article_list = content.get("articles", [])
        else:
            article_list = []

        headlines = [
            (a.get("headline") or a.get("title", ""))
            for a in article_list
            if isinstance(a, dict)
        ]
        headlines = [h for h in headlines if h]

        if headlines:
            views_by_headline: dict[str, int] = {}
            if metrics:
                for m in metrics:
                    views_by_headline[m.headline] = m.page_views

            lines.append(f"YOUR PREVIOUS EDITION ({edition_date}):")
            for h in headlines:
                views = views_by_headline.get(h)
                if views is not None:
                    lines.append(f'- "{h}" \u2014 {views} views')
                else:
                    lines.append(f'- "{h}"')

    # Deeper history — strip yesterday (already above) to avoid duplication
    if recent_headlines:
        older = [(d, h) for (d, h) in recent_headlines if d != edition_date]
        if older:
            if lines:
                lines.append("")
            lines.append(
                "STORIES YOU ALREADY LED WITH THIS WEEK — do NOT re-use "
                "the same angle. If a storyline warrants another article, "
                "it MUST advance with new named sources, a new concrete "
                "development, and a new lede:"
            )
            for date, headline in older:
                lines.append(f'- [{date}] "{headline}"')

    return "\n".join(lines)


def run_persona_reflection(
    persona: PersonaConfig,
    edition_date: str,
    persona_articles_json: str,
    curator_text: str,
    previous_entries: list[JournalEntry],
    generation_strategy: GenerationStrategy,
    metrics_text: str = "",
) -> str | None:
    """Run self-reflection for a single persona. Returns the reflection text."""
    system, user = _build_persona_reflection_prompt(
        persona, edition_date, persona_articles_json,
        curator_text, previous_entries,
        metrics_text=metrics_text,
    )

    try:
        response = generation_strategy.generate(system, "pro", user)
        if response and len(response.strip()) > 20:
            return response.strip()
        logger.warning(
            "Reflection for %s too short, discarding", persona.id,
        )
        return None
    except Exception:
        logger.exception(
            "Reflection failed for %s, skipping", persona.id,
        )
        return None


def run_pipeline_observation(
    edition_date: str,
    all_articles_text: str,
    previous_entries: list[JournalEntry],
    generation_strategy: GenerationStrategy,
    metrics_text: str = "",
) -> str | None:
    """Run pipeline-level editorial observation. Returns the observation text."""
    system, user = _build_pipeline_observation_prompt(
        edition_date, all_articles_text, previous_entries,
        metrics_text=metrics_text,
    )

    try:
        response = generation_strategy.generate(system, "pro", user)
        if response and len(response.strip()) > 20:
            return response.strip()
        logger.warning("Pipeline observation too short, discarding")
        return None
    except Exception:
        logger.exception("Pipeline observation failed, skipping")
        return None
