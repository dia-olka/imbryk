"""News Scout orchestrator — pre-batch job entry point.

Loads the WorldLedger, generates search queries via Gemini Flash,
executes them via Tavily, and stores results in the news_items table.
"""

from __future__ import annotations

import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone

from ..config import (
    DATABASE_URL,
    ENABLE_EDITORIAL_JOURNAL,
    ENABLE_READER_METRICS,
    JOURNAL_LOOKBACK_DAYS,
    NEWS_SCOUT_ENABLED,
    TAVILY_API_KEY,
    TAVILY_MAX_RESULTS_PER_QUERY,
    TAVILY_MONTHLY_LIMIT,
    TAVILY_RPM,
    TAVILY_SEARCH_DEPTH,
    VERTEX_AI_LOCATION,
    VERTEX_AI_PROJECT,
)
from ..db import (
    get_engine,
    get_session_factory,
    load_edition_metrics,
    load_recent_headlines,
    load_recent_journal,
    load_world_ledger,
    save_news_item,
)
from ..generation import GenerationStrategy, StubGenerationStrategy, VertexAIStrategy
from ..logging_config import configure_logging
from ..personas import NEWSPAPER_PERSONAS
from ..taxonomy import CATEGORY_IDS
from ..world_ledger import INITIAL_WORLD_LEDGER, serialize_ledger_to_synopsis
from ..world_ledger.serialise_dict import ledger_from_dict
from .context import format_scout_context
from .query_generator import generate_queries
from .searcher import RateLimitExceeded, SearchStrategy, StubSearcher, TavilySearcher

logger = logging.getLogger(__name__)


def _previous_date(edition_date: str) -> str:
    """Return the day before *edition_date* as YYYY-MM-DD."""
    dt = datetime.strptime(edition_date, "%Y-%m-%d") - timedelta(days=1)
    return dt.strftime("%Y-%m-%d")


