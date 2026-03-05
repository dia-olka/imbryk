"""Tests for the categoriser strategy."""

from ingestion_api.categoriser import FALLBACK_CATEGORY, StubCategoriser
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


def test_fallback_category_is_valid():
    assert FALLBACK_CATEGORY in CATEGORY_ID_SET


def test_fallback_category_is_entertainment():
    assert FALLBACK_CATEGORY == "entertainment"


def test_gemini_categoriser_falls_back_on_invalid_json(monkeypatch):
    """GeminiFlashCategoriser returns FALLBACK_CATEGORY when Gemini returns garbage."""
    from unittest.mock import MagicMock

    from ingestion_api.categoriser import GeminiFlashCategoriser

    categoriser = GeminiFlashCategoriser(project=None)

    mock_response = MagicMock()
    mock_response.text = "not valid json at all!!!"

    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response

    mock_model_class = MagicMock(return_value=mock_model)

    monkeypatch.setattr(
        "vertexai.init", MagicMock()
    )
    monkeypatch.setattr(
        "vertexai.generative_models.GenerativeModel", mock_model_class
    )

    result = categoriser.categorise("asdkjhasdkjh gibberish")
    assert result == [FALLBACK_CATEGORY]


def test_gemini_categoriser_falls_back_on_empty_valid_categories(monkeypatch):
    """GeminiFlashCategoriser returns FALLBACK_CATEGORY when all parsed IDs are invalid."""
    from unittest.mock import MagicMock

    from ingestion_api.categoriser import GeminiFlashCategoriser

    categoriser = GeminiFlashCategoriser(project=None)

    mock_response = MagicMock()
    mock_response.text = '["not-a-real-category", "also-fake"]'

    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response

    monkeypatch.setattr(
        "vertexai.init", MagicMock()
    )
    monkeypatch.setattr(
        "vertexai.generative_models.GenerativeModel",
        MagicMock(return_value=mock_model),
    )

    result = categoriser.categorise("nonsense input")
    assert result == [FALLBACK_CATEGORY]
