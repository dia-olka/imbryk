# Imbryk — Production Release Plan

## Status Key

- [ ] Not started
- [~] In progress
- [x] Done

---

## Phase 1: Genesis (Monorepo Foundation) [x]

- [x] Nx workspace with React frontend scaffold
- [x] `@org/world-state` library — WorldLedger types + empty template
- [x] `@org/ai-personas` library — newsroom personas with system prompt templates
- [x] `apps/ingestion-api` scaffold — FastAPI with stub endpoints
- [x] `apps/newsroom-director` scaffold — Morning Press pipeline outline
- [x] `@nxlv/python` plugin registered, all projects lint/typecheck/test green

---

## Phase 2: Taxonomy & Category System [x]

- [x] Finalise the 30-category taxonomy — 6 groups, curated topic labels (see ARCHITECTURE.md)
- [x] Create `packages/taxonomy` library — category registry, subscription map, router, pricing helper
- [x] Define newspaper-to-category subscription mappings (8-9 categories per newspaper) for the 6 newspapers
- [x] Implement routing function: given prompt categories, return matching newspapers via set intersection
- [x] Implement pricing helper: `newspapers_reached` count for cost calculation
- [x] Redesign `packages/ai-personas` — replace old 7 personas with the 6 audience-archetype newspapers (The Sovereign, The Aspirant, The Owner, The Moralist, The Radical, The Hedonist) plus The Curator
- [x] Add `subscribedCategories`, `modelTier`, `regionalBias`, and `toneAdjustment` to each persona definition
- [x] Update system prompt templates — `{{CLUSTER_DIGESTS}}` placeholder, weighting instructions, output schema guidance
- [x] Write tests: taxonomy (15 tests), personas (13 tests) — routing, pricing, edge cases, field coverage

---

## Phase 3: World Lore & Prompt Engineering [x]

- [x] Author the initial WorldLedger — populate the template with founding lore (nations, alliances, economic blocs, tech landscape, environmental state, seed history)
- [x] Write a `WorldLedger -> synopsis` serialiser that compresses the ledger into a text block for `{{WORLD_LEDGER_SYNOPSIS}}`
- [x] Write a `WorldLedger + event -> updated WorldLedger` mutation function (`LedgerMutation` + `applyMutation`)
- [x] Add `packages/prompt-engine` library with template interpolation utilities (`interpolateTemplate`, `buildNewspaperPrompt`, `buildCuratorPrompt`)
- [x] Update persona system prompt templates to use `{{CLUSTER_DIGESTS}}` placeholder (replacing `{{EVENT_DESCRIPTION}}`) — completed in Phase 2
- [x] Add weighting instructions to system prompts — how to interpret aggregate_weight and verbatim markers `[w:XXXX]` — completed in Phase 2
- [x] Add output schema to system prompts — newspaper structure with sections, article slots, "In Brief" for minor clusters — completed in Phase 2
- [x] Write integration tests: template interpolation -> valid prompt string for each persona

---

## Phase 4: Prompt Distillation Pipeline [x]

- [x] Add `sentence-transformers` dependency to newsroom-director (`all-MiniLM-L6-v2`, torch 2.2, numpy 1.x, hdbscan, scikit-learn)
- [x] Implement prompt embedding — `distillation/embedder.py` using sentence-transformers, `embed()` and `embed_weighted()` methods
- [x] Implement weight scoring — `distillation/scorer.py`: `weight = payment_amount_norm x uniqueness_bonus` with cosine-similarity near-duplicate detection
- [x] Implement HDBSCAN clustering — `distillation/clusterer.py`: groups prompts into clusters, ranks by aggregate_weight, handles small pools gracefully
- [x] Implement cluster ranking by aggregate_weight (integrated into clusterer, sorted descending)
- [x] Implement cluster digest construction — `distillation/digest.py`:
  - [x] Sort prompts by weight descending within each cluster
  - [x] Select top K prompts verbatim (K = min(20, cluster_size))
  - [x] LexRank-inspired extractive summarisation for remaining prompts
  - [x] Assemble digest: cluster_size, aggregate_weight, verbatim prompts, long-tail summary, keywords
- [x] Implement token budget allocation — `distillation/budget.py`:
  - [x] Total budget ~800K tokens (configurable)
  - [x] Proportional allocation: `tokens_per_cluster = (cluster_weight / total_weight) x budget`
  - [x] Minimum floor (500 tokens) and maximum cap (150K tokens) per cluster
  - [x] Low-volume handling: equal allocation when no weight info
  - [x] High-volume handling: `merge_low_weight_clusters()` into "Other Topics"
