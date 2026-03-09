"""Generation strategies for LLM article generation."""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from google import genai

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
    def generate(
        self,
        system_prompt: str,
        model_tier: str,
        user_content: str = "",
        response_schema: type | None = None,
    ) -> str:
        """Generate text from a system prompt using the specified model tier.

        When response_schema is provided, the response is constrained to valid
        JSON matching that schema (Gemini controlled generation).
        """


class VertexAIStrategy(GenerationStrategy):
    """Calls Gemini via the Google Gen AI SDK."""

    def __init__(self, project: str, location: str | None = None) -> None:
        self._project = project
        self._location = location or config.VERTEX_AI_LOCATION
        self._client: genai.Client | None = None

    def _get_client(self) -> genai.Client:
        if self._client is None:
            from google import genai
            from google.genai import types

            self._client = genai.Client(
                vertexai=True,
                project=self._project,
                location=self._location,
                http_options=types.HttpOptions(
                    retry_options=types.HttpRetryOptions(),
                ),
            )
        return self._client

    def generate(
        self,
        system_prompt: str,
        model_tier: str,
        user_content: str = "",
        response_schema: type | None = None,
    ) -> str:
        from google.genai import types

        client = self._get_client()
        model_name = MODEL_MAP.get(model_tier, MODEL_MAP["flash"])
        contents = user_content or "Generate today's edition."

        config_kwargs: dict = {"system_instruction": system_prompt}
        if response_schema is not None:
            config_kwargs["response_mime_type"] = "application/json"
            config_kwargs["response_schema"] = response_schema

        def _call() -> str:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(**config_kwargs),
            )
            return response.text

        return with_retry(_call)


class StubGenerationStrategy(GenerationStrategy):
    """Returns canned responses for testing."""

    def __init__(self, responses: dict[str, str] | None = None) -> None:
        self._responses = responses or {}
        self._calls: list[dict[str, str]] = []

    def generate(
        self,
        system_prompt: str,
        model_tier: str,
        user_content: str = "",
        response_schema: type | None = None,
    ) -> str:
        self._calls.append(
            {"system_prompt": system_prompt, "model_tier": model_tier, "user_content": user_content}
        )
        if model_tier in self._responses:
            return self._responses[model_tier]
        # When a schema is expected, return minimal valid JSON so validation passes.
        if response_schema is not None:
            from .output_schemas import CuratorOutput, NewspaperOutput
            if response_schema is CuratorOutput:
                return json.dumps({"text": (
                    "## CONSENSUS\nStub consensus point one. Stub consensus point two.\n\n"
                    "## FAULT LINES\nStub fault line analysis.\n\n"
                    "## UNCOVERED ANGLES\nStub uncovered angle.\n\n"
                    "## WHAT TO WATCH\nStub watch item."
                )})
            if response_schema is NewspaperOutput:
                return json.dumps({
                    "newspaper_name": f"Stub {model_tier}",
                    "articles": [{"headline": "Stub headline", "body": "Stub body text."}],
                    "in_brief": [],
                })
        return f"[Stub article generated with {model_tier} model]"

    @property
    def calls(self) -> list[dict[str, str]]:
        return self._calls
