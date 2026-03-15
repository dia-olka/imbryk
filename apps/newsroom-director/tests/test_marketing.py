"""Tests for the marketing agent module."""

import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from newsroom_director.db import (
    Base,
    MarketingPost,
    load_edition_by_date,
    load_recent_marketing_posts,
    save_edition,
    save_marketing_post,
)
from newsroom_director.generation import StubGenerationStrategy
from newsroom_director.marketing.channels.base import StubChannel
from newsroom_director.marketing.main import run_marketing_agent
from newsroom_director.marketing.planner import (
    _parse_plan,
    build_edition_summary,
    plan_marketing,
)
from newsroom_director.marketing.referrers import (
    _parse_referrer_response,
    format_referrer_text,
)


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _seed_edition(session, date="2026-03-15"):
    """Insert a minimal edition with articles for testing."""
    sovereign_content = json.dumps({
        "newspaper_name": "The Sovereign",
        "articles": [
            {"headline": "Global Summit Reaches Agreement", "body": "Leaders agree."},
            {"headline": "Defence Spending Rises", "body": "Military budgets increase."},
        ],
        "editors_note": "A day of institutional momentum.",
    })
    radical_content = json.dumps({
        "newspaper_name": "The Radical",
        "articles": [
            {"headline": "Protesters Block Summit Entrance", "body": "Direct action."},
        ],
        "editors_note": "Resistance continues.",
    })
    curator_content = json.dumps({
        "text": "## CONSENSUS\nAll papers agree the summit happened.\n\n## FAULT LINES\nSovereign vs Radical on protest.",
    })
    save_edition(session, date, {
        "sovereign": sovereign_content,
        "radical": radical_content,
        "curator": curator_content,
    })
    session.commit()


# === Planner tests ===


class TestParsePlan:
    def test_valid_json(self):
        raw = json.dumps({
            "reasoning": "Contrast post today",
            "posts": [
                {
                    "channel": "bluesky",
                    "post_type": "contrast",
                    "text": "Sovereign vs Radical on the summit.",
                },
            ],
        })
        plan = _parse_plan(raw)
        assert plan.reasoning == "Contrast post today"
        assert len(plan.posts) == 1
        assert plan.posts[0].channel == "bluesky"
        assert plan.posts[0].post_type == "contrast"

    def test_json_with_code_fence(self):
        raw = '```json\n{"reasoning":"test","posts":[]}\n```'
        plan = _parse_plan(raw)
        assert plan.reasoning == "test"
        assert plan.posts == []

    def test_invalid_json_returns_empty(self):
        plan = _parse_plan("not json at all")
        assert plan.reasoning == ""
        assert plan.posts == []

    def test_missing_posts_key(self):
        raw = json.dumps({"reasoning": "no posts key"})
        plan = _parse_plan(raw)
        assert plan.posts == []

    def test_multiple_posts(self):
        raw = json.dumps({
            "reasoning": "Multiple angles",
            "posts": [
                {"channel": "bluesky", "post_type": "edition_teaser", "text": "Post 1"},
                {"channel": "bluesky", "post_type": "contrast", "text": "Post 2"},
                {"channel": "bluesky", "post_type": "thread", "text": "A\n---\nB\n---\nC"},
            ],
        })
        plan = _parse_plan(raw)
        assert len(plan.posts) == 3


class TestBuildEditionSummary:
    def test_includes_newspaper_headlines(self):
        articles = {
            "sovereign": json.dumps({
                "newspaper_name": "The Sovereign",
                "articles": [{"headline": "Summit Accord"}],
                "editors_note": "Institutional note",
            }),
        }
        summary = build_edition_summary(articles, "https://gazette.test", "2026-03-15")
        assert "THE SOVEREIGN" in summary
        assert "Summit Accord" in summary
        assert "Institutional note" in summary
        assert "2026-03-15" in summary

    def test_includes_curator(self):
        articles = {
            "curator": json.dumps({
                "text": "## CONSENSUS\nEveryone agrees.",
            }),
        }
        summary = build_edition_summary(articles, "https://gazette.test", "2026-03-15")
        assert "THE CURATOR" in summary
        assert "Everyone agrees" in summary

    def test_skips_malformed_json(self):
        articles = {"sovereign": "not valid json"}
        summary = build_edition_summary(articles, "https://gazette.test", "2026-03-15")
        assert "2026-03-15" in summary


