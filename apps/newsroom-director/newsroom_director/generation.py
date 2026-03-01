"""Generation strategies for LLM article generation."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Gemini model names by tier
MODEL_MAP = {
    "pro": "gemini-2.0-pro",
    "flash": "gemini-2.0-flash",
}


class GenerationStrategy(ABC):
    """Abstract base for LLM generation backends."""

    @abstractmethod
    def generate(self, system_prompt: str, model_tier: str) -> str:
        """Generate text from a system prompt using the specified model tier."""


class VertexAIStrategy(GenerationStrategy):
    """Calls Gemini via the Vertex AI SDK."""

    def __init__(self, project: str, location: str = "us-central1") -> None:
        self._project = project
        self._location = location
        self._initialized = False

    def _init_vertex(self) -> None:
        if self._initialized:
            return
        import vertexai

        vertexai.init(project=self._project, location=self._location)
        self._initialized = True

    def generate(self, system_prompt: str, model_tier: str) -> str:
        self._init_vertex()
        from vertexai.generative_models import GenerativeModel

        model_name = MODEL_MAP.get(model_tier, MODEL_MAP["flash"])
        model = GenerativeModel(
            model_name,
            system_instruction=system_prompt,
        )
        response = model.generate_content("Generate today's edition.")
        return response.text


class StubGenerationStrategy(GenerationStrategy):
    """Returns canned responses for testing."""

    def __init__(self, responses: dict[str, str] | None = None) -> None:
        self._responses = responses or {}
        self._calls: list[dict[str, str]] = []

    def generate(self, system_prompt: str, model_tier: str) -> str:
        self._calls.append(
            {"system_prompt": system_prompt, "model_tier": model_tier}
        )
        # Return a response keyed by model_tier, or a default
        if model_tier in self._responses:
            return self._responses[model_tier]
        return f"[Stub article generated with {model_tier} model]"

    @property
    def calls(self) -> list[dict[str, str]]:
        return self._calls
