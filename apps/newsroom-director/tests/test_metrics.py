"""Tests for reader metrics module."""


import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from newsroom_director.db import (
    ArticleMetric,
    Base,
    load_edition_metrics,
    save_edition_metrics,
)
from newsroom_director.metrics import (
    MetricsClient,
    StubMetricsClient,
    enrich_metrics_with_headlines,
    format_metrics_for_pipeline_observation,
    format_metrics_for_reflection,
)


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture()
def sample_metrics():
    return [
        ArticleMetric("sovereign", "fed-raises-rates", "Fed Raises Rates", 150),
        ArticleMetric("sovereign", "nato-summit", "NATO Summit Recap", 80),
        ArticleMetric("sovereign", "china-trade-deal", "China Trade Deal", 40),
        ArticleMetric("aspirant", "workers-unite", "Workers Unite", 200),
        ArticleMetric("aspirant", "climate-march", "Climate March", 90),
        ArticleMetric("owner", "markets-surge", "Markets Surge", 120),
        ArticleMetric("owner", "crypto-crash", "Crypto Crash", 300),
    ]


# --- DB layer tests ---


class TestSaveEditionMetrics:
    def test_save_and_load_roundtrip(self, db_session):
        metrics = [
            ArticleMetric("sovereign", "test-slug", "Test Headline", 42),
        ]
        count = save_edition_metrics(db_session, metrics, "2026-03-13")
        db_session.commit()
        assert count == 1

        loaded = load_edition_metrics(db_session, "2026-03-13")
        assert "sovereign" in loaded
        assert len(loaded["sovereign"]) == 1
        assert loaded["sovereign"][0].page_views == 42
        assert loaded["sovereign"][0].headline == "Test Headline"

    def test_upsert_updates_views(self, db_session):
        metrics_v1 = [ArticleMetric("sovereign", "slug", "Headline", 10)]
        save_edition_metrics(db_session, metrics_v1, "2026-03-13")
        db_session.commit()

        metrics_v2 = [ArticleMetric("sovereign", "slug", "Headline", 50)]
        save_edition_metrics(db_session, metrics_v2, "2026-03-13")
        db_session.commit()

        loaded = load_edition_metrics(db_session, "2026-03-13")
        assert loaded["sovereign"][0].page_views == 50

    def test_multiple_newspapers(self, db_session, sample_metrics):
        save_edition_metrics(db_session, sample_metrics, "2026-03-13")
        db_session.commit()

        loaded = load_edition_metrics(db_session, "2026-03-13")
        assert "sovereign" in loaded
        assert "aspirant" in loaded
        assert "owner" in loaded
        assert len(loaded["sovereign"]) == 3

    def test_sorted_by_views_descending(self, db_session, sample_metrics):
        save_edition_metrics(db_session, sample_metrics, "2026-03-13")
        db_session.commit()

        loaded = load_edition_metrics(db_session, "2026-03-13")
        sovereign = loaded["sovereign"]
        assert sovereign[0].page_views >= sovereign[1].page_views
        assert sovereign[1].page_views >= sovereign[2].page_views

    def test_empty_when_no_data(self, db_session):
        loaded = load_edition_metrics(db_session, "2026-03-13")
        assert loaded == {}


# --- Stub client tests ---


class TestStubMetricsClient:
    def test_returns_canned_metrics(self):
        metrics = [ArticleMetric("sovereign", "slug", "H", 10)]
        client = StubMetricsClient(metrics=metrics)
        result = client.fetch_article_views("2026-03-13")
        assert result == metrics
        assert client.calls == ["2026-03-13"]

    def test_empty_by_default(self):
        client = StubMetricsClient()
        assert client.fetch_article_views("2026-03-13") == []


# --- Response parsing tests ---


