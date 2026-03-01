"""HDBSCAN clustering of embedded prompts.

Groups prompts into topically coherent clusters and ranks them by
aggregate weight (sum of member prompt weights).
"""

from __future__ import annotations

import hdbscan
import numpy as np

from .types import Cluster, WeightedPrompt

# HDBSCAN defaults — tunable per PLAN Phase 10
MIN_CLUSTER_SIZE = 5
MIN_SAMPLES = 3


def cluster_prompts(
    weighted_prompts: list[WeightedPrompt],
    min_cluster_size: int = MIN_CLUSTER_SIZE,
    min_samples: int = MIN_SAMPLES,
) -> list[Cluster]:
    """Cluster weighted prompts via HDBSCAN and rank by aggregate weight.

    Noise points (label -1) are collected into a single "unclustered" group
    with cluster_id = -1 so nothing is lost.

    Returns clusters sorted by aggregate_weight descending.
    """
    if not weighted_prompts:
        return []

    # If fewer prompts than min_cluster_size, return them all as one cluster
    if len(weighted_prompts) < min_cluster_size:
        return [
            Cluster(
                cluster_id=0,
                prompts=list(weighted_prompts),
                aggregate_weight=sum(wp.weight for wp in weighted_prompts),
            )
        ]

    embeddings = np.vstack([wp.embedding for wp in weighted_prompts])

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric="euclidean",
    )
    labels = clusterer.fit_predict(embeddings)

    # Group prompts by cluster label
    cluster_map: dict[int, list[WeightedPrompt]] = {}
    for wp, label in zip(weighted_prompts, labels):
        label_int = int(label)
        cluster_map.setdefault(label_int, []).append(wp)

    clusters = [
        Cluster(
            cluster_id=cid,
            prompts=members,
            aggregate_weight=sum(wp.weight for wp in members),
        )
        for cid, members in cluster_map.items()
    ]

    # Sort by aggregate weight descending
    clusters.sort(key=lambda c: c.aggregate_weight, reverse=True)

    return clusters
