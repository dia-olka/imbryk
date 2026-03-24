"""Translation strategy ABC and stub client for testing."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TranslationResult:
    """Result of translating one text segment."""

    source_text: str
    translated_text: str
    target_lang: str
    chars_used: int


class TranslationStrategy(ABC):
    """Abstract base for text translation backends."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider identifier (e.g. 'azure', 'deepl', 'google')."""

    @abstractmethod
    def translate_batch(
        self,
        texts: list[str],
        target_lang: str,
        source_lang: str = "en",
    ) -> list[TranslationResult | None]:
        """Translate multiple texts to *target_lang*.

        Returns one result per input text, in order.
        Failed translations return ``None`` (never raise).
        """

    @property
    @abstractmethod
    def max_batch_size(self) -> int:
        """Maximum number of texts per single API call."""

    @property
    @abstractmethod
    def max_chars_per_request(self) -> int:
        """Maximum total characters per single API call."""


class StubTranslationClient(TranslationStrategy):
    """Returns canned translations for testing."""

    def __init__(self, should_fail: bool = False) -> None:
        self._should_fail = should_fail
        self._calls: list[dict] = []

    @property
    def provider_name(self) -> str:
        return "stub"

    @property
    def max_batch_size(self) -> int:
        return 25

    @property
    def max_chars_per_request(self) -> int:
        return 50_000

    @property
    def calls(self) -> list[dict]:
        return self._calls

    def translate_batch(
        self,
        texts: list[str],
        target_lang: str,
        source_lang: str = "en",
    ) -> list[TranslationResult | None]:
        self._calls.append({
            "texts": texts,
            "target_lang": target_lang,
            "source_lang": source_lang,
        })
        if self._should_fail:
            return [None] * len(texts)
        return [
            TranslationResult(
                source_text=text,
                translated_text=f"[{target_lang}] {text}",
                target_lang=target_lang,
                chars_used=len(text),
            )
            for text in texts
        ]
