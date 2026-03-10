"""Image generation clients — Vertex AI Imagen and stub for testing."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from google import genai

from .. import config
from ..retry import with_retry

logger = logging.getLogger(__name__)


class ImageGenerationStrategy(ABC):
    """Abstract base for image generation backends."""

    @abstractmethod
    def generate(self, prompt: str) -> bytes | None:
        """Generate an image from a text prompt.

        Returns PNG image bytes on success, or None on failure.
        Image generation failures must never raise — they are non-blocking.
        """


class ImagenClient(ImageGenerationStrategy):
    """Calls Vertex AI Imagen to generate images from text prompts."""

    def __init__(
        self,
        project: str,
        location: str | None = None,
        model: str | None = None,
    ) -> None:
        self._project = project
        self._location = location or config.IMAGE_GENERATION_LOCATION
        self._model = model or config.IMAGE_GENERATION_MODEL
        self._client: genai.Client | None = None

    def _get_client(self) -> genai.Client:
        if self._client is None:
            from google import genai
            from google.genai import types

            self._client = genai.Client(
                vertexai=True,
                project=self._project,
                location=self._location,
                http_options=types.HttpOptions(
                    retry_options=types.HttpRetryOptions(),
                ),
            )
        return self._client

    def generate(self, prompt: str) -> bytes | None:
        """Generate an image using the Google Gen AI SDK.

        Returns PNG image bytes on success, None on any failure.
        """
        try:
            from google.genai import types

            client = self._get_client()

            def _call() -> bytes:
                response = client.models.generate_images(
                    model=self._model,
                    prompt=prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        aspect_ratio="16:9",
                        output_mime_type="image/png",
                        person_generation="ALLOW_ALL",
                    ),
                )
                return response.generated_images[0].image.image_bytes

            return with_retry(_call)
        except Exception:
            logger.warning(
                "Image generation failed for prompt: %.80s",
                prompt,
                exc_info=True,
            )
            return None


class StubImageClient(ImageGenerationStrategy):
    """Returns canned image bytes for testing."""

    # Minimal valid WebP header (RIFF + WEBP + VP8 chunk)
    STUB_WEBP = (
        b"RIFF"
        b"\x24\x00\x00\x00"  # file size
        b"WEBP"
        b"VP8 "
        b"\x18\x00\x00\x00"  # chunk size
        b"\x30\x01\x00\x9d"
        b"\x01\x2a\x01\x00"
        b"\x01\x00\x01\x40"
        b"\x25\xa4\x00\x03"
        b"\x70\x00\xfe\xfb"
        b"\x94\x00\x00"
    )

    def __init__(self, should_fail: bool = False) -> None:
        self._should_fail = should_fail
        self._calls: list[str] = []

    def generate(self, prompt: str) -> bytes | None:
        self._calls.append(prompt)
        if self._should_fail:
            return None
        return self.STUB_WEBP
