"""Application configuration."""

import logging
import os

SENTRY_DSN = os.getenv("SENTRY_DSN", "")

# Logging level
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
_log_level_int = getattr(logging, LOG_LEVEL, logging.WARNING)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./imbryk.db")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

PROMPT_MIN_LENGTH = 10
PROMPT_MAX_LENGTH = 2000

WEIGHT_MULTIPLIER_MIN = 1
WEIGHT_MULTIPLIER_MAX = 100

RATE_LIMIT_QUOTE = os.getenv("RATE_LIMIT_QUOTE", "10/minute")

# Cloudflare Turnstile — set TURNSTILE_SECRET_KEY to enable verification.
# Leave empty to disable (local dev without a widget).
TURNSTILE_SECRET_KEY = os.getenv("TURNSTILE_SECRET_KEY", "")
TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

# Vertex AI — set VERTEX_PROJECT to activate GeminiFlashCategoriser
VERTEX_PROJECT = os.getenv("VERTEX_PROJECT", "")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "global")
CATEGORISER_MODEL = os.getenv("CATEGORISER_MODEL", "gemini-3.1-flash-lite-preview")

# CORS — comma-separated list of allowed origins
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:4200").split(",")
    if origin.strip()
]
