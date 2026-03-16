"""Format editorial context for the News Scout query generator.

Assembles journal entries, previous headlines, and reader metrics into
a compact text block (~2-3K tokens) that supplements the WorldLedger
synopsis — giving the LLM awareness of editorial history and reader
engagement when deciding what to search for.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta

from ..db import ArticleMetric, JournalEntry

logger = logging.getLogger(__name__)


def _previous_date(edition_date: str) -> str:
    """Return the day before *edition_date* as YYYY-MM-DD."""
    dt = datetime.strptime(edition_date, "%Y-%m-%d") - timedelta(days=1)
    return dt.strftime("%Y-%m-%d")


def _format_journal_context(
    journal_entries: list[JournalEntry],
) -> str:
    """Condense journal entries into a compact editorial context block.

    Shows: latest pipeline observation + per-persona intentions.
    """
    if not journal_entries:
        return ""

    pipeline_entries = [
        e for e in journal_entries if e.persona_id == "_pipeline"
    ]
    persona_entries = [
        e for e in journal_entries if e.persona_id != "_pipeline"
    ]

    parts: list[str] = []

    # Latest pipeline observation
    observations = [e for e in pipeline_entries if e.entry_type == "observation"]
    if observations:
        latest = observations[-1]
        parts.append(
            f"EDITORIAL DIRECTOR'S OBSERVATION ({latest.entry_date}):\n"
            f"{latest.content}"
        )

    # Per-persona latest intentions
    intentions_by_persona: dict[str, JournalEntry] = {}
    for e in persona_entries:
        if e.entry_type == "intention":
            intentions_by_persona[e.persona_id] = e
        elif e.entry_type == "reflection" and e.persona_id not in intentions_by_persona:
            intentions_by_persona[e.persona_id] = e

    if intentions_by_persona:
        parts.append("NEWSPAPER EDITORIAL INTENTIONS:")
        for persona_id, entry in sorted(intentions_by_persona.items()):
            parts.append(f"- {persona_id} ({entry.entry_type}, {entry.entry_date}): {entry.content[:300]}")

    return "\n".join(parts)


def _format_previous_headlines(
    edition_data: dict[str, str] | None,
) -> str:
    """Extract headlines from the previous edition's content JSON.

    Returns a compact list of headlines grouped by newspaper.
    """
    if not edition_data:
        return ""

    parts: list[str] = ["PREVIOUS EDITION HEADLINES:"]
    for newspaper_id, content_json in sorted(edition_data.items()):
        try:
            articles = json.loads(content_json)
            if isinstance(articles, list):
                headlines = [
                    a.get("headline") or a.get("title", "")
                    for a in articles
                    if isinstance(a, dict)
                ]
            elif isinstance(articles, dict):
                article_list = articles.get("articles", [])
                headlines = [
                    a.get("headline") or a.get("title", "")
                    for a in article_list
                    if isinstance(a, dict)
                ]
            else:
                continue
            headlines = [h for h in headlines if h]
            if headlines:
                parts.append(f"  {newspaper_id}:")
                for h in headlines:
                    parts.append(f"    - {h}")
        except (json.JSONDecodeError, TypeError):
            continue

    return "\n".join(parts) if len(parts) > 1 else ""


def _format_reader_metrics(
    metrics: dict[str, list[ArticleMetric]],
) -> str:
    """Format reader engagement data as a compact summary.

    Shows top articles by views per newspaper.
    """
    if not metrics:
        return ""

    parts: list[str] = ["READER ENGAGEMENT (previous edition):"]
    for newspaper_id, article_metrics in sorted(metrics.items()):
        if not article_metrics:
            continue
        parts.append(f"  {newspaper_id}:")
        # Show top 3 articles by views
        for am in article_metrics[:3]:
            parts.append(f"    - \"{am.headline}\" — {am.page_views} views")

    return "\n".join(parts) if len(parts) > 1 else ""


def format_scout_context(
    journal_entries: list[JournalEntry],
    previous_edition: dict[str, str] | None,
    reader_metrics: dict[str, list[ArticleMetric]],
) -> str:
    """Build the editorial context string for the News Scout.

    Combines journal entries, previous headlines, and reader metrics
    into a single compact text block. Returns empty string if no
    context is available.
    """
    sections = [
        _format_journal_context(journal_entries),
        _format_previous_headlines(previous_edition),
        _format_reader_metrics(reader_metrics),
    ]

    result = "\n\n".join(s for s in sections if s)
    if result:
        logger.info(
            "Scout editorial context: %d chars",
            len(result),
            extra={"step": "news_scout_context"},
        )
    return result
