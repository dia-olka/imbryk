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
    def generate(
        self,
        prompt: str,
        *,
        negative_prompt: str = "",
        aspect_ratio: str = "16:9",
    ) -> bytes | None:
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

    def generate(
        self,
        prompt: str,
        *,
        negative_prompt: str = "",
        aspect_ratio: str = "16:9",
    ) -> bytes | None:
        """Generate an image using the Google Gen AI SDK.

        Returns PNG image bytes on success, None on any failure.
        """
        try:
            from google.genai import types

            client = self._get_client()

            def _call() -> bytes | None:
                img_config_kwargs: dict = {
                    "number_of_images": 1,
                    "aspect_ratio": aspect_ratio,
                    "output_mime_type": "image/png",
                    "person_generation": "ALLOW_ALL",
                }
                if negative_prompt:
                    img_config_kwargs["negative_prompt"] = negative_prompt
                response = client.models.generate_images(
                    model=self._model,
                    prompt=prompt,
                    config=types.GenerateImagesConfig(**img_config_kwargs),
                )
                if not response.generated_images:
                    logger.warning(
                        "Imagen returned 0 images (safety filter / content "
                        "policy?) for prompt: %s | model=%s",
                        prompt,
                        self._model,
                    )
                    return None
                image_bytes = response.generated_images[0].image.image_bytes
                if not image_bytes:
                    logger.warning(
                        "Imagen returned empty image bytes (content policy?) "
                        "for prompt: %s | model=%s",
                        prompt,
                        self._model,
                    )
                    return None
                logger.debug(
                    "Imagen returned %d bytes for prompt: %.80s",
                    len(image_bytes),
                    prompt,
                )
                return image_bytes

            return with_retry(_call)
        except Exception:
            logger.warning(
                "Imagen API error for prompt: %s | model=%s",
                prompt,
                self._model,
                exc_info=True,
            )
            return None


class StubImageClient(ImageGenerationStrategy):
    """Returns canned image bytes for testing."""

    # Minimal 1×1 white PNG (matches the .png extension used by the pipeline)
    STUB_PNG = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    def __init__(self, should_fail: bool = False) -> None:
        self._should_fail = should_fail
        self._calls: list[dict[str, str]] = []

    def generate(
        self,
        prompt: str,
        *,
        negative_prompt: str = "",
        aspect_ratio: str = "16:9",
    ) -> bytes | None:
        self._calls.append(
            {"prompt": prompt, "negative_prompt": negative_prompt, "aspect_ratio": aspect_ratio}
        )
        if self._should_fail:
            return None
        return self.STUB_PNG
