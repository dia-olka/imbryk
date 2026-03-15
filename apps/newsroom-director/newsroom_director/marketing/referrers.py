"""Referrer traffic metrics from Cloudflare Analytics.

Extends the existing MetricsClient pattern to fetch referrer breakdown
data — which external sources (Bluesky, Twitter, Reddit, direct) are
driving traffic to the gazette.
"""

from __future__ import annotations

import json
import logging
import urllib.request
from collections import defaultdict

logger = logging.getLogger(__name__)


def fetch_referrer_breakdown(
    zone_id: str,
    api_token: str,
    date: str,
) -> dict[str, int]:
    """Fetch page views grouped by referrer host for a given date.

    Returns a dict of {referrer_host: page_views}, e.g.:
        {"bsky.app": 42, "t.co": 18, "(direct)": 150}
    """
    query = """
query ($zoneTag: string!, $dateStart: Date!, $dateEnd: Date!) {
  viewer {
    zones(filter: {zoneTag: $zoneTag}) {
      rumPageloadEventsAdaptiveGroups(
        filter: {
          date_geq: $dateStart
          date_leq: $dateEnd
        }
        limit: 100
        orderBy: [count_DESC]
      ) {
        dimensions { refererHost }
        count
      }
    }
  }
}"""
    variables = {
        "zoneTag": zone_id,
        "dateStart": date,
        "dateEnd": date,
    }

    payload = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        "https://api.cloudflare.com/client/v4/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except Exception:
        logger.warning("Failed to fetch referrer analytics", exc_info=True)
        return {}

    return _parse_referrer_response(data)


def _parse_referrer_response(data: dict) -> dict[str, int]:
    """Parse Cloudflare GraphQL response into {host: views} dict."""
    result: dict[str, int] = defaultdict(int)
    try:
        zones = data.get("data", {}).get("viewer", {}).get("zones", [])
        if not zones:
            return dict(result)

        groups = zones[0].get("rumPageloadEventsAdaptiveGroups", [])
        for group in groups:
            host = group.get("dimensions", {}).get("refererHost", "") or "(direct)"
            count = group.get("count", 0)
            result[host] += count
    except (KeyError, TypeError, IndexError):
        logger.warning("Unexpected referrer response structure", exc_info=True)

    return dict(result)


def format_referrer_text(referrers: dict[str, int]) -> str:
    """Format referrer breakdown for the marketing planner prompt."""
    if not referrers:
        return "No referrer data available."

    total = sum(referrers.values())
    lines = [f"Total page views: {total:,}"]
    lines.append("")

    sorted_refs = sorted(referrers.items(), key=lambda x: x[1], reverse=True)
    for host, views in sorted_refs[:15]:
        pct = (views / total * 100) if total > 0 else 0
        lines.append(f"  {host}: {views:,} ({pct:.0f}%)")

    return "\n".join(lines)
