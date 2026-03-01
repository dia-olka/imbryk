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
        "DeadlineExceeded",
        "InternalServerError",
    }
)


def _is_retryable(exc: BaseException) -> bool:
    """Check if an exception is a retryable Google API error."""
    return type(exc).__name__ in RETRYABLE_EXCEPTIONS


def with_retry(
    fn: Callable[..., T],
    *args: object,
    max_retries: int = 3,
    backoff_base: float = 2.0,
    **kwargs: object,
) -> T:
    """Call *fn* with exponential backoff on transient Gemini errors.

    Retries on ServiceUnavailable, ResourceExhausted, DeadlineExceeded,
    and InternalServerError.  Non-retryable exceptions propagate immediately.
    """
    last_exc: BaseException | None = None
    for attempt in range(max_retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            if not _is_retryable(exc) or attempt == max_retries:
                raise
            last_exc = exc
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
