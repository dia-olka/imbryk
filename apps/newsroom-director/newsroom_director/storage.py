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
    def list_editions(self) -> list[dict]:
        """List stored editions."""


class StubEditionStorage(EditionStorage):
    """In-memory storage for testing."""

    def __init__(self) -> None:
        self._editions: list[dict] = []

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

    def list_editions(self) -> list[dict]:
        return list(self._editions)
