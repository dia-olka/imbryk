"""Imbryk Morning Press — AI newspaper generation orchestrator.

Orchestrates the daily newspaper generation pipeline:
1. Fetch unprocessed paid prompts from DB
2. Load/initialise WorldLedger
3. Route prompts to newspapers via taxonomy
4. Serialize WorldLedger synopsis
5. Run coherence validation on prompts
6. Run distillation pipeline per newspaper
7. Generate articles via Gemini (per persona)
8. Run Curator synthesis
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

import sentry_sdk
from sentry_sdk.crons import monitor
from sentry_sdk.integrations.logging import LoggingIntegration

from .config import (
    CF_DEPLOY_HOOK_URL,
    DATABASE_URL,
    LOG_LEVEL_INT,
    R2_ACCOUNT_ID,
    SENTRY_DSN,
    VERTEX_AI_LOCATION,
    VERTEX_AI_PROJECT,
)

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=1.0,  # Capture 100% of transactions for performance monitoring
        send_default_pii=False,
        integrations=[
            LoggingIntegration(
                level=LOG_LEVEL_INT,  # Capture logs at configured level or higher
                event_level=logging.ERROR,  # Send only ERROR logs as Sentry events
            ),
        ],
    )
    logging.captureWarnings(True)  # Route warnings.warn() through logging so Sentry sees them
from .db import (
    fetch_unprocessed_prompts,
    get_engine,
    get_session_factory,
    load_world_ledger,
    mark_prompts_processed,
    save_edition,
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
from .personas import (
    CURATOR_PERSONA,
    NEWSPAPER_PERSONAS,
)
from .storage import EditionStorage, StubEditionStorage
from .taxonomy import route_prompt
from .validation import validate_prompts
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
    "max_runtime": 60*60*60,  # 1 hour
    "failure_issue_threshold": 1,
    "recovery_threshold": 1,
}

def run_morning_press(
    database_url: str | None = None,
    generation_strategy: GenerationStrategy | None = None,
    storage: EditionStorage | None = None,
    distillation_pipeline: DistillationPipeline | None = None,
    imagen_client: ImageGenerationStrategy | None = None,
    enable_validation: bool = True,
) -> dict:
    """Execute the full Morning Press generation pipeline.

    Args:
        database_url: Override for the database connection string.
        generation_strategy: LLM generation backend (defaults to stub).
        storage: Edition output storage (defaults to stub).
        distillation_pipeline: Override for the distillation pipeline.
        imagen_client: Image generation backend (defaults to stub).
        enable_validation: Run coherence validation on prompts.

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

    try:
        # Step 2: Fetch unprocessed prompts
        prompt_records = fetch_unprocessed_prompts(session)
        logger.info(
            "Fetched prompts",
            extra={"step": "fetch", "cluster_count": len(prompt_records)},
        )

        if not prompt_records:
            logger.info("No unprocessed prompts found, skipping edition")
            return {
                "edition_id": None,
                "newspaper_count": 0,
                "article_count": 0,
            }

        # Step 3: Load WorldLedger from DB (or use initial)
        ledger_dict = load_world_ledger(session)
        if ledger_dict is not None:
            ledger = ledger_from_dict(ledger_dict)
        else:
            ledger = INITIAL_WORLD_LEDGER

        # Step 4: Serialize WorldLedger to synopsis
        synopsis = serialize_ledger_to_synopsis(ledger)

        # Step 5: Coherence validation — filter prompts against world state
        if enable_validation:
            prompt_records = validate_prompts(
                prompt_records, synopsis, gen
            )
            if not prompt_records:
                logger.info(
                    "All prompts rejected by coherence validation, "
                    "skipping edition"
                )
                return {
                    "edition_id": None,
                    "newspaper_count": 0,
                    "article_count": 0,
                }

        # Step 6: Route prompts to newspapers
        newspaper_prompts: dict[str, list] = defaultdict(list)
        for pr in prompt_records:
            routes = route_prompt(pr.category_ids)
            for route in routes:
                newspaper_prompts[route.newspaper_id].append(pr)

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
                # Convert to distillation Prompt objects
                dist_prompts = [
                    DistillationPrompt(
                        text=pr.text,
                        payment_amount=pr.payment_amount,
                        prompt_id=pr.prompt_id,
                    )
                    for pr in prompts_for_paper
                ]

                # Run distillation pipeline
                budgeted = pipeline.run(dist_prompts)
                digests_text = pipeline.serialize_all(budgeted)

                # System instruction: persona identity + world context
                system_instruction = persona.system_prompt_template.replace(
                    "{{WORLD_LEDGER_SYNOPSIS}}", synopsis
                ).replace("{{CLUSTER_DIGESTS}}", "[See user content below]")

                # User content: cluster digests (may contain verbatim user prompts)
                user_content = f"CLUSTER DIGESTS:\n{digests_text}\n\nGenerate today's edition."

                # Call LLM
                gen_start = time.monotonic()
                article = gen.generate(system_instruction, persona.model_tier, user_content)
                gen_ms = int((time.monotonic() - gen_start) * 1000)

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
                curator_system = CURATOR_PERSONA.system_prompt_template.replace(
                    "{{ALL_ARTICLES}}", "[See user content below]"
                )
                curator_content = f"TODAY'S ARTICLES:\n{all_articles_text}\n\nGenerate today's synthesis."
                curator_article = gen.generate(
                    curator_system, CURATOR_PERSONA.model_tier, curator_content
                )
                articles["curator"] = curator_article
            except Exception:
                logger.exception(
                    "Curator synthesis failed, skipping curator article"
                )

        # Step 9: WorldLedger mutation via LLM
        if articles:
            try:
                mutation_system, mutation_content = _build_mutation_prompt(synopsis, articles)
                mutation_response = gen.generate(mutation_system, "pro", mutation_content)
                mutation = _parse_mutation(mutation_response)
                if mutation:
                    ledger = apply_mutation(ledger, mutation)
                    save_world_ledger(session, ledger_to_dict(ledger))
            except Exception:
                logger.exception(
                    "WorldLedger mutation failed, skipping world state update"
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
            article_list = parsed.get("articles", [])
            front_page_prompt = parsed.get("frontPageImagePrompt")

            result = generate_images_for_newspaper(
                newspaper_id=newspaper_id,
                articles=article_list,
                front_page_image_prompt=front_page_prompt,
                imagen_client=img_client,
                storage=store,
                edition_id=str(
                    datetime.now(timezone.utc).strftime("%Y-%m-%d")
                ),
            )

            # Embed image URLs into articles
            for idx, url in result.article_image_urls.items():
                if idx < len(article_list):
                    article_list[idx]["image_url"] = url
                    image_counts += 1
            if result.hero_image_url:
                parsed["heroImageUrl"] = result.hero_image_url
                image_counts += 1

            # Re-serialize back to JSON string
            articles[newspaper_id] = json.dumps(
                parsed, ensure_ascii=False
            )

        logger.info(
            "Image generation complete",
            extra={"step": "images", "image_count": image_counts},
        )

        # Step 10: Save edition to DB
        edition_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        edition_id = save_edition(session, edition_date, articles)

        # Step 11: Write edition to storage
        store.write_edition(edition_id, edition_date, articles)

        # Step 12: Mark prompts as processed
        prompt_ids = [pr.prompt_id for pr in prompt_records]
        mark_prompts_processed(session, prompt_ids)

        session.commit()

        # Step 13: Write index manifest to R2
        _write_edition_index(store, edition_id, edition_date, articles)

        # Step 14: Trigger gazette rebuild via Cloudflare deploy hook
        _trigger_deploy_hook()

        # Step 15: Backfill missing images from previous editions (best-effort).
        # Runs after today's edition is committed and published so a slow
        # Imagen backfill cannot delay the current edition reaching readers.
        try:
            from .config import MAX_BACKFILL_IMAGES_PER_RUN
            from .image_gen.backfill import run_image_backfill

            run_image_backfill(
                session=session,
                today_date=edition_date,
                imagen_client=img_client,
                storage=store,
                max_images_per_run=MAX_BACKFILL_IMAGES_PER_RUN,
            )
        except Exception:
            logger.warning(
                "Image backfill step failed, today's edition unaffected",
                exc_info=True,
            )

        total_ms = int((time.monotonic() - start_time) * 1000)
        summary = {
            "edition_id": edition_id,
            "newspaper_count": len(
                [k for k in articles if k != "curator"]
            ),
            "article_count": len(articles),
            "latency_ms": total_ms,
        }

        logger.info(
            "Edition complete",
            extra={
                "step": "complete",
                "edition_id": edition_id,
                "latency_ms": total_ms,
            },
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


def _try_parse_edition_json(content: str) -> dict | None:
    """Attempt to parse a newspaper edition content string as JSON.

    The Gemini output may be raw JSON or wrapped in markdown code fences.
    Returns the parsed dict, or None if parsing fails.
    """
    text = content.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]  # remove opening fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        logger.warning(
            "Could not parse newspaper content as JSON for image generation"
        )
        return None


