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

## Phase 8: Frontend — Prompt Submission UI

- [ ] Remove NxWelcome boilerplate, establish app shell
- [ ] Build prompt submission form — event description textarea
- [ ] Build cost calculator — show estimated cost based on newspapers_reached (calls `/prompts/quote`)
- [ ] Show which newspapers will cover the prompt (category routing preview)
- [ ] Integrate Braintree Drop-in UI for payment
- [ ] Build confirmation view — payment success, prompt queued for next morning edition, list of newspapers that will receive it
- [ ] Mobile-first layout, WCAG 2.2 AA compliance
- [ ] Keyboard navigation and screen reader testing
- [ ] Loading states, error boundaries, empty states
- [ ] Deploy to Cloudflare Pages

---

## Phase 9: Integration & DevOps

- [ ] Set up CI/CD pipeline (GitHub Actions) — lint, typecheck, test on PR
- [ ] Configure Cloudflare R2 bucket and access credentials
- [ ] Set up Vertex AI project, service account, and API keys
- [ ] Set up GCP Pub/Sub topic and subscription
- [ ] Configure Cloud Scheduler for daily morning trigger
- [ ] Containerise Python apps (Dockerfile per app, include sentence-transformers model in newsroom-director image)
- [ ] Deploy ingestion-api to Cloud Run
- [ ] Deploy newsroom-director as Cloud Run Job
- [ ] Set up environment variable management (secrets for API keys, Braintree keys)
- [ ] Configure CORS between prompt UI and API
- [ ] Set up monitoring and alerting (error rates, API latency, Gemini token spend, cluster quality metrics)
- [ ] Set up Cloudflare Pages deployment for gazette output
- [ ] Automate: morning run completes -> gazette rebuild -> deploy

---

## Phase 10: Hardening & Launch Prep

- [ ] Security audit — OWASP top 10 review, dependency scanning
- [ ] Verify zero PII — audit all database tables, logs, and error reports for personal data leakage
- [ ] Performance testing — Gemini call latency, embedding/clustering throughput, end-to-end pipeline timing
- [ ] Cost modelling — Gemini token usage per edition (~$3/newspaper x 6 newspapers = ~$18/day), R2 storage growth, Pub/Sub costs
- [ ] Pipeline validation on real data — run full pipeline with sample prompts, manually inspect cluster quality and article output
- [ ] Tune HDBSCAN parameters (min_cluster_size, min_samples) based on real prompt data
- [ ] Calibrate weight formula against editorial judgment — A/B test which prompts get coverage
- [ ] Calibrate "In Brief" threshold — what weight floor separates a full article from a brief mention
- [ ] User acceptance testing with sample world events
- [ ] Set up error tracking (Sentry or similar)
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

## Open Questions

1. **Verbatim attribution** — should the newspaper quote user prompts directly in articles, or only use them for internal LLM grounding?
2. **Slow news day handling** — pre-compute yesterday's unused low-weight clusters as "continuing stories" backfill? Set minimum article count floor?
