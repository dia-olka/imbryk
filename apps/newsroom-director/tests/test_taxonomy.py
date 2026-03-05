"""Tests for taxonomy routing."""

from newsroom_director.taxonomy import CATEGORY_IDS, route_prompt


class TestRoutePrompt:
    def test_geopolitics_routes_to_sovereign_aspirant(self):
        results = route_prompt(["geopolitics-and-diplomacy"])
        ids = {r.newspaper_id for r in results}
        assert "sovereign" in ids
        assert "aspirant" in ids

    def test_markets_routes_to_owner(self):
        results = route_prompt(["markets-and-macroeconomics"])
        ids = {r.newspaper_id for r in results}
        assert "owner" in ids
        assert "sovereign" not in ids

    def test_entertainment_routes_to_hedonist_moralist(self):
        results = route_prompt(["entertainment-and-hollywood"])
        ids = {r.newspaper_id for r in results}
        assert "hedonist" in ids
        assert "moralist" in ids

    def test_empty_categories_returns_empty(self):
        assert route_prompt([]) == []

    def test_unknown_category_returns_empty(self):
        assert route_prompt(["nonexistent-category"]) == []

    def test_multiple_categories(self):
        results = route_prompt(["geopolitics-and-diplomacy", "markets-and-macroeconomics"])
        ids = {r.newspaper_id for r in results}
        assert "sovereign" in ids
        assert "owner" in ids

    def test_matched_categories_correct(self):
        results = route_prompt(
            ["geopolitics-and-diplomacy", "domestic-politics-and-policy", "entertainment-and-hollywood"]
        )
        sovereign = next(r for r in results if r.newspaper_id == "sovereign")
        assert "geopolitics-and-diplomacy" in sovereign.matched_categories
        assert "domestic-politics-and-policy" in sovereign.matched_categories
        assert "entertainment-and-hollywood" not in sovereign.matched_categories

    def test_category_ids_has_30_entries(self):
        assert len(CATEGORY_IDS) == 30
