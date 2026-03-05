"""Taxonomy categories, newspaper subscriptions, and routing logic.

Data generated from data/taxonomy.json — single source of truth.
Run `npx nx run newsroom-director:generate-data` to regenerate.
"""

from __future__ import annotations

from dataclasses import dataclass

from newsroom_director._generated_data import TAXONOMY_DATA as _raw

CATEGORY_IDS: list[str] = [
    cat["id"] for group in _raw["groups"] for cat in group["categories"]
]

CATEGORY_ID_SET: set[str] = set(CATEGORY_IDS)

NEWSPAPER_SUBSCRIPTIONS: dict[str, list[str]] = _raw["subscriptions"]


@dataclass
class RoutingResult:
    newspaper_id: str
    matched_categories: list[str]


def route_prompt(category_ids: list[str]) -> list[RoutingResult]:
    """Route a prompt to newspapers based on category overlap."""
    if not category_ids:
        return []
    category_set = set(category_ids)
    results: list[RoutingResult] = []
    for newspaper_id, subscribed in NEWSPAPER_SUBSCRIPTIONS.items():
        matched = [c for c in subscribed if c in category_set]
        if matched:
            results.append(
                RoutingResult(
                    newspaper_id=newspaper_id, matched_categories=matched
                )
            )
    return results


def count_newspapers_reached(category_ids: list[str]) -> int:
    """Count how many newspapers a set of categories reaches."""
    return len(route_prompt(category_ids))
