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
    """Set up JSON-formatted structured logging.
    
    Args:
        level: Logging level (defaults to LOG_LEVEL_INT from config, or INFO if not specified).
    """
    if level is None:
        from .config import LOG_LEVEL_INT
        level = LOG_LEVEL_INT
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root = logging.getLogger("newsroom_director")
    root.setLevel(level)
    root.addHandler(handler)
    # Keep propagate=True (the default) so Sentry's LoggingIntegration,
    # which attaches to the Python root logger, receives all newsroom_director
    # records. The JSONFormatter handler above still emits structured JSON to
    # stdout; the root logger has no other handlers unless explicitly added
    # (e.g., by Sentry), so there is no duplicate plain-text output.
