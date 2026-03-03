"""Tests for the prompt embedding module.

These tests use the actual sentence-transformers model (all-MiniLM-L6-v2).
They verify the embedder produces valid embeddings.
"""

import numpy as np
import pytest

from newsroom_director.distillation.embedder import PromptEmbedder
from newsroom_director.distillation.types import Prompt, WeightedPrompt


@pytest.fixture(scope="module")
def embedder():
    """Shared embedder instance to avoid loading the model multiple times."""
    return PromptEmbedder()


class TestPromptEmbedder:
    def test_empty_input(self, embedder):
        assert embedder.embed([]) == []

    def test_single_prompt_returns_vector(self, embedder):
        prompts = [Prompt(text="Solar panel efficiency dropping", payment_amount=5.0)]
        result = embedder.embed(prompts)

        assert len(result) == 1
        assert isinstance(result[0], np.ndarray)
        assert result[0].shape[0] > 0  # Non-empty vector

    def test_multiple_prompts_same_count(self, embedder):
        prompts = [
            Prompt(text="Solar energy", payment_amount=5.0),
            Prompt(text="Nuclear fusion", payment_amount=10.0),
            Prompt(text="Wind turbines", payment_amount=3.0),
        ]
        result = embedder.embed(prompts)

        assert len(result) == 3
        # All embeddings should have the same dimensionality
        dim = result[0].shape[0]
        assert all(e.shape[0] == dim for e in result)

    def test_similar_prompts_have_high_cosine(self, embedder):
        prompts = [
            Prompt(text="Solar panel installation cost", payment_amount=5.0),
            Prompt(text="Cost of installing solar panels", payment_amount=5.0),
            Prompt(text="Medieval castle architecture", payment_amount=5.0),
        ]
        result = embedder.embed(prompts)

        # Cosine similarity between similar prompts should be higher
        sim_01 = _cosine_sim(result[0], result[1])
        sim_02 = _cosine_sim(result[0], result[2])

        assert sim_01 > sim_02

    def test_embed_weighted(self, embedder):
        weighted = [
            WeightedPrompt(
                prompt=Prompt(text="test prompt", payment_amount=5.0),
                weight=1.0,
            ),
        ]
        result = embedder.embed_weighted(weighted)

        assert len(result) == 1
        assert result[0].weight == 1.0
        assert result[0].embedding.shape[0] > 0

    def test_embed_weighted_empty(self, embedder):
        assert embedder.embed_weighted([]) == []

    def test_long_prompt_does_not_error(self, embedder):
        # sentence-transformers truncates to its token limit; verify no error is raised
        # and a valid embedding is returned
        long_text = "renewable energy solar panels " * 100  # ~600 tokens
        prompts = [Prompt(text=long_text, payment_amount=5.0)]
        result = embedder.embed(prompts)

        assert len(result) == 1
        assert result[0].shape[0] > 0

    def test_non_ascii_text_handled(self, embedder):
        # CJK, Arabic, and emoji should not crash the embedder
        prompts = [
            Prompt(text="太阳能电池板效率下降", payment_amount=5.0),      # Chinese
            Prompt(text="كفاءة الألواح الشمسية تنخفض", payment_amount=5.0),  # Arabic
            Prompt(text="Solar panel efficiency 🌞 dropping ⚡", payment_amount=5.0),  # Emoji
        ]
        result = embedder.embed(prompts)

        assert len(result) == 3
        for embedding in result:
            assert embedding.shape[0] > 0

    def test_empty_string_prompt_handled(self, embedder):
        # An empty string is a degenerate but valid input; must not raise
        prompts = [Prompt(text="", payment_amount=5.0)]
        result = embedder.embed(prompts)

        assert len(result) == 1
        assert result[0].shape[0] > 0


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