def run_news_scout(
    database_url: str | None = None,
    generation_strategy: GenerationStrategy | None = None,
    searcher: SearchStrategy | None = None,
    edition_date: str | None = None,
) -> dict:
    """Execute the News Scout pipeline.

    Args:
        database_url: Override for the database connection string.
        generation_strategy: LLM backend (defaults to stub).
        searcher: Search backend (defaults to stub).
        edition_date: Target edition date (defaults to today UTC).

    Returns:
        Summary dict with counts of queries executed and items stored.
    """
    start_time = time.monotonic()

    db_url = database_url or DATABASE_URL
    gen = generation_strategy or StubGenerationStrategy()
    search = searcher or StubSearcher()

    from ..config import EDITION_DATE

    target_date = edition_date or EDITION_DATE or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    engine = get_engine(db_url)
    session_factory = get_session_factory(engine)
    session = session_factory()

    try:
        # Step 1: Load WorldLedger
        ledger_dict = load_world_ledger(session)
        if ledger_dict is not None:
            ledger = ledger_from_dict(ledger_dict)
            logger.info("WorldLedger loaded from DB")
        else:
            ledger = INITIAL_WORLD_LEDGER
            logger.info("No WorldLedger in DB, using initial lore")

        # Step 2: Serialize to synopsis
        synopsis = serialize_ledger_to_synopsis(ledger)

        # Step 2b: Load editorial context from DB
        editorial_context = ""
        prev_date = _previous_date(target_date)

        if ENABLE_EDITORIAL_JOURNAL:
            # load_recent_journal includes _pipeline entries alongside
            # each persona's own, so deduplicate by (persona_id, date, type).
            seen_keys: set[tuple[str, str, str]] = set()
            journal_entries = []
            for persona in NEWSPAPER_PERSONAS:
                for entry in load_recent_journal(
                    session,
                    persona.id,
                    lookback_days=JOURNAL_LOOKBACK_DAYS,
                    current_date=target_date,
                ):
                    key = (entry.persona_id, entry.entry_date, entry.entry_type)
                    if key not in seen_keys:
                        seen_keys.add(key)
                        journal_entries.append(entry)
        else:
            journal_entries = []

        recent_headlines = load_recent_headlines(
            session, target_date, lookback_days=5
        )

        if ENABLE_READER_METRICS:
            reader_metrics = load_edition_metrics(session, prev_date)
        else:
            reader_metrics = {}

        editorial_context = format_scout_context(
            journal_entries=journal_entries,
            recent_headlines=recent_headlines,
            reader_metrics=reader_metrics,
        )
        if editorial_context:
            logger.info(
                "Editorial context loaded for scout (%d chars)",
                len(editorial_context),
            )

        # Step 3: Generate search queries via Gemini Flash
        logger.info(
            "Generating search queries",
            extra={"step": "news_scout_generate", "category_count": len(CATEGORY_IDS)},
        )
        queries_by_category = generate_queries(
            synopsis, CATEGORY_IDS, gen, NEWSPAPER_PERSONAS,
            editorial_context=editorial_context,
            today_date=target_date,
        )

        if not queries_by_category:
            logger.warning("No queries generated, exiting News Scout")
            return {"queries_executed": 0, "items_stored": 0}

        # Step 4: Execute searches and store results
        total_queries = 0
        total_stored = 0
        seen_urls: set[str] = set()
        budget_exhausted = False

        for category_id, queries in queries_by_category.items():
            if budget_exhausted:
                break
            for query_text in queries:
                if budget_exhausted:
                    break
                total_queries += 1
                try:
                    results = search.search(query_text, max_results=TAVILY_MAX_RESULTS_PER_QUERY)
                except RateLimitExceeded:
                    logger.warning(
                        "Tavily monthly limit reached, stopping searches"
                    )
                    budget_exhausted = True
                    break
                except Exception:
                    logger.warning(
                        "Search failed for query: %s",
                        query_text,
                        exc_info=True,
                    )
                    continue

                for result in results:
                    # Deduplicate by URL within this run
                    if result.url in seen_urls:
                        continue
                    seen_urls.add(result.url)

                    saved = save_news_item(
                        session=session,
                        edition_date=target_date,
                        category_id=category_id,
                        query=query_text,
                        headline=result.title,
                        snippet=result.snippet,
                        source_url=result.url,
                        relevance_score=result.score,
                    )
                    if saved:
                        total_stored += 1

        session.commit()

        total_ms = int((time.monotonic() - start_time) * 1000)
        summary = {
            "edition_date": target_date,
            "categories_covered": len(queries_by_category),
            "queries_executed": total_queries,
            "items_stored": total_stored,
            "latency_ms": total_ms,
        }
        logger.info(
            "News Scout complete: %d queries, %d items stored in %.1fs",
            total_queries,
            total_stored,
            total_ms / 1000,
            extra={"step": "news_scout_complete", **summary},
        )
        return summary

    except Exception as exc:
        session.rollback()
        logger.exception("News Scout pipeline failed: %s", exc)
        raise
    finally:
        session.close()


def cli_main() -> None:
    """CLI entry point for News Scout Cloud Run Job."""
    configure_logging()

    if not NEWS_SCOUT_ENABLED:
        logger.info("News Scout disabled via NEWS_SCOUT_ENABLED=false")
        sys.exit(0)

    db_url = os.getenv("DATABASE_URL", DATABASE_URL)

    # Choose generation strategy
    gen: GenerationStrategy
    if VERTEX_AI_PROJECT:
        gen = VertexAIStrategy(
            project=VERTEX_AI_PROJECT,
            location=VERTEX_AI_LOCATION,
        )
    else:
        logger.warning(
            "VERTEX_AI_PROJECT not set, using StubGenerationStrategy"
        )
        gen = StubGenerationStrategy()

    # Choose search backend
    search: SearchStrategy
    if TAVILY_API_KEY:
        search = TavilySearcher(
            api_key=TAVILY_API_KEY,
            rpm=TAVILY_RPM,
            monthly_limit=TAVILY_MONTHLY_LIMIT,
            search_depth=TAVILY_SEARCH_DEPTH,
        )
    else:
        logger.warning("TAVILY_API_KEY not set, using StubSearcher")
        search = StubSearcher()

    summary = run_news_scout(
        database_url=db_url,
        generation_strategy=gen,
        searcher=search,
    )
    logger.info("News Scout finished", extra={"summary": summary})


if __name__ == "__main__":
    cli_main()
