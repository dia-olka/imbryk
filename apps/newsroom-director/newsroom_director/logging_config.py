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

        return json.dumps(log_entry, ensure_ascii=False)


def configure_logging(level: int = logging.INFO) -> None:
    """Set up JSON-formatted structured logging."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root = logging.getLogger("newsroom_director")
    root.setLevel(level)
    root.addHandler(handler)
    root.propagate = False
