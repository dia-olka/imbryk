"""Tavily search client wrapper for News Scout.

Executes search queries with per-minute and per-month rate limiting.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# Persistent file tracking monthly usage across runs.
# Stored next to the SQLite DB in local dev; in prod the value resets
# with each container but the monthly limit is mainly a cost safety net.
_MONTHLY_COUNTER_FILE = Path("/tmp/tavily_monthly_count.txt")


@dataclass
class SearchResult:
    """A single search result from Tavily."""

    title: str
    snippet: str
    url: str
    score: float


class SearchStrategy(ABC):
    """Abstract search backend for testability."""

    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """Execute a search query and return results."""


@dataclass
class _RateLimiter:
    """Simple token-bucket rate limiter for Tavily API calls.

    Enforces:
    - Per-minute limit (RPM): sleeps when the limit would be exceeded.
    - Per-month limit: raises RateLimitExceeded when the budget is exhausted.
    """

    rpm: int = 99
    monthly_limit: int = 999
    _timestamps: list[float] = field(default_factory=list)
    _monthly_count: int = 0

    def __post_init__(self) -> None:
        self._monthly_count = self._load_monthly_count()

    def acquire(self) -> None:
        """Block until a request slot is available, or raise if monthly budget exhausted."""
        if self._monthly_count >= self.monthly_limit:
            raise RateLimitExceeded(
                f"Tavily monthly limit reached ({self.monthly_limit})"
            )

        now = time.monotonic()
        # Prune timestamps older than 60 seconds
        cutoff = now - 60.0
        self._timestamps = [t for t in self._timestamps if t > cutoff]

        if len(self._timestamps) >= self.rpm:
            # Sleep until the oldest timestamp in the window expires
            sleep_for = self._timestamps[0] - cutoff
            if sleep_for > 0:
                logger.debug("Rate limit: sleeping %.1fs", sleep_for)
                time.sleep(sleep_for)

        self._timestamps.append(time.monotonic())
        self._monthly_count += 1
        self._save_monthly_count()

    @property
    def monthly_remaining(self) -> int:
        return max(0, self.monthly_limit - self._monthly_count)

    @staticmethod
    def _load_monthly_count() -> int:
        """Load the monthly counter from the persistent file."""
        try:
            from datetime import datetime, timezone

            if not _MONTHLY_COUNTER_FILE.exists():
                return 0
            text = _MONTHLY_COUNTER_FILE.read_text().strip()
            if not text:
                return 0
            parts = text.split(":")
            if len(parts) != 2:
                return 0
            saved_month, count_str = parts
            current_month = datetime.now(timezone.utc).strftime("%Y-%m")
            if saved_month != current_month:
                return 0  # New month, reset counter
            return int(count_str)
        except Exception:
            return 0

    def _save_monthly_count(self) -> None:
        """Persist the monthly counter to file."""
        try:
            from datetime import datetime, timezone

            current_month = datetime.now(timezone.utc).strftime("%Y-%m")
            _MONTHLY_COUNTER_FILE.write_text(
                f"{current_month}:{self._monthly_count}"
            )
        except Exception:
            pass  # Best-effort; don't block searches on counter persistence


class RateLimitExceeded(Exception):
    """Raised when the Tavily monthly request budget is exhausted."""


class TavilySearcher(SearchStrategy):
    """Tavily Search API client with rate limiting."""

    def __init__(
        self,
        api_key: str,
        rpm: int = 99,
        monthly_limit: int = 999,
    ) -> None:
        self._api_key = api_key
        self._client = None
        self._limiter = _RateLimiter(rpm=rpm, monthly_limit=monthly_limit)

    def _get_client(self):
        if self._client is None:
            from tavily import TavilyClient

            self._client = TavilyClient(api_key=self._api_key)
        return self._client

    @property
    def monthly_remaining(self) -> int:
        return self._limiter.monthly_remaining

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        self._limiter.acquire()

        client = self._get_client()
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="basic",
            include_answer=False,
        )
        results: list[SearchResult] = []
        for item in response.get("results", []):
            title = (item.get("title") or "").strip()
            content = (item.get("content") or "").strip()
            url = (item.get("url") or "").strip()
            score = float(item.get("score", 0.0))
            if title and content and url:
                results.append(
                    SearchResult(
                        title=title,
                        snippet=content,
                        url=url,
                        score=score,
                    )
                )
        return results


class StubSearcher(SearchStrategy):
    """Returns canned results for testing."""

    def __init__(self, results: list[SearchResult] | None = None) -> None:
        self._results = results or []
        self._calls: list[str] = []

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        self._calls.append(query)
        return self._results[:max_results]

    @property
    def calls(self) -> list[str]:
        return self._calls
