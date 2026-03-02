"""HDBSCAN clustering of embedded prompts.

Groups prompts into topically coherent clusters and ranks them by
aggregate weight (sum of member prompt weights).

HDBSCAN parameter guidance by data volume
==========================================
+--------------+------------------+--------------+---------------------------+
| Prompt count | min_cluster_size | min_samples  | Notes                     |
+--------------+------------------+--------------+---------------------------+
| 10 – 50      | 3                | 2            | Small pool — keep clusters |
|              |                  |              | tiny; most points may be   |
|              |                  |              | noise-labelled.            |
| 50 – 200     | 5 (default)      | 3 (default)  | Balanced; good starting    |
|              |                  |              | point for daily volumes.   |
| 200 – 1 000  | 10               | 5            | Larger clusters, fewer     |
|              |                  |              | noise points.              |
| 1 000+       | 15 – 25          | 7 – 10       | High volume; raise both to |
|              |                  |              | avoid micro-clusters.      |
+--------------+------------------+--------------+---------------------------+

General rules:
- min_cluster_size sets the smallest group HDBSCAN will form. Lower values
  produce more (smaller) clusters; higher values merge small topics together.
- min_samples controls density: higher values mean a point needs more
  neighbours to be considered core, producing tighter clusters and more noise.
- When all embeddings are nearly identical (low variance), HDBSCAN may label
  everything as noise (-1). The pipeline handles this by collecting noise
  points into a single "unclustered" group.
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
