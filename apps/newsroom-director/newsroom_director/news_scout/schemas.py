"""Structured output schemas for News Scout LLM calls.

Passed to Gemini's response_schema to enforce exact JSON structure
in the query generation response.
"""

from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass
class CategoryQueries:
    """Search queries for a single taxonomy category."""

    category_id: str
    queries: list[str]


@dataclass
class QueryGenerationOutput:
    """Top-level schema for the query generation LLM call.

    The LLM returns a list of categories, each with 1-3 search queries
    tailored to the current WorldLedger state.
    """

    categories: list[CategoryQueries]


def is_valid_query_output(raw: str) -> bool:
    """Return True if *raw* parses as a valid query generation response.

    Validates:
    - Parses as JSON
    - Has a 'categories' list
    - At least one category has at least one non-empty query
    """
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return False

    categories = parsed.get("categories")
    if not isinstance(categories, list) or len(categories) == 0:
        return False

    return any(
        isinstance(cat, dict)
        and isinstance(cat.get("queries"), list)
        and any(isinstance(q, str) and q.strip() for q in cat["queries"])
        for cat in categories
    )


def parse_query_output(raw: str) -> dict[str, list[str]]:
    """Parse validated query output into a category_id -> queries dict.

    Call only after is_valid_query_output() returns True.
    """
    parsed = json.loads(raw)
    result: dict[str, list[str]] = {}
    for cat in parsed["categories"]:
        category_id = cat.get("category_id", "")
        queries = [
            q.strip()
            for q in cat.get("queries", [])
            if isinstance(q, str) and q.strip()
        ]
        if category_id and queries:
            result[category_id] = queries
    return result
