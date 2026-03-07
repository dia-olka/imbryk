"""Cluster digest construction.

Transforms each cluster into a rich text digest that preserves the actual
language of high-value prompts while compressing the redundant long tail.

Per-cluster algorithm:
1. Sort prompts by weight descending
2. Select top K prompts verbatim (K = min(20, cluster_size))
3. For remaining prompts, run extractive summarisation (LexRank-inspired)
4. Assemble digest with cluster metadata, verbatim prompts, summary, keywords
"""

from __future__ import annotations

from collections import Counter

import numpy as np
from numpy.typing import NDArray

from ..validation import sanitize_prompt_text
from .types import Cluster, ClusterDigest, WeightedPrompt

# Maximum number of verbatim prompts per cluster
MAX_VERBATIM = 20

# Number of top keywords to extract
TOP_KEYWORDS = 7

# Stop words for keyword extraction (minimal set)
_STOP_WORDS = frozenset([
    "a", "an", "the", "and", "or", "but", "in", "on",
    "at", "to", "for", "of", "is", "it", "its", "this",
    "that", "was", "were", "be", "been", "being", "have",
    "has", "had", "do", "does", "did", "will", "would",
    "shall", "should", "may", "might", "can", "could",
    "with", "from", "by", "as", "are", "am", "i", "we",
    "they", "them", "their", "he", "she", "his", "her",
    "you", "your", "my", "our",
])


def build_digest(cluster: Cluster) -> ClusterDigest:
    """Build a compressed digest from a cluster of weighted prompts."""
    sorted_prompts = sorted(cluster.prompts, key=lambda wp: wp.weight, reverse=True)

    k = min(MAX_VERBATIM, len(sorted_prompts))
    verbatim = [(wp.weight, sanitize_prompt_text(wp.prompt.text)) for wp in sorted_prompts[:k]]

    # Long-tail summary for remaining prompts
    remaining = sorted_prompts[k:]
    long_tail_summary = _extractive_summary(remaining) if remaining else ""

    # Extract keywords from all prompts
    all_texts = [wp.prompt.text for wp in sorted_prompts]
    keywords = _extract_keywords(all_texts)

    return ClusterDigest(
        cluster_id=cluster.cluster_id,
        cluster_size=len(cluster.prompts),
        aggregate_weight=cluster.aggregate_weight,
        verbatim_prompts=verbatim,
        long_tail_summary=long_tail_summary,
        keywords=keywords,
    )


def build_digests(clusters: list[Cluster]) -> list[ClusterDigest]:
    """Build digests for all clusters."""
    return [build_digest(c) for c in clusters]


def serialize_digest(digest: ClusterDigest) -> str:
    """Serialize a digest into a text block for the LLM prompt."""
    lines = [
        f"CLUSTER #{digest.cluster_id} | "
        f"aggregate_weight: {digest.aggregate_weight:,.0f} | "
        f"prompt_count: {digest.cluster_size:,}",
    ]

    if digest.verbatim_prompts:
        lines.append("High-value verbatim prompts:")
        for weight, text in digest.verbatim_prompts:
            lines.append(f'  [w:{weight:,.0f}] "{text}"')

    if digest.long_tail_summary:
        tail_count = digest.cluster_size - len(digest.verbatim_prompts)
        lines.append(f"Long-tail summary ({tail_count:,} prompts):")
        lines.append(f"  {digest.long_tail_summary}")

    if digest.keywords:
        lines.append(f"Keywords: {', '.join(digest.keywords)}")

    return "\n".join(lines)


def _extractive_summary(
    prompts: list[WeightedPrompt], max_sentences: int = 5
) -> str:
    """LexRank-inspired extractive summarisation.

    Selects the most representative sentences from the remaining prompts
    using a simplified centrality-based approach.
    """
    if not prompts:
        return ""

    texts = [wp.prompt.text for wp in prompts]

    if len(texts) <= max_sentences:
        return " ".join(texts)

    # Use embeddings if available, otherwise fall back to text selection
    embeddings = [wp.embedding for wp in prompts]
    has_embeddings = all(e.size > 0 for e in embeddings)

    if has_embeddings:
        return _lexrank_select(texts, embeddings, max_sentences)

    # Fallback: pick evenly spaced prompts
    step = max(1, len(texts) // max_sentences)
    selected = texts[::step][:max_sentences]
    return " ".join(selected)


def _lexrank_select(
    texts: list[str],
    embeddings: list[NDArray[np.float32]],
    max_sentences: int,
) -> str:
    """Select most central sentences via cosine-similarity centrality."""
    matrix = np.vstack(embeddings).astype(np.float64)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-10)
    normalised = matrix / norms

    similarity = normalised @ normalised.T
    # Centrality = average similarity to all other sentences
    centrality = similarity.mean(axis=1)

    top_indices = centrality.argsort()[-max_sentences:][::-1]
    # Maintain original order
    top_indices = sorted(top_indices)

    return " ".join(texts[i] for i in top_indices)


def _extract_keywords(texts: list[str]) -> list[str]:
    """Extract top keywords by frequency, excluding stop words."""
    word_counts: Counter[str] = Counter()
    for text in texts:
        words = text.lower().split()
        for word in words:
            cleaned = word.strip(".,!?;:\"'()-[]{}").lower()
            if cleaned and cleaned not in _STOP_WORDS and len(cleaned) > 2:
                word_counts[cleaned] += 1

    return [word for word, _ in word_counts.most_common(TOP_KEYWORDS)]
