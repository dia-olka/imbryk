"""Structured logging configuration for the Newsroom Director."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Formats log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Include extra structured fields
        for key in (
            "edition_id",
            "newspaper_id",
            "model_tier",
            "latency_ms",
            "token_usage",
            "cluster_count",
            "step",
        ):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        # Include exception info when present (e.g. logger.exception(...) calls)
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


def configure_logging(level: int | None = None) -> None:
    """Set up JSON-formatted structured logging and Sentry integration.

    Initialises Sentry when ``SENTRY_DSN`` is set.  Safe to call from both
    the Morning Press and News Scout entry points — ``sentry_sdk.init`` is
    idempotent so duplicate calls are harmless.

    Args:
        level: Logging level (defaults to LOG_LEVEL_INT from config, or INFO if not specified).
    """
    if level is None:
        from .config import LOG_LEVEL_INT
        level = LOG_LEVEL_INT

    # --- Sentry ----------------------------------------------------------
    from .config import SENTRY_DSN

    if SENTRY_DSN:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            traces_sample_rate=1.0,
            send_default_pii=False,
            integrations=[
                LoggingIntegration(
                    level=level,  # Capture logs at configured level as breadcrumbs
                    event_level=logging.WARNING,  # Send WARNING+ as Sentry events
                ),
            ],
        )
        logging.captureWarnings(True)  # Route warnings.warn() through logging

    # --- Structured JSON logging -----------------------------------------
    root = logging.getLogger("newsroom_director")
    root.setLevel(level)

    # Guard against duplicate handlers when called more than once
    # (e.g. __main__.py + cli_main both call configure_logging).
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        root.addHandler(handler)
    # Keep propagate=True (the default) so Sentry's LoggingIntegration,
    # which attaches to the Python root logger, receives all newsroom_director
    # records. The JSONFormatter handler above still emits structured JSON to
    # stdout; the root logger has no other handlers unless explicitly added
    # (e.g., by Sentry), so there is no duplicate plain-text output.
