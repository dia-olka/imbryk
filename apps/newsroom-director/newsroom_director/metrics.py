"""Reader metrics — fetch page views from Cloudflare Web Analytics.

Queries the Cloudflare GraphQL Analytics API for page views on the
previous edition's article pages, then formats them for injection into
the editorial reflection prompt.
"""

from __future__ import annotations

import json
import logging
import re
import urllib.request
from dataclasses import dataclass

from .db import ArticleMetric

logger = logging.getLogger(__name__)

_CF_GRAPHQL_URL = "https://api.cloudflare.com/client/v4/graphql"

# Gazette URL pattern: /edition/{date}/{newspaper_id}/{article_slug}/
_PATH_PATTERN = re.compile(
    r"^/edition/(?P<date>\d{4}-\d{2}-\d{2})/(?P<newspaper>[^/]+)/(?P<slug>[^/]+)/?$"
)


@dataclass
class NewspaperMetrics:
    newspaper_id: str
    total_views: int
    articles: list[ArticleMetric]


@dataclass
class EditionMetricsSummary:
    edition_date: str
    total_views: int
    by_newspaper: dict[str, NewspaperMetrics]


class MetricsClient:
    """Fetches page-view data from the Cloudflare GraphQL Analytics API."""

    def __init__(self, zone_id: str, api_token: str) -> None:
        self._zone_id = zone_id
        self._api_token = api_token

    def fetch_article_views(
        self,
        edition_date: str,
    ) -> list[ArticleMetric]:
        """Query Cloudflare for page views on articles from a given edition.

        Returns a list of ArticleMetric with page_views populated.
        Headlines are set to the slug (actual headlines are matched later
        from DB data).
        """
        query = """
query ($zoneTag: string!, $dateStart: Date!, $dateEnd: Date!, $pathPrefix: string!) {
  viewer {
    zones(filter: {zoneTag: $zoneTag}) {
      rumPageloadEventsAdaptiveGroups(
        filter: {
          date_geq: $dateStart
          date_leq: $dateEnd
          requestPath_like: $pathPrefix
        }
        limit: 500
        orderBy: [count_DESC]
      ) {
        dimensions { requestPath }
        count
      }
    }
  }
}"""
        variables = {
            "zoneTag": self._zone_id,
            "dateStart": edition_date,
            "dateEnd": edition_date,
            "pathPrefix": f"/edition/{edition_date}/%",
        }

        payload = json.dumps({"query": query, "variables": variables}).encode()
        req = urllib.request.Request(
            _CF_GRAPHQL_URL,
            data=payload,
            headers={
                "Authorization": f"Bearer {self._api_token}",
                "Content-Type": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
        except Exception:
            logger.exception("Failed to fetch Cloudflare analytics")
            return []

        return self._parse_response(data, edition_date)

    def _parse_response(
        self,
        data: dict,
        edition_date: str,
    ) -> list[ArticleMetric]:
        """Parse the GraphQL response into ArticleMetric objects."""
        metrics: list[ArticleMetric] = []

        try:
            zones = data.get("data", {}).get("viewer", {}).get("zones", [])
            if not zones:
                return []

            groups = zones[0].get("rumPageloadEventsAdaptiveGroups", [])
            for group in groups:
                path = group.get("dimensions", {}).get("requestPath", "")
                count = group.get("count", 0)

                match = _PATH_PATTERN.match(path)
                if not match:
                    continue

                if match.group("date") != edition_date:
                    continue

                newspaper_id = match.group("newspaper")
                slug = match.group("slug")

                # Skip non-article pages (newspaper index pages have no slug)
                if not slug or newspaper_id == "curator":
                    continue

                metrics.append(
                    ArticleMetric(
                        newspaper_id=newspaper_id,
                        article_slug=slug,
                        headline=slug,  # placeholder; matched from DB later
                        page_views=count,
                    )
                )
        except (KeyError, TypeError, IndexError):
            logger.warning("Unexpected Cloudflare analytics response structure")

        return metrics


class StubMetricsClient:
    """Returns canned metrics for testing."""

    def __init__(self, metrics: list[ArticleMetric] | None = None) -> None:
        self._metrics = metrics or []
        self._calls: list[str] = []

    def fetch_article_views(self, edition_date: str) -> list[ArticleMetric]:
        self._calls.append(edition_date)
        return self._metrics

    @property
    def calls(self) -> list[str]:
        return self._calls


def enrich_metrics_with_headlines(
    metrics: list[ArticleMetric],
    db_metrics: dict[str, list[ArticleMetric]],
) -> list[ArticleMetric]:
    """Replace slug-based headlines with actual headlines from the DB.

    If a metric was previously stored with a real headline, use that.
    Otherwise keep the slug as-is.
    """
    # Build lookup: (newspaper_id, slug) -> headline
    headline_map: dict[tuple[str, str], str] = {}
    for newspaper_id, items in db_metrics.items():
        for item in items:
            headline_map[(newspaper_id, item.article_slug)] = item.headline

    result = []
    for m in metrics:
        key = (m.newspaper_id, m.article_slug)
        headline = headline_map.get(key, m.headline)
        result.append(
            ArticleMetric(
                newspaper_id=m.newspaper_id,
                article_slug=m.article_slug,
                headline=headline,
                page_views=m.page_views,
            )
        )
    return result


def format_metrics_for_reflection(
    metrics: list[ArticleMetric],
    persona_id: str,
    all_newspaper_totals: dict[str, int],
) -> str:
    """Format reader metrics as text for injection into reflection prompts.

    Args:
        metrics: All article metrics for the edition.
        persona_id: The persona whose reflection is being built.
        all_newspaper_totals: {newspaper_id: total_views} for cross-comparison.

    Returns:
        Formatted text block, or empty string if no metrics.
    """
    if not metrics and not all_newspaper_totals:
        return ""

    persona_articles = [m for m in metrics if m.newspaper_id == persona_id]
    persona_total = all_newspaper_totals.get(persona_id, 0)

    parts: list[str] = []
    parts.append("READER METRICS FOR YOUR PREVIOUS EDITION:")
    parts.append(f"Total views for your newspaper: {persona_total}")

    if persona_articles:
        # Top performers
        top = sorted(persona_articles, key=lambda m: m.page_views, reverse=True)[:3]
        parts.append("\nTop-performing articles:")
        for i, m in enumerate(top, 1):
            parts.append(f"  {i}. \"{m.headline}\" — {m.page_views} views")

        # Lowest performers (if more than 3 articles)
        if len(persona_articles) > 3:
            bottom = sorted(persona_articles, key=lambda m: m.page_views)[:2]
            parts.append("\nLowest-performing articles:")
            for i, m in enumerate(bottom, 1):
                parts.append(f"  {i}. \"{m.headline}\" — {m.page_views} views")

    # Cross-newspaper comparison
    if all_newspaper_totals:
        parts.append("\nCross-newspaper comparison:")
        for nid, total in sorted(
            all_newspaper_totals.items(), key=lambda x: x[1], reverse=True
        ):
            marker = " (you)" if nid == persona_id else ""
            parts.append(f"  - {nid}: {total} total views{marker}")

    parts.append(
        "\nConsider: What made your top articles resonate? What can you learn "
        "from the newspapers that outperformed yours? Stay true to your "
        "editorial identity, but understand what your readers value."
    )

    return "\n".join(parts)


def format_metrics_for_pipeline_observation(
    all_newspaper_totals: dict[str, int],
    metrics: list[ArticleMetric],
) -> str:
    """Format metrics summary for the pipeline-level observation prompt."""
    if not all_newspaper_totals:
        return ""

    parts: list[str] = []
    parts.append("READER METRICS FOR PREVIOUS EDITION:")

    total_all = sum(all_newspaper_totals.values())
    parts.append(f"Total views across all newspapers: {total_all}")

    parts.append("\nBy newspaper:")
    for nid, total in sorted(
        all_newspaper_totals.items(), key=lambda x: x[1], reverse=True
    ):
        share = (total / total_all * 100) if total_all > 0 else 0
        parts.append(f"  - {nid}: {total} views ({share:.0f}%)")

    # Top 5 articles overall
    top = sorted(metrics, key=lambda m: m.page_views, reverse=True)[:5]
    if top:
        parts.append("\nTop 5 articles overall:")
        for i, m in enumerate(top, 1):
            parts.append(
                f"  {i}. [{m.newspaper_id}] \"{m.headline}\" — {m.page_views} views"
            )

    return "\n".join(parts)
