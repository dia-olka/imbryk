"""Dataclass schemas for structured LLM output.

Passed to Gemini's response_schema to enforce exact field names and
structure in the generated JSON, preventing field name deviations
(e.g. "title"/"content"/"fullArticles") that cause gazette parse errors.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass
class ArticleOutput:
    headline: str
    body: str
    weight: float | None = None
    clusters: list[int] | None = None
    imagePrompt: str | None = None


@dataclass
class InBriefOutput:
    headline: str
    summary: str
    clusters: list[int] | None = None


@dataclass
class NewspaperOutput:
    newspaper_name: str
    frontPageImagePrompt: str
    articles: list[ArticleOutput]
    in_brief: list[InBriefOutput] | None = None
    editors_note: str | None = None
    metadata: dict | None = field(default=None)


@dataclass
class CuratorOutput:
    """Structured curator synthesis — one list per section."""
    consensus: list[str]
    fault_lines: list[str]
    uncovered_angles: list[str]
    what_to_watch: list[str]


# ─── Output validation ────────────────────────────────────────────────────────

def is_valid_newspaper(raw: str) -> bool:
    """Return True if *raw* parses as a newspaper with at least one usable article."""
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return False
    articles = parsed.get("articles") or []
    return (
        isinstance(articles, list)
        and len(articles) > 0
        and any(a.get("headline") and a.get("body") for a in articles)
    )


def is_valid_curator(raw: str) -> bool:
    """Return True if *raw* parses as a non-empty curator synthesis."""
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return False
    # New structured format
    consensus = parsed.get("consensus")
    if isinstance(consensus, list) and len(consensus) > 0:
        return True
    # Legacy text format
    text = parsed.get("text", "")
    return isinstance(text, str) and len(text.strip()) > 100
