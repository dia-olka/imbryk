# Imbryk — Marketing Agent

## Problem

Nobody knows Imbryk exists. The platform generates daily newspaper editions but has zero organic discovery. Manual marketing doesn't scale and isn't sustainable for a solo project. The editorial system already understands what content resonates (reader metrics, editorial reflection) — it should use that intelligence to autonomously promote itself.

## Approach: Agentic Marketing Loop

An autonomous marketing agent runs daily after each edition is published. It reads the edition, reviews what worked before, decides what to promote and where, executes the posts, and journals its results. Over time it learns which angles, formats, and channels drive traffic.

```
Cloud Scheduler (~08:00 UTC, 2h after edition)
    ↓
Marketing Agent (JOB_MODE=marketing)
    │
    ├─ OBSERVE
    │   ├─ Load today's edition from R2
    │   ├─ Load marketing journal (strategy history + results)
    │   └─ Load referrer metrics from Cloudflare (which channels drove traffic yesterday)
    │
    ├─ PLAN (LLM call)
    │   ├─ Select 2-3 most promotable articles (weight, controversy, novelty)
    │   ├─ Choose angles (contrast between newspapers, surprising takes, world events)
    │   ├─ Decide channel strategy (which platform, what format, what time)
    │   └─ Output: structured action plan (posts to create + reasoning)
    │
    ├─ ACT
    │   ├─ Generate post text per channel (character limits, hashtags, tone)
    │   ├─ Post via platform APIs
    │   └─ Record post IDs + URLs in DB
    │
    └─ REFLECT
        ├─ Compare yesterday's plan vs actual referrer traffic
        ├─ Write marketing journal entry (what was tried, what worked, what to change)
        └─ Journal feeds into tomorrow's PLAN step
```

## Channels (phased rollout)

### Phase 1: Bluesky
- **Why first**: open AT Protocol API, free, no rate limit anxiety, growing news/tech audience
- **Post types**:
  - Edition teaser (Curator voice): "Today's Imbryk: six AI newspapers can't agree whether [X] changes everything or nothing"
  - Contrast post: "The Owner calls it the deal of the decade. The Radical calls it theft."
  - Thread: 1 post per newspaper's hottest take, linked together
- **Account**: single @imbryk.bsky.social account, posts in Curator voice
- **Engagement**: the agent can like/repost relevant posts (future — requires monitoring feed)

### Phase 2: Twitter/X
- **Why second**: largest news audience, but API costs money ($100/mo basic tier)
- **Same post types** as Bluesky, adapted for character limits
- **Account**: @imbryk

### Phase 3: Reddit
- **Why third**: subreddit communities drive high-intent traffic, but anti-spam rules require careful approach
- **Target subreddits**: r/worldbuilding, r/AIgenerated, r/artificial, r/MediaSynthesis, niche topic subs matching the day's biggest story
- **Format**: thoughtful self-post with context, not link spam. "We built an AI platform with 6 competing newspaper personas. Here's how they covered [X] today."
- **Frequency**: 1-2 posts per week maximum (community norms)

### Phase 4: Newsletter / RSS
- **Weekly digest** email with the week's most-read articles and biggest editorial clashes
- **RSS feed** for aggregators (may already exist via gazette)

## Data Model

### marketing_posts table (new)

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| edition_date | TEXT | Which edition was promoted |
| channel | TEXT | `bluesky`, `twitter`, `reddit` |
| post_type | TEXT | `edition_teaser`, `contrast`, `thread`, `community_post` |
| content | TEXT | Post text as sent |
| post_url | TEXT | URL of the published post (nullable — null if posting failed) |
| post_id | TEXT | Platform-native post ID for tracking engagement |
| status | TEXT | `posted`, `failed`, `scheduled` |
| created_at | TIMESTAMP | When the post was created |

### marketing journal

