"""Tests for the HDBSCAN clustering module."""

import numpy as np
import pytest

from newsroom_director.distillation.clusterer import cluster_prompts
from newsroom_director.distillation.types import Prompt, WeightedPrompt


def _make_wp(text: str, weight: float, embedding: list[float]) -> WeightedPrompt:
    return WeightedPrompt(
        prompt=Prompt(text=text, payment_amount=weight),
        weight=weight,
        embedding=np.array(embedding, dtype=np.float32),
    )


class TestClusterPrompts:
    def test_empty_input(self):
        assert cluster_prompts([]) == []

    def test_fewer_than_min_cluster_size(self):
        prompts = [
            _make_wp("a", 1.0, [1.0, 0.0]),
            _make_wp("b", 2.0, [0.0, 1.0]),
        ]
        clusters = cluster_prompts(prompts, min_cluster_size=5)

        assert len(clusters) == 1
        assert clusters[0].cluster_id == 0
        assert len(clusters[0].prompts) == 2
        assert clusters[0].aggregate_weight == pytest.approx(3.0)

    def test_clusters_are_sorted_by_weight(self):
        # Create two clear groups far apart in embedding space
        prompts = []
        # Group A: high weight, clustered around [10, 0]
        for i in range(10):
            prompts.append(
                _make_wp(f"group_a_{i}", 10.0, [10.0 + i * 0.01, 0.0])
            )
        # Group B: low weight, clustered around [0, 10]
        for i in range(10):
            prompts.append(
                _make_wp(f"group_b_{i}", 1.0, [0.0, 10.0 + i * 0.01])
            )

        clusters = cluster_prompts(prompts, min_cluster_size=5, min_samples=3)

        # Should produce at least one cluster
        assert len(clusters) >= 1

        # First cluster should have highest aggregate weight
        for i in range(len(clusters) - 1):
            assert clusters[i].aggregate_weight >= clusters[i + 1].aggregate_weight

    def test_all_prompts_preserved(self):
        # Even noise points should be preserved
        prompts = [
            _make_wp(f"p{i}", float(i), [float(i), float(i)])
            for i in range(20)
        ]
        clusters = cluster_prompts(prompts, min_cluster_size=5, min_samples=3)

        total_prompts = sum(len(c.prompts) for c in clusters)
        assert total_prompts == 20

    def test_aggregate_weight_is_sum(self):
        prompts = [
            _make_wp("a", 3.0, [1.0, 0.0]),
            _make_wp("b", 7.0, [1.01, 0.0]),
        ]
        clusters = cluster_prompts(prompts, min_cluster_size=5)

        # With fewer than min_cluster_size, all go in one cluster
        assert clusters[0].aggregate_weight == pytest.approx(10.0)