def _build_mutation_prompt(
    synopsis: str, articles: dict[str, str]
) -> tuple[str, str]:
    """Build a system instruction + user content for WorldLedger mutation."""
    articles_text = _format_all_articles(articles)

    system_instruction = """\
You are a world-state updater. Given the current world state and today's \
newspaper articles, produce a JSON object describing changes to the world \
ledger. Only include fields that should change.

The mutation JSON should follow this schema (all fields optional):
- synopsis: string (updated world synopsis)
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
sectors}}

Respond with ONLY the JSON mutation object, no explanation."""

    user_content = f"""\
CURRENT WORLD STATE:
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
            "Failed to parse WorldLedger mutation from LLM response"
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
            location=VERTEX_AI_LOCATION,
        )
    else:
        if not enable_images:
            logger.info("Image generation disabled via ENABLE_IMAGES=false")
        img_client = StubImageClient(should_fail=not enable_images)

    enable_validation = os.getenv("ENABLE_VALIDATION", "true").lower() == "true"

    summary = run_morning_press(
        database_url=db_url,
        generation_strategy=gen,
        storage=store,
        imagen_client=img_client,
        enable_validation=enable_validation,
    )

    logger.info("Pipeline finished", extra={"summary": summary})
    if summary["edition_id"] is None:
        sys.exit(0)


if __name__ == "__main__":
    cli_main()
