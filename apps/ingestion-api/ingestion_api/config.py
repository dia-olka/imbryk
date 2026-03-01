"""Application configuration."""

import os

SENTRY_DSN = os.getenv("SENTRY_DSN", "")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./imbryk.db")

BRAINTREE_MERCHANT_ID = os.getenv("BRAINTREE_MERCHANT_ID", "")
BRAINTREE_PUBLIC_KEY = os.getenv("BRAINTREE_PUBLIC_KEY", "")
BRAINTREE_PRIVATE_KEY = os.getenv("BRAINTREE_PRIVATE_KEY", "")
BRAINTREE_ENVIRONMENT = os.getenv("BRAINTREE_ENVIRONMENT", "sandbox")

PROMPT_MIN_LENGTH = 10
PROMPT_MAX_LENGTH = 2000

RATE_LIMIT_QUOTE = os.getenv("RATE_LIMIT_QUOTE", "10/minute")

# CORS — comma-separated list of allowed origins
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:4200").split(",")
    if origin.strip()
]
