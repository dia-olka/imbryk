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
        contents = user_content

        # Gemini 3.x: temperature must be 1.0 (sub-1.0 causes looping).
        # thinking_level replaces thinking_budget: "high" for pro, "medium" for flash.
        thinking_level = "high" if model_tier == "pro" else "medium"
        config_kwargs: dict = {
            "system_instruction": system_prompt,
            "temperature": 1.0,
            "thinking_config": types.ThinkingConfig(thinking_level=thinking_level),
        }
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
            from .output_schemas import (
                CuratorOutput,
                CuratorOutputV2,
                LedgerMutationOutput,
                NewspaperOutput,
            )
            if response_schema is LedgerMutationOutput:
                return json.dumps({})
            if response_schema is CuratorOutputV2:
                return json.dumps({
                    "version": 2,
                    "consensus": [
                        {"text": "Stub consensus point.", "voices": ["sovereign", "aspirant", "owner"]},
                    ],
                    "fault_lines": [{
                        "topic": "Stub fault line",
                        "label_left": "Position A",
                        "label_right": "Position B",
                        "stances": [
                            {"newspaper_id": "sovereign", "score": 25},
                            {"newspaper_id": "aspirant", "score": 15},
                            {"newspaper_id": "owner", "score": 75},
                            {"newspaper_id": "radical", "score": 5},
                            {"newspaper_id": "moralist", "score": 60},
                            {"newspaper_id": "hedonist", "score": 50},
                        ],
                        "summary": "Stub fault line summary.",
                    }],
                    "gaps": [{"topic": "Stub gap", "description": "Stub gap description."}],
                    "what_to_watch": ["Stub watch item."],
                })
            if response_schema is CuratorOutput:
                return json.dumps({
                    "consensus": [
                        "Stub consensus point one.",
                        "Stub consensus point two.",
                    ],
                    "fault_lines": ["Stub fault line analysis."],
                    "uncovered_angles": ["Stub uncovered angle."],
                    "what_to_watch": ["Stub watch item."],
                })
            if response_schema is NewspaperOutput:
                return json.dumps({
                    "newspaper_name": f"Stub {model_tier}",
                    "frontPageImagePrompt": "A dramatic aerial view of a modern city skyline at golden hour, 4K, HDR, professional photography",
                    "articles": [{"headline": "Stub headline", "body": "Stub body text."}],
                    "in_brief": [],
                })
        return f"[Stub article generated with {model_tier} model]"

    @property
    def calls(self) -> list[dict[str, str]]:
        return self._calls
