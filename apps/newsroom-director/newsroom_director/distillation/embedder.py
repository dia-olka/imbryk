"""Prompt embedding using local sentence-transformers."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from sentence_transformers import SentenceTransformer

from .types import Prompt, WeightedPrompt

DEFAULT_MODEL = "all-MiniLM-L6-v2"


class PromptEmbedder:
    """Embeds prompts using a local sentence-transformer model."""

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        self._model = SentenceTransformer(model_name)

    def embed(self, prompts: list[Prompt]) -> list[NDArray[np.float32]]:
        """Embed a list of prompts and return their vector representations.

        Returns one embedding per prompt, in the same order.
        """
        if not prompts:
            return []

        texts = [p.text for p in prompts]
        embeddings: NDArray[np.float32] = self._model.encode(
            texts, show_progress_bar=False, convert_to_numpy=True
        )
        return [embeddings[i] for i in range(len(prompts))]

    def embed_weighted(
        self, weighted_prompts: list[WeightedPrompt]
    ) -> list[WeightedPrompt]:
        """Attach embeddings to already-weighted prompts. Returns new list."""
        if not weighted_prompts:
            return []

        texts = [wp.prompt.text for wp in weighted_prompts]
        embeddings: NDArray[np.float32] = self._model.encode(
            texts, show_progress_bar=False, convert_to_numpy=True
        )
        return [
            WeightedPrompt(
                prompt=wp.prompt,
                weight=wp.weight,
                embedding=embeddings[i],
            )
            for i, wp in enumerate(weighted_prompts)
        ]
