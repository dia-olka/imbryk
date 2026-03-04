"""Image generation package — Vertex AI Imagen integration."""

from .client import ImageGenerationStrategy, ImagenClient, StubImageClient
from .pipeline import generate_images_for_newspaper

__all__ = [
    "ImageGenerationStrategy",
    "ImagenClient",
    "StubImageClient",
    "generate_images_for_newspaper",
]
