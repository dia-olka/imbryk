"""Imbryk Morning Press — AI newspaper generation orchestrator.

Orchestrates the daily newspaper generation pipeline:
1. Fetch unprocessed paid prompts from DB
2. Load/initialise WorldLedger
3. Route prompts to newspapers via taxonomy
4. Serialize WorldLedger synopsis
5. Run coherence validation on prompts
6. Run distillation pipeline per newspaper
7. Generate articles via Gemini (per persona)
8. Run Curator synthe sis
9. Apply WorldLedger mutation
10. Save edition and mark prompts processed

Note: Vertex AI implicit caching is enabled by default for all projects.
The pipeline places the WorldLedger synopsis at the start of every prompt
so that repeated calls within the same run benefit from automatic cache
hits (90% discount on cached input tokens) without any explicit cache
management.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

from sentry_sdk.crons import monitor

from .config import (
    CF_DEPLOY_HOOK_URL,
    DATABASE_URL,
    ENABLE_EDITORIAL_JOURNAL,
    ENABLE_READER_METRICS,
    IMAGE_GENERATION_LOCATION,
    JOURNAL_LOOKBACK_DAYS,
    NEWS_ITEM_BASE_WEIGHT,
    R2_ACCOUNT_ID,
    TOPIC_RESEARCH_ENABLED,
    VERTEX_AI_LOCATION,
    VERTEX_AI_PROJECT,
)
from .db import (
    ArticleMetric,
    NewsItemRecord,
    fetch_pending_news_items,
    fetch_unprocessed_prompts,
    get_engine,
    get_session_factory,
    load_edition_by_date,
    load_edition_metrics,
    load_recent_journal,
    load_world_ledger,
    mark_news_items_processed,
    mark_prompts_processed,
    save_edition,
    save_edition_metrics,
    save_journal_entry,
    save_world_ledger,
)
from .distillation.pipeline import DistillationPipeline
from .distillation.types import Prompt as DistillationPrompt
from .generation import GenerationStrategy, StubGenerationStrategy, VertexAIStrategy
from .image_gen import (
    ImageGenerationStrategy,
    StubImageClient,
    generate_images_for_newspaper,
)
from .logging_config import configure_logging
from .metrics import (
    format_metrics_for_pipeline_observation,
    format_metrics_for_reflection,
)
from .output_schemas import (
    CuratorOutputV2,
    NewspaperOutput,
    is_valid_curator,
    is_valid_newspaper,
)
from .personas import (
    CURATOR_PERSONA,
    NEWSPAPER_PERSONAS,
)
from .reflection import (
    format_journal_for_generation,
    format_previous_edition_summary,
    run_persona_reflection,
    run_pipeline_observation,
)
from .storage import EditionStorage, StubEditionStorage
from .taxonomy import route_prompt
from .world_ledger import (
    INITIAL_WORLD_LEDGER,
    LedgerMutation,
    apply_mutation,
    serialize_ledger_to_synopsis,
)
from .world_ledger.serialise_dict import (
    ledger_from_dict,
    ledger_to_dict,
)

logger = logging.getLogger(__name__)

_MONITOR_CONFIG = {
    "schedule": {"type": "crontab", "value": "0 6 * * *"},  # Every day at 6am UTC
    "timezone": "UTC",
    "checkin_margin": 120,  # 2 minutes
    "max_runtime": 60*60,  # 1 hour
    "failure_issue_threshold": 1,
    "recovery_threshold": 1,
}

def run_morning_press(
    database_url: str | None = None,
    generation_strategy: GenerationStrategy | None = None,
    storage: EditionStorage | None = None,
    distillation_pipeline: DistillationPipeline | None = None,
    imagen_client: ImageGenerationStrategy | None = None,
    edition_date: str | None = None,
) -> dict:
    """Execute the full Morning Press generation pipeline.

    Args:
        database_url: Override for the database connection string.
        generation_strategy: LLM generation backend (defaults to stub).
        storage: Edition output storage (defaults to stub).
        distillation_pipeline: Override for the distillation pipeline.
        imagen_client: Image generation backend (defaults to stub).

    Returns:
        Summary dict with edition_id, newspaper_count, article_count.
    """
    configure_logging()
    start_time = time.monotonic()

    db_url = database_url or DATABASE_URL
    gen = generation_strategy or StubGenerationStrategy()
    store = storage or StubEditionStorage()
    pipeline = distillation_pipeline or DistillationPipeline()
    img_client = imagen_client or StubImageClient()

    # Step 1: Connect to DB
    engine = get_engine(db_url)
    session_factory = get_session_factory(engine)
    session = session_factory()

    from .config import EDITION_DATE

    today_date = edition_date or EDITION_DATE or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _run_backfill() -> bool:
        """Run image backfill. Returns True if any editions were updated."""
        try:
            from .config import MAX_BACKFILL_IMAGES_PER_RUN
            from .image_gen.backfill import run_image_backfill

            result = run_image_backfill(
                session=session,
                today_date=today_date,
                imagen_client=img_client,
                storage=store,
                max_images_per_run=MAX_BACKFILL_IMAGES_PER_RUN,
                llm=gen,
            )
            return result.editions_updated > 0
        except Exception:
            logger.warning(
                "Image backfill step failed, today's edition unaffected",
                exc_info=True,
            )
            return False

    try:
        # Step 2: Fetch unprocessed prompts
        prompt_records = fetch_unprocessed_prompts(session)
        logger.info(
            "Fetched prompts",
            extra={"step": "fetch", "prompt_count": len(prompt_records)},
        )

        # Step 2b: Fetch today's news items
        news_items = fetch_pending_news_items(session, today_date)
        logger.info(
            "Fetched news items",
            extra={"step": "fetch_news", "news_item_count": len(news_items)},
        )

        if not prompt_records and not news_items:
            logger.info("No prompts or news items found, skipping edition")
            return {
                "edition_id": None,
                "newspaper_count": 0,
                "article_count": 0,
            }

        # Step 3: Load WorldLedger from DB (or use initial)
        ledger_dict = load_world_ledger(session)
        if ledger_dict is not None:
            ledger = ledger_from_dict(ledger_dict)
            logger.info("WorldLedger loaded from DB")
        else:
            ledger = INITIAL_WORLD_LEDGER
            logger.info("No WorldLedger in DB, using initial lore")

        # Step 4: Serialize WorldLedger to synopsis
        synopsis = serialize_ledger_to_synopsis(ledger)
        logger.info(
            "WorldLedger synopsis serialized",
            extra={"synopsis_length": len(synopsis)},
        )

        # Step 5: Topic research — replace raw prompts with researched news
        # Prompts that fail research are left as 'accepted' for retry on the
        # next pipeline run (up to TOPIC_RESEARCH_MAX_RETRIES attempts).
        original_prompt_ids = [pr.prompt_id for pr in prompt_records]
        research_failed_ids: list[str] = []
        if TOPIC_RESEARCH_ENABLED and prompt_records:
            from .config import (
                TAVILY_API_KEY,
                TAVILY_MONTHLY_LIMIT,
                TAVILY_RPM,
                TAVILY_SEARCH_DEPTH,
            )
            from .news_scout.searcher import TavilySearcher
            from .topic_researcher import research_prompts

            if TAVILY_API_KEY:
                topic_searcher = TavilySearcher(
                    api_key=TAVILY_API_KEY,
                    rpm=TAVILY_RPM,
                    monthly_limit=TAVILY_MONTHLY_LIMIT,
                    search_depth=TAVILY_SEARCH_DEPTH,
                )
                # Exclude URLs already in pipeline via News Scout
                news_urls = {
                    ni.source_url
                    for ni in news_items
                    if hasattr(ni, "source_url") and ni.source_url
                }
                research_result = research_prompts(
                    prompt_records, topic_searcher, gen,
                    exclude_urls=news_urls,
                    session=session,
                    edition_date=today_date,
                )
                research_failed_ids = research_result.failed_prompt_ids
                logger.info(
                    "Topic research replaced %d prompts with %d researched items "
                    "(%d prompts deferred for retry)",
                    len(prompt_records),
                    len(research_result.researched),
                    len(research_failed_ids),
                )
                # Replace prompt_records with researched items for routing.
                # ResearchedPrompt has the same interface (prompt_id, text,
                # payment_amount, category_ids) so routing works unchanged.
                prompt_records = research_result.researched  # type: ignore[assignment]

                if not prompt_records and not news_items:
                    logger.info(
                        "Topic research produced no results and no news items, skipping edition"
                    )
                    session.commit()  # persist research logs
                    return {
                        "edition_id": None,
                        "newspaper_count": 0,
                        "article_count": 0,
                    }
            else:
                logger.warning(
                    "TOPIC_RESEARCH_ENABLED but TAVILY_API_KEY not set, "
                    "falling back to verbatim prompts"
                )

        # Step 6: Route prompts + news items to newspapers
        newspaper_prompts: dict[str, list] = defaultdict(list)
        for pr in prompt_records:
            routes = route_prompt(pr.category_ids)
            for route in routes:
                newspaper_prompts[route.newspaper_id].append(pr)

        # Route news items via the same taxonomy routing
        for ni in news_items:
            routes = route_prompt([ni.category_id])
            for route in routes:
                newspaper_prompts[route.newspaper_id].append(ni)

        logger.info(
            "Prompts routed to newspapers",
            extra={
                "step": "routing",
                "newspapers": {
                    nid: len(ps) for nid, ps in newspaper_prompts.items()
                },
            },
        )

        # Step 6b: Load editorial journal entries for generation prompts
        journal_by_persona: dict[str, str] = {}
        if ENABLE_EDITORIAL_JOURNAL:
            for persona in NEWSPAPER_PERSONAS:
                entries = load_recent_journal(
                    session, persona.id,
                    lookback_days=JOURNAL_LOOKBACK_DAYS,
                    current_date=today_date,
                )
                journal_by_persona[persona.id] = format_journal_for_generation(
                    entries, persona.id,
                )
            logger.info(
                "Editorial journal loaded",
                extra={
                    "step": "journal_load",
                    "personas_with_entries": sum(
                        1 for v in journal_by_persona.values()
                        if "No editorial journal" not in v
                    ),
                },
            )

        # Step 6c: Load previous edition data for persona generation prompts
        from datetime import timedelta as _td

        prev_date_str = (
            datetime.strptime(today_date, "%Y-%m-%d") - _td(days=1)
        ).strftime("%Y-%m-%d")
        prev_edition = load_edition_by_date(session, prev_date_str)
        prev_edition_metrics_by_persona: dict[str, list[ArticleMetric]] = {}
        if ENABLE_READER_METRICS:
            prev_edition_metrics_by_persona = load_edition_metrics(session, prev_date_str)

        prev_edition_by_persona: dict[str, str] = {}
        if prev_edition:
            for persona in NEWSPAPER_PERSONAS:
                content_json = prev_edition.get(persona.id)
                persona_metrics = prev_edition_metrics_by_persona.get(persona.id)
                summary = format_previous_edition_summary(
                    persona.id,
                    prev_date_str,
                    content_json,
                    metrics=persona_metrics,
                )
                if summary:
                    prev_edition_by_persona[persona.id] = summary
            if prev_edition_by_persona:
                logger.info(
                    "Previous edition summaries loaded for %d personas",
                    len(prev_edition_by_persona),
                )

        # Step 7: For each newspaper, distill and generate.
        # Failures for individual newspapers are isolated — a single Gemini error
        # skips that paper but allows the remaining newspapers to proceed.
        articles: dict[str, str] = {}
        for persona in NEWSPAPER_PERSONAS:
            prompts_for_paper = newspaper_prompts.get(persona.id, [])
            if not prompts_for_paper:
                continue

            logger.info(
                "Processing newspaper",
                extra={
                    "step": "generate",
                    "newspaper_id": persona.id,
                    "cluster_count": len(prompts_for_paper),
                },
            )

            try:
                # Convert to distillation Prompt objects.
                # NewsItemRecords use a fixed low base weight;
                # PromptRecords use actual payment amount.
                dist_prompts = []
                for item in prompts_for_paper:
                    if isinstance(item, NewsItemRecord):
                        dist_prompts.append(
                            DistillationPrompt(
                                text=f"{item.headline}\n{item.snippet}",
                                payment_amount=NEWS_ITEM_BASE_WEIGHT,
                                prompt_id=item.id,
                            )
                        )
                    else:
                        dist_prompts.append(
                            DistillationPrompt(
                                text=item.text,
                                payment_amount=item.payment_amount,
                                prompt_id=item.prompt_id,
                                source_url=getattr(item, "source_url", ""),
                            )
                        )

                # Run distillation pipeline
                dist_start = time.monotonic()
                budgeted = pipeline.run(dist_prompts)
                digests_text = pipeline.serialize_all(budgeted)
                logger.info(
                    "Distillation complete for %s",
                    persona.id,
                    extra={
                        "step": "distillation",
                        "newspaper_id": persona.id,
                        "cluster_count": len(budgeted),
                        "digest_length": len(digests_text),
                        "latency_ms": int((time.monotonic() - dist_start) * 1000),
                    },
                )

                # System instruction: persona identity, voice, rules, exemplars
                # (no context data — that goes in the user turn for cache efficiency)
                system_instruction = persona.system_prompt_template

                # User turn: WorldLedger FIRST (identical across all 6 calls,
                # so Vertex AI implicit prefix caching gives 90% cost discount),
                # then editorial journal, then cluster digests, then task.
                journal_text = (
                    journal_by_persona.get(persona.id, "")
                    if ENABLE_EDITORIAL_JOURNAL
                    else ""
                )
                prev_summary = prev_edition_by_persona.get(persona.id, "")
                if prev_summary:
                    journal_text = f"{journal_text}\n\n{prev_summary}" if journal_text else prev_summary

                user_parts = [f"WORLD HISTORY:\n{synopsis}"]
                if journal_text:
                    user_parts.append(
                        "YOUR EDITORIAL JOURNAL (recent entries — use these to "
                        "inform your editorial decisions today, but do not "
                        "reference the journal itself in your articles):\n"
                        + journal_text
                    )
                user_parts.append(f"CLUSTER DIGESTS:\n{digests_text}")
                user_parts.append(
                    "<task>\nBased on the context and clusters above, produce "
                    "today's edition. Follow all rules in your system instruction.\n</task>"
                )
                user_content = "\n\n".join(user_parts)

                # Call LLM — response_schema enforces exact field names so the
                # gazette always receives canonical JSON (no "title"/"content"/
                # "fullArticles" deviations, no markdown fences, no plain text).
                # Retry up to 3 times if the model returns empty/invalid output.
                logger.info(
                    "Calling Gemini for %s (%s tier)",
                    persona.id,
                    persona.model_tier,
                    extra={
                        "step": "llm_call",
                        "newspaper_id": persona.id,
                        "model_tier": persona.model_tier,
                    },
                )
                gen_start = time.monotonic()
                article = None
                for attempt in range(1, 4):
                    candidate = gen.generate(
                        system_instruction, persona.model_tier, user_content,
                        response_schema=NewspaperOutput,
                    )
                    if is_valid_newspaper(candidate):
                        article = candidate
                        break
                    logger.warning(
                        "Invalid newspaper output for %s (attempt %d/3), "
                        "retrying | model_tier=%s | response_length=%d | "
                        "preview: %.300s",
                        persona.id, attempt, persona.model_tier,
                        len(candidate) if candidate else 0,
                        candidate[:300] if candidate else "<empty>",
                        extra={
                            "step": "generate_retry",
                            "newspaper_id": persona.id,
                            "model_tier": persona.model_tier,
                            "response_length": len(candidate) if candidate else 0,
                        },
                    )
                gen_ms = int((time.monotonic() - gen_start) * 1000)

                if article is None:
                    logger.error(
                        "All 3 attempts produced invalid output for %s, "
                        "skipping | model_tier=%s | last response preview: %.500s",
                        persona.id, persona.model_tier,
                        candidate[:500] if candidate else "<empty>",
                        extra={
                            "step": "generate_failed",
                            "newspaper_id": persona.id,
                            "model_tier": persona.model_tier,
                        },
                    )
                else:
                    logger.info(
                        "Article generated",
                        extra={
                            "step": "generated",
                            "newspaper_id": persona.id,
                            "model_tier": persona.model_tier,
                            "latency_ms": gen_ms,
                        },
                    )
                    articles[persona.id] = article

            except Exception:
                logger.exception(
                    "Failed to generate articles for newspaper %s, skipping",
                    persona.id,
                )

        # Step 8: Run Curator synthesis
        if articles:
            try:
                all_articles_text = _format_all_articles(articles)
                # Prefix-caching: articles go in the user turn, not the system prompt,
                # so the static system prompt can be cached across retries.
                # The TypeScript buildCuratorPrompt inlines articles directly; here we
                # substitute a placeholder and pass articles as user content instead.
                curator_system = CURATOR_PERSONA.system_prompt_template.replace(
                    "{{ALL_ARTICLES}}", "[See user content below]"
                )
                curator_content = f"TODAY'S ARTICLES:\n{all_articles_text}\n\nGenerate today's synthesis."
                curator_article = None
                for attempt in range(1, 4):
                    candidate = gen.generate(
                        curator_system, CURATOR_PERSONA.model_tier, curator_content,
                        response_schema=CuratorOutputV2,
                    )
                    if is_valid_curator(candidate):
                        curator_article = candidate
                        break
                    logger.warning(
                        "Invalid curator output (attempt %d/3), retrying "
                        "| model_tier=%s | response_length=%d | preview: %.300s",
                        attempt, CURATOR_PERSONA.model_tier,
                        len(candidate) if candidate else 0,
                        candidate[:300] if candidate else "<empty>",
                        extra={
                            "step": "curator_retry",
                            "model_tier": CURATOR_PERSONA.model_tier,
                            "response_length": len(candidate) if candidate else 0,
                        },
                    )
                if curator_article is None:
                    logger.error(
                        "All 3 attempts produced invalid curator output, "
                        "skipping | last response preview: %.500s",
                        candidate[:500] if candidate else "<empty>",
                        extra={"step": "curator_failed"},
                    )
                else:
                    articles["curator"] = curator_article
            except Exception:
                logger.exception(
                    "Curator synthesis failed, skipping curator article"
                )

        # Step 8b: Fetch reader metrics for the previous edition (if enabled).
        prev_metrics: list[ArticleMetric] = []
        prev_newspaper_totals: dict[str, int] = {}
        if articles and ENABLE_READER_METRICS:
            try:
                from datetime import timedelta as _td

                # Always fetches the previous calendar day. If the pipeline
                # is down for a day and two editions are generated
                # back-to-back, the second run will attempt to fetch metrics
                # for a date that may have no data yet — this will produce
                # "0 views" feedback rather than last-edition data.
                prev_date_dt = datetime.strptime(today_date, "%Y-%m-%d") - _td(days=1)
                prev_date = prev_date_dt.strftime("%Y-%m-%d")

                from .config import CF_ANALYTICS_API_TOKEN, CF_ANALYTICS_ZONE_ID
                from .metrics import MetricsClient

                if CF_ANALYTICS_ZONE_ID and CF_ANALYTICS_API_TOKEN:
                    mclient = MetricsClient(CF_ANALYTICS_ZONE_ID, CF_ANALYTICS_API_TOKEN)
                    prev_metrics = mclient.fetch_article_views(prev_date)

                    # Try to enrich slug-based headlines from DB
                    db_prev_metrics = load_edition_metrics(session, prev_date)
                    if db_prev_metrics:
                        from .metrics import enrich_metrics_with_headlines
                        prev_metrics = enrich_metrics_with_headlines(
                            prev_metrics, db_prev_metrics,
                        )

                    # Compute per-newspaper totals
                    for m in prev_metrics:
                        prev_newspaper_totals[m.newspaper_id] = (
                            prev_newspaper_totals.get(m.newspaper_id, 0)
                            + m.page_views
                        )

                    # Persist fetched metrics
                    if prev_metrics:
                        save_edition_metrics(session, prev_metrics, prev_date)

                    logger.info(
                        "Reader metrics fetched",
                        extra={
                            "step": "metrics",
                            "prev_date": prev_date,
                            "article_count": len(prev_metrics),
                            "total_views": sum(prev_newspaper_totals.values()),
                        },
                    )
            except Exception:
                logger.warning(
                    "Failed to fetch reader metrics, continuing without",
                    exc_info=True,
                )

        # Step 8c: Editorial self-reflection — each persona critiques its output.
        # Runs after curator so reflections can reference the curator's analysis.
        if articles and ENABLE_EDITORIAL_JOURNAL:
            try:
                curator_text = ""
                if "curator" in articles:
                    import json as _json
                    try:
                        parsed_curator = _json.loads(articles["curator"])
                        version = parsed_curator.get("version")
                        if version == 2:
                            # V2 structured format — extract text for reflection prompt
                            sections = []
                            consensus = parsed_curator.get("consensus", [])
                            if consensus:
                                items = "\n".join(
                                    f"{i}. {c['text']}" for i, c in enumerate(consensus, 1)
                                    if isinstance(c, dict)
                                )
                                sections.append(f"CONSENSUS\n{items}")
                            faults = parsed_curator.get("fault_lines", [])
                            if faults:
                                items = "\n".join(
                                    f"{i}. {f['topic']}: {f.get('summary', '')}"
                                    for i, f in enumerate(faults, 1)
                                    if isinstance(f, dict)
                                )
                                sections.append(f"FAULT LINES\n{items}")
                            gaps = parsed_curator.get("gaps", [])
                            if gaps:
                                items = "\n".join(
                                    f"{i}. {g['topic']}: {g.get('description', '')}"
                                    for i, g in enumerate(gaps, 1)
                                    if isinstance(g, dict)
                                )
                                sections.append(f"GAPS\n{items}")
                            watch = parsed_curator.get("what_to_watch", [])
                            if watch:
                                numbered = "\n".join(
                                    f"{i}. {item}" for i, item in enumerate(watch, 1)
                                )
                                sections.append(f"WHAT TO WATCH\n{numbered}")
                            curator_text = "\n\n".join(sections)
                        elif "consensus" in parsed_curator:
                            # V1 structured format — plain string lists
                            sections = []
                            for key, label in [
                                ("consensus", "CONSENSUS"),
                                ("fault_lines", "FAULT LINES"),
                                ("uncovered_angles", "UNCOVERED ANGLES"),
                                ("what_to_watch", "WHAT TO WATCH"),
                            ]:
                                items = parsed_curator.get(key, [])
                                if items:
                                    numbered = "\n".join(
                                        f"{i}. {item}" for i, item in enumerate(items, 1)
                                    )
                                    sections.append(f"{label}\n{numbered}")
                            curator_text = "\n\n".join(sections)
                        else:
                            # Legacy text format
                            curator_text = parsed_curator.get("text", "")
                    except (ValueError, TypeError, AttributeError):
                        curator_text = articles.get("curator", "")

                all_articles_text_for_reflection = _format_all_articles(articles)

                for persona in NEWSPAPER_PERSONAS:
                    if persona.id not in articles:
                        continue

                    persona_entries = load_recent_journal(
                        session, persona.id,
                        lookback_days=JOURNAL_LOOKBACK_DAYS,
                        current_date=today_date,
                    )

                    # Build metrics text for this persona
                    persona_metrics_text = ""
                    if prev_metrics:
                        persona_metrics_text = format_metrics_for_reflection(
                            prev_metrics, persona.id, prev_newspaper_totals,
                        )

                    reflection = run_persona_reflection(
                        persona=persona,
                        edition_date=today_date,
                        persona_articles_json=articles[persona.id],
                        curator_text=curator_text,
                        previous_entries=persona_entries,
                        generation_strategy=gen,
                        metrics_text=persona_metrics_text,
                    )
                    if reflection:
                        save_journal_entry(
                            session, persona.id, today_date,
                            "reflection", reflection,
                        )
                        logger.info(
                            "Journal entry saved for %s", persona.id,
                            extra={
                                "step": "reflection",
                                "persona_id": persona.id,
                            },
                        )

                # Pipeline-level observation
                pipeline_entries = load_recent_journal(
                    session, "_pipeline",
                    lookback_days=JOURNAL_LOOKBACK_DAYS,
                    current_date=today_date,
                )

                pipeline_metrics_text = ""
                if prev_metrics:
                    pipeline_metrics_text = format_metrics_for_pipeline_observation(
                        prev_newspaper_totals, prev_metrics,
                    )

                observation = run_pipeline_observation(
                    edition_date=today_date,
                    all_articles_text=all_articles_text_for_reflection,
                    previous_entries=pipeline_entries,
                    generation_strategy=gen,
                    metrics_text=pipeline_metrics_text,
                )
                if observation:
                    save_journal_entry(
                        session, "_pipeline", today_date,
                        "observation", observation,
                    )
                    logger.info(
                        "Pipeline observation saved",
                        extra={"step": "reflection"},
                    )

            except Exception:
                logger.exception(
                    "Editorial reflection step failed, continuing without journal updates"
                )

        # Step 9: World History update via LLM
        # Always run when articles were generated — record real-world facts
        # regardless of whether any user prompts were processed in this edition.
        if articles:
            try:
                mutation_system, mutation_content = _build_mutation_prompt(synopsis, articles)
                mutation_response = gen.generate(mutation_system, "flash", mutation_content)
                mutation = _parse_mutation(mutation_response)
                if mutation:
                    ledger = apply_mutation(ledger, mutation)
                    save_world_ledger(session, ledger_to_dict(ledger), edition_date=today_date)
                    logger.info(
                        "World Ledger updated for %s | mutation: %s",
                        today_date,
                        mutation_response[:500],
                        extra={"step": "world_ledger_update", "edition_date": today_date},
                    )
                else:
                    logger.warning(
                        "World Ledger mutation was empty/unparseable for %s | raw: %s",
                        today_date,
                        mutation_response[:500],
                        extra={"step": "world_ledger_update", "edition_date": today_date},
                    )
            except Exception:
                logger.exception(
                    "World History update failed, skipping history mutation",
                    extra={"step": "world_ledger_update", "edition_date": today_date},
                )

        # Step 9b: Image generation — parse article JSON, generate images,
        # embed image URLs back into the content.
        image_counts = 0
        for newspaper_id, content in list(articles.items()):
            if newspaper_id == "curator":
                continue
            parsed = _try_parse_edition_json(content)
            if parsed is None:
                continue

            # Always re-serialize to clean JSON (strips any markdown fences 
            # that the LLM may have emitted) before attempting image generation.
            # This ensures R2 always receives valid JSON regardless of whether
            # image generation succeeds or fails.
            articles[newspaper_id] = json.dumps(parsed, ensure_ascii=False)

            article_list = parsed.get("articles", [])
            front_page_prompt = parsed.get("frontPageImagePrompt")

            try:
                # Look up per-persona negative prompt for Imagen
                persona_neg = next(
                    (p.negative_prompt for p in NEWSPAPER_PERSONAS if p.id == newspaper_id),
                    "",
                )
                result = generate_images_for_newspaper(
                    newspaper_id=newspaper_id,
                    articles=article_list,
                    front_page_image_prompt=front_page_prompt,
                    imagen_client=img_client,
                    storage=store,
                    edition_id=str(
                        datetime.now(timezone.utc).strftime("%Y-%m-%d")
                    ),
                    negative_prompt=persona_neg,
                    llm=gen,
                )

                # Embed image URLs into articles
                for idx, url in result.article_image_urls.items():
                    if idx < len(article_list):
                        article_list[idx]["image_url"] = url
                        image_counts += 1
                if result.hero_image_url:
                    parsed["heroImageUrl"] = result.hero_image_url
                    image_counts += 1

                # Re-serialize with image URLs embedded
                articles[newspaper_id] = json.dumps(parsed, ensure_ascii=False)
            except Exception:
                logger.exception(
                    "Image generation failed for newspaper %s "
                    "| article_count=%d | front_page_prompt=%s, "
                    "continuing without images",
                    newspaper_id,
                    len(article_list),
                    front_page_prompt[:80] if front_page_prompt else None,
                )

        logger.info(
            "Image generation complete",
            extra={"step": "images", "image_count": image_counts},
        )

        # Step 10: Save edition to DB
        edition_date = today_date
        logger.info(
            "Saving edition to DB",
            extra={"step": "save", "edition_date": edition_date},
        )
        edition_id = save_edition(session, edition_date, articles)

        # Step 11: Write edition to storage
        store.write_edition(edition_id, edition_date, articles)

        # Step 12: Mark prompts and news items as processed.
        # Exclude prompts whose topic research failed — they stay as
        # 'accepted' so the next pipeline run can retry them.
        failed_set = set(research_failed_ids)
        prompt_ids = [
            pid for pid in original_prompt_ids
            if pid not in failed_set
        ]
        mark_prompts_processed(session, prompt_ids)
        if news_items:
            mark_news_items_processed(session, today_date)

        session.commit()

        # Step 13: Write index manifest to R2
        _write_edition_index(store, edition_id, edition_date, articles)

        # Step 14: Trigger gazette rebuild via Cloudflare deploy hook
        _trigger_deploy_hook()

        # Step 15: Backfill missing images from previous editions (best-effort).
        # Runs after today's edition is committed and published so a slow
        # Imagen backfill cannot delay the current edition reaching readers.
        if _run_backfill():
            # Backfill updated past editions on R2 — trigger a second rebuild
            # so the gazette picks up the newly generated hero/article images.
            _trigger_deploy_hook()

        total_ms = int((time.monotonic() - start_time) * 1000)
        newspaper_ids = [k for k in articles if k != "curator"]
        summary = {
            "edition_id": edition_id,
            "edition_date": edition_date,
            "newspaper_count": len(newspaper_ids),
            "newspaper_ids": newspaper_ids,
            "has_curator": "curator" in articles,
            "image_count": image_counts,
            "prompt_count": len(prompt_records),
            "news_item_count": len(news_items),
            "latency_ms": total_ms,
        }

        logger.info(
            "Edition complete: %s | %d newspapers (%s) | curator=%s | "
            "%d images | %d prompts | %.1fs",
            edition_id,
            len(newspaper_ids),
            ", ".join(newspaper_ids),
            "curator" in articles,
            image_counts,
            len(prompt_records),
            total_ms / 1000,
            extra={"step": "complete", **summary},
        )

        return summary

    except Exception as exc:
        session.rollback()
        logger.exception("Morning Press pipeline failed: %s", exc)
        raise
    finally:
        session.close()


def _write_edition_index(
    store: EditionStorage,
    edition_id: str,
    edition_date: str,
    articles: dict[str, str],
) -> None:
    """Build and write an index.json manifest listing all editions."""
    try:
        existing = store.list_editions()
        # Collect known edition dates from existing index entries
        known_dates: set[str] = set()
        index_entries: list[dict] = []
        for entry in existing:
            # Entries from list_editions have {key, last_modified}
            key = entry.get("key", "")
            if key.endswith(".json") and key != "editions/index.json":
                parts = key.split("/")
                if len(parts) >= 3:
                    date = parts[1]
                    known_dates.add(date)
                    index_entries.append(
                        {
                            "edition_id": parts[2].replace(".json", ""),
                            "date": date,
                            "newspaper_ids": [],
                        }
                    )

        # Add current edition if not already present
        if edition_date not in known_dates:
            newspaper_ids = [k for k in articles if k != "curator"]
            index_entries.append(
                {
                    "edition_id": edition_id,
                    "date": edition_date,
                    "newspaper_ids": newspaper_ids,
                }
            )

        # Sort by date descending (newest first)
        index_entries.sort(key=lambda e: e["date"], reverse=True)
        store.write_index(index_entries)
    except Exception:
        logger.warning(
            "Failed to write edition index, gazette will use stale index",
            exc_info=True,
        )


def _trigger_deploy_hook() -> None:
    """POST to Cloudflare Pages deploy hook to trigger gazette rebuild.

    Best-effort: logs a warning on failure but never raises.
    """
    if not CF_DEPLOY_HOOK_URL:
        logger.info("CF_DEPLOY_HOOK_URL not set, skipping gazette rebuild trigger")
        return

    try:
        import urllib.request

        req = urllib.request.Request(CF_DEPLOY_HOOK_URL, method="POST", data=b"")
        with urllib.request.urlopen(req, timeout=30) as resp:
            logger.info(
                "Gazette deploy hook triggered",
                extra={"status": resp.status},
            )
    except Exception:
        logger.warning(
            "Failed to trigger gazette deploy hook",
            exc_info=True,
        )


def _format_all_articles(articles: dict[str, str]) -> str:
    """Format all newspaper articles for the Curator prompt."""
    sections = []
    for newspaper_id, content in articles.items():
        sections.append(f"=== {newspaper_id.upper()} ===\n{content}")
    return "\n\n".join(sections)


def _normalize_newspaper_json(parsed: dict) -> dict:
    """Normalize LLM field name deviations to the canonical gazette schema.

    Applied before writing to R2 as defense-in-depth — even when
    response_schema is in use, this ensures R2 always has canonical names
    in case a model tier bypasses controlled generation.

    Canonical names:
      articles     (not fullArticles / article_list)
      headline     (not title)
      body         (not content / text)
      in_brief     (not inBrief / inBriefs)
      editors_note (not editorsNote / editorNote / editor_note)
      summary      (not content / text, inside in_brief items)
    """
    # Normalize articles key
    if not isinstance(parsed.get("articles"), list):
        parsed["articles"] = parsed.pop("fullArticles", None) or parsed.pop("article_list", None) or []

    # Normalize articles field names
    parsed["articles"] = [
        {
            **a,
            "headline": a.get("headline") or a.get("title"),
            "body": a.get("body") or a.get("content") or a.get("text"),
        }
        for a in parsed["articles"]
    ]

    # Normalize in_brief key
    if not isinstance(parsed.get("in_brief"), list):
        parsed["in_brief"] = parsed.pop("inBrief", None) or parsed.pop("inBriefs", None) or []

    # Normalize in_brief item field names
    normalized_brief = []
    for item in parsed["in_brief"]:
        if isinstance(item, str):
            first_sentence = item.split(".")[0].strip()[:80]
            normalized_brief.append({"headline": first_sentence or item[:80], "summary": item})
        else:
            headline = item.get("headline") or item.get("title")
            summary = item.get("summary") or item.get("content") or item.get("text")
            if not headline and summary:
                headline = summary.split(".")[0].strip()[:80]
            normalized_brief.append({**item, "headline": headline, "summary": summary})
    parsed["in_brief"] = normalized_brief

    # Normalize editors_note key
    if not parsed.get("editors_note"):
        for alt in ("editorsNote", "editorNote", "editor_note"):
            if isinstance(parsed.get(alt), str):
                parsed["editors_note"] = parsed.pop(alt)
                break

    return parsed


def _try_parse_edition_json(content: str) -> dict | None:
    """Attempt to parse a newspaper edition content string as JSON.

    The Gemini output may be raw JSON or wrapped in markdown code fences.
    Returns the parsed and normalized dict, or None if parsing fails.
    """
    text = content.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]  # remove opening fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    try:
        parsed = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        logger.warning(
            "Could not parse newspaper content as JSON for image generation"
        )
        return None

    return _normalize_newspaper_json(parsed)


def _build_mutation_prompt(
    synopsis: str, articles: dict[str, str]
) -> tuple[str, str]:
    """Build a system instruction + user content for World History mutation."""
    articles_text = _format_all_articles(articles)

    system_instruction = """\