class TestMetricsClientParsing:
    def test_parses_valid_response(self):
        client = MetricsClient(zone_id="test", api_token="test")
        data = {
            "data": {
                "viewer": {
                    "zones": [{
                        "rumPageloadEventsAdaptiveGroups": [
                            {
                                "dimensions": {"requestPath": "/edition/2026-03-13/sovereign/fed-rates/"},
                                "count": 42,
                            },
                            {
                                "dimensions": {"requestPath": "/edition/2026-03-13/aspirant/workers/"},
                                "count": 15,
                            },
                        ]
                    }]
                }
            }
        }

        result = client._parse_response(data, "2026-03-13")
        assert len(result) == 2
        assert result[0].newspaper_id == "sovereign"
        assert result[0].article_slug == "fed-rates"
        assert result[0].page_views == 42
        assert result[1].newspaper_id == "aspirant"

    def test_ignores_non_article_paths(self):
        client = MetricsClient(zone_id="test", api_token="test")
        data = {
            "data": {
                "viewer": {
                    "zones": [{
                        "rumPageloadEventsAdaptiveGroups": [
                            {
                                "dimensions": {"requestPath": "/edition/2026-03-13/sovereign/"},
                                "count": 100,
                            },
                            {
                                "dimensions": {"requestPath": "/about/"},
                                "count": 50,
                            },
                        ]
                    }]
                }
            }
        }
        result = client._parse_response(data, "2026-03-13")
        assert len(result) == 0

    def test_ignores_wrong_date(self):
        client = MetricsClient(zone_id="test", api_token="test")
        data = {
            "data": {
                "viewer": {
                    "zones": [{
                        "rumPageloadEventsAdaptiveGroups": [
                            {
                                "dimensions": {"requestPath": "/edition/2026-03-12/sovereign/slug/"},
                                "count": 10,
                            },
                        ]
                    }]
                }
            }
        }
        result = client._parse_response(data, "2026-03-13")
        assert len(result) == 0

    def test_ignores_curator(self):
        client = MetricsClient(zone_id="test", api_token="test")
        data = {
            "data": {
                "viewer": {
                    "zones": [{
                        "rumPageloadEventsAdaptiveGroups": [
                            {
                                "dimensions": {"requestPath": "/edition/2026-03-13/curator/synthesis/"},
                                "count": 10,
                            },
                        ]
                    }]
                }
            }
        }
        result = client._parse_response(data, "2026-03-13")
        assert len(result) == 0

    def test_handles_empty_response(self):
        client = MetricsClient(zone_id="test", api_token="test")
        result = client._parse_response({}, "2026-03-13")
        assert result == []


# --- Headline enrichment ---


class TestEnrichMetrics:
    def test_replaces_slug_with_headline(self):
        metrics = [ArticleMetric("sovereign", "slug", "slug", 10)]
        db_metrics = {"sovereign": [ArticleMetric("sovereign", "slug", "Real Headline", 5)]}
        enriched = enrich_metrics_with_headlines(metrics, db_metrics)
        assert enriched[0].headline == "Real Headline"

    def test_keeps_slug_when_no_match(self):
        metrics = [ArticleMetric("sovereign", "new-slug", "new-slug", 10)]
        db_metrics = {}
        enriched = enrich_metrics_with_headlines(metrics, db_metrics)
        assert enriched[0].headline == "new-slug"


# --- Formatting tests ---


class TestFormatMetricsForReflection:
    def test_empty_metrics(self):
        result = format_metrics_for_reflection([], "sovereign", {})
        assert result == ""

    def test_includes_top_articles(self, sample_metrics):
        totals = {"sovereign": 270, "aspirant": 290, "owner": 420}
        result = format_metrics_for_reflection(
            sample_metrics, "sovereign", totals,
        )
        assert "Fed Raises Rates" in result
        assert "150 views" in result
        assert "Top-performing" in result

    def test_includes_cross_comparison(self, sample_metrics):
        totals = {"sovereign": 270, "aspirant": 290, "owner": 420}
        result = format_metrics_for_reflection(
            sample_metrics, "sovereign", totals,
        )
        assert "Cross-newspaper comparison" in result
        assert "(you)" in result
        assert "owner" in result

    def test_includes_lowest_when_enough_articles(self, sample_metrics):
        totals = {"sovereign": 270}
        # sovereign has 3 articles, not >3, so lowest shouldn't appear
        result = format_metrics_for_reflection(
            sample_metrics, "sovereign", totals,
        )
        assert "Lowest-performing" not in result

    def test_includes_lowest_when_many_articles(self):
        metrics = [
            ArticleMetric("sovereign", f"slug-{i}", f"Article {i}", i * 10)
            for i in range(5)
        ]
        totals = {"sovereign": sum(m.page_views for m in metrics)}
        result = format_metrics_for_reflection(metrics, "sovereign", totals)
        assert "Lowest-performing" in result


class TestFormatMetricsForPipelineObservation:
    def test_empty_totals(self):
        result = format_metrics_for_pipeline_observation({}, [])
        assert result == ""

    def test_includes_newspaper_totals(self, sample_metrics):
        totals = {"sovereign": 270, "aspirant": 290, "owner": 420}
        result = format_metrics_for_pipeline_observation(totals, sample_metrics)
        assert "owner: 420 views" in result
        assert "Total views across all newspapers" in result

    def test_includes_top_articles(self, sample_metrics):
        totals = {"sovereign": 270, "aspirant": 290, "owner": 420}
        result = format_metrics_for_pipeline_observation(totals, sample_metrics)
        assert "Top 5 articles overall" in result
        # Crypto Crash (300) should be first
        assert "Crypto Crash" in result
