"""Tests for the end-to-end distillation pipeline."""

import pytest

from newsroom_director.distillation.embedder import PromptEmbedder
from newsroom_director.distillation.pipeline import DistillationPipeline
from newsroom_director.distillation.types import Prompt


@pytest.fixture(scope="module")
def pipeline():
    """Shared pipeline instance to avoid reloading the model."""
    return DistillationPipeline(embedder=PromptEmbedder())


class TestDistillationPipeline:
    def test_empty_input(self, pipeline):
        result = pipeline.run([])
        assert result == []

    def test_single_prompt(self, pipeline):
        prompts = [
            Prompt(
                text="A solar flare disrupts comms",
                payment_amount=10.0,
            )
        ]
        result = pipeline.run(prompts)

        assert len(result) >= 1
        assert result[0].serialized != ""
        assert result[0].digest.cluster_size == 1

    def test_multiple_prompts(self, pipeline):
        prompts = [
            Prompt(
                text="Central bank raises interest rates",
                payment_amount=20.0,
            ),
            Prompt(
                text="Stock market plunges after rate hike",
                payment_amount=15.0,
            ),
            Prompt(
                text="New deep-sea fish species discovered",
                payment_amount=5.0,
            ),
            Prompt(
                text="Mortgage rates surge after bank decision",
                payment_amount=10.0,
            ),
        ]
        result = pipeline.run(prompts)

        assert len(result) >= 1
        # All prompts should be accounted for
        total = sum(bd.digest.cluster_size for bd in result)
        assert total == 4

    def test_serialize_all(self, pipeline):
        prompts = [
            Prompt(text="Solar panel costs drop 20%", payment_amount=10.0),
            Prompt(text="Wind energy capacity doubles", payment_amount=8.0),
        ]
        result = pipeline.run(prompts)
        text = pipeline.serialize_all(result)

        assert "CLUSTER" in text
        assert len(text) > 50

    def test_high_weight_prompt_appears_verbatim(self, pipeline):
        prompts = [
            Prompt(text="UNIQUE_MARKER_TEXT_12345", payment_amount=100.0),
            Prompt(text="Some other generic prompt", payment_amount=1.0),
        ]
        result = pipeline.run(prompts)
        text = pipeline.serialize_all(result)

        assert "UNIQUE_MARKER_TEXT_12345" in text

    def test_budget_allocated(self, pipeline):
        prompts = [
            Prompt(text=f"Prompt about topic {i}", payment_amount=float(i))
            for i in range(1, 6)
        ]
        result = pipeline.run(prompts)

        for bd in result:
            assert bd.allocated_tokens > 0
