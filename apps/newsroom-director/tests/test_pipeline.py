"""Tests for the end-to-end distillation pipeline."""

from unittest.mock import MagicMock

import numpy as np
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

    def test_all_identical_prompts(self, pipeline):
        prompts = [
            Prompt(text="identical prompt text", payment_amount=10.0)
            for _ in range(5)
        ]
        result = pipeline.run(prompts)

        assert len(result) >= 1
        total = sum(bd.digest.cluster_size for bd in result)
        assert total == 5

    def test_zero_payment_prompts(self, pipeline):
        prompts = [
            Prompt(text=f"Free prompt {i}", payment_amount=0.0)
            for i in range(3)
        ]
        result = pipeline.run(prompts)

        assert len(result) >= 1
        total = sum(bd.digest.cluster_size for bd in result)
        assert total == 3

    def test_non_ascii_prompts(self, pipeline):
        # Full pipeline must not raise for non-ASCII input
        prompts = [
            Prompt(text="太阳能电池板效率", payment_amount=10.0),
            Prompt(text="كفاءة الألواح الشمسية", payment_amount=8.0),
            Prompt(text="Solar efficiency 🌞", payment_amount=5.0),
        ]
        result = pipeline.run(prompts)

        assert len(result) >= 1
        total = sum(bd.digest.cluster_size for bd in result)
        assert total == 3

    def test_large_prompt_count_with_mock_embedder(self):
        """1000 prompts with a deterministic mock embedder must complete without error."""

        n = 1000
        # Produce random but reproducible embeddings
        rng = np.random.default_rng(42)
        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = [
            rng.standard_normal(384).astype(np.float32) for _ in range(n)
        ]

        p = DistillationPipeline(embedder=mock_embedder)
        prompts = [
            Prompt(text=f"Prompt about topic {i % 20}", payment_amount=float(i % 50 + 1))
            for i in range(n)
        ]
        result = p.run(prompts)

        assert len(result) >= 1
        total = sum(bd.digest.cluster_size for bd in result)
        assert total == n

    def test_noise_only_clusters_handled(self):
        """When HDBSCAN labels everything as noise, the pipeline must still return results."""

        # Highly dispersed embeddings → HDBSCAN produces only noise
        n = 10
        rng = np.random.default_rng(0)
        embeddings = [rng.standard_normal(384).astype(np.float32) * 1000 for _ in range(n)]

        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = embeddings

        p = DistillationPipeline(embedder=mock_embedder)
        prompts = [Prompt(text=f"Prompt {i}", payment_amount=float(i + 1)) for i in range(n)]
        result = p.run(prompts)

        assert len(result) >= 1
        total = sum(bd.digest.cluster_size for bd in result)
        assert total == n

    def test_negative_payment_prompts_handled(self, pipeline):
        # Negative payments must be clamped, not produce negative weights or errors
        prompts = [
            Prompt(text="First story idea", payment_amount=-10.0),
            Prompt(text="Second story idea", payment_amount=5.0),
            Prompt(text="Third story idea", payment_amount=0.0),
        ]
        result = pipeline.run(prompts)

        assert len(result) >= 1
        total = sum(bd.digest.cluster_size for bd in result)
        assert total == 3