You are a world history recorder. Given the current historical record and \
today's newspaper articles, produce a JSON object describing factual updates \
to the world history ledger. Only include fields that should change.

Your job is to record real-world facts — events, developments, and trends \
that actually happened — not to speculate or editorialize. Extract concrete \
facts from today's articles and update the historical record accordingly.

The mutation JSON should follow this schema (all fields optional):
- synopsis: string (updated world history synopsis — a factual summary of \
the current state of world affairs)
- add_nations: list of new nations
- update_nations: list of {name, ...fields_to_update}
- add_alliances, add_conflicts, update_conflicts
- add_currencies, add_trading_blocs, add_scarcities
- update_global_gdp_trend: string
- update_ai, update_energy, update_biotech: partial tech domain update objects \
with optional keys: {"name": str, "maturity_level": "emerging"|"growth"|\
"mature"|"declining", "key_players": [str], "description": str}
- add_dominant_narratives: list of strings
- add_movements: list of {name, reach, description}
- update_media_landscape: string
- add_forces, update_forces
- add_arms_races, add_doctrine_shifts: lists of strings
- update_temperature_anomaly: float
- add_crises, add_mitigation_efforts
- add_historical_events: list of {date, headline, description, impact, \
sectors} — record significant real-world events from today's coverage
- add_story_threads: list of {name, status, started, last_covered, summary, \
related_nations, sectors} — create NEW threads for developing real-world \
stories that span multiple days. Status: "developing" | "ongoing" | "resolved".
- update_story_threads: list of {name, ...fields_to_update} — update existing \
story threads by name. Use this to update summaries with new facts, change \
status to "resolved" when a story concludes, or update last_covered dates.

