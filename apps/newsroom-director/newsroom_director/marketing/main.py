"""Marketing agent orchestrator — observe, plan, act, reflect.

Entry point for the JOB_MODE=marketing Cloud Run Job.
"""

from __future__ import annotations

import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone

from ..config import (
    BLUESKY_APP_PASSWORD,
    BLUESKY_HANDLE,
    CF_ANALYTICS_API_TOKEN,
    CF_ANALYTICS_ZONE_ID,
    DATABASE_URL,
    GAZETTE_FALLBACK_URL,
    MARKETING_ENABLED,
    VERTEX_AI_LOCATION,
    VERTEX_AI_PROJECT,
)
from ..db import (
    MarketingPost,
    get_engine,
    get_session_factory,
    load_edition_by_date,
    load_recent_journal,
    load_recent_marketing_posts,
    save_journal_entry,
    save_marketing_post,
)
from ..generation import GenerationStrategy, StubGenerationStrategy, VertexAIStrategy
from ..logging_config import configure_logging
from .channels.base import ChannelStrategy, StubChannel
from .planner import build_edition_summary, plan_marketing
from .referrers import fetch_referrer_breakdown, format_referrer_text

logger = logging.getLogger(__name__)


def run_marketing_agent(
    database_url: str | None = None,
    generation_strategy: GenerationStrategy | None = None,
    channel: ChannelStrategy | None = None,
    edition_date: str | None = None,
) -> dict:
    """Execute the marketing agent pipeline.

    Args:
        database_url: Override for the database connection string.
        generation_strategy: LLM backend (defaults to stub).
        channel: Social media channel backend (defaults to stub).
        edition_date: Target edition date (defaults to today UTC).

    Returns:
        Summary dict with counts of posts created.
    """
    start_time = time.monotonic()

    db_url = database_url or DATABASE_URL
    gen = generation_strategy or StubGenerationStrategy()
    ch = channel or StubChannel()

    from ..config import EDITION_DATE

    today = edition_date or EDITION_DATE or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    yesterday = (datetime.strptime(today, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")

    gazette_url = GAZETTE_FALLBACK_URL.rstrip("/")

    engine = get_engine(db_url)
    session_factory = get_session_factory(engine)
    session = session_factory()

    try:
        # === OBSERVE ===
        logger.info("Marketing agent: OBSERVE phase", extra={"step": "observe"})

        # Load today's edition
        articles = load_edition_by_date(session, today)
        if not articles:
            logger.info("No edition found for %s, skipping marketing", today)
            return {"edition_date": today, "posts_created": 0, "reason": "no_edition"}

        # Build edition summary for the planner
        edition_summary = build_edition_summary(articles, gazette_url, today)

        # Load marketing journal (strategy history)
        journal_entries = load_recent_journal(
            session, "_marketing", lookback_days=7, current_date=today,
        )
        journal_text = "\n\n".join(
            f"[{e.entry_date}] {e.content}" for e in journal_entries
        ) if journal_entries else ""

        # Load past marketing posts for context
        past_posts = load_recent_marketing_posts(session, lookback_days=7, current_date=today)

        # Idempotency: skip if posts for today's edition already exist.
        # Prevents duplicate publishing if the Cloud Run job is retried.
        today_posts = [p for p in past_posts if p.edition_date == today]
        if today_posts:
            logger.info(
                "Posts already published for edition %s (%d posts), skipping to prevent duplicates",
                today,
                len(today_posts),
            )
            return {"edition_date": today, "posts_created": 0, "reason": "already_posted"}

        if past_posts:
            posts_text = "\n".join(
                f"  [{p.edition_date}] {p.channel}/{p.post_type}: {p.content[:100]}... "
                f"({'OK' if p.status == 'posted' else p.status})"
                for p in past_posts[:10]
            )
            journal_text += f"\n\nRecent posts:\n{posts_text}"

        # Load referrer metrics from Cloudflare
        referrer_text = ""
        if CF_ANALYTICS_ZONE_ID and CF_ANALYTICS_API_TOKEN:
            referrers = fetch_referrer_breakdown(
                CF_ANALYTICS_ZONE_ID, CF_ANALYTICS_API_TOKEN, yesterday,
            )
            referrer_text = format_referrer_text(referrers)

        # === PLAN ===
        logger.info("Marketing agent: PLAN phase", extra={"step": "plan"})
        plan = plan_marketing(
            edition_summary=edition_summary,
            journal_text=journal_text,
            referrer_text=referrer_text,
            gazette_url=gazette_url,
            generation_strategy=gen,
        )

        if not plan.posts:
            logger.warning("Marketing planner produced no posts")
            return {"edition_date": today, "posts_created": 0, "reason": "empty_plan"}

        logger.info(
            "Marketing plan: %d posts | reasoning: %s",
            len(plan.posts),
            plan.reasoning[:200],
            extra={
                "step": "plan_complete",
                "post_count": len(plan.posts),
                "reasoning": plan.reasoning,
            },
        )

        # === ACT ===
        logger.info("Marketing agent: ACT phase", extra={"step": "act"})
        posts_created = 0

        edition_link = f"{gazette_url}/edition/{today}/"

        def _ensure_link(text: str) -> str:
            """Append the edition link if the post doesn't already contain a gazette URL."""
            if gazette_url in text:
                return text
            return f"{text}\n{edition_link}"

        for planned in plan.posts:
            if planned.channel != ch.channel_name:
                logger.info(
                    "Skipping post for channel %s (active channel: %s)",
                    planned.channel,
                    ch.channel_name,
                )
                continue

            if planned.post_type == "thread":
                # Split thread text on separator
                thread_texts = [
                    t.strip() for t in planned.text.split("\n---\n") if t.strip()
                ]
                if not thread_texts:
                    continue

                # Ensure the last thread post has the edition link
                thread_texts[-1] = _ensure_link(thread_texts[-1])

                results = ch.post_thread(thread_texts)
                for i, result in enumerate(results):
                    post = MarketingPost(
                        edition_date=today,
                        channel=ch.channel_name,
                        post_type=f"thread_{i}",
                        content=thread_texts[i] if i < len(thread_texts) else "",
                        post_url=result.post_url,
                        post_id=result.post_id,
                        status="posted" if result.success else "failed",
                    )
                    save_marketing_post(session, post)
                    if result.success:
                        posts_created += 1
                    else:
                        logger.warning(
                            "Thread post %d failed: %s",
                            i,
                            result.error,
                        )
            else:
                planned_text = _ensure_link(planned.text)
                result = ch.post(planned_text)
                post = MarketingPost(
                    edition_date=today,
                    channel=ch.channel_name,
                    post_type=planned.post_type,
                    content=planned_text,
                    post_url=result.post_url,
                    post_id=result.post_id,
                    status="posted" if result.success else "failed",
                )
                save_marketing_post(session, post)
                if result.success:
                    posts_created += 1
                    logger.info(
                        "Post published: %s/%s -> %s",
                        ch.channel_name,
                        planned.post_type,
                        result.post_url,
                        extra={
                            "step": "posted",
                            "channel": ch.channel_name,
                            "post_type": planned.post_type,
                            "post_url": result.post_url,
                        },
                    )
                else:
                    logger.warning(
                        "Post failed: %s/%s — %s",
                        ch.channel_name,
                        planned.post_type,
                        result.error,
                    )

        # === REFLECT ===
        logger.info("Marketing agent: REFLECT phase", extra={"step": "reflect"})
        reflection = (
            f"Strategy: {plan.reasoning}\n"
            f"Posts attempted: {len(plan.posts)}\n"
            f"Posts published: {posts_created}\n"
            f"Channel: {ch.channel_name}\n"
            f"Referrer summary: {referrer_text[:300] if referrer_text else 'N/A'}"
        )
        save_journal_entry(session, "_marketing", today, "observation", reflection)

        session.commit()

        total_ms = int((time.monotonic() - start_time) * 1000)
        summary = {
            "edition_date": today,
            "posts_created": posts_created,
            "posts_planned": len(plan.posts),
            "channel": ch.channel_name,
            "latency_ms": total_ms,
        }
        logger.info(
            "Marketing agent complete: %d/%d posts published in %.1fs",
            posts_created,
            len(plan.posts),
            total_ms / 1000,
            extra={"step": "complete", **summary},
        )
        return summary

    except Exception as exc:
        session.rollback()
        logger.exception("Marketing agent failed: %s", exc)
        raise
    finally:
        session.close()


def cli_main() -> None:
    """CLI entry point for Marketing Agent Cloud Run Job."""
    configure_logging()

    if not MARKETING_ENABLED:
        logger.info("Marketing agent disabled via MARKETING_ENABLED=false")
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
        logger.warning("VERTEX_AI_PROJECT not set, using StubGenerationStrategy")
        gen = StubGenerationStrategy()

    # Choose channel backend
    ch: ChannelStrategy
    if BLUESKY_HANDLE and BLUESKY_APP_PASSWORD:
        from .channels.bluesky import BlueskyChannel

        ch = BlueskyChannel(
            handle=BLUESKY_HANDLE,
            app_password=BLUESKY_APP_PASSWORD,
        )
    else:
        logger.warning("BLUESKY_HANDLE not set, using StubChannel")
        ch = StubChannel()

    summary = run_marketing_agent(
        database_url=db_url,
        generation_strategy=gen,
        channel=ch,
    )
    logger.info("Marketing agent finished", extra={"summary": summary})