Reuses the existing `editorial_journal` table with `persona_id='_marketing'`. Entries contain:
- **Strategy reflections**: what channels/angles are working
- **Referrer analysis**: which posts drove actual gazette traffic
- **Adaptation notes**: explicit reasoning about strategy changes

## Marketing Strategy Prompt (LLM)

The planning LLM call receives:

1. **Today's edition summary** — newspaper names, top article headlines + weight, Curator's FAULT LINES and CONSENSUS sections
2. **Marketing journal** — last 7 days of strategy entries (what was posted, referrer results)
3. **Referrer metrics** — Cloudflare analytics grouped by source (direct, bluesky.app, twitter.com, reddit.com, etc.)
4. **Channel constraints** — character limits, posting frequency caps, community rules
5. **Brand voice guidelines** — Curator's analytical voice for teasers; provocative-but-not-clickbait for contrast posts

The LLM outputs a structured `MarketingPlan`:
```json
{
  "reasoning": "Yesterday's contrast post got 12 reposts vs 2 for the edition teaser. Leaning into newspaper disagreements.",
  "posts": [
    {
      "channel": "bluesky",
      "post_type": "contrast",
      "target_articles": ["sovereign/article-0", "radical/article-2"],
      "angle": "Two newspapers, same event, opposite conclusions",
      "draft": "..."
    }
  ]
}
```

## Implementation Plan

### Module structure
```
newsroom_director/
  marketing/
    __init__.py
    main.py           # CLI entry point (run_marketing_agent)
    planner.py         # LLM strategy call
    channels/
      __init__.py
      base.py          # Abstract ChannelStrategy
      bluesky.py       # AT Protocol posting client
      twitter.py       # (Phase 2)
      reddit.py        # (Phase 3)
    referrers.py       # Cloudflare referrer metrics parser
```

### Entry point
- `JOB_MODE=marketing` in `__main__.py` dispatches to `marketing.main.cli_main()`
- New Cloud Run Job: `newsroom-director-marketing`, scheduled ~08:00 UTC
- Same Docker image as morning press and news scout

### Dependencies
- `atproto` — Bluesky AT Protocol client (pip package)
- Cloudflare Analytics API — already integrated in `metrics.py` (extend for referrer breakdown)

### Secrets
- `BLUESKY_HANDLE` + `BLUESKY_APP_PASSWORD` — Bluesky account credentials
- (Phase 2) `TWITTER_API_KEY` etc.

## Cost Estimate

| Component | Daily | Monthly |
|-----------|-------|---------|
| LLM planning call (Gemini Flash) | ~$0.01 | ~$0.30 |
| Bluesky API | Free | Free |
| Twitter/X API (Phase 2) | — | ~$100 |
| Additional Cloud Run Job execution | ~$0 (free tier) | ~$0 |

## Success Metrics

The agent tracks these in its journal and uses them to adapt:

- **Referrer traffic**: gazette page views originating from each channel (Cloudflare referrer data)
- **Post engagement**: reposts, likes, replies (fetched from platform APIs on next run)
- **Follower growth**: tracked weekly
- **Cost per visit**: LLM + API costs / referrer visits

## Design Decisions

1. **Curator voice for marketing** — the Curator is the only persona without ideology, making it the natural brand voice. Individual newspaper voices are too partisan for marketing.
2. **Contrast posts over summaries** — "two newspapers disagree" is inherently more shareable than "here's today's edition". The editorial tension IS the product.
3. **Journal-driven adaptation** — the marketing agent uses the same Reflexion pattern as editorial (observe → reflect → adapt). No hardcoded "post at 9am" rules — the LLM discovers what works.
4. **Single image, not Docker image** — the marketing agent runs from the same newsroom-director container. Adding a JOB_MODE is cheaper than maintaining a separate service.
5. **Bluesky first** — zero API cost, open protocol, right audience (tech-forward early adopters). Proves the loop before paying for Twitter.
6. **No automated engagement** — Phase 1 only posts, never auto-replies or auto-follows. Engagement automation is a separate decision with its own risks.
