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
MAX_BACKFILL_IMAGES_PER_RUN = int(os.getenv("MAX_BACKFILL_IMAGES_PER_RUN", "5"))

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
TAVILY_SEARCH_DEPTH = os.getenv("TAVILY_SEARCH_DEPTH", "basic")  # "basic" (1 credit) or "advanced" (2 credits)
TAVILY_MAX_QUERIES_PER_CATEGORY = int(os.getenv("TAVILY_MAX_QUERIES_PER_CATEGORY", "1"))
NEWS_ITEM_BASE_WEIGHT = float(os.getenv("NEWS_ITEM_BASE_WEIGHT", "0.3"))

# Topic Research — transforms user prompts into real-world news research
TOPIC_RESEARCH_ENABLED = os.getenv("TOPIC_RESEARCH_ENABLED", "false").lower() == "true"
TOPIC_RESEARCH_MAX_QUERIES = int(os.getenv("TOPIC_RESEARCH_MAX_QUERIES", "3"))
TOPIC_RESEARCH_MAX_RETRIES = int(os.getenv("TOPIC_RESEARCH_MAX_RETRIES", "1"))

# Editorial Journal — persistent per-persona editorial memory
ENABLE_EDITORIAL_JOURNAL = os.getenv("ENABLE_EDITORIAL_JOURNAL", "true").lower() == "true"
JOURNAL_LOOKBACK_DAYS = int(os.getenv("JOURNAL_LOOKBACK_DAYS", "7"))

# Quality Grading — autonomous LLM-as-judge + deterministic metrics
ENABLE_QUALITY_GRADING = os.getenv("ENABLE_QUALITY_GRADING", "false").lower() == "true"
QUALITY_GATE_THRESHOLD = float(os.getenv("QUALITY_GATE_THRESHOLD", "2.5"))

# Marketing Agent — autonomous social media promotion
MARKETING_ENABLED = os.getenv("MARKETING_ENABLED", "false").lower() == "true"
BLUESKY_HANDLE = os.getenv("BLUESKY_HANDLE", "")
BLUESKY_APP_PASSWORD = os.getenv("BLUESKY_APP_PASSWORD", "")
GAZETTE_FALLBACK_URL = os.getenv("GAZETTE_FALLBACK_URL", "https://imbryk.news")

# Reader Metrics — Cloudflare Web Analytics feedback loop
ENABLE_READER_METRICS = os.getenv("ENABLE_READER_METRICS", "false").lower() == "true"
CF_ANALYTICS_ZONE_ID = os.getenv("CF_ANALYTICS_ZONE_ID", "")
CF_ANALYTICS_API_TOKEN = os.getenv("CF_ANALYTICS_API_TOKEN", "")

# Translation — multi-provider article translation
TRANSLATION_ENABLED = os.getenv("TRANSLATION_ENABLED", "false").lower() == "true"
TRANSLATION_PROVIDER = os.getenv("TRANSLATION_PROVIDER", "azure")
AZURE_TRANSLATOR_KEY = os.getenv("AZURE_TRANSLATOR_KEY", "")
AZURE_TRANSLATOR_REGION = os.getenv("AZURE_TRANSLATOR_REGION", "")
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY", "")
GOOGLE_TRANSLATE_KEY = os.getenv("GOOGLE_TRANSLATE_KEY", "")
TRANSLATION_CHAR_BUDGET = os.getenv("TRANSLATION_CHAR_BUDGET", "")  # empty = provider default
TRANSLATION_BACKFILL = os.getenv("TRANSLATION_BACKFILL", "false").lower() == "true"
