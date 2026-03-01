"""Tests for the token budget allocation module."""

import pytest

from newsroom_director.distillation.budget import (
    OTHER_TOPICS_CLUSTER_ID,
    allocate_budget,
    merge_low_weight_clusters,
)
from newsroom_director.distillation.types import ClusterDigest


def _make_digest(
    cluster_id: int, weight: float, size: int = 10
) -> ClusterDigest:
    return ClusterDigest(
        cluster_id=cluster_id,
        cluster_size=size,
        aggregate_weight=weight,
        verbatim_prompts=[(weight, f"prompt for cluster {cluster_id}")],
        long_tail_summary="",
        keywords=["test"],
    )


class TestAllocateBudget:
    def test_empty_input(self):
        assert allocate_budget([]) == []

    def test_single_cluster_gets_full_budget(self):
        digests = [_make_digest(0, 100.0)]
        result = allocate_budget(digests, total_budget=10000)

        assert len(result) == 1
        assert result[0].allocated_tokens <= 10000

    def test_proportional_allocation(self):
        digests = [
            _make_digest(0, 300.0),  # 75%
            _make_digest(1, 100.0),  # 25%
        ]
        result = allocate_budget(
            digests,
            total_budget=10000,
            min_per_cluster=100,
            max_per_cluster=9000,
        )

        assert len(result) == 2
        # Higher weight cluster gets more tokens
        assert result[0].allocated_tokens > result[1].allocated_tokens

    def test_minimum_floor_respected(self):
        digests = [
            _make_digest(0, 999.0),
            _make_digest(1, 1.0),  # very small weight
        ]
        result = allocate_budget(
            digests, total_budget=10000, min_per_cluster=500
        )

        for bd in result:
            assert bd.allocated_tokens >= 500

    def test_maximum_cap_respected(self):
        digests = [_make_digest(0, 1000.0)]
        result = allocate_budget(
            digests,
            total_budget=1_000_000,
            max_per_cluster=150_000,
        )

        assert result[0].allocated_tokens <= 150_000

    def test_sorted_by_weight_descending(self):
        digests = [
            _make_digest(0, 10.0),
            _make_digest(1, 100.0),
            _make_digest(2, 50.0),
        ]
        result = allocate_budget(digests, total_budget=10000)

        weights = [bd.digest.aggregate_weight for bd in result]
        assert weights == sorted(weights, reverse=True)

    def test_serialized_output_not_empty(self):
        digests = [_make_digest(0, 100.0)]
        result = allocate_budget(digests, total_budget=10000)

        assert len(result[0].serialized) > 0

    def test_zero_weight_equal_allocation(self):
        digests = [
            _make_digest(0, 0.0),
            _make_digest(1, 0.0),
        ]
        result = allocate_budget(digests, total_budget=10000)

        assert result[0].allocated_tokens == result[1].allocated_tokens


class TestMergeLowWeightClusters:
    def test_no_merge_when_under_limit(self):
        digests = [_make_digest(i, float(i)) for i in range(5)]
        result = merge_low_weight_clusters(digests, max_clusters=10)

        assert len(result) == 5

    def test_merges_when_over_limit(self):
        digests = [_make_digest(i, float(10 - i)) for i in range(10)]
        result = merge_low_weight_clusters(digests, max_clusters=5)

        assert len(result) == 5
        # Last cluster should be the merged "Other Topics"
        other = [d for d in result if d.cluster_id == OTHER_TOPICS_CLUSTER_ID]
        assert len(other) == 1

    def test_merged_cluster_has_combined_weight(self):
        digests = [_make_digest(i, 10.0) for i in range(6)]
        result = merge_low_weight_clusters(digests, max_clusters=3)

        other = next(
            d for d in result if d.cluster_id == OTHER_TOPICS_CLUSTER_ID
        )
        # 4 clusters merged, each with weight 10 = 40
        assert other.aggregate_weight == pytest.approx(40.0)
        assert other.cluster_size == 40  # 4 * 10

    def test_merged_cluster_preserves_top_verbatim(self):
        digests = [_make_digest(i, float(i)) for i in range(8)]
        result = merge_low_weight_clusters(digests, max_clusters=3)

        other = next(
            d for d in result if d.cluster_id == OTHER_TOPICS_CLUSTER_ID
        )
        assert len(other.verbatim_prompts) > 0