- [x] Write unit tests for each pipeline stage (50 tests: scorer 10, clusterer 5, digest 10, budget 12, embedder 6, pipeline 6, hello 1)

---

## Phase 5: Ingestion API & Database [x]

- [x] Design schema: `prompts`, `categorised_prompts`, `payment_refs`, `editions`, `edition_articles` (SQLAlchemy 2.x models, Alembic migrations)
- [x] Set up database layer — SQLAlchemy engine, session dependency, in-memory SQLite for tests, Alembic initial migration
- [x] Implement `POST /prompts/quote` — accept draft prompt, run categoriser, compute newspaper routing, return cost estimate (newspapers_reached x base price)
- [x] Implement `CategoriserStrategy` interface, `StubCategoriser`, and `GeminiFlashCategoriser` — classify prompt into 1-K categories from the 30-category taxonomy
- [x] Port taxonomy routing to Python — 30 categories, 6 newspaper subscriptions, `route_prompt` set intersection, `count_newspapers_reached`
- [x] Implement `POST /payments/stripe-webhook` — on payment success: save prompt, categorise, route, store payment ref
- [x] Implement `GET /editions` — list editions from DB
- [x] Implement pricing module — `calculate_cost(newspapers_reached)`
- [x] Add input validation — prompt length limits (10-2000 chars)
- [x] Add rate limiting — SlowAPI middleware on `/prompts/quote`
- [x] Write tests — 23 tests across taxonomy (10), categoriser (4), pricing (3), API integration (6)

---

## Phase 6: Newsroom Director Implementation [x]

- [x] Implement batch job entry point (Cloud Run Job trigger)
- [x] Implement: pull unprocessed categorised prompts from PostgreSQL
- [x] Implement: route prompts to newspapers via taxonomy (set intersection)
- [x] Implement: load WorldLedger from PostgreSQL
- [x] Implement Vertex AI context cache creation from WorldLedger synopsis
- [x] Implement world coherence validation (Pro model) — accept/reject prompts against current world state
- [x] Implement per-newspaper distillation pipeline integration:
  - [x] Embed newspaper's prompt pool (local sentence-transformers)
  - [x] Cluster via HDBSCAN
  - [x] Build weighted cluster digests
  - [x] Allocate token budget
  - [x] Single Gemini call with persona system prompt, ledger context, and allocated digests
