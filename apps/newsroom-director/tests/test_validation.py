"""Tests for world coherence validation."""

import json

from newsroom_director.db import PromptRecord
from newsroom_director.generation import StubGenerationStrategy
from newsroom_director.validation import (
    BATCH_SIZE,
    _parse_validation_response,
    validate_prompts,
)


def _make_prompt(prompt_id: str, text: str) -> PromptRecord:
    return PromptRecord(
        prompt_id=prompt_id,
        text=text,
        payment_amount=1.0,
        category_ids=["geopolitics"],
    )


class TestParseValidationResponse:
    def test_parses_json(self):
        response = json.dumps({"accepted": ["p-1", "p-3"]})
        result = _parse_validation_response(response, {"p-1", "p-2", "p-3"})
        assert result == {"p-1", "p-3"}

    def test_strips_code_fences(self):
        response = "```json\n" + json.dumps({"accepted": ["p-1"]}) + "\n```"
        result = _parse_validation_response(response, {"p-1", "p-2"})
        assert result == {"p-1"}

    def test_filters_unknown_ids(self):
        response = json.dumps({"accepted": ["p-1", "p-99"]})
        result = _parse_validation_response(response, {"p-1", "p-2"})
        assert result == {"p-1"}

    def test_fallback_on_bad_json(self):
        result = _parse_validation_response(
            "not json at all", {"p-1", "p-2"}
        )
        assert result == {"p-1", "p-2"}

    def test_empty_accepted(self):
        response = json.dumps({"accepted": []})
        result = _parse_validation_response(response, {"p-1"})
        assert result == set()


class TestValidatePrompts:
    def test_empty_prompts(self):
        gen = StubGenerationStrategy()
        result = validate_prompts([], "synopsis", gen)
        assert result == []

    def test_all_accepted_by_stub(self):
        """StubGenerationStrategy returns non-JSON, so fallback accepts all."""
        gen = StubGenerationStrategy()
        prompts = [
            _make_prompt("p-1", "Caspian Basin conflict update"),
            _make_prompt("p-2", "Meridian currency status"),
        ]
        result = validate_prompts(prompts, "synopsis", gen)
        assert len(result) == 2

    def test_filters_rejected_prompts(self):
        """Use a custom stub that returns specific accepted IDs."""
        accepted_json = json.dumps({"accepted": ["p-1"]})
        gen = StubGenerationStrategy(responses={"pro": accepted_json})
        prompts = [
            _make_prompt("p-1", "Caspian Basin conflict"),
            _make_prompt("p-2", "Something incoherent"),
        ]
        result = validate_prompts(prompts, "synopsis", gen)
        assert len(result) == 1
        assert result[0].prompt_id == "p-1"

    def test_batching(self):
        """Prompts beyond BATCH_SIZE are sent in multiple calls."""
        # Create BATCH_SIZE + 5 prompts
        all_ids = [f"p-{i}" for i in range(BATCH_SIZE + 5)]
        prompts = [_make_prompt(pid, f"text {pid}") for pid in all_ids]

        # Accept all
        gen = StubGenerationStrategy()
        result = validate_prompts(prompts, "synopsis", gen)
        assert len(result) == BATCH_SIZE + 5
        # Should have made 2 generation calls (BATCH_SIZE + 5 remaining)
        assert len(gen.calls) == 2

    def test_validation_uses_pro_model(self):
        gen = StubGenerationStrategy()
        prompts = [_make_prompt("p-1", "test prompt")]
        validate_prompts(prompts, "synopsis", gen)
        assert gen.calls[0]["model_tier"] == "pro"
