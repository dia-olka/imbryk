"""Tests for the categoriser strategy."""

from ingestion_api.categoriser import FALLBACK_CATEGORY, StubCategoriser
from ingestion_api.taxonomy import CATEGORY_ID_SET


def test_stub_categoriser_returns_configured_categories():
    categoriser = StubCategoriser(categories=["geopolitics-and-diplomacy", "energy-and-transition"])
    result = categoriser.categorise("test prompt")
    assert result == ["geopolitics-and-diplomacy", "energy-and-transition"]


def test_stub_categoriser_filters_invalid_categories():
    categoriser = StubCategoriser(categories=["geopolitics-and-diplomacy", "invalid-cat"])
    result = categoriser.categorise("test prompt")
    assert result == ["geopolitics-and-diplomacy"]


def test_stub_categoriser_default():
    categoriser = StubCategoriser()
    result = categoriser.categorise("test prompt")
    assert result == ["geopolitics-and-diplomacy"]


def test_stub_categoriser_results_are_valid():
    categoriser = StubCategoriser(
        categories=["geopolitics-and-diplomacy", "entertainment-and-hollywood", "energy-and-transition"]
    )
    result = categoriser.categorise("anything")
    for cat in result:
        assert cat in CATEGORY_ID_SET


def test_fallback_category_is_valid():
    assert FALLBACK_CATEGORY in CATEGORY_ID_SET


def test_fallback_category_is_entertainment_and_hollywood():
    assert FALLBACK_CATEGORY == "entertainment-and-hollywood"


def test_gemini_categoriser_falls_back_on_invalid_json(monkeypatch):
    """GeminiFlashCategoriser returns FALLBACK_CATEGORY when Gemini returns garbage."""
    from unittest.mock import MagicMock, patch

    from ingestion_api.categoriser import GeminiFlashCategoriser

    categoriser = GeminiFlashCategoriser(project=None)

    mock_response = MagicMock()
    mock_response.text = "not valid json at all!!!"

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("google.genai.Client", return_value=mock_client):
        result = categoriser.categorise("asdkjhasdkjh gibberish")
    assert result == [FALLBACK_CATEGORY]


def test_gemini_categoriser_falls_back_on_empty_valid_categories(monkeypatch):
    """GeminiFlashCategoriser returns FALLBACK_CATEGORY when all parsed IDs are invalid."""
    from unittest.mock import MagicMock, patch

    from ingestion_api.categoriser import GeminiFlashCategoriser

    categoriser = GeminiFlashCategoriser(project=None)

    mock_response = MagicMock()
    mock_response.text = '["not-a-real-category", "also-fake"]'

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("google.genai.Client", return_value=mock_client):
        result = categoriser.categorise("nonsense input")
    assert result == [FALLBACK_CATEGORY]


def test_gemini_categoriser_system_prompt_accepts_any_language():
    """GeminiFlashCategoriser system prompt instructs the model to accept any language."""
    from unittest.mock import MagicMock, patch

    from ingestion_api.categoriser import GeminiFlashCategoriser

    categoriser = GeminiFlashCategoriser(project=None)

    captured_prompt = {}

    def capture_call(model, contents, config):
        captured_prompt["system"] = config.system_instruction
        mock_response = MagicMock()
        mock_response.text = '["geopolitics-and-diplomacy"]'
        return mock_response

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = capture_call

    with patch("google.genai.Client", return_value=mock_client):
        categoriser.categorise("Les taux d'intérêt montent")

    assert "any language" in captured_prompt["system"]


def test_stub_categoriser_handles_non_english_prompt():
    """StubCategoriser classifies a non-English prompt without error."""
    categoriser = StubCategoriser(categories=["geopolitics-and-diplomacy"])
    result = categoriser.categorise("Les taux d'intérêt montent")
    assert result == ["geopolitics-and-diplomacy"]