- [x] Implement per-newspaper model tier config map (Pro vs Flash per persona)
- [x] Implement Curator synthesis (Pro model) — input: all generated articles, output: meta-analysis
- [x] Implement WorldLedger mutation (Pro model) — apply consequences, write back to PostgreSQL transactionally
- [x] Implement R2 write — store edition articles as JSON (full articles, in brief, editor's note, metadata block)
- [x] Implement context cache force-deletion
- [x] Add retry logic and error handling for Gemini API failures (cache cluster digests so failed calls can retry without recomputing)
- [x] Add structured logging (edition ID, newspaper ID, model tier, latency, token usage, cluster count)
- [x] Write end-to-end test: sample prompts -> full edition output across multiple newspapers

---

## Phase 7: Gazette — Static Site Generator [x]

- [x] Scaffold `apps/gazette` with 11ty v3 — package.json, project.json, eleventy.config.js
- [x] Data files importing from workspace packages (`@org/ai-personas`, `@org/world-state`, `@org/taxonomy`)
- [x] Sample edition JSON fixture for template development
- [x] Design newspaper page templates (edition index, per-newspaper article pages, In Brief section, Editor's note, Curator synthesis)
- [x] Build persona identity cards (ideology, biases, blindspots, subscribed categories) into article templates
- [x] Build world timeline page from WorldLedger history
- [x] Build edition archive with pagination
- [x] Build newspaper directory — the 6 newspapers with their identity cards and category subscriptions
- [x] Mobile-first responsive design, WCAG 2.2 AA (skip links, focus indicators, semantic HTML, ARIA landmarks, contrast ratios)

---

## Phase 8: Frontend — Prompt Submission UI ("The Orb") [x]

- [x] Set up Tailwind CSS v4 + shadcn/ui + @stripe/stripe-js dependencies
- [x] Remove NxWelcome boilerplate, establish app shell with ARIA landmarks (SkipLink, Header, Footer)
- [x] Build the Orb — glowing sphere centerpiece with breathing animation, focus glow, and release animation (custom CSS keyframes + `prefers-reduced-motion` support)
- [x] Build OrbInput — shadcn Textarea inside the orb visual, character count with `aria-live`
- [x] Build cost calculator with live QuotePreview — debounced `POST /prompts/quote`, newspaper routing cards (shadcn Card + Badge)
- [x] Build PromptFlow state machine — `useReducer` with `input → payment → confirmed → error` states
- [x] Integrate Stripe Checkout (hosted redirect) for payment (PaymentForm component)
- [x] Build Confirmation view — success alert, newspaper list, "Submit another" button
- [x] Build ErrorBoundary with retry
- [x] Mobile-first layout, WCAG 2.2 AA compliance (skip link, focus rings, labels, contrast, touch targets)
- [x] Keyboard navigation and screen reader testing — ARIA landmarks, skip link, focus rings, labels verified in tests
- [x] Write tests — app shell, OrbInput, QuotePreview, useQuote hook (25 tests passing)
- [x] Deploy to Cloudflare Pages — requires Cloudflare account setup (see DEPLOYMENT.md)

---

## Phase 9: Integration & DevOps [x]

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed infrastructure setup, containerisation, and deployment procedures.

- [x] Set up CI/CD pipeline (GitHub Actions) — JS job (lint, test, build, typecheck) + Python job (lint, test) + Docker build check
- [x] Configure Cloudflare R2 bucket and access credentials — requires Cloudflare account
- [x] Set up Vertex AI project, service account, and API keys — requires GCP project
- [x] Set up GCP Pub/Sub topic and subscription — requires GCP project
- [x] Configure Cloud Scheduler for daily morning trigger — requires GCP project
- [x] Containerise Python apps (Dockerfile per app, include sentence-transformers model in newsroom-director image)
- [x] Deploy ingestion-api to Cloud Run — requires GCP project + container registry
- [x] Deploy newsroom-director as Cloud Run Job — requires GCP project + container registry
- [x] Set up environment variable management (secrets for API keys, Stripe keys) — requires GCP Secret Manager
- [x] Configure CORS between prompt UI and API — CORSMiddleware added, configurable via `CORS_ALLOWED_ORIGINS` env var
- [x] Set up monitoring and alerting (error rates, API latency, Gemini token spend, cluster quality metrics) — requires GCP project
- [x] Set up Cloudflare Pages deployment for gazette output — requires Cloudflare account
- [x] Automate: morning run completes -> gazette rebuild -> deploy — requires deploy hook URL

---

## Phase 10: Article Image Generation [x]

Article images generated by Vertex AI Imagen give each newspaper edition a visual identity. The Gemini generation step already produces the article structure — this phase adds an `imagePrompt` field to each article and a post-generation step that calls Imagen to produce images.

### Design

- **Which articles get images:** top articles by cluster weight (configurable, default: top 3 per newspaper) + the front-page/hero image. "In Brief" items do not get images.
- **imagePrompt field:** nullable `string | null` on each article in the Gemini output schema. The Gemini call is instructed to produce an `imagePrompt` — a short, vivid scene description optimised for image generation — for articles that warrant one, and `null` for the rest. The persona's editorial lens should colour the image prompt (e.g., The Hedonist's images are glamorous, The Sovereign's are institutional).
- **Imagen call:** after Gemini generates all articles, a post-generation step iterates articles with non-null `imagePrompt` and calls Vertex AI Imagen to produce one image per prompt. Images are stored alongside the edition JSON in R2.
- **Front-page image:** each newspaper edition gets one hero image. The Gemini output includes a top-level `frontPageImagePrompt` (nullable) — a single scene description capturing the day's dominant story. If null, the gazette renders without a hero image.
- **Fallback:** if Imagen fails for a specific article, the article publishes without an image. Image generation failures must not block the edition pipeline.
- **Storage:** images stored in R2 at `editions/{edition_id}/{newspaper_id}/{article_index}.webp` (and `hero.webp` for the front page). WebP format for size efficiency.
- **Model:** Vertex AI Imagen (the current production image generation model available via Vertex AI).

### Tasks

- [x] Add `imagePrompt: string | null` to article type in `NewsroomPersona` output schema (TypeScript types in `ai-personas`, Python dataclass in newsroom-director)
- [x] Add `frontPageImagePrompt: string | null` to the top-level newspaper edition output schema
- [x] Update Gemini system prompt templates — instruct each persona to produce `imagePrompt` for top articles and a `frontPageImagePrompt` for the edition, with persona-appropriate visual direction
- [x] Add `image_url: string | null` column to `edition_articles` table (Alembic migration)
- [x] Implement Imagen client in newsroom-director — `image_gen/client.py`: accepts a text prompt, calls Vertex AI Imagen, returns image bytes
- [x] Implement image generation step in the pipeline — after Gemini generation, iterate articles with non-null `imagePrompt`, call Imagen, upload to R2
- [x] Implement front-page image generation — call Imagen with `frontPageImagePrompt`, upload as `hero.webp`
- [x] Store image URLs in `content_json` (alongside article text) and in the `image_url` column
- [x] Update gazette templates — render `<img>` with `loading="lazy"`, `alt` text from imagePrompt, and `<figure>`/`<figcaption>` semantics
- [x] Update gazette front page / edition index — render hero image if present
- [x] Add `srcset` / responsive images in gazette for mobile vs desktop
- [x] Add WCAG-compliant `alt` text — use the imagePrompt as the alt text (it is already a scene description)
- [x] Write tests — image client (mock Imagen API), pipeline integration (articles with/without imagePrompt), gazette template rendering with images
- [x] Update DEPLOYMENT.md — add Imagen API enablement, cost estimates, and any additional IAM roles

### Cost Estimate

| Component | Per Image | Daily (est.) | Monthly (est.) |
|---|---|---|---|
| Imagen generation | ~$0.02-0.04/image | ~$0.40-1.00 (6 papers x 3-4 images) | ~$12-30 |
| R2 storage (WebP, ~100KB each) | — | ~20 images/day | ~$0 (free tier) |

### Design Decisions (resolved)

- **Image style:** distinct per-persona — The Sovereign uses institutional/documentary photography, The Aspirant uses documentary/aspirational, The Owner uses financial/corporate, The Moralist uses warm/traditional, The Radical uses raw/urgent photojournalism, The Hedonist uses glamorous/saturated lifestyle imagery.
- **Image count:** Gemini decides which articles get `imagePrompt`; pipeline renders top 3 by weight + 1 hero per newspaper. Configured via `MAX_ARTICLE_IMAGES` (default: 3).
- **Imagen model:** `imagen-3.0-generate-002`, 16:9 aspect ratio, WebP output.

---

## Phase 11: Hardening & Launch Prep

### Gazette R2 Integration

- [x] Add `write_index()` to `EditionStorage` interface and `R2EditionStorage` — writes `editions/index.json` manifest after each edition
- [x] Add deploy hook trigger to newsroom-director — POSTs to Cloudflare Pages deploy hook after edition commit (`CF_DEPLOY_HOOK_URL`)
- [x] Create `loadEditions()` helper for gazette — fetches from R2 (prod) or reads local fixture (dev), with `transformR2Edition()` shape converter
- [x] Refactor gazette data files (`editions.js`, `newspaperPages.js`, `articlePages.js`) to use shared `loadEditions()` instead of hardcoded fixture reads
- [x] Enable R2 public access in DEPLOYMENT.md (Step 3.2)
- [x] Add `R2_PUBLIC_URL` env var to gazette Cloudflare Pages config
- [x] Add `CF_DEPLOY_HOOK_URL` secret to newsroom-director deploy command (Step 5.3)
- [x] Update env vars reference tables in DEPLOYMENT.md
- [x] Verify end-to-end: newsroom-director writes edition + index → triggers deploy hook → gazette builds from R2

### General Hardening

- [x] Security audit — OWASP top 10 review (A01–A08, A10 addressed in code; A09 dependency scanning not yet automated in CI)
- [ ] Verify zero PII — audit all database tables, logs, and error reports for personal data leakage
- [ ] Performance testing — Gemini call latency, embedding/clustering throughput, end-to-end pipeline timing
- [ ] Cost modelling — Gemini token usage per edition (~$3/newspaper x 6 newspapers = ~$18/day), R2 storage growth, Pub/Sub costs
- [ ] Pipeline validation on real data — run full pipeline with sample prompts, manually inspect cluster quality and article output
- [ ] Tune HDBSCAN parameters (min_cluster_size, min_samples) based on real prompt data
- [ ] Calibrate weight formula against editorial judgment — A/B test which prompts get coverage
- [ ] Calibrate "In Brief" threshold — what weight floor separates a full article from a brief mention
- [ ] User acceptance testing with sample world events
- [x] Set up error tracking (Sentry) — `@sentry/react` in frontend (ErrorBoundary + browser tracing), `sentry-sdk[fastapi]` in ingestion API. DSN via `VITE_SENTRY_DSN` / `SENTRY_DSN` env vars. Disabled when DSN is empty.
- [ ] Define and implement backup strategy for WorldLedger in PostgreSQL
- [ ] Define failure behaviour: if pipeline fails, publish nothing vs last successful edition vs stub
- [ ] Refine persona system prompt templates — test each against sample events, tune voice/bias fidelity
- [ ] Validate distillation pipeline on sample data — embed 10K-100K sample prompts, inspect clusters manually
- [ ] Validate weight scoring — confirm high-weight prompts surface meaningfully different content than count-weighted selection
- [ ] Validate digest quality — does the digest faithfully represent the cluster and preserve verbatim voice?
- [ ] Launch checklist: DNS, SSL, rate limits, monitoring dashboards

---

## Phase 12: News Scout — Real-World Gap Filling

When user prompts don't cover all 30 categories, newspapers have thin or empty editions. The News Scout fills gaps by using an LLM (informed by the WorldLedger) to generate search queries, executing them via Tavily, and feeding results into the existing pipeline at lower weight than paid prompts. See ARCHITECTURE.md § "News Scout — Real-World Gap Filling" for full design.

### Database & Models

- [x] Add `news_items` table — Alembic migration (`id`, `edition_date`, `category_id`, `query`, `headline`, `snippet`, `source_url`, `relevance_score`, `status`, `created_at`; unique on `(source_url, edition_date)`)
- [x] Add SQLAlchemy model in `ingestion-api/models.py`
- [x] Mirror model in `newsroom-director/db.py`

### News Scout Module (newsroom-director)

- [x] Add `tavily-python` dependency to newsroom-director
- [x] Implement `news_scout/query_generator.py` — Gemini Flash call that takes WorldLedger synopsis + 30 categories and returns a `dict[category_id, list[str]]` of search queries
- [x] Design query generation prompt — instruct the LLM to reason from the WorldLedger about what's editorially interesting, not what's popular; output 2–3 queries per category
- [x] Implement `news_scout/searcher.py` — Tavily client wrapper; executes queries, returns structured results (headline, snippet, source_url, relevance_score). Abstract `SearchStrategy` + `TavilySearcher` + `StubSearcher`.
- [x] Implement `news_scout/schemas.py` — Gemini structured output schema (`QueryGenerationOutput`), validation (`is_valid_query_output`), parsing (`parse_query_output`)
- [x] Implement `news_scout/main.py` — entry point: load WorldLedger → generate queries → execute searches → deduplicate by URL → store in `news_items` table
- [x] Add `NEWS_SCOUT_ENABLED` env var (default `true`) — allows disabling the scout without redeploying
- [x] Add `TAVILY_API_KEY` to config — env var for secret management
- [x] Write tests — schema validation (7), query generator (4), searcher (2), DB operations (6), scout pipeline (3) = 22 tests

### Morning Batch Integration (newsroom-director)

- [x] Add `fetch_pending_news_items(edition_date)` to `db.py` — reads today's news items with `status='pending'`
- [x] Add `NewsItemRecord` → `DistillationPrompt` converter in `main.py` — wraps news items with `weight=NEWS_ITEM_BASE_WEIGHT` (configurable, default `0.3`)
- [x] Update `main.py` — after fetching user prompts, also fetch news items and merge into the prompt pool via taxonomy routing
- [x] Update coherence validation — skip news items (only validate user-submitted prompts)
- [x] Implement `NEWS_MUTATES_LEDGER` flag (env var, default `true`) — when `true`, mutation runs on all published articles; when `false`, mutation only runs if at least one user prompt was processed in this edition
- [x] Update `mark_processed` step — also set `news_items.status='processed'` for today's items
- [x] Add `NEWS_ITEM_BASE_WEIGHT` to configuration (env var, default `0.3`)
- [x] Write tests — news-only edition, mixed sources, weight verification, mutation flag both modes, validation skips news items = 7 tests

### Infrastructure & Deployment

- [x] Create Cloud Scheduler job for News Scout (~03:00 UTC, ~3 hours before morning batch)
- [x] Add `TAVILY_API_KEY` to GCP Secret Manager
- [x] Add News Scout entry point to newsroom-director Dockerfile — `JOB_MODE` env var + `__main__.py` dispatcher, separate `newsroom-director-scout` Cloud Run Job
- [x] Update `cd.yml` — deploys both `newsroom-director` (`JOB_MODE=morning-press`) and `newsroom-director-scout` (`JOB_MODE=news-scout`)
- [x] Update DEPLOYMENT.md — two Cloud Run Jobs, separate scheduler URIs, `JOB_MODE` docs
- [x] Add monitoring/alerting for News Scout failures — Sentry `event_level=WARNING`, shared `configure_logging()` init for both entry points
- [x] Run Alembic migration `007` on production PostgreSQL

### Validation & Tuning

- [ ] Test News Scout end-to-end: WorldLedger → queries → Tavily → news_items → morning batch → edition with mixed sources
- [ ] Verify weight hierarchy: in a category with both user prompts and news items, user prompts dominate digests
- [ ] Verify gap filling: in a category with only news items, the newspaper still generates meaningful articles
- [ ] Tune `NEWS_ITEM_BASE_WEIGHT` — too high and news drowns user voice; too low and news items cluster as noise
- [ ] Tune query count per category — balance coverage breadth vs Tavily cost
- [ ] Verify News Scout failure is non-blocking — disable Tavily API and confirm morning batch runs cleanly with user prompts only

---

## Phase 13: Editorial Memory — Journal & Reader Metrics

Each AI editor develops persistent editorial memory across runs via two complementary systems: an **Editorial Journal** (self-reflection after each edition) and **Reader Metrics** (Cloudflare page-view data feeding back into editorial decisions). Uses the Scratchpad + Reflexion pattern: Generate → Reflect → Record → Improve.

### Phase 13a: Editorial Journal

- [x] Add `editorial_journal` table — Alembic migration 008 (`id`, `persona_id`, `entry_date`, `entry_type`, `content`, `created_at`; unique on `(persona_id, entry_date, entry_type)`)
- [x] Add SQLAlchemy model in `ingestion-api/models.py` (`EditorialJournal`)
- [x] Add ORM model + dataclasses in `newsroom-director/db.py` (`EditorialJournalRow`, `JournalEntry`)
- [x] Implement `save_journal_entry()` — upserts by (persona_id, entry_date, entry_type)
- [x] Implement `load_recent_journal()` — loads entries within configurable lookback window
- [x] Implement `reflection.py` — per-persona self-reflection (`run_persona_reflection`, Flash tier) and pipeline-level observation (`run_pipeline_observation`, Pro tier)
- [x] Implement `format_journal_for_generation()` — condensed view for `{{EDITORIAL_JOURNAL}}` placeholder (latest intention + last 3 reflections + latest pipeline observation)
- [x] Add `{{EDITORIAL_JOURNAL}}` placeholder to all 6 newspaper persona prompts in `data/personas.json`
- [x] Wire journal loading + injection into `main.py` (Step 6b: load entries, Step 7: inject into system prompt)
- [x] Wire reflection into `main.py` (Step 8c: run per-persona reflections + pipeline observation after generation)
- [x] Add config: `ENABLE_EDITORIAL_JOURNAL` (default: true), `JOURNAL_LOOKBACK_DAYS` (default: 7)
- [x] Write tests — 17 tests (DB operations, formatting, reflection execution)

### Phase 13b: Reader Metrics

- [x] Add `edition_metrics` table — Alembic migration 009 (`id`, `edition_date`, `newspaper_id`, `article_slug`, `headline`, `page_views`, `fetched_at`; unique on `(edition_date, newspaper_id, article_slug)`)
- [x] Add SQLAlchemy model in `ingestion-api/models.py` (`EditionMetric`)
- [x] Add ORM model + dataclasses in `newsroom-director/db.py` (`EditionMetricRow`, `ArticleMetric`)
- [x] Implement `save_edition_metrics()` and `load_edition_metrics()` — upsert and load by edition date
- [x] Implement `metrics.py` — `MetricsClient` (Cloudflare GraphQL Analytics API), `StubMetricsClient`, `enrich_metrics_with_headlines()`, `format_metrics_for_reflection()`, `format_metrics_for_pipeline_observation()`
- [x] Wire metrics fetching into `main.py` (Step 8b: fetch previous day's metrics from Cloudflare, enrich headlines, persist to DB)
- [x] Wire metrics text into reflection prompts (Step 8c: per-persona and pipeline metrics injected into reflection)
- [x] Add Cloudflare Web Analytics beacon to gazette `base.njk` (conditional on `CF_WEB_ANALYTICS_TOKEN`)
- [x] Add `cfWebAnalyticsToken` to gazette `site.js`
- [x] Add config: `ENABLE_READER_METRICS` (default: false), `CF_ANALYTICS_ZONE_ID`, `CF_ANALYTICS_API_TOKEN`
- [x] Write tests — 22 tests (DB operations, client parsing, enrichment, formatting)
- [x] Update DEPLOYMENT.md — new env vars, Cloudflare Web Analytics setup (Step 3.7), Secret Manager (Step 3.4b), CD workflow
- [x] Update `cd.yml` — add new env vars and secrets to newsroom-director deploy step

### Infrastructure & Deployment

- [x] Create Cloudflare API token with `Analytics:Read` permission
- [x] Store `cf-analytics-zone-id` and `cf-analytics-api-token` in GCP Secret Manager
- [x] Set `CF_WEB_ANALYTICS_TOKEN` on gazette Cloudflare Pages project
- [x] Set GitHub Actions vars: `ENABLE_READER_METRICS=true` (set 2026-03-14). `ENABLE_EDITORIAL_JOURNAL` and `JOURNAL_LOOKBACK_DAYS` use defaults in `cd.yml` (true / 7).
- [x] Run Alembic migrations 008 + 009 on production PostgreSQL
- [x] Enable `ENABLE_READER_METRICS=true` — live on newsroom-director job

---

## Phase 14: Marketing Agent — Autonomous Promotion

An agentic marketing loop that reads each day's edition, plans a promotion strategy informed by past performance, posts to social channels, and journals results for continuous adaptation. See [MARKETING.md](MARKETING.md) for full design, data model, channel strategy, and cost estimates.

### Phase 14a: Foundation & Bluesky

- [ ] Add `marketing_posts` table — Alembic migration (`id`, `edition_date`, `channel`, `post_type`, `content`, `post_url`, `post_id`, `status`, `created_at`)
- [ ] Add SQLAlchemy model in `ingestion-api/models.py`, mirror in `newsroom-director/db.py`
- [ ] Implement `marketing/main.py` — CLI entry point (`run_marketing_agent`): observe → plan → act → reflect
- [ ] Implement `marketing/planner.py` — LLM strategy call (Gemini Flash): receives edition summary + marketing journal + referrer metrics, outputs structured `MarketingPlan`
- [ ] Implement `marketing/channels/base.py` — abstract `ChannelStrategy` (post, fetch_engagement)
- [ ] Implement `marketing/channels/bluesky.py` — AT Protocol client (`atproto` package): create post, create thread, fetch post engagement stats
- [ ] Implement `marketing/referrers.py` — extend Cloudflare Analytics client to fetch referrer breakdown (bluesky.app, twitter.com, reddit.com, direct)
- [ ] Reuse editorial journal table with `persona_id='_marketing'` for strategy reflections
- [ ] Add `JOB_MODE=marketing` dispatch in `__main__.py`
- [ ] Add `atproto` dependency to `pyproject.toml`
- [ ] Add config: `MARKETING_ENABLED` (default: false), `BLUESKY_HANDLE`, `BLUESKY_APP_PASSWORD`
- [ ] Write tests — planner (structured output validation), Bluesky client (mock AT Protocol), referrer parsing, journal integration
- [ ] Create Bluesky account (@imbryk.bsky.social)

### Phase 14b: Infrastructure & Deployment

- [ ] Create `newsroom-director-marketing` Cloud Run Job (same image, `JOB_MODE=marketing`)
- [ ] Create Cloud Scheduler trigger (~08:00 UTC, 2h after morning press)
- [ ] Add `BLUESKY_HANDLE` + `BLUESKY_APP_PASSWORD` to GCP Secret Manager
- [ ] Update `cd.yml` — add third Cloud Run Job update step for `newsroom-director-marketing`
- [ ] Run Alembic migration on production PostgreSQL

### Phase 14c: Twitter/X (when budget allows)

- [ ] Implement `marketing/channels/twitter.py` — Twitter API v2 client
- [ ] Add `TWITTER_API_KEY`, `TWITTER_API_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_SECRET` to secrets
- [ ] Update planner prompt — multi-channel strategy (Bluesky + Twitter, avoid duplicate content)
- [ ] Create Twitter/X account (@imbryk)

### Phase 14d: Reddit (when community presence is established)

- [ ] Implement `marketing/channels/reddit.py` — Reddit API client (self-posts only, no link spam)
- [ ] Define subreddit allowlist and frequency caps (max 1-2 posts/week per subreddit)
- [ ] Update planner prompt — Reddit community norms, long-form format, weekly cadence
- [ ] Create Reddit account

---

## Resolved Decisions

1. **Trigger model** — daily batch ("morning press"). Strictly once daily.
2. **World state** — single canonical ledger in PostgreSQL, no branching.
3. **Language** — English only.
4. **Monetisation** — per-prompt payment via Stripe Checkout. Cost = base x newspapers_reached. Stripe Adaptive Pricing handles multi-currency (EUR/GBP/etc.) display automatically.
5. **User data** — zero PII stored. Stripe owns identity.
6. **Reading experience** — static HTML via 11ty + Cloudflare Pages. Free, no registration.
7. **Prompt UI** — separate React SPA (`apps/imbryk`).
8. **Categorisation model** — Gemini Flash via `CategoriserStrategy` interface (swappable to local model later).
9. **Two-level taxonomy** — 30 curated categories route prompts. 6 audience-archetype newspapers subscribe to categories and run independent pipelines. Categories are stable; newspaper count is fixed at 6.
10. **Newspaper roster** — The Sovereign (establishment), The Aspirant (idealist), The Owner (financial), The Moralist (traditionalist), The Radical (anti-establishment), The Hedonist (entertainment), plus The Curator (synthesis). Inspired by the *Yes Minister* newspaper readership archetypes.
11. **Per-newspaper model tiers** — Pro for The Sovereign, The Owner, Curator, validation, ledger mutation. Flash for The Aspirant, The Moralist, The Radical, The Hedonist. Configurable per newspaper.
12. **Content moderation** — the Newsroom Director (Pro model with full world context) validates prompt coherence before article generation. The categoriser does not gate content. Payment itself filters casual abuse.
13. **Prompt distillation** — four-stage local pipeline (embed, cluster, digest, allocate) before a single Gemini call per newspaper. Distillation quality sets the article quality ceiling.
14. **Prompt merging** — multiple prompts landing in the same newspaper are clustered via HDBSCAN, then distilled into weighted digests with verbatim high-value prompts and extractively summarised long tail.
15. **Overlap between newspapers** — intentional. When multiple newspapers receive the same prompt via shared categories, independent pipelines produce genuinely distinct articles from different editorial lenses.
16. **Article output format** — full articles (8-18) for top clusters, "In Brief" section for minor clusters, Editor's note for cross-cluster observations, metadata block for auditability.
17. **Article images** — Vertex AI Imagen generates images for top articles and a front-page hero per newspaper. The Gemini output includes a nullable `imagePrompt` per article and a `frontPageImagePrompt` per edition. Images stored as WebP in R2. Failures are non-blocking — articles publish without images if Imagen fails.
18. **Gap filling via LLM-driven news scouting** — instead of Google Trends or human curation, the system uses its own LLM (informed by the WorldLedger) to decide what real-world news is editorially interesting. Queries are executed via Tavily. News items enter the same distillation pipeline at lower weight than any paid prompt, so user voice always dominates. WorldLedger mutation from news is controlled by `NEWS_MUTATES_LEDGER` flag (default `true` at launch so the world evolves even with zero users; set to `false` once user volume is sufficient).
19. **News Scout is strictly additive** — the scout runs as a separate pre-batch job. Its failure never blocks the morning batch. The system degrades gracefully to user-prompts-only mode if the scout fails or is disabled.
20. **Editorial memory via Reflexion pattern** — after each edition, every persona reflects on its output (what worked, what fell short, tomorrow's intentions) and saves a journal entry. These entries are loaded into the next day's generation prompt via `{{EDITORIAL_JOURNAL}}`. A pipeline-level observation by an "editorial director" provides cross-publication feedback. Reader metrics from Cloudflare Web Analytics optionally inform reflections. Both features are independently toggleable and fail gracefully.
21. **Autonomous marketing via agentic loop** — a separate Marketing Agent (same Docker image, `JOB_MODE=marketing`) runs ~2 hours after each edition. It reads the edition, reviews its own journal of past marketing actions + referrer metrics, uses an LLM to plan the day's promotion strategy, posts to social channels (Bluesky first, then Twitter/X, then Reddit), and journals results. The agent adapts over time — the same Reflexion pattern used for editorial quality now drives audience growth. See [MARKETING.md](MARKETING.md).

## Open Questions

1. **Verbatim attribution** — should the newspaper quote user prompts directly in articles, or only use them for internal LLM grounding?
2. ~~**Slow news day handling**~~ — resolved by Phase 12 (News Scout). Real-world news fills category gaps on quiet days.
3. **News item attribution in articles** — should generated articles cite real-world sources (e.g. "according to Reuters") when content originates from a news item, or treat all input uniformly without source attribution?
4. **News Scout query freshness** — should the scout account for which categories already have user prompts today (generate fewer queries for covered categories) or always generate queries for all 30 categories regardless?

## TODO

- [ ] **R2 backfill for malformed editions** — existing editions in R2 (e.g. 2026-03-06) were generated before the explicit JSON schema was added to the persona preamble. The gazette normaliser (`loadEditions.js`) works around this at read time, but the canonical R2 files still contain wrong field names (`title`/`content` instead of `headline`/`body`). Write a one-off migration script that fetches each edition JSON from R2, renames the mismatched fields, and re-uploads, so the stored data matches the schema without relying on the normaliser forever. See PLAN.md Option B discussion.
