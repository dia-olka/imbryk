"""Application configuration via environment variables."""

import logging
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./imbryk.db")
SENTRY_DSN = os.getenv("SENTRY_DSN", "")

# Logging level
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_LEVEL_INT = getattr(logging, LOG_LEVEL, logging.WARNING)

VERTEX_AI_PROJECT = os.getenv("VERTEX_AI_PROJECT", "")
VERTEX_AI_LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")

TOTAL_BUDGET_TOKENS = int(os.getenv("TOTAL_BUDGET_TOKENS", "800000"))
MAX_CLUSTERS = int(os.getenv("MAX_CLUSTERS", "30"))

# Cloudflare R2 storage
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "imbryk-editions")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL", "")

# Cloudflare Pages deploy hook (triggers gazette rebuild after edition publish)
CF_DEPLOY_HOOK_URL = os.getenv("CF_DEPLOY_HOOK_URL", "")
