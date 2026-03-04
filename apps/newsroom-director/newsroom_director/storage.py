"""Edition storage backends."""

from __future__ import annotations

from abc import ABC, abstractmethod


class EditionStorage(ABC):
    """Abstract base for edition output storage."""

    @abstractmethod
    def write_edition(
        self, edition_id: str, date: str, articles: dict[str, str]
    ) -> None:
        """Write a complete edition to storage."""

    @abstractmethod
    def write_image(
        self,
        edition_id: str,
        newspaper_id: str,
        filename: str,
        image_bytes: bytes,
    ) -> str:
        """Write an image to storage and return its public URL."""

    @abstractmethod
    def list_editions(self) -> list[dict]:
        """List stored editions."""

    @abstractmethod
    def write_index(self, editions: list[dict]) -> None:
        """Write an index manifest listing all editions."""


class StubEditionStorage(EditionStorage):
    """In-memory storage for testing."""

    def __init__(self) -> None:
        self._editions: list[dict] = []
        self._images: dict[str, bytes] = {}
        self._index: list[dict] | None = None

    def write_edition(
        self, edition_id: str, date: str, articles: dict[str, str]
    ) -> None:
        self._editions.append(
            {
                "edition_id": edition_id,
                "date": date,
                "articles": dict(articles),
            }
        )

    def write_image(
        self,
        edition_id: str,
        newspaper_id: str,
        filename: str,
        image_bytes: bytes,
    ) -> str:
        key = f"editions/{edition_id}/{newspaper_id}/{filename}"
        self._images[key] = image_bytes
        return f"https://stub-r2.example.com/{key}"

    def list_editions(self) -> list[dict]:
        return list(self._editions)

    def write_index(self, editions: list[dict]) -> None:
        self._index = list(editions)
