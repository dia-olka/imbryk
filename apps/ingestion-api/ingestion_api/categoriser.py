"""Categoriser strategy for classifying prompts into taxonomy categories."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ingestion_api.taxonomy import CATEGORY_ID_SET, CATEGORY_IDS


class CategoriserStrategy(ABC):
    @abstractmethod
    def categorise(self, prompt_text: str) -> list[str]:
        """Classify prompt text into 1-K taxonomy category IDs."""


class StubCategoriser(CategoriserStrategy):
    """Returns preconfigured categories. For tests."""

    def __init__(self, categories: list[str] | None = None):
        self._categories = categories or ["geopolitics"]

    def categorise(self, prompt_text: str) -> list[str]:
        return [c for c in self._categories if c in CATEGORY_ID_SET]


class GeminiFlashCategoriser(CategoriserStrategy):
    """Calls Gemini Flash to classify prompt into 1-K categories."""

    def __init__(self, project: str | None = None, location: str = "us-central1"):
        self._project = project
        self._location = location

    def categorise(self, prompt_text: str) -> list[str]:
        import vertexai
        from vertexai.generative_models import GenerativeModel

        if self._project:
            vertexai.init(project=self._project, location=self._location)

        model = GenerativeModel("gemini-2.0-flash")
        category_list = ", ".join(CATEGORY_IDS)
        system_prompt = (
            "You are a news categoriser. Given a user prompt, classify it into "
            "one or more of these categories. Return ONLY a JSON array of "
            f"category ID strings. Valid categories: [{category_list}]"
        )

        response = model.generate_content(
            [system_prompt, f"User prompt: {prompt_text}"]
        )

        import json

        try:
            raw = response.text.strip()
            # Handle markdown code blocks
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [c for c in parsed if c in CATEGORY_ID_SET]
        except (json.JSONDecodeError, AttributeError, IndexError):
            pass

        return []