IMPORTANT: Story threads track evolving real-world narratives across editions. \
When today's articles cover a significant new developing story, create a thread. \
When a thread's story concludes or becomes irrelevant, mark it "resolved". \
Always update last_covered for threads that appear in today's coverage.

Respond with ONLY the JSON mutation object, no explanation."""

    user_content = f"""\
CURRENT WORLD HISTORY:
{synopsis}

TODAY'S ARTICLES:
{articles_text}"""

    return system_instruction, user_content


def _parse_mutation(response: str) -> LedgerMutation | None:
    """Parse an LLM response into a LedgerMutation, or None on failure."""
    try:
        # Strip markdown code fences if present
        text = response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:]  # remove opening fence
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)

        data = json.loads(text)
        return _dict_to_mutation(data)
    except (json.JSONDecodeError, KeyError, TypeError):
        logger.warning(
            "Failed to parse WorldLedger mutation from LLM response: %.500s",
            text,
            exc_info=True,
        )
        return None


def _dict_to_mutation(data: dict) -> LedgerMutation:
    """Convert a raw dict into a LedgerMutation dataclass."""
    from .world_ledger.types import (
        Alliance,
        Conflict,
        CulturalMovement,
        Currency,
        EnvironmentalCrisis,
        HistoricalEvent,
        MilitaryForce,
        Nation,
        Scarcity,
        StoryThread,
        TechDomain,
        TradingBloc,
    )

    mutation = LedgerMutation()

    if "synopsis" in data:
        mutation.synopsis = data["synopsis"]

    if "add_nations" in data:
        mutation.add_nations = [
            Nation(
                name=n["name"],
                government_type=n.get("government_type", ""),
                leader=n.get("leader", ""),
                stability=n.get("stability", 50),
                description=n.get("description", ""),
            )
            for n in data["add_nations"]
        ]

    if "update_nations" in data:
        mutation.update_nations = data["update_nations"]

    if "add_alliances" in data:
        mutation.add_alliances = [
            Alliance(
                name=a["name"],
                members=a.get("members", []),
                purpose=a.get("purpose", ""),
            )
            for a in data["add_alliances"]
        ]

    if "add_conflicts" in data:
        mutation.add_conflicts = [
            Conflict(
                name=c["name"],
                parties=c.get("parties", []),
                status=c.get("status", "active"),
                description=c.get("description", ""),
            )
            for c in data["add_conflicts"]
        ]

    if "update_conflicts" in data:
        mutation.update_conflicts = data["update_conflicts"]

    if "add_currencies" in data:
        mutation.add_currencies = [
            Currency(
                name=c["name"],
                issuing_entity=c.get("issuing_entity", ""),
                strength=c.get("strength", 50),
                description=c.get("description", ""),
            )
            for c in data["add_currencies"]
        ]

    if "add_trading_blocs" in data:
        mutation.add_trading_blocs = [
            TradingBloc(
                name=t["name"],
                members=t.get("members", []),
                focus=t.get("focus", ""),
            )
            for t in data["add_trading_blocs"]
        ]

    if "add_scarcities" in data:
        mutation.add_scarcities = [
            Scarcity(
                resource=s["resource"],
                severity=s.get("severity", "moderate"),
                affected_regions=s.get("affected_regions", []),
                description=s.get("description", ""),
            )
            for s in data["add_scarcities"]
        ]

    if "update_global_gdp_trend" in data:
        mutation.update_global_gdp_trend = data["update_global_gdp_trend"]

    for tech_key in ("update_ai", "update_energy", "update_biotech"):
        if tech_key in data:
            val = data[tech_key]
            if isinstance(val, str):
                # LLM returned a prose string; wrap it as a description update
                logger.warning(
                    "LLM returned string for %s, coercing to dict", tech_key
                )
                val = {"description": val}
            if isinstance(val, dict):
                setattr(mutation, tech_key, val)

    if "add_tech_domains" in data:
        mutation.add_tech_domains = [
            TechDomain(
                name=t["name"],
                maturity_level=t.get("maturity_level", "emerging"),
                key_players=t.get("key_players", []),
                description=t.get("description", ""),
            )
            for t in data["add_tech_domains"]
        ]

    if "add_dominant_narratives" in data:
        mutation.add_dominant_narratives = data["add_dominant_narratives"]

    if "add_movements" in data:
        mutation.add_movements = [
            CulturalMovement(
                name=m["name"],
                reach=m.get("reach", "local"),
                description=m.get("description", ""),
            )
            for m in data["add_movements"]
        ]

    if "update_media_landscape" in data:
        mutation.update_media_landscape = data["update_media_landscape"]

    if "add_forces" in data:
        mutation.add_forces = [
            MilitaryForce(
                entity=f["entity"],
                conventional_strength=f.get("conventional_strength", 50),
                nuclear_capable=f.get("nuclear_capable", False),
                special_capabilities=f.get("special_capabilities", []),
            )
            for f in data["add_forces"]
        ]

    if "update_forces" in data:
        mutation.update_forces = data["update_forces"]

    if "add_arms_races" in data:
        mutation.add_arms_races = data["add_arms_races"]

    if "add_doctrine_shifts" in data:
        mutation.add_doctrine_shifts = data["add_doctrine_shifts"]

    if "update_temperature_anomaly" in data:
        mutation.update_temperature_anomaly = data[
            "update_temperature_anomaly"
        ]

    if "add_crises" in data:
        mutation.add_crises = [
            EnvironmentalCrisis(
                name=c["name"],
                severity=c.get("severity", "moderate"),
                affected_regions=c.get("affected_regions", []),
                description=c.get("description", ""),
            )
            for c in data["add_crises"]
        ]

    if "add_mitigation_efforts" in data:
        mutation.add_mitigation_efforts = data["add_mitigation_efforts"]

    if "add_story_threads" in data:
        mutation.add_story_threads = [
            StoryThread(
                name=t["name"],
                status=t.get("status", "developing"),
                started=t.get("started", ""),
                last_covered=t.get("last_covered", ""),
                summary=t.get("summary", ""),
                related_nations=t.get("related_nations", []),
                sectors=t.get("sectors", []),
            )
            for t in data["add_story_threads"]
        ]

    if "update_story_threads" in data:
        mutation.update_story_threads = data["update_story_threads"]

    if "add_historical_events" in data:
        mutation.add_historical_events = [
            HistoricalEvent(
                date=e["date"],
                headline=e["headline"],
                description=e.get("description", ""),
                impact=e.get("impact", ""),
                sectors=e.get("sectors", []),
            )
            for e in data["add_historical_events"]
        ]

    return mutation

@monitor(monitor_slug="morning-press", monitor_config=_MONITOR_CONFIG)
def cli_main() -> None:
    """CLI entry point for Cloud Run Job execution."""
    configure_logging()

    db_url = os.getenv("DATABASE_URL", DATABASE_URL)

    # Choose generation strategy based on environment
    if VERTEX_AI_PROJECT:
        gen: GenerationStrategy = VertexAIStrategy(
            project=VERTEX_AI_PROJECT,
            location=VERTEX_AI_LOCATION,
        )
    else:
        logger.warning(
            "VERTEX_AI_PROJECT not set, using StubGenerationStrategy"
        )
        gen = StubGenerationStrategy()

    # Choose storage backend
    store: EditionStorage
    if R2_ACCOUNT_ID:
        from .r2_storage import R2EditionStorage

        store = R2EditionStorage()
    else:
        logger.warning("R2_ACCOUNT_ID not set, using StubEditionStorage")
        store = StubEditionStorage()

    # Choose image generation backend
    enable_images = os.getenv("ENABLE_IMAGES", "true").lower() == "true"
    img_client: ImageGenerationStrategy
    if enable_images and VERTEX_AI_PROJECT:
        from .image_gen import ImagenClient

        img_client = ImagenClient(
            project=VERTEX_AI_PROJECT,
            location=IMAGE_GENERATION_LOCATION,
        )
    else:
        if not enable_images:
            logger.info("Image generation disabled via ENABLE_IMAGES=false")
        img_client = StubImageClient(should_fail=not enable_images)

    summary = run_morning_press(
        database_url=db_url,
        generation_strategy=gen,
        storage=store,
        imagen_client=img_client,
    )

    logger.info("Pipeline finished", extra={"summary": summary})
    if summary["edition_id"] is None:
        sys.exit(0)


if __name__ == "__main__":
    cli_main()
