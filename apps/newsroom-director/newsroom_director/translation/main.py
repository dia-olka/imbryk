"""Translation orchestrator — translates all articles for system languages.

Entry point for the JOB_MODE=translate Cloud Run Job.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from ..config import (
    AZURE_TRANSLATOR_KEY,
    AZURE_TRANSLATOR_REGION,
    CF_DEPLOY_HOOK_URL,
    DATABASE_URL,
    R2_ACCOUNT_ID,
    TRANSLATION_BACKFILL,
    TRANSLATION_CHAR_BUDGET,
    TRANSLATION_ENABLED,
    TRANSLATION_PROVIDER,
)
from ..db import (
    get_engine,
    get_session_factory,
    load_edition_by_date,
    load_world_ledger,
)
from ..logging_config import configure_logging
from ..storage import EditionStorage, StubEditionStorage
from .budget import TranslationBudget
from .client import StubTranslationClient, TranslationResult, TranslationStrategy

logger = logging.getLogger(__name__)


def _load_system_languages() -> list[dict]:
    """Load system language definitions from data/languages.json."""
    languages_path = Path(__file__).resolve().parents[4] / "data" / "languages.json"
    if not languages_path.exists():
        logger.warning("data/languages.json not found at %s", languages_path)
        return []
    with open(languages_path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("system", [])


def _extract_articles(content_json: str) -> list[dict]:
    """Extract all articles from a newspaper's content JSON.

    Returns a list of dicts with keys: original_index, headline, body, imageAlt.
    """
    try:
        parsed = json.loads(content_json)
    except (json.JSONDecodeError, TypeError):
        return []

    articles = parsed.get("articles", [])
    result: list[dict] = []
    for i, article in enumerate(articles):
        headline = article.get("headline", "")
        body = article.get("body", "")
        if not headline and not body:
            continue
        result.append({
            "original_index": i,
            "headline": headline,
            "body": body,
            "imageAlt": article.get("imageAlt", ""),
        })
    return result


def _batch_texts_for_article(article: dict) -> list[tuple[str, str]]:
    """Return (field_name, text) pairs for a single article to translate."""
    pairs: list[tuple[str, str]] = []
    if article.get("headline"):
        pairs.append(("headline", article["headline"]))
    if article.get("body"):
        pairs.append(("body", article["body"]))
    if article.get("imageAlt"):
        pairs.append(("imageAlt", article["imageAlt"]))
    return pairs


def run_backfill(
    database_url: str | None = None,
    storage: EditionStorage | None = None,
    translator: TranslationStrategy | None = None,
) -> dict:
    """Backfill translations for all historical editions.

    Reads the R2 edition index, iterates newest-first, and translates
    any missing (edition, language) pairs.  Budget-aware: stops when the
    monthly character cap is reached.

    Returns:
        Summary dict with total counts across all editions.
    """
    start_time = time.monotonic()

    db_url = database_url or DATABASE_URL
    store = storage or StubEditionStorage()
    trans = translator or StubTranslationClient()

    languages = _load_system_languages()
    if not languages:
        logger.info("No system languages configured, skipping backfill")
        return {"editions_processed": 0, "translations_written": 0, "reason": "no_languages"}

    lang_codes = [lang["code"] for lang in languages]
    logger.info(
        "Backfill starting | languages=%s | provider=%s",
        lang_codes, trans.provider_name,
    )

    # Read the full edition index from R2
    try:
        index = store.read_json("editions/index.json")
    except Exception:
        logger.error("Failed to read editions/index.json from R2", exc_info=True)
        return {"editions_processed": 0, "translations_written": 0, "reason": "index_read_error"}

    if not index or not isinstance(index, list):
        logger.warning("No editions found in R2 index")
        return {"editions_processed": 0, "translations_written": 0, "reason": "empty_index"}

    # Sort newest-first so the most recent editions get translated first
    index.sort(key=lambda e: e.get("date", ""), reverse=True)

    # Shared budget tracker across all editions
    budget_limit = int(TRANSLATION_CHAR_BUDGET) if TRANSLATION_CHAR_BUDGET else None
    budget = TranslationBudget(store, trans.provider_name, budget_limit)

    engine = get_engine(db_url)
    session_factory = get_session_factory(engine)

    editions_processed = 0
    total_translations = 0
    total_chars = 0
    budget_exhausted = False

    for entry in index:
        edition_date = entry.get("date")
        edition_id = entry.get("edition_id")
        if not edition_date or not edition_id:
            continue

        if budget_exhausted:
            break

        edition_translations = 0

        for lang in languages:
            lang_code = lang["code"]
            r2_key = f"editions/{edition_date}/translations/{lang_code}/{edition_id}.json"

            # Skip if translation already exists
            existing = store.read_json(r2_key)
            if existing is not None:
                continue

            # Load edition articles from DB
            session = session_factory()
            try:
                edition_articles = load_edition_by_date(session, edition_date)
            finally:
                session.close()

            if not edition_articles:
                logger.info("No DB edition for %s, skipping", edition_date)
                break  # no point trying other languages for this date

            # Extract articles
            articles_by_newspaper: dict[str, list[dict]] = {}
            for newspaper_id, content_json in edition_articles.items():
                if newspaper_id == "curator":
                    continue
                articles = _extract_articles(content_json)
                if articles:
                    articles_by_newspaper[newspaper_id] = articles

            if not articles_by_newspaper:
                break

            # Collect texts
            all_texts: list[str] = []
            text_map: list[tuple[str, int, str]] = []

            for newspaper_id, articles in articles_by_newspaper.items():
                for article in articles:
                    for field_name, text in _batch_texts_for_article(article):
                        all_texts.append(text)
                        text_map.append((newspaper_id, article["original_index"], field_name))

            if not all_texts:
                continue

            total_batch_chars = sum(len(t) for t in all_texts)

            if budget.would_exceed(total_batch_chars):
                logger.warning(
                    "Budget exhausted during backfill at %s/%s (%d remaining)",
                    edition_date, lang_code, budget.remaining(),
                )
                budget_exhausted = True
                break

            # Translate
            results = _translate_all(trans, all_texts, lang_code)

            # Assemble translation JSON
            translated_articles: dict[str, list[dict]] = {}
            chars_used = 0

            for i, result in enumerate(results):
                if result is None:
                    continue
                newspaper_id, original_index, field_name = text_map[i]
                if newspaper_id not in translated_articles:
                    translated_articles[newspaper_id] = []

                entry_item = None
                for existing_entry in translated_articles[newspaper_id]:
                    if existing_entry["original_index"] == original_index:
                        entry_item = existing_entry
                        break
                if entry_item is None:
                    entry_item = {"original_index": original_index}
                    translated_articles[newspaper_id].append(entry_item)

                entry_item[field_name] = result.translated_text
                chars_used += result.chars_used

            if not translated_articles:
                continue

            translation_payload = {
                "edition_id": edition_id,
                "date": edition_date,
                "lang": lang_code,
                "provider": trans.provider_name,
                "translated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "articles": translated_articles,
            }

            store.write_raw(
                r2_key,
                json.dumps(translation_payload, ensure_ascii=False).encode("utf-8"),
                "application/json",
            )

            budget.record_usage(chars_used)
            total_chars += chars_used
            edition_translations += 1

            logger.info(
                "Backfill: translated %s/%s | %d newspapers, %d chars",
                edition_date, lang_code,
                len(translated_articles), chars_used,
            )

        if edition_translations > 0:
            editions_processed += 1
            total_translations += edition_translations

    # Also backfill timeline translations (idempotency built in)
    timeline_written = _translate_timeline(
        session_factory=session_factory,
        store=store,
        translator=trans,
        budget=budget,
        languages=languages,
    )
    total_translations += timeline_written

    # Trigger rebuild if anything was written
    if total_translations > 0:
        _trigger_deploy_hook()

    total_ms = int((time.monotonic() - start_time) * 1000)
    summary = {
        "mode": "backfill",
        "editions_processed": editions_processed,
        "translations_written": total_translations,
        "total_chars": total_chars,
        "budget_exhausted": budget_exhausted,
        "provider": trans.provider_name,
        "latency_ms": total_ms,
    }
    logger.info(
        "Backfill complete: %d editions, %d translations, %d chars in %.1fs%s",
        editions_processed, total_translations, total_chars, total_ms / 1000,
        " (budget exhausted)" if budget_exhausted else "",
        extra={"step": "backfill_complete", **summary},
    )
    return summary


def run_translation(
    database_url: str | None = None,
    storage: EditionStorage | None = None,
    translator: TranslationStrategy | None = None,
    edition_date: str | None = None,
) -> dict:
    """Execute the translation pipeline.

    Translates all articles for every system language defined in
    data/languages.json.

    Args:
        database_url: Override for the database connection string.
        storage: R2 storage backend.
        translator: Translation provider backend.
        edition_date: Target edition date (defaults to today UTC).

    Returns:
        Summary dict with counts of translations produced.
    """
    start_time = time.monotonic()

    db_url = database_url or DATABASE_URL
    store = storage or StubEditionStorage()
    trans = translator or StubTranslationClient()

    from ..config import EDITION_DATE

    today = edition_date or EDITION_DATE or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Load system languages
    languages = _load_system_languages()
    if not languages:
        logger.info("No system languages configured, skipping translation")
        return {"edition_date": today, "translations_written": 0, "reason": "no_languages"}

    lang_codes = [lang["code"] for lang in languages]
    logger.info(
        "Translation job starting for %s | languages=%s | provider=%s",
        today, lang_codes, trans.provider_name,
        extra={"step": "start", "edition_date": today},
    )

    # Load today's edition from DB
    engine = get_engine(db_url)
    session_factory = get_session_factory(engine)
    session = session_factory()

    try:
        edition_articles = load_edition_by_date(session, today)
    finally:
        session.close()

    if not edition_articles:
        logger.info("No edition found for %s, skipping translation", today)
        return {"edition_date": today, "translations_written": 0, "reason": "no_edition"}

    # Find the edition_id from R2 (needed for file paths)
    edition_id = _find_edition_id(store, today)
    if not edition_id:
        logger.warning("Could not find edition_id in R2 for %s", today)
        return {"edition_date": today, "translations_written": 0, "reason": "no_edition_in_r2"}

    # Extract all articles per newspaper (skip curator)
    articles_by_newspaper: dict[str, list[dict]] = {}
    for newspaper_id, content_json in edition_articles.items():
        if newspaper_id == "curator":
            continue
        articles = _extract_articles(content_json)
        if articles:
            articles_by_newspaper[newspaper_id] = articles

    if not articles_by_newspaper:
        logger.info("No articles found to translate for %s", today)
        return {"edition_date": today, "translations_written": 0, "reason": "no_articles"}

    # Budget tracker
    budget_limit = int(TRANSLATION_CHAR_BUDGET) if TRANSLATION_CHAR_BUDGET else None
    budget = TranslationBudget(store, trans.provider_name, budget_limit)

    translations_written = 0
    total_chars = 0

    for lang in languages:
        lang_code = lang["code"]
        r2_key = f"editions/{today}/translations/{lang_code}/{edition_id}.json"

        # Idempotency: skip if translation already exists
        existing = store.read_json(r2_key)
        if existing is not None:
            logger.info(
                "Translation already exists for %s/%s, skipping",
                today, lang_code,
            )
            continue

        # Collect all texts to translate for this language
        all_texts: list[str] = []
        text_map: list[tuple[str, int, str]] = []  # (newspaper_id, article_idx, field)

        for newspaper_id, articles in articles_by_newspaper.items():
            for article in articles:
                for field_name, text in _batch_texts_for_article(article):
                    all_texts.append(text)
                    text_map.append((newspaper_id, article["original_index"], field_name))

        if not all_texts:
            continue

        total_batch_chars = sum(len(t) for t in all_texts)

        # Check budget
        if budget.would_exceed(total_batch_chars):
            logger.warning(
                "Translation budget would be exceeded for %s/%s (%d chars, %d remaining)",
                today, lang_code, total_batch_chars, budget.remaining(),
                extra={"step": "budget_exceeded", "lang": lang_code},
            )
            continue

        # Translate in batches respecting provider limits
        results = _translate_all(trans, all_texts, lang_code)

        # Assemble translation JSON
        translated_articles: dict[str, list[dict]] = {}
        chars_used = 0

        for i, result in enumerate(results):
            if result is None:
                continue
            newspaper_id, original_index, field_name = text_map[i]
            # Find or create the article entry
            if newspaper_id not in translated_articles:
                translated_articles[newspaper_id] = []

            # Find existing entry for this original_index
            entry = None
            for existing_entry in translated_articles[newspaper_id]:
                if existing_entry["original_index"] == original_index:
                    entry = existing_entry
                    break
            if entry is None:
                entry = {"original_index": original_index}
                translated_articles[newspaper_id].append(entry)

            entry[field_name] = result.translated_text
            chars_used += result.chars_used

        if not translated_articles:
            logger.warning("All translations failed for %s/%s", today, lang_code)
            continue

        # Write translation JSON to R2
        translation_payload = {
            "edition_id": edition_id,
            "date": today,
            "lang": lang_code,
            "provider": trans.provider_name,
            "translated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "articles": translated_articles,
        }

        store.write_raw(
            r2_key,
            json.dumps(translation_payload, ensure_ascii=False).encode("utf-8"),
            "application/json",
        )

        budget.record_usage(chars_used)
        total_chars += chars_used
        translations_written += 1

        logger.info(
            "Translation written: %s/%s | %d newspapers, %d chars",
            today, lang_code,
            len(translated_articles), chars_used,
            extra={
                "step": "translation_written",
                "lang": lang_code,
                "chars_used": chars_used,
            },
        )

    # Translate world history timeline
    timeline_written = _translate_timeline(
        session_factory=session_factory,
        store=store,
        translator=trans,
        budget=budget,
        languages=languages,
    )
    translations_written += timeline_written

    # Trigger gazette rebuild if we wrote any translations
    if translations_written > 0:
        _trigger_deploy_hook()

    total_ms = int((time.monotonic() - start_time) * 1000)
    summary = {
        "edition_date": today,
        "translations_written": translations_written,
        "languages_attempted": len(languages),
        "total_chars": total_chars,
        "provider": trans.provider_name,
        "latency_ms": total_ms,
    }
    logger.info(
        "Translation job complete: %d/%d languages in %.1fs (%d chars)",
        translations_written, len(languages), total_ms / 1000, total_chars,
        extra={"step": "complete", **summary},
    )
    return summary


def _translate_timeline(
    *,
    session_factory,
    store: EditionStorage,
    translator: TranslationStrategy,
    budget: TranslationBudget,
    languages: list[dict],
) -> int:
    """Translate world history timeline events for all system languages.

    Reads the canonical world ledger from DB, translates epoch, synopsis,
    and each historical event's headline/description/impact, then writes
    to R2 at translations/_meta/timeline-{lang}.json.

    Returns the number of timeline translations written.
    """
    session = session_factory()
    try:
        ledger_dict = load_world_ledger(session)
    finally:
        session.close()

    if not ledger_dict:
        # Fall back to initial world state (raw dict from codegen)
        from ..world_ledger._generated_world_state import WORLD_STATE_DATA

        ledger_dict = WORLD_STATE_DATA

    history = ledger_dict.get("history", [])
    if not history:
        logger.info("No world history events to translate")
        return 0

    epoch = ledger_dict.get("epoch", "")
    synopsis = ledger_dict.get("synopsis", "")
    written = 0

    for lang in languages:
        lang_code = lang["code"]
        r2_key = f"translations/_meta/timeline-{lang_code}.json"

        # Idempotency: skip if already exists
        existing = store.read_json(r2_key)
        if existing is not None:
            logger.info("Timeline translation already exists for %s, skipping", lang_code)
            continue

        # Collect texts: epoch, synopsis, then per-event headline/description/impact
        texts: list[str] = []
        text_map: list[tuple[str, int]] = []  # (field, event_index or -1 for top-level)

        if epoch:
            texts.append(epoch)
            text_map.append(("epoch", -1))
        if synopsis:
            texts.append(synopsis)
            text_map.append(("synopsis", -1))

        for i, event in enumerate(history):
            for field_name in ("headline", "description", "impact"):
                text = event.get(field_name, "")
                if text:
                    texts.append(text)
                    text_map.append((field_name, i))

        if not texts:
            continue

        total_chars = sum(len(t) for t in texts)
        if budget.would_exceed(total_chars):
            logger.warning(
                "Budget exceeded for timeline/%s (%d chars)",
                lang_code, total_chars,
            )
            continue

        results = _translate_all(translator, texts, lang_code)

        # Assemble translated timeline
        translated_epoch = ""
        translated_synopsis = ""
        # Deep-copy history events (keep date, sectors untranslated)
        translated_history = [
            {
                "date": event.get("date", ""),
                "headline": event.get("headline", ""),
                "description": event.get("description", ""),
                "impact": event.get("impact", ""),
                "sectors": event.get("sectors", []),
            }
            for event in history
        ]

        chars_used = 0
        for j, result in enumerate(results):
            if result is None:
                continue
            field_name, event_index = text_map[j]
            if event_index == -1:
                if field_name == "epoch":
                    translated_epoch = result.translated_text
                elif field_name == "synopsis":
                    translated_synopsis = result.translated_text
            else:
                translated_history[event_index][field_name] = result.translated_text
            chars_used += result.chars_used

        # Write to R2
        payload = {
            "lang": lang_code,
            "provider": translator.provider_name,
            "translated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "title": "World History",  # Will be translated in UI strings
            "epoch": translated_epoch or epoch,
            "synopsis": translated_synopsis or synopsis,
            "history": translated_history,
        }

        store.write_raw(
            r2_key,
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            "application/json",
        )

        budget.record_usage(chars_used)
        written += 1
        logger.info(
            "Timeline translation written: %s | %d events, %d chars",
            lang_code, len(translated_history), chars_used,
        )

    return written


def _find_edition_id(store: EditionStorage, date: str) -> str | None:
    """Find the edition_id for a given date by reading the R2 index."""
    try:
        index = store.read_json("editions/index.json")
        if index and isinstance(index, list):
            for entry in index:
                if entry.get("date") == date:
                    return entry.get("edition_id")
    except Exception:
        logger.warning("Failed to read edition index from R2", exc_info=True)
    return None


def _translate_all(
    translator: TranslationStrategy,
    texts: list[str],
    target_lang: str,
) -> list[TranslationResult | None]:
    """Translate all texts, respecting provider batch limits."""
    results: list[TranslationResult | None] = []
    batch_size = translator.max_batch_size
    max_chars = translator.max_chars_per_request

    i = 0
    while i < len(texts):
        # Build a batch respecting both size and char limits
        batch: list[str] = []
        batch_chars = 0
        while i < len(texts) and len(batch) < batch_size:
            text_chars = len(texts[i])
            if batch and batch_chars + text_chars > max_chars:
                break
            batch.append(texts[i])
            batch_chars += text_chars
            i += 1

        batch_results = translator.translate_batch(batch, target_lang)
        results.extend(batch_results)

    return results


def _trigger_deploy_hook() -> None:
    """POST to Cloudflare Pages deploy hook to trigger gazette rebuild."""
    if not CF_DEPLOY_HOOK_URL:
        logger.info("CF_DEPLOY_HOOK_URL not set, skipping gazette rebuild trigger")
        return

    try:
        import urllib.request

        req = urllib.request.Request(CF_DEPLOY_HOOK_URL, method="POST", data=b"")
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            logger.info(
                "Gazette rebuild triggered (status %d)",
                resp.status,
                extra={"step": "deploy_hook"},
            )
    except Exception:
        logger.warning("Failed to trigger gazette rebuild", exc_info=True)


def cli_main() -> None:
    """CLI entry point for Translation Cloud Run Job.

    Supports ``--backfill`` flag to translate all historical editions
    instead of just today's.
    """
    configure_logging()

    backfill = "--backfill" in sys.argv or TRANSLATION_BACKFILL

    if not TRANSLATION_ENABLED:
        logger.info("Translation disabled via TRANSLATION_ENABLED=false")
        sys.exit(0)

    # Choose storage backend
    store: EditionStorage
    if R2_ACCOUNT_ID:
        from ..r2_storage import R2EditionStorage

        store = R2EditionStorage()
    else:
        logger.warning("R2_ACCOUNT_ID not set, using StubEditionStorage")
        store = StubEditionStorage()

    # Choose translation provider
    trans: TranslationStrategy
    provider = TRANSLATION_PROVIDER.lower()
    if provider == "azure":
        if AZURE_TRANSLATOR_KEY and AZURE_TRANSLATOR_REGION:
            from .azure import AzureTranslationClient

            trans = AzureTranslationClient(
                subscription_key=AZURE_TRANSLATOR_KEY,
                region=AZURE_TRANSLATOR_REGION,
            )
        else:
            logger.warning(
                "AZURE_TRANSLATOR_KEY/REGION not set, using StubTranslationClient"
            )
            trans = StubTranslationClient()
    elif provider == "deepl":
        # DeepL client not yet implemented
        logger.warning("DeepL provider selected but not yet implemented, using stub")
        trans = StubTranslationClient()
    elif provider == "google":
        # Google Translate client not yet implemented
        logger.warning("Google provider selected but not yet implemented, using stub")
        trans = StubTranslationClient()
    else:
        logger.warning("Unknown TRANSLATION_PROVIDER=%s, using stub", provider)
        trans = StubTranslationClient()

    if backfill:
        summary = run_backfill(storage=store, translator=trans)
    else:
        summary = run_translation(storage=store, translator=trans)
    logger.info("Translation job finished", extra={"summary": summary})
