"""Image generation package — Vertex AI Imagen integration."""

from .backfill import BackfillResult, run_image_backfill
from .client import ImageGenerationStrategy, ImagenClient, StubImageClient
from .pipeline import generate_images_for_newspaper

__all__ = [
    "BackfillResult",
    "ImageGenerationStrategy",
    "ImagenClient",
    "StubImageClient",
    "generate_images_for_newspaper",
    "run_image_backfill",
]
