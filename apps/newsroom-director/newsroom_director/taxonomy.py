"""Taxonomy categories, newspaper subscriptions, and routing logic.

Copy of ingestion_api/taxonomy.py — keeps newsroom-director self-contained.
"""

from dataclasses import dataclass

CATEGORY_IDS: list[str] = [
    # Power & Governance
    "geopolitics",
    "domestic-politics",
    "military-and-defence",
    "law-and-justice",
    "immigration",
    "intelligence-and-surveillance",
    # Finance & Economy
    "finance-and-markets",
    "trade-and-commerce",
    "real-estate-and-property",
    "cryptocurrency",
    "labour-and-employment",
    # Science & Technology
    "technology-and-innovation",
    "artificial-intelligence",
    "science-and-research",
    "energy",
    # Society & Values
    "social-issues",
    "education",
    "religion-and-faith",
    "crime-and-public-safety",
    "health-and-medicine",
    # Environment
    "climate-and-environment",
    "food-and-agriculture",
    # Culture & Entertainment
    "entertainment",
    "celebrity-and-personalities",
    "culture-and-arts",
    "sports",
    "fashion-and-style",
    "food-and-lifestyle",
    "travel",
    "corruption-and-scandal",
]

CATEGORY_ID_SET: set[str] = set(CATEGORY_IDS)

NEWSPAPER_SUBSCRIPTIONS: dict[str, list[str]] = {
    "sovereign": [
        "geopolitics",
        "domestic-politics",
        "military-and-defence",
        "law-and-justice",
        "immigration",
        "intelligence-and-surveillance",
        "trade-and-commerce",
        "energy",
        "technology-and-innovation",
    ],
    "aspirant": [
        "geopolitics",
        "social-issues",
        "climate-and-environment",
        "health-and-medicine",
        "education",
        "immigration",
        "science-and-research",
        "food-and-agriculture",
        "culture-and-arts",
    ],
    "owner": [
        "finance-and-markets",
        "trade-and-commerce",
        "real-estate-and-property",
        "cryptocurrency",
        "labour-and-employment",
        "technology-and-innovation",
        "artificial-intelligence",
        "energy",
    ],
    "moralist": [
        "domestic-politics",
        "religion-and-faith",
        "education",
        "crime-and-public-safety",
        "health-and-medicine",
        "immigration",
        "law-and-justice",
        "social-issues",
        "entertainment",
    ],
    "radical": [
        "domestic-politics",
        "labour-and-employment",
        "corruption-and-scandal",
        "intelligence-and-surveillance",
        "cryptocurrency",
        "social-issues",
        "immigration",
        "geopolitics",
        "climate-and-environment",
    ],
    "hedonist": [
        "entertainment",
        "celebrity-and-personalities",
        "culture-and-arts",
        "sports",
        "fashion-and-style",
        "food-and-lifestyle",
        "travel",
        "corruption-and-scandal",
    ],
}


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
                    newspaper_id=newspaper_id,
                    matched_categories=matched,
                )
            )

    return results


def count_newspapers_reached(category_ids: list[str]) -> int:
    """Count how many newspapers a set of categories reaches."""
    return len(route_prompt(category_ids))
