"""Shared types for the distillation pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray


@dataclass
class Prompt:
    """A user-submitted prompt with payment metadata."""

    text: str
    payment_amount: float
    prompt_id: str = ""


@dataclass
class WeightedPrompt:
    """A prompt enriched with its computed weight and embedding."""

    prompt: Prompt
    weight: float
    embedding: NDArray[np.float32] = field(
        default_factory=lambda: np.array([], dtype=np.float32)
    )


@dataclass
class Cluster:
    """A group of topically related weighted prompts."""

    cluster_id: int
    prompts: list[WeightedPrompt]
    aggregate_weight: float


@dataclass
class ClusterDigest:
    """A compressed representation of a cluster for the LLM."""

    cluster_id: int
    cluster_size: int
    aggregate_weight: float
    verbatim_prompts: list[tuple[float, str]]  # (weight, text)
    long_tail_summary: str
    keywords: list[str]


@dataclass
class BudgetedDigest:
    """A cluster digest with an allocated token budget."""

    digest: ClusterDigest
    allocated_tokens: int
    serialized: str
