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
- [x] Implement `POST /payments/braintree-webhook` — on payment success: save prompt, categorise, route, store payment ref
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

- [x] Set up Tailwind CSS v4 + shadcn/ui + braintree-web-drop-in dependencies
- [x] Remove NxWelcome boilerplate, establish app shell with ARIA landmarks (SkipLink, Header, Footer)
- [x] Build the Orb — glowing sphere centerpiece with breathing animation, focus glow, and release animation (custom CSS keyframes + `prefers-reduced-motion` support)
- [x] Build OrbInput — shadcn Textarea inside the orb visual, character count with `aria-live`
- [x] Build cost calculator with live QuotePreview — debounced `POST /prompts/quote`, newspaper routing cards (shadcn Card + Badge)
- [x] Build PromptFlow state machine — `useReducer` with `input → payment → confirmed → error` states
- [x] Integrate Braintree Drop-in UI for payment (PaymentForm + useBraintree hook)
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
- [x] Set up environment variable management (secrets for API keys, Braintree keys) — requires GCP Secret Manager
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

- [ ] Security audit — OWASP top 10 review, dependency scanning
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

## Resolved Decisions

1. **Trigger model** — daily batch ("morning press"). Strictly once daily.
2. **World state** — single canonical ledger in PostgreSQL, no branching.
3. **Language** — English only.
4. **Monetisation** — per-prompt payment via Braintree. Cost = base x newspapers_reached.
5. **User data** — zero PII stored. Braintree owns identity.
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

## Open Questions

1. **Verbatim attribution** — should the newspaper quote user prompts directly in articles, or only use them for internal LLM grounding?
2. **Slow news day handling** — pre-compute yesterday's unused low-weight clusters as "continuing stories" backfill? Set minimum article count floor?
