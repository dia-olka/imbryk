"""Application configuration via environment variables."""

import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./imbryk.db")

VERTEX_AI_PROJECT = os.getenv("VERTEX_AI_PROJECT", "")
VERTEX_AI_LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")

TOTAL_BUDGET_TOKENS = int(os.getenv("TOTAL_BUDGET_TOKENS", "800000"))
MAX_CLUSTERS = int(os.getenv("MAX_CLUSTERS", "30"))

# Cloudflare R2 storage
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "imbryk-editions")
