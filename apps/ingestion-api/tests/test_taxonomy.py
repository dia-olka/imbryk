"""Tests for taxonomy routing — mirrors TypeScript test coverage."""

from ingestion_api.taxonomy import (
    CATEGORY_ID_SET,
    CATEGORY_IDS,
    NEWSPAPER_SUBSCRIPTIONS,
    count_newspapers_reached,
    route_prompt,
)


def test_has_30_categories():
    assert len(CATEGORY_IDS) == 30


def test_all_category_ids_unique():
    assert len(CATEGORY_ID_SET) == 30


def test_each_newspaper_subscribes_to_9_to_10_categories():
    for newspaper_id, cats in NEWSPAPER_SUBSCRIPTIONS.items():
        assert 9 <= len(cats) <= 10, f"{newspaper_id} has {len(cats)} categories"


def test_all_categories_covered_by_at_least_one_newspaper():
    covered = set()
    for cats in NEWSPAPER_SUBSCRIPTIONS.values():
        covered.update(cats)
    assert covered == CATEGORY_ID_SET


def test_subscriptions_only_use_valid_categories():
    for newspaper_id, cats in NEWSPAPER_SUBSCRIPTIONS.items():
        for cat in cats:
            assert cat in CATEGORY_ID_SET, (
                f"{newspaper_id} references invalid category: {cat}"
            )


def test_route_prompt_empty_returns_empty():
    assert route_prompt([]) == []


def test_route_prompt_geopolitics_reaches_sovereign_aspirant():
    results = route_prompt(["geopolitics-and-diplomacy"])
    newspaper_ids = {r.newspaper_id for r in results}
    assert newspaper_ids == {"sovereign", "aspirant"}


def test_route_prompt_entertainment_reaches_moralist_hedonist():
    results = route_prompt(["entertainment-and-hollywood"])
    newspaper_ids = {r.newspaper_id for r in results}
    assert newspaper_ids == {"moralist", "hedonist"}


def test_route_prompt_matched_categories_correct():
    results = route_prompt(["geopolitics-and-diplomacy", "entertainment-and-hollywood"])
    result_map = {r.newspaper_id: r.matched_categories for r in results}
    assert "geopolitics-and-diplomacy" in result_map["sovereign"]
    assert "entertainment-and-hollywood" not in result_map["sovereign"]
    assert "entertainment-and-hollywood" in result_map["hedonist"]


def test_count_newspapers_reached():
    assert count_newspapers_reached(["geopolitics-and-diplomacy"]) == 2
    assert count_newspapers_reached([]) == 0
    assert count_newspapers_reached(["markets-and-macroeconomics"]) == 1
