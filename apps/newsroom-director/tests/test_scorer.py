"""Tests for the weight scoring module."""

import numpy as np
import pytest

from newsroom_director.distillation.scorer import _compute_uniqueness, compute_weights
from newsroom_director.distillation.types import Prompt


class TestComputeWeights:
    def test_empty_input(self):
        assert compute_weights([], []) == []

    def test_single_prompt(self):
        prompts = [Prompt(text="test", payment_amount=10.0)]
        embeddings = [np.array([1.0, 0.0, 0.0], dtype=np.float32)]

        result = compute_weights(prompts, embeddings)

        assert len(result) == 1
        assert result[0].prompt.text == "test"
        # Single prompt: payment_norm=1.0, uniqueness=1.0 -> weight=1.0
        assert result[0].weight == pytest.approx(1.0)

    def test_payment_normalisation(self):
        prompts = [
            Prompt(text="high", payment_amount=100.0),
            Prompt(text="low", payment_amount=25.0),
        ]
        # Use orthogonal embeddings so uniqueness is 1.0 for both
        embeddings = [
            np.array([1.0, 0.0], dtype=np.float32),
            np.array([0.0, 1.0], dtype=np.float32),
        ]

        result = compute_weights(prompts, embeddings)

        assert result[0].weight == pytest.approx(1.0)  # 100/100 * 1.0
        assert result[1].weight == pytest.approx(0.25)  # 25/100 * 1.0

    def test_zero_payment_gives_equal_weights(self):
        prompts = [
            Prompt(text="a", payment_amount=0.0),
            Prompt(text="b", payment_amount=0.0),
        ]
        embeddings = [
            np.array([1.0, 0.0], dtype=np.float32),
            np.array([0.0, 1.0], dtype=np.float32),
        ]

        result = compute_weights(prompts, embeddings)

        assert result[0].weight == pytest.approx(result[1].weight)

    def test_duplicate_prompts_get_lower_weight(self):
        prompts = [
            Prompt(text="unique idea", payment_amount=10.0),
            Prompt(text="same thing", payment_amount=10.0),
            Prompt(text="same thing again", payment_amount=10.0),
        ]
        # First is unique, second and third are near-duplicates
        embeddings = [
            np.array([1.0, 0.0, 0.0], dtype=np.float32),
            np.array([0.0, 1.0, 0.0], dtype=np.float32),
            np.array([0.0, 0.999, 0.01], dtype=np.float32),  # near-dupe of [1]
        ]

        result = compute_weights(prompts, embeddings)

        # The unique one should have higher weight
        assert result[0].weight > result[1].weight
        assert result[0].weight > result[2].weight

    def test_embeddings_attached_to_result(self):
        prompts = [Prompt(text="test", payment_amount=5.0)]
        embeddings = [np.array([1.0, 2.0, 3.0], dtype=np.float32)]

        result = compute_weights(prompts, embeddings)

        np.testing.assert_array_equal(result[0].embedding, embeddings[0])


class TestComputeUniqueness:
    def test_empty(self):
        result = _compute_uniqueness([])
        assert len(result) == 0

    def test_single(self):
        result = _compute_uniqueness([np.array([1.0, 0.0], dtype=np.float32)])
        assert result[0] == pytest.approx(1.0)

    def test_orthogonal_vectors_all_unique(self):
        embeddings = [
            np.array([1.0, 0.0], dtype=np.float32),
            np.array([0.0, 1.0], dtype=np.float32),
        ]
        result = _compute_uniqueness(embeddings)
        assert result[0] == pytest.approx(1.0)
        assert result[1] == pytest.approx(1.0)

    def test_identical_vectors_penalised(self):
        embeddings = [
            np.array([1.0, 0.0], dtype=np.float32),
            np.array([1.0, 0.0], dtype=np.float32),
            np.array([1.0, 0.0], dtype=np.float32),
        ]
        result = _compute_uniqueness(embeddings)
        # Each has 3 near-duplicates (including self), so uniqueness = 1/3
        assert result[0] == pytest.approx(1.0 / 3.0)

    def test_all_identical_embeddings_equal_uniqueness(self):
        n = 5
        embeddings = [np.array([1.0, 0.0, 0.0], dtype=np.float32)] * n
        result = _compute_uniqueness(embeddings)
        expected = 1.0 / n
        for val in result:
            assert val == pytest.approx(expected)


class TestEdgeCases:
    def test_negative_payment_treated_as_zero(self):
        prompts = [
            Prompt(text="a", payment_amount=-5.0),
            Prompt(text="b", payment_amount=10.0),
        ]
        embeddings = [
            np.array([1.0, 0.0], dtype=np.float32),
            np.array([0.0, 1.0], dtype=np.float32),
        ]
        result = compute_weights(prompts, embeddings)
        # Negative payment is clamped to 0; weight for "b" should be highest
        assert result[1].weight > result[0].weight

    def test_negative_payment_produces_non_negative_weight(self):
        # Negative payment amounts must be clamped to 0, not produce negative weights
        prompts = [
            Prompt(text="a", payment_amount=-100.0),
            Prompt(text="b", payment_amount=10.0),
        ]
        embeddings = [
            np.array([1.0, 0.0], dtype=np.float32),
            np.array([0.0, 1.0], dtype=np.float32),
        ]
        result = compute_weights(prompts, embeddings)

        assert result[0].weight >= 0.0
        assert result[1].weight >= 0.0

    def test_all_negative_payments_equal_weights(self):
        # When all payments are negative, all are clamped to 0 → equal fallback
        prompts = [
            Prompt(text="a", payment_amount=-5.0),
            Prompt(text="b", payment_amount=-10.0),
        ]
        embeddings = [
            np.array([1.0, 0.0], dtype=np.float32),
            np.array([0.0, 1.0], dtype=np.float32),
        ]
        result = compute_weights(prompts, embeddings)

        # Both clamped to 0 → max_payment=0 → equal payment_norms=1 → equal weights
        assert result[0].weight == pytest.approx(result[1].weight)

    def test_single_prompt_zero_payment_weight_is_one(self):
        prompts = [Prompt(text="solo", payment_amount=0.0)]
        embeddings = [np.array([1.0, 0.0], dtype=np.float32)]
        result = compute_weights(prompts, embeddings)
        # zero max_payment → all-ones normalisation, single → uniqueness 1.0
        assert result[0].weight == pytest.approx(1.0)

    def test_mismatched_lengths_raises_value_error(self):
        prompts = [Prompt(text="a", payment_amount=1.0)]
        embeddings = [
            np.array([1.0, 0.0], dtype=np.float32),
            np.array([0.0, 1.0], dtype=np.float32),
        ]
        with pytest.raises(ValueError, match="Length mismatch"):
            compute_weights(prompts, embeddings)