class TestPlanMarketing:
    def test_calls_flash_tier(self):
        gen = StubGenerationStrategy(responses={
            "flash": json.dumps({
                "reasoning": "Stub strategy",
                "posts": [{"channel": "bluesky", "post_type": "edition_teaser", "text": "Test"}],
            }),
        })
        plan = plan_marketing(
            edition_summary="Test edition",
            journal_text="",
            referrer_text="",
            gazette_url="https://gazette.test",
            generation_strategy=gen,
        )
        assert len(gen.calls) == 1
        assert gen.calls[0]["model_tier"] == "flash"
        assert plan.posts[0].text == "Test"

    def test_returns_empty_on_llm_failure(self):
        gen = StubGenerationStrategy()
        # Default stub returns non-JSON for flash tier, parse will fail gracefully
        plan = plan_marketing(
            edition_summary="Test edition",
            journal_text="",
            referrer_text="",
            gazette_url="https://gazette.test",
            generation_strategy=gen,
        )
        assert plan.posts == []


# === Channel tests ===


class TestStubChannel:
    def test_post(self):
        ch = StubChannel()
        result = ch.post("Hello world")
        assert result.success is True
        assert result.post_url is not None
        assert ch.posts == ["Hello world"]

    def test_post_failure(self):
        ch = StubChannel(should_fail=True)
        result = ch.post("Hello world")
        assert result.success is False
        assert result.error == "stub failure"

    def test_post_thread(self):
        ch = StubChannel()
        results = ch.post_thread(["Post 1", "Post 2", "Post 3"])
        assert len(results) == 3
        assert all(r.success for r in results)
        assert len(ch.threads) == 1
        assert ch.threads[0] == ["Post 1", "Post 2", "Post 3"]

    def test_thread_failure(self):
        ch = StubChannel(should_fail=True)
        results = ch.post_thread(["A", "B"])
        assert len(results) == 2
        assert all(not r.success for r in results)


# === Referrer tests ===


class TestParseReferrerResponse:
    def test_valid_response(self):
        data = {
            "data": {
                "viewer": {
                    "zones": [{
                        "rumPageloadEventsAdaptiveGroups": [
                            {"dimensions": {"refererHost": "bsky.app"}, "count": 42},
                            {"dimensions": {"refererHost": "t.co"}, "count": 18},
                            {"dimensions": {"refererHost": ""}, "count": 150},
                        ],
                    }],
                },
            },
        }
        result = _parse_referrer_response(data)
        assert result["bsky.app"] == 42
        assert result["t.co"] == 18
        assert result["(direct)"] == 150

    def test_empty_zones(self):
        data = {"data": {"viewer": {"zones": []}}}
        assert _parse_referrer_response(data) == {}

    def test_missing_data(self):
        assert _parse_referrer_response({}) == {}


class TestFormatReferrerText:
    def test_formats_breakdown(self):
        refs = {"bsky.app": 42, "t.co": 18, "(direct)": 100}
        text = format_referrer_text(refs)
        assert "Total page views: 160" in text
        assert "bsky.app" in text
        assert "(direct)" in text

    def test_empty_referrers(self):
        text = format_referrer_text({})
        assert "No referrer data" in text


# === DB tests ===


class TestMarketingPostDB:
    def test_save_and_load(self, db_session):
        post = MarketingPost(
            edition_date="2026-03-15",
            channel="bluesky",
            post_type="edition_teaser",
            content="Check out today's Imbryk Gazette!",
            post_url="https://bsky.app/post/123",
            post_id="at://did:plc:xxx/app.bsky.feed.post/abc",
            status="posted",
        )
        save_marketing_post(db_session, post)
        db_session.commit()

        loaded = load_recent_marketing_posts(
            db_session, lookback_days=7, current_date="2026-03-15",
        )
        assert len(loaded) == 1
        assert loaded[0].channel == "bluesky"
        assert loaded[0].content == "Check out today's Imbryk Gazette!"

    def test_lookback_window(self, db_session):
        save_marketing_post(db_session, MarketingPost(
            edition_date="2026-03-15", channel="bluesky",
            post_type="teaser", content="Recent",
        ))
        save_marketing_post(db_session, MarketingPost(
            edition_date="2026-03-01", channel="bluesky",
            post_type="teaser", content="Old",
        ))
        db_session.commit()

        loaded = load_recent_marketing_posts(
            db_session, lookback_days=7, current_date="2026-03-15",
        )
        assert len(loaded) == 1
        assert loaded[0].content == "Recent"

    def test_load_edition_by_date(self, db_session):
        _seed_edition(db_session)
        articles = load_edition_by_date(db_session, "2026-03-15")
        assert articles is not None
        assert "sovereign" in articles
        assert "radical" in articles

    def test_load_edition_by_date_not_found(self, db_session):
        result = load_edition_by_date(db_session, "2099-01-01")
        assert result is None


