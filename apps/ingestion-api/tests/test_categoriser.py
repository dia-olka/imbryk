"""Tests for the categoriser strategy."""

from ingestion_api.categoriser import StubCategoriser
from ingestion_api.taxonomy import CATEGORY_ID_SET


def test_stub_categoriser_returns_configured_categories():
    categoriser = StubCategoriser(categories=["geopolitics", "energy"])
    result = categoriser.categorise("test prompt")
    assert result == ["geopolitics", "energy"]


def test_stub_categoriser_filters_invalid_categories():
    categoriser = StubCategoriser(categories=["geopolitics", "invalid-cat"])
    result = categoriser.categorise("test prompt")
    assert result == ["geopolitics"]


def test_stub_categoriser_default():
    categoriser = StubCategoriser()
    result = categoriser.categorise("test prompt")
    assert result == ["geopolitics"]


def test_stub_categoriser_results_are_valid():
    categoriser = StubCategoriser(
        categories=["geopolitics", "entertainment", "energy"]
    )
    result = categoriser.categorise("anything")
    for cat in result:
        assert cat in CATEGORY_ID_SET
