"""Application configuration via environment variables."""

import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./imbryk.db")

VERTEX_AI_PROJECT = os.getenv("VERTEX_AI_PROJECT", "")
VERTEX_AI_LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")

TOTAL_BUDGET_TOKENS = int(os.getenv("TOTAL_BUDGET_TOKENS", "800000"))
MAX_CLUSTERS = int(os.getenv("MAX_CLUSTERS", "30"))
