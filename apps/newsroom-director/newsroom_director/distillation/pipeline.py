"""End-to-end distillation pipeline orchestrator.

Takes a newspaper's raw prompt pool and produces budgeted cluster digests
ready to be injected into the Gemini system prompt.

Pipeline stages:
1. Embed prompts (local sentence-transformers)
2. Score weights (payment_norm * uniqueness_bonus)
3. Cluster via HDBSCAN
4. Build weighted cluster digests
5. Allocate token budget
"""

from __future__ import annotations

from .budget import allocate_budget, merge_low_weight_clusters
from .clusterer import cluster_prompts
from .digest import build_digests
from .embedder import PromptEmbedder
from .scorer import compute_weights
from .types import BudgetedDigest, Prompt


class DistillationPipeline:
    """Orchestrates the four-stage prompt distillation pipeline."""

    def __init__(
        self,
        embedder: PromptEmbedder | None = None,
        max_clusters: int = 30,
        total_budget_tokens: int = 800_000,
    ) -> None:
        self._embedder = embedder
        self._max_clusters = max_clusters
        self._total_budget = total_budget_tokens

    @property
    def embedder(self) -> PromptEmbedder:
        if self._embedder is None:
            self._embedder = PromptEmbedder()
        return self._embedder

    def run(self, prompts: list[Prompt]) -> list[BudgetedDigest]:
        """Execute the full distillation pipeline.

        Args:
            prompts: Raw prompts with payment metadata for one newspaper.

        Returns:
            Budgeted cluster digests, sorted by aggregate weight descending,
            ready for injection into the Gemini system prompt.
        """
        if not prompts:
            return []

        # Stage 1: Embed
        embeddings = self.embedder.embed(prompts)

        # Stage 2: Score
        weighted = compute_weights(prompts, embeddings)

        # Stage 3: Cluster
        clusters = cluster_prompts(weighted)

        # Stage 4a: Build digests
        digests = build_digests(clusters)

        # Stage 4b: Merge low-weight clusters if too many
        digests = merge_low_weight_clusters(digests, self._max_clusters)

        # Stage 5: Allocate token budget
        budgeted = allocate_budget(digests, self._total_budget)

        return budgeted

    def serialize_all(self, budgeted_digests: list[BudgetedDigest]) -> str:
        """Serialize all budgeted digests into a single text block.

        This is the final output injected into {{CLUSTER_DIGESTS}}.
        """
        return "\n\n".join(bd.serialized for bd in budgeted_digests)
