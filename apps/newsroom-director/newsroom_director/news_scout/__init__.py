"""News Scout — LLM-driven real-world news gap filling."""

from .main import run_news_scout
from .query_generator import generate_queries
from .schemas import QueryGenerationOutput, is_valid_query_output
from .searcher import RateLimitExceeded, TavilySearcher

__all__ = [
    "generate_queries",
    "is_valid_query_output",
    "QueryGenerationOutput",
    "RateLimitExceeded",
    "run_news_scout",
    "TavilySearcher",
]
