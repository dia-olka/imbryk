"""Application configuration."""

import logging
import os

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

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
# Per-IP rate limit on /prompts/quote
RATE_LIMIT_GLOBAL_QUOTE = os.getenv("RATE_LIMIT_GLOBAL_QUOTE", "100/minute")
# Global ceiling across all IPs — caps LLM spend even with rotating proxies.
# NOTE: With multiple Gunicorn workers the effective ceiling becomes
# RATE_LIMIT_GLOBAL_QUOTE * num_workers unless a shared backend is used.
# Set REDIS_URL to a Redis instance to enforce a true global limit.
RATE_LIMIT_EDITIONS = os.getenv("RATE_LIMIT_EDITIONS", "30/minute")

QUOTE_EXPIRY_HOURS = int(os.getenv("QUOTE_EXPIRY_HOURS", "24"))
MAX_CHECKOUT_SESSIONS_PER_QUOTE = int(os.getenv("MAX_CHECKOUT_SESSIONS_PER_QUOTE", "3"))

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

# Redis URL for shared rate-limit storage across multiple workers.
# When unset, slowapi uses in-memory storage (per-process).
REDIS_URL = os.getenv("REDIS_URL", "")


def validate_production_config() -> None:
    """Raise RuntimeError if required env vars are missing in production.

    Called at startup so the process refuses to start with a misconfigured
    environment rather than silently degrading.
    """
    if ENVIRONMENT != "production":
        return

    errors: list[str] = []

    if not STRIPE_SECRET_KEY:
        errors.append("STRIPE_SECRET_KEY is required in production")
    if not STRIPE_WEBHOOK_SECRET:
        errors.append("STRIPE_WEBHOOK_SECRET is required in production")
    if not VERTEX_PROJECT:
        errors.append("VERTEX_PROJECT is required in production")
    if "sqlite" in DATABASE_URL.lower():
        errors.append(
            "SQLite is not allowed in production; set DATABASE_URL to a PostgreSQL URL"
        )

    if errors:
        raise RuntimeError(
            "Missing required production configuration:\n"
            + "\n".join(f"  - {e}" for e in errors)
        )
