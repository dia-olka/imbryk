"""Retry logic for transient Gemini API failures."""

from __future__ import annotations

import logging
import random
import time
from typing import Callable, TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)

# Minimum seconds between successive API calls (prevents bursting).
_MIN_CALL_INTERVAL = 1.5
_last_call_ts: float = 0.0


def _is_retryable(exc: BaseException) -> bool:
    """Check if an exception is a retryable Google API error.

    google-genai raises exceptions with a `code` attribute for HTTP status.
    We retry on 429 (rate limit) and 5xx (server errors).
    """
    code = getattr(exc, "code", None)
    if code is None:
        return False
    return code == 429 or 500 <= code < 600


def _is_rate_limit(exc: BaseException) -> bool:
    """Check if an exception is a rate-limit (429) error."""
    return getattr(exc, "code", None) == 429


def throttle() -> None:
    """Sleep if needed to maintain *_MIN_CALL_INTERVAL* between API calls."""
    global _last_call_ts
    now = time.monotonic()
    elapsed = now - _last_call_ts
    if _last_call_ts and elapsed < _MIN_CALL_INTERVAL:
        time.sleep(_MIN_CALL_INTERVAL - elapsed)
    _last_call_ts = time.monotonic()


def with_retry(
    fn: Callable[..., T],
    *args: object,
    max_retries: int = 3,
    backoff_base: float = 2.0,
    **kwargs: object,
) -> T:
    """Call *fn* with exponential backoff on transient Gemini errors.

    Retries on 429 and 5xx errors.  Non-retryable exceptions propagate
    immediately.  The SDK already performs up to 4 internal retries, so
    the default max_retries is kept low (3).

    Rate-limit errors (429) use a longer initial delay to let quotas reset.
    """
    last_exc: BaseException | None = None
    for attempt in range(max_retries + 1):
        try:
            throttle()
            return fn(*args, **kwargs)
        except Exception as exc:
            if not _is_retryable(exc) or attempt == max_retries:
                raise
            last_exc = exc
            if _is_rate_limit(exc):
                # Longer backoff for 429: 15s, 30s, 60s, 120s, 240s …
                delay = 15 * backoff_base**attempt + random.uniform(0, 3)
            else:
                delay = backoff_base**attempt + random.uniform(0, 1)
            logger.warning(
                "Retrying Gemini call",
                extra={
                    "attempt": attempt + 1,
                    "max_retries": max_retries,
                    "error": str(exc),
                    "delay_s": round(delay, 2),
                },
            )
            time.sleep(delay)
    # Unreachable, but keeps mypy happy
    raise last_exc  # type: ignore[misc]
