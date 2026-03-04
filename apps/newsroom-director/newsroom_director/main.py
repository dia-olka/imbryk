"""Imbryk Morning Press — AI newspaper generation orchestrator.

Orchestrates the daily newspaper generation pipeline:
1. Fetch unprocessed paid prompts from DB
2. Load/initialise WorldLedger
3. Route prompts to n ewspapers via taxonomy
4. Serialize WorldLedger synopsis & create context cache
5. Run coherence validation on prompts
6. Run distillation pipeline per newspaper
7. Generate articles via Gemini (per persona)
8. Run Curator synthesis
9. Apply WorldLedger mutation
10. Save edition and mark prompts processed
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

from .config import (
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
        traces_sample_rate=0.1,
        send_default_pii=False,
        integrations=[
            sentry_sdk.integrations.logging.LoggingIntegration(
                level=LOG_LEVEL_INT,  # Capture logs at configured level or higher
                event_level=logging.ERROR,  # Send only ERROR logs as Sentry events
            ),
        ],
    )
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


def run_morning_press(
    database_url: str | None = None,
    generation_strategy: GenerationStrategy | None = None,
    storage: EditionStorage | None = None,
    distillation_pipeline: DistillationPipeline | None = None,
    enable_validation: bool = True,
    enable_caching: bool = True,
) -> dict:
    """Execute the full Morning Press generation pipeline.

    Args:
        database_url: Override for the database connection string.
        generation_strategy: LLM generation backend (defaults to stub).
        storage: Edition output storage (defaults to stub).
        distillation_pipeline: Override for the distillation pipeline.
        enable_validation: Run coherence validation on prompts.
        enable_caching: Use Vertex AI context caching when available.

    Returns:
        Summary dict with edition_id, newspaper_count, article_count.
    """
    configure_logging()
    start_time = time.monotonic()

    db_url = database_url or DATABASE_URL
    gen = generation_strategy or StubGenerationStrategy()
    store = storage or StubEditionStorage()
    pipeline = distillation_pipeline or DistillationPipeline()

    # Step 1: Connect to DB
    engine = get_engine(db_url)
    session_factory = get_session_factory(engine)
    session = session_factory()

    cached_content = None

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

        # Step 4b: Create context cache for synopsis (shared across newspapers).
        # Falls back to uncached generation if cache creation fails.
        if enable_caching:
            try:
                cached_content = gen.create_cache(synopsis)
            except Exception:
                logger.warning(
                    "Context cache creation failed, falling back to uncached generation",
                    exc_info=True,
                )

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

                # Build the user prompt with cluster digests for this newspaper
                user_prompt = persona.system_prompt_template.replace(
                    "{{WORLD_LEDGER_SYNOPSIS}}", synopsis
                ).replace("{{CLUSTER_DIGESTS}}", digests_text)

                # Call LLM — use cached generation when cache is available
                gen_start = time.monotonic()
                if cached_content is not None:
                    article = gen.generate_with_cache(
                        cached_content, user_prompt, persona.model_tier
                    )
                else:
                    article = gen.generate(user_prompt, persona.model_tier)
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
            all_articles_text = _format_all_articles(articles)
            curator_prompt = CURATOR_PERSONA.system_prompt_template.replace(
                "{{ALL_ARTICLES}}", all_articles_text
            )
            curator_article = gen.generate(
                curator_prompt, CURATOR_PERSONA.model_tier
            )
            articles["curator"] = curator_article

        # Step 9: WorldLedger mutation via LLM
        if articles:
            mutation_prompt = _build_mutation_prompt(synopsis, articles)
            mutation_response = gen.generate(mutation_prompt, "pro")
            mutation = _parse_mutation(mutation_response)
            if mutation:
                ledger = apply_mutation(ledger, mutation)
                save_world_ledger(session, ledger_to_dict(ledger))

        # Step 10: Save edition to DB
        edition_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        edition_id = save_edition(session, edition_date, articles)

        # Step 11: Write edition to storage
        store.write_edition(edition_id, edition_date, articles)

        # Step 12: Mark prompts as processed
        prompt_ids = [pr.prompt_id for pr in prompt_records]
        mark_prompts_processed(session, prompt_ids)

        session.commit()

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
        # Force-delete context cache to avoid stale billing
        if cached_content is not None:
            gen.delete_cache(cached_content)
        session.close()


def _format_all_articles(articles: dict[str, str]) -> str:
    """Format all newspaper articles for the Curator prompt."""
    sections = []
    for newspaper_id, content in articles.items():
        sections.append(f"=== {newspaper_id.upper()} ===\n{content}")
    return "\n\n".join(sections)


def _build_mutation_prompt(
    synopsis: str, articles: dict[str, str]
) -> str:
    """Build a prompt asking the LLM to produce a WorldLedger mutation."""
    articles_text = _format_all_articles(articles)
    return f"""\
You are a world-state updater. Given the current world state and today's \
newspaper articles, produce a JSON object describing changes to the world \
ledger. Only include fields that should change.

The mutation JSON should follow this schema (all fields optional):
- synopsis: string (updated world synopsis)
- add_nations: list of new nations
- update_nations: list of {{name, ...fields_to_update}}
- add_alliances, add_conflicts, update_conflicts
- add_currencies, add_trading_blocs, add_scarcities
- update_global_gdp_trend: string
- update_ai, update_energy, update_biotech: partial tech domain updates
- add_dominant_narratives: list of strings
- add_movements: list of {{name, reach, description}}
- update_media_landscape: string
- add_forces, update_forces
- add_arms_races, add_doctrine_shifts: lists of strings
- update_temperature_anomaly: float
- add_crises, add_mitigation_efforts
- add_historical_events: list of {{date, headline, description, impact, \
sectors}}

CURRENT WORLD STATE:
{synopsis}

TODAY'S ARTICLES:
{articles_text}

Respond with ONLY the JSON mutation object, no explanation."""


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
            setattr(mutation, tech_key, data[tech_key])

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

    enable_validation = os.getenv("ENABLE_VALIDATION", "true").lower() == "true"
    enable_caching = os.getenv("ENABLE_CACHING", "true").lower() == "true"

    summary = run_morning_press(
        database_url=db_url,
        generation_strategy=gen,
        storage=store,
        enable_validation=enable_validation,
        enable_caching=enable_caching,
    )

    logger.info("Pipeline finished", extra={"summary": summary})
    if summary["edition_id"] is None:
        sys.exit(0)


if __name__ == "__main__":
    cli_main()
