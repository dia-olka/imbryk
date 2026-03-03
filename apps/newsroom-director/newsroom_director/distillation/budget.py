"""Token budget allocation for cluster digests.

Allocates tokens proportionally to cluster importance (aggregate weight)
with a minimum floor and maximum cap per cluster. Handles low-volume and
high-volume edge cases.
"""

from __future__ import annotations

from .digest import serialize_digest
from .types import BudgetedDigest, ClusterDigest

# Budget parameters — see ARCHITECTURE.md
TOTAL_BUDGET_TOKENS = 800_000
MIN_TOKENS_PER_CLUSTER = 500
MAX_TOKENS_PER_CLUSTER = 150_000

# Approximate tokens per character (conservative estimate for English)
CHARS_PER_TOKEN = 4

# Weight threshold for merging low-weight clusters into "Other Topics"
OTHER_TOPICS_CLUSTER_ID = -99


def allocate_budget(
    digests: list[ClusterDigest],
    total_budget: int = TOTAL_BUDGET_TOKENS,
    min_per_cluster: int = MIN_TOKENS_PER_CLUSTER,
    max_per_cluster: int = MAX_TOKENS_PER_CLUSTER,
) -> list[BudgetedDigest]:
    """Allocate token budget proportionally to cluster importance.

    Returns BudgetedDigest list sorted by aggregate_weight descending,
    each with allocated tokens and a serialized text representation
    trimmed to fit the budget.
    """
    if not digests:
        return []

    # Cap the effective floor so that floor * N never exceeds total_budget
    effective_floor = min(min_per_cluster, total_budget // len(digests))

    total_weight = sum(d.aggregate_weight for d in digests)
    if total_weight <= 0:
        # Equal allocation when no weight info
        per_cluster = min(total_budget // len(digests), max_per_cluster)
        return [
            _build_budgeted(d, per_cluster)
            for d in digests
        ]

    # Initial proportional allocation
    allocations: list[tuple[ClusterDigest, int]] = []
    for d in digests:
        proportion = d.aggregate_weight / total_weight
        raw_tokens = int(proportion * total_budget)
        clamped = max(effective_floor, min(raw_tokens, max_per_cluster))
        allocations.append((d, clamped))

    # Redistribute: if total exceeds budget, iteratively scale down.
    # Re-applying the floor after scaling can push total back over budget,
    # so we iterate until convergence.
    for _ in range(10):  # converges quickly in practice
        total_allocated = sum(t for _, t in allocations)
        if total_allocated <= total_budget:
            break
        scale = total_budget / total_allocated
        allocations = [
            (d, max(effective_floor, int(t * scale)))
            for d, t in allocations
        ]

    # Sort by weight descending (already should be, but enforce)
    allocations.sort(key=lambda x: x[0].aggregate_weight, reverse=True)

    return [_build_budgeted(d, tokens) for d, tokens in allocations]


def merge_low_weight_clusters(
    digests: list[ClusterDigest],
    max_clusters: int = 30,
) -> list[ClusterDigest]:
    """Merge lowest-weight clusters into an 'Other Topics' group.

    Used on high-volume days when there are too many clusters to fit
    in the context window effectively.
    """
    if max_clusters < 1:
        raise ValueError(f"max_clusters must be >= 1, got {max_clusters}")

    if len(digests) <= max_clusters:
        return list(digests)

    # Sort by weight descending
    sorted_digests = sorted(
        digests, key=lambda d: d.aggregate_weight, reverse=True
    )

    kept = sorted_digests[: max_clusters - 1]
    merged = sorted_digests[max_clusters - 1 :]

    # Combine merged clusters into one "Other Topics" digest
    all_verbatim: list[tuple[float, str]] = []
    all_keywords: list[str] = []
    total_size = 0
    total_weight = 0.0

    for d in merged:
        all_verbatim.extend(d.verbatim_prompts[:3])  # keep top 3 from each
        all_keywords.extend(d.keywords[:3])
        total_size += d.cluster_size
        total_weight += d.aggregate_weight

    # Deduplicate keywords
    seen: set[str] = set()
    unique_keywords: list[str] = []
    for kw in all_keywords:
        if kw not in seen:
            seen.add(kw)
            unique_keywords.append(kw)

    other = ClusterDigest(
        cluster_id=OTHER_TOPICS_CLUSTER_ID,
        cluster_size=total_size,
        aggregate_weight=total_weight,
        verbatim_prompts=sorted(all_verbatim, key=lambda x: x[0], reverse=True)[
            :20
        ],
        long_tail_summary=f"Merged from {len(merged)} smaller topic clusters.",
        keywords=unique_keywords[:7],
    )

    return kept + [other]


def _build_budgeted(digest: ClusterDigest, allocated_tokens: int) -> BudgetedDigest:
    """Build a BudgetedDigest, trimming serialized output to fit budget."""
    serialized = serialize_digest(digest)
    max_chars = allocated_tokens * CHARS_PER_TOKEN

    if len(serialized) > max_chars:
        # Find the last complete newline before the cut point
        cut = serialized.rfind("\n", 0, max_chars)
        serialized = serialized[:cut] if cut > 0 else serialized[:max_chars]

    return BudgetedDigest(
        digest=digest,
        allocated_tokens=allocated_tokens,
        serialized=serialized,
    )
