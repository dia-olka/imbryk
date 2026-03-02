"""Weight scoring for prompts.

weight = payment_amount_norm x uniqueness_bonus

Payment amount is the primary signal. Uniqueness (inverse of near-duplicate
count) gives rare ideas a bonus over repetitive submissions.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from .types import Prompt, WeightedPrompt

# Cosine similarity threshold for near-duplicate detection
DUPLICATE_THRESHOLD = 0.92


def compute_weights(
    prompts: list[Prompt],
    embeddings: list[NDArray[np.float32]],
) -> list[WeightedPrompt]:
    """Score each prompt: weight = payment_norm * uniqueness_bonus.

    Args:
        prompts: The raw prompts with payment amounts.
        embeddings: Pre-computed embeddings, one per prompt (same order).

    Returns:
        List of WeightedPrompt with computed weights and embeddings attached.
    """
    if not prompts:
        return []

    if len(prompts) != len(embeddings):
        raise ValueError(
            f"Length mismatch: {len(prompts)} prompts vs {len(embeddings)} embeddings"
        )

    # Normalise payment amounts to [0, 1]
    payments = np.array([p.payment_amount for p in prompts], dtype=np.float64)
    max_payment = payments.max()
    if max_payment > 0:
        payment_norms = payments / max_payment
    else:
        payment_norms = np.ones_like(payments)

    # Compute uniqueness bonus
    uniqueness = _compute_uniqueness(embeddings)

    weights = payment_norms * uniqueness

    return [
        WeightedPrompt(
            prompt=prompts[i],
            weight=float(weights[i]),
            embedding=embeddings[i],
        )
        for i in range(len(prompts))
    ]


def _compute_uniqueness(
    embeddings: list[NDArray[np.float32]],
) -> NDArray[np.float64]:
    """Compute uniqueness bonus for each prompt.

    Uniqueness = 1 / (number of near-duplicates). A prompt with no
    near-duplicates gets a bonus of 1.0. A prompt with 4 near-duplicates
    gets 0.2.
    """
    n = len(embeddings)
    if n == 0:
        return np.array([], dtype=np.float64)

    if n == 1:
        return np.array([1.0], dtype=np.float64)

    # Stack embeddings into a matrix and normalise for cosine similarity
    matrix = np.vstack(embeddings).astype(np.float64)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-10)
    normalised = matrix / norms

    # Cosine similarity matrix
    similarity = normalised @ normalised.T

    # Count near-duplicates (excluding self)
    near_dupes = (similarity >= DUPLICATE_THRESHOLD).sum(axis=1)  # includes self
    # near_dupes is at minimum 1 (self), so uniqueness = 1/near_dupes
    uniqueness = 1.0 / near_dupes.astype(np.float64)

    return uniqueness
