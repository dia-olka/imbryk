"""Application configuration via environment variables."""

import logging
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./imbryk.db")
SENTRY_DSN = os.getenv("SENTRY_DSN", "")

# Logging level
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_LEVEL_INT = getattr(logging, LOG_LEVEL, logging.WARNING)

VERTEX_AI_PROJECT = os.getenv("VERTEX_AI_PROJECT", "")
VERTEX_AI_LOCATION = os.getenv("VERTEX_AI_LOCATION", "global")

# Generative model names — override per environment without code changes
GENERATION_MODEL_PRO = os.getenv("GENERATION_MODEL_PRO", "gemini-3.1-pro-preview")
GENERATION_MODEL_FLASH = os.getenv("GENERATION_MODEL_FLASH", "gemini-3-flash-preview")
IMAGE_GENERATION_MODEL = os.getenv("IMAGE_GENERATION_MODEL", "imagen-4.0-generate-001")
IMAGE_GENERATION_LOCATION = os.getenv("IMAGE_GENERATION_LOCATION", "us-central1")

TOTAL_BUDGET_TOKENS = int(os.getenv("TOTAL_BUDGET_TOKENS", "800000"))
MAX_CLUSTERS = int(os.getenv("MAX_CLUSTERS", "30"))

# Image backfill — max images to generate per pipeline run when catching up
# on previous editions with failed image generation.
MAX_BACKFILL_IMAGES_PER_RUN = int(os.getenv("MAX_BACKFILL_IMAGES_PER_RUN", "20"))

# Override the edition date (default: today UTC). Used for one-off regeneration.
EDITION_DATE = os.getenv("EDITION_DATE", "")

# Cloudflare R2 storage
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "imbryk-editions")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL", "")

# Cloudflare Pages deploy hook (triggers gazette rebuild after edition publish)
CF_DEPLOY_HOOK_URL = os.getenv("CF_DEPLOY_HOOK_URL", "")

# News Scout — real-world gap filling
NEWS_SCOUT_ENABLED = os.getenv("NEWS_SCOUT_ENABLED", "true").lower() == "true"
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
TAVILY_RPM = int(os.getenv("TAVILY_RPM", "99"))  # max requests per minute
TAVILY_MONTHLY_LIMIT = int(os.getenv("TAVILY_MONTHLY_LIMIT", "999"))  # max requests per calendar month
TAVILY_MAX_RESULTS_PER_QUERY = int(os.getenv("TAVILY_MAX_RESULTS_PER_QUERY", "5"))  # Tavily max is 20
NEWS_ITEM_BASE_WEIGHT = float(os.getenv("NEWS_ITEM_BASE_WEIGHT", "0.3"))
NEWS_MUTATES_LEDGER = os.getenv("NEWS_MUTATES_LEDGER", "true").lower() == "true"

# Editorial Journal — persistent per-persona editorial memory
ENABLE_EDITORIAL_JOURNAL = os.getenv("ENABLE_EDITORIAL_JOURNAL", "true").lower() == "true"
JOURNAL_LOOKBACK_DAYS = int(os.getenv("JOURNAL_LOOKBACK_DAYS", "7"))
