"""Generation strategies for LLM article generation."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from . import config
from .retry import with_retry

logger = logging.getLogger(__name__)

# Gemini model names by tier — sourced from config (env-overridable)
MODEL_MAP = {
    "pro": config.GENERATION_MODEL_PRO,
    "flash": config.GENERATION_MODEL_FLASH,
}


class GenerationStrategy(ABC):
    """Abstract base for LLM generation backends."""

    @abstractmethod
    def generate(self, system_prompt: str, model_tier: str) -> str:
        """Generate text from a system prompt using the specified model tier."""

    def create_cache(self, system_instruction: str) -> Any:
        """Create a context cache with the given system instruction.

        Returns an opaque cached-content handle.  The default
        implementation returns ``None`` (no caching).
        """
        return None

    def generate_with_cache(
        self, cached_content: Any, user_prompt: str, model_tier: str
    ) -> str:
        """Generate using a previously created context cache.

        The default falls back to :meth:`generate`.
        """
        return self.generate(user_prompt, model_tier)

    def delete_cache(self, cached_content: Any) -> None:  # noqa: B027
        """Force-delete a context cache.  Default is a no-op."""


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

        def _call() -> str:
            model = GenerativeModel(
                model_name,
                system_instruction=system_prompt,
            )
            response = model.generate_content("Generate today's edition.")
            return response.text

        return with_retry(_call)

    def create_cache(self, system_instruction: str) -> Any:
        self._init_vertex()
        from vertexai.preview.caching import CachedContent

        model_name = MODEL_MAP["pro"]
        cached = CachedContent.create(
            model_name=model_name,
            system_instruction=system_instruction,
        )
        logger.info(
            "Context cache created",
            extra={"cache_name": cached.name},
        )
        return cached

    def generate_with_cache(
        self, cached_content: Any, user_prompt: str, model_tier: str
    ) -> str:
        self._init_vertex()
        from vertexai.generative_models import GenerativeModel

        def _call() -> str:
            model = GenerativeModel.from_cached_content(cached_content)
            response = model.generate_content(user_prompt)
            return response.text

        return with_retry(_call)

    def delete_cache(self, cached_content: Any) -> None:
        try:
            cached_content.delete()
            logger.info(
                "Context cache deleted",
                extra={"cache_name": cached_content.name},
            )
        except Exception:
            logger.warning("Failed to delete context cache", exc_info=True)


class StubGenerationStrategy(GenerationStrategy):
    """Returns canned responses for testing."""

    def __init__(self, responses: dict[str, str] | None = None) -> None:
        self._responses = responses or {}
        self._calls: list[dict[str, str]] = []
        self._cache_calls: list[str] = []
        self._cache_generate_calls: list[dict[str, str]] = []
        self._cache_delete_calls: list[object] = []

    def generate(self, system_prompt: str, model_tier: str) -> str:
        self._calls.append(
            {"system_prompt": system_prompt, "model_tier": model_tier}
        )
        if model_tier in self._responses:
            return self._responses[model_tier]
        return f"[Stub article generated with {model_tier} model]"

    def create_cache(self, system_instruction: str) -> Any:
        self._cache_calls.append(system_instruction)
        return "stub-cache-handle"

    def generate_with_cache(
        self, cached_content: Any, user_prompt: str, model_tier: str
    ) -> str:
        self._cache_generate_calls.append(
            {"user_prompt": user_prompt, "model_tier": model_tier}
        )
        if model_tier in self._responses:
            return self._responses[model_tier]
        return f"[Stub cached article generated with {model_tier} model]"

    def delete_cache(self, cached_content: Any) -> None:
        self._cache_delete_calls.append(cached_content)

    @property
    def calls(self) -> list[dict[str, str]]:
        return self._calls