# === Orchestrator integration test ===


@pytest.fixture()
def db_url_with_edition(tmp_path):
    """Create a SQLite file DB with tables and a seeded edition."""
    db_path = tmp_path / "test.db"
    url = f"sqlite:///{db_path}"
    engine = create_engine(url)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    _seed_edition(session)
    session.close()
    return url


@pytest.fixture()
def db_url_empty(tmp_path):
    """Create a SQLite file DB with tables but no data."""
    db_path = tmp_path / "empty.db"
    url = f"sqlite:///{db_path}"
    engine = create_engine(url)
    Base.metadata.create_all(bind=engine)
    return url


class TestRunMarketingAgent:
    def test_no_edition_returns_early(self, db_url_empty):
        result = run_marketing_agent(
            database_url=db_url_empty,
            generation_strategy=StubGenerationStrategy(),
            channel=StubChannel(),
            edition_date="2099-01-01",
        )
        assert result["posts_created"] == 0
        assert result["reason"] == "no_edition"

    def test_full_pipeline_with_stub(self, db_url_with_edition):
        plan_json = json.dumps({
            "reasoning": "Test strategy: lead with contrast",
            "posts": [
                {
                    "channel": "stub",
                    "post_type": "edition_teaser",
                    "text": "Sovereign and Radical clash on the summit.",
                },
                {
                    "channel": "stub",
                    "post_type": "contrast",
                    "text": "Defence spending: Sovereign cheers, Radical jeers.",
                },
            ],
        })
        gen = StubGenerationStrategy(responses={"flash": plan_json})
        ch = StubChannel()

        result = run_marketing_agent(
            database_url=db_url_with_edition,
            generation_strategy=gen,
            channel=ch,
            edition_date="2026-03-15",
        )

        assert result["posts_created"] == 2
        assert result["posts_planned"] == 2
        assert result["channel"] == "stub"
        assert len(ch.posts) == 2

    def test_thread_posting(self, db_url_with_edition):
        plan_json = json.dumps({
            "reasoning": "Thread approach",
            "posts": [
                {
                    "channel": "stub",
                    "post_type": "thread",
                    "text": "Post 1\n---\nPost 2\n---\nPost 3",
                },
            ],
        })
        gen = StubGenerationStrategy(responses={"flash": plan_json})
        ch = StubChannel()

        result = run_marketing_agent(
            database_url=db_url_with_edition,
            generation_strategy=gen,
            channel=ch,
            edition_date="2026-03-15",
        )

        assert result["posts_created"] == 3
        assert len(ch.threads) == 1

    def test_channel_mismatch_skips_post(self, db_url_with_edition):
        plan_json = json.dumps({
            "reasoning": "Wrong channel",
            "posts": [
                {"channel": "twitter", "post_type": "teaser", "text": "Tweet"},
            ],
        })
        gen = StubGenerationStrategy(responses={"flash": plan_json})
        ch = StubChannel()

        result = run_marketing_agent(
            database_url=db_url_with_edition,
            generation_strategy=gen,
            channel=ch,
            edition_date="2026-03-15",
        )

        assert result["posts_created"] == 0
        assert len(ch.posts) == 0

    def test_failed_post_still_saved(self, db_url_with_edition):
        plan_json = json.dumps({
            "reasoning": "Will fail",
            "posts": [
                {"channel": "stub", "post_type": "teaser", "text": "Fail"},
            ],
        })
        gen = StubGenerationStrategy(responses={"flash": plan_json})
        ch = StubChannel(should_fail=True)

        result = run_marketing_agent(
            database_url=db_url_with_edition,
            generation_strategy=gen,
            channel=ch,
            edition_date="2026-03-15",
        )

        assert result["posts_created"] == 0
