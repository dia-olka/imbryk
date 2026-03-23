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

    def read_json(self, key: str) -> dict | list | None:
        """Read a JSON object from storage by key.

        Returns ``None`` if the key does not exist.  Subclasses may override;
        the default implementation raises ``NotImplementedError``.
        """
        raise NotImplementedError

    def write_raw(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        """Write raw bytes to storage at *key*.

        Subclasses may override; the default raises ``NotImplementedError``.
        """
        raise NotImplementedError


class StubEditionStorage(EditionStorage):
    """In-memory storage for testing."""

    def __init__(self) -> None:
        self._editions: list[dict] = []
        self._images: dict[str, bytes] = {}
        self._index: list[dict] | None = None
        self._raw: dict[str, bytes] = {}

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
        return key

    def list_editions(self) -> list[dict]:
        return list(self._editions)

    def write_index(self, editions: list[dict]) -> None:
        self._index = list(editions)

    def read_json(self, key: str) -> dict | list | None:
        import json

        data = self._raw.get(key)
        if data is None:
            return None
        return json.loads(data)

    def write_raw(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        self._raw[key] = data
