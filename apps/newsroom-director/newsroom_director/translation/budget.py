"""Translation budget tracker — reads/writes monthly usage to R2."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from ..storage import EditionStorage

logger = logging.getLogger(__name__)

# Default monthly character budgets per provider.
DEFAULT_BUDGETS: dict[str, int] = {
    "azure": 2_000_000,
    "deepl": 500_000,
    "google": 500_000,
    "stub": 999_999_999,
}


class TranslationBudget:
    """Track cumulative character usage per provider per calendar month.

    Usage is stored as a small JSON file in R2 at:
    ``translations/_meta/usage-{provider}-{YYYY-MM}.json``
    """

    def __init__(
        self,
        storage: EditionStorage,
        provider_name: str,
        monthly_limit: int | None = None,
    ) -> None:
        self._storage = storage
        self._provider = provider_name
        self._monthly_limit = monthly_limit or DEFAULT_BUDGETS.get(provider_name, 2_000_000)
        self._month = datetime.now(timezone.utc).strftime("%Y-%m")
        self._chars_used: int | None = None  # lazy loaded

    @property
    def _key(self) -> str:
        return f"translations/_meta/usage-{self._provider}-{self._month}.json"

    def _load(self) -> int:
        """Load current usage from R2. Returns 0 if file doesn't exist."""
        if self._chars_used is not None:
            return self._chars_used
        try:
            data = self._storage.read_json(self._key)
            if data is not None:
                self._chars_used = data.get("chars_used", 0)
            else:
                self._chars_used = 0
        except Exception:
            logger.warning("Failed to read translation budget from R2", exc_info=True)
            self._chars_used = 0
        return self._chars_used

    def remaining(self) -> int:
        """Return characters remaining in this month's budget."""
        used = self._load()
        return max(0, self._monthly_limit - used)

    def would_exceed(self, chars: int) -> bool:
        """Return True if translating *chars* characters would exceed the budget."""
        return chars > self.remaining()

    def record_usage(self, chars: int) -> None:
        """Add *chars* to the running total and persist to R2."""
        used = self._load()
        self._chars_used = used + chars

        payload = json.dumps({
            "provider": self._provider,
            "month": self._month,
            "chars_used": self._chars_used,
            "char_budget": self._monthly_limit,
        }, ensure_ascii=False)

        try:
            self._storage.write_raw(self._key, payload.encode("utf-8"), "application/json")
        except Exception:
            logger.warning(
                "Failed to write translation budget to R2",
                exc_info=True,
            )
