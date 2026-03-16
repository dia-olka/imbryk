"""Marketing strategy planner — LLM call to decide what to promote and how."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from ..generation import GenerationStrategy

logger = logging.getLogger(__name__)


@dataclass
class PlannedPost:
    """A single social media post planned by the LLM."""

    channel: str
    post_type: str  # edition_teaser, contrast, thread
    text: str  # For threads, newline-separated posts
    reasoning: str = ""


@dataclass
class MarketingPlan:
    """Structured output from the planning LLM call."""

    reasoning: str = ""
    posts: list[PlannedPost] = field(default_factory=list)


_SYSTEM_PROMPT = """\
You are the Marketing Agent for Imbryk Gazette — an AI-powered newspaper \
platform with 6 ideologically distinct newspapers covering the same events \
from different perspectives, plus a Curator synthesis.

Your job: write 2-3 social media posts that make people curious enough to \
visit the gazette. You are posting from the @imbryk-gazette.bsky.social account.

VOICE: The Curator's voice — analytical, witty, never partisan. You illuminate \
the editorial tension between newspapers without taking sides.

POST TYPES (use 1-2 per day):
- "edition_teaser": One post that captures the day's most interesting angle. \
Lead with the conflict or surprise, not a summary.
- "contrast": Highlight when two newspapers disagree sharply on the same event. \
Name the newspapers. Quote or paraphrase their positions.
- "thread": 3-5 linked posts, each covering a different newspaper's hottest take. \
Use the newspaper name as a label. End with a link to the full edition.

RULES:
- Maximum 255 characters per post (a gazette link is appended automatically).
- Do NOT include the gazette URL in post text — it is added for you.
- Never be generic ("check out today's edition!"). Always name specific \
articles, newspapers, or tensions.
- Learn from the marketing journal — if contrast posts got more engagement, \
lean into contrasts. If a topic drove traffic, find similar angles.
- Do NOT invent article content. Only reference headlines and angles that \
appear in the edition data below.

OUTPUT: Respond with ONLY a JSON object matching this schema:
{
  "reasoning": "Brief explanation of your strategy for today",
  "posts": [
    {
      "channel": "bluesky",
      "post_type": "edition_teaser" | "contrast" | "thread",
      "text": "Post text here (for threads, separate posts with \\n---\\n)"
    }
  ]
}
"""


def plan_marketing(
    edition_summary: str,
    journal_text: str,
    referrer_text: str,
    gazette_url: str,
    generation_strategy: GenerationStrategy,
) -> MarketingPlan:
    """Call the LLM to plan today's marketing posts.

    Args:
        edition_summary: Today's edition headlines and Curator highlights.
        journal_text: Recent marketing journal entries (strategy + results).
        referrer_text: Referrer traffic breakdown from Cloudflare.
        gazette_url: Base URL for the gazette (e.g. https://gazette.imbryk.news).
        generation_strategy: LLM backend.

    Returns:
        MarketingPlan with structured post list.
    """
    user_content = f"""\
TODAY'S EDITION:
{edition_summary}

MARKETING JOURNAL (last 7 days):
{journal_text or "No previous marketing activity."}

REFERRER TRAFFIC (yesterday):
{referrer_text or "No referrer data available yet."}

GAZETTE URL: {gazette_url}

Plan today's social media posts."""

    try:
        response = generation_strategy.generate(
            _SYSTEM_PROMPT, "flash", user_content,
        )
        return _parse_plan(response)
    except Exception:
        logger.warning(
            "Marketing plan LLM call failed",
            exc_info=True,
        )
        return MarketingPlan()


def _parse_plan(response: str) -> MarketingPlan:
    """Parse LLM response into a MarketingPlan."""
    text = response.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        logger.warning(
            "Failed to parse marketing plan JSON: %.500s",
            text,
            exc_info=True,
        )
        return MarketingPlan()

    posts = []
    for p in data.get("posts", []):
        posts.append(PlannedPost(
            channel=p.get("channel", "bluesky"),
            post_type=p.get("post_type", "edition_teaser"),
            text=p.get("text", ""),
            reasoning=p.get("reasoning", ""),
        ))

    return MarketingPlan(
        reasoning=data.get("reasoning", ""),
        posts=posts,
    )


def build_edition_summary(
    articles: dict[str, str],
    gazette_url: str,
    edition_date: str,
) -> str:
    """Build a concise edition summary for the marketing planner.

    Extracts headlines from each newspaper's JSON content.
    """
    sections = []
    for newspaper_id, content_json in articles.items():
        try:
            parsed = json.loads(content_json)
        except (json.JSONDecodeError, TypeError):
            continue

        if newspaper_id == "curator":
            text = parsed.get("text", "")
            if text:
                sections.append(f"=== THE CURATOR ===\n{text[:500]}")
            continue

        headlines = []
        for a in parsed.get("articles", []):
            h = a.get("headline", "")
            if h:
                headlines.append(f"  - {h}")

        editors_note = parsed.get("editors_note", "")
        name = parsed.get("newspaper_name", newspaper_id)

        section = f"=== {name.upper()} ===\n"
        if headlines:
            section += "\n".join(headlines[:5])
        if editors_note:
            section += f"\nEditor's note: {editors_note[:200]}"
        sections.append(section)

    header = f"Edition date: {edition_date}\nGazette: {gazette_url}/edition/{edition_date}/\n"
    return header + "\n\n".join(sections)
