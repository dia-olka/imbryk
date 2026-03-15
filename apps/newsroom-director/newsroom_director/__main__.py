"""Unified entry point — dispatches based on JOB_MODE env var.

JOB_MODE values:
  morning-press  (default) — run the daily newspaper generation pipeline
  news-scout               — run Tavily collection pre-batch job
"""

import os
import sys

# Initialise logging + Sentry early so that the @monitor decorator on
# cli_main (morning-press) sees an initialised SDK when it fires.
from .logging_config import configure_logging

configure_logging()

mode = os.getenv("JOB_MODE", "morning-press").lower().strip()

if mode == "news-scout":
    from .news_scout.main import cli_main
elif mode == "morning-press":
    from .main import cli_main
else:
    print(f"Unknown JOB_MODE={mode!r}. Expected 'morning-press' or 'news-scout'.", file=sys.stderr)
    sys.exit(1)

cli_main()
