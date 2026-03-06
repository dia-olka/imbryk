"""Retry logic for transient Gemini API failures."""

from __future__ import annotations

import logging
import random
import time
from typing import Callable, TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)

# Exception class names that are retryable (checked by name to avoid
# hard-importing google.api_core at module level).
RETRYABLE_EXCEPTIONS = frozenset(
    {
        "ServiceUnavailable",
        "ResourceExhausted",
        "TooManyRequests",
        "DeadlineExceeded",
        "InternalServerError",
    }
)

# Subset that should use a longer backoff because the API is rate-limiting.
_RATE_LIMIT_EXCEPTIONS = frozenset({"ResourceExhausted", "TooManyRequests"})

# HTTP 429 status code — google.genai raises ClientError for all 4xx responses,
# so we also inspect the status_code attribute to catch rate-limit errors that
# don't match by class name alone (e.g. when google-genai's internal tenacity
# exhausts its retries and re-raises as ClientError).
_RATE_LIMIT_HTTP_STATUS = 429

# Minimum seconds between successive API calls (prevents bursting).
_MIN_CALL_INTERVAL = 1.5
_last_call_ts: float = 0.0


def _is_retryable(exc: BaseException) -> bool:
    """Check if an exception is a retryable Google API error."""
    if type(exc).__name__ in RETRYABLE_EXCEPTIONS:
        return True
    # google.genai wraps all 4xx/5xx as ClientError/ServerError.  A 429
    # response is a transient rate-limit and should be retried.
    status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    return status == _RATE_LIMIT_HTTP_STATUS


def _is_rate_limit(exc: BaseException) -> bool:
    """Check if an exception is a rate-limit (429) error."""
    if type(exc).__name__ in _RATE_LIMIT_EXCEPTIONS:
        return True
    status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    return status == _RATE_LIMIT_HTTP_STATUS


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
    max_retries: int = 5,
    backoff_base: float = 2.0,
    **kwargs: object,
) -> T:
    """Call *fn* with exponential backoff on transient Gemini errors.

    Retries on ServiceUnavailable, ResourceExhausted, TooManyRequests,
    DeadlineExceeded, and InternalServerError.  Non-retryable exceptions
    propagate immediately.

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
