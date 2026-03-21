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
    url: str = ""  # Target URL for embed card (for threads: comma-separated per post)


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
Lead with the conflict or surprise, not a summary. Set "url" to the edition page.
- "contrast": Highlight when two newspapers disagree sharply on the same event. \
Name the newspapers. Quote or paraphrase their positions. Set "url" to the \
more provocative newspaper's page.
- "thread": A HIERARCHICAL thread — readers see the root post first, then \
expand to see per-newspaper takes as replies. Structure it as:
  1. Root post: an intriguing hook about today's edition (url = edition page).
  2. Reply posts (2-4): each focuses on ONE newspaper's hottest take \
(url = that newspaper's page). Name the newspaper. Be specific.
  3. Final reply: the Curator's synthesis or a "read the full edition" nudge \
(url = curator page or edition page).
Separate posts with \\n---\\n. Provide matching URLs comma-separated in "url".

URL GUIDELINES:
- Every post MUST have a "url" field pointing to the most relevant page.
- The edition summary below includes URLs for the edition, each newspaper, \
and the curator. Use them directly — do not fabricate URLs.
- URLs in post text become clickable links AND show as embed cards \
(with title, description, and preview image) on Bluesky.
- For threads: "url" is a comma-separated list matching the posts in order.

RULES:
- Maximum 255 characters per post (leave room for the URL).
- Include the relevant URL at the end of each post text.
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
      "text": "Post text here (for threads, separate posts with \\n---\\n)",
      "url": "https://gazette.example/edition/2026-03-15/ (for threads: comma-separated per post)"
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
            url=p.get("url", ""),
        ))

    return MarketingPlan(
        reasoning=data.get("reasoning", ""),
        posts=posts,
    )


def build_edition_thread(
    articles: dict[str, str],
    gazette_url: str,
    edition_date: str,
    channel: str = "bluesky",
) -> list[PlannedPost] | None:
    """Build a deterministic edition thread from today's content.

    Returns a single ``thread`` PlannedPost with:
    - Root post: curator synthesis excerpt + edition URL
    - Reply posts: each newspaper's lead headline + newspaper URL

    Returns ``None`` if there's not enough content.
    """
    edition_page = f"{gazette_url}/edition/{edition_date}/"

    # --- Build curator root post ---
    curator_text = ""
    curator_json = articles.get("curator")
    if curator_json:
        try:
            parsed = json.loads(curator_json)
            # Structured format — use first consensus point + first fault line
            consensus = parsed.get("consensus", [])
            fault_lines = parsed.get("fault_lines", [])
            parts = []
            if consensus:
                parts.append(consensus[0])
            if fault_lines:
                parts.append(fault_lines[0])
            curator_text = " | ".join(parts) if parts else parsed.get("text", "")[:200]
        except (json.JSONDecodeError, TypeError):
            pass

    if not curator_text:
        curator_text = f"Today's edition is live — {edition_date}"

    # Truncate to leave room for URL (300 char limit, ~50 for URL)
    root_text = curator_text[:240]
    root_text = f"{root_text}\n{edition_page}"

    # --- Build newspaper reply posts ---
    thread_texts = [root_text]
    thread_urls = [edition_page]

    for newspaper_id, content_json in articles.items():
        if newspaper_id == "curator":
            continue

        try:
            parsed = json.loads(content_json)
        except (json.JSONDecodeError, TypeError):
            continue

        name = parsed.get("newspaper_name", newspaper_id)
        lead_headline = ""
        for a in parsed.get("articles", []):
            h = a.get("headline", "")
            if h:
                lead_headline = h
                break

        if not lead_headline:
            continue

        newspaper_page = f"{gazette_url}/edition/{edition_date}/{newspaper_id}/"
        reply_text = f"{name}: {lead_headline}"[:240]
        reply_text = f"{reply_text}\n{newspaper_page}"

        thread_texts.append(reply_text)
        thread_urls.append(newspaper_page)

    if len(thread_texts) < 2:
        return None

    # Combine into a single thread PlannedPost
    return [PlannedPost(
        channel=channel,
        post_type="thread",
        text="\n---\n".join(thread_texts),
        url=",".join(thread_urls),
        reasoning="Deterministic edition thread: curator root + newspaper replies",
    )]


def build_edition_summary(
    articles: dict[str, str],
    gazette_url: str,
    edition_date: str,
) -> str:
    """Build a concise edition summary for the marketing planner.

    Extracts headlines from each newspaper's JSON content.
    """
    edition_page = f"{gazette_url}/edition/{edition_date}/"
    curator_page = f"{gazette_url}/edition/{edition_date}/curator/"

    sections = []
    for newspaper_id, content_json in articles.items():
        try:
            parsed = json.loads(content_json)
        except (json.JSONDecodeError, TypeError):
            continue

        if newspaper_id == "curator":
            text = parsed.get("text", "")
            if text:
                sections.append(
                    f"=== THE CURATOR ===\nURL: {curator_page}\n{text[:500]}"
                )
            continue

        newspaper_page = f"{gazette_url}/edition/{edition_date}/{newspaper_id}/"

        headlines = []
        for a in parsed.get("articles", []):
            h = a.get("headline", "")
            if h:
                headlines.append(f"  - {h}")

        editors_note = parsed.get("editors_note", "")
        name = parsed.get("newspaper_name", newspaper_id)

        section = f"=== {name.upper()} ===\nURL: {newspaper_page}\n"
        if headlines:
            section += "\n".join(headlines[:5])
        if editors_note:
            section += f"\nEditor's note: {editors_note[:200]}"
        sections.append(section)

    header = f"Edition date: {edition_date}\nEdition URL: {edition_page}\nCurator URL: {curator_page}\n"
    return header + "\n\n".join(sections)
