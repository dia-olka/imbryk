# Imbryk — Production Release Plan

## Status Key

- [ ] Not started
- [~] In progress
- [x] Done

---

## Phase 1: Genesis (Monorepo Foundation) [x]

- [x] Nx workspace with React frontend scaffold
- [x] `@org/world-state` library — WorldLedger types + empty template
- [x] `@org/ai-personas` library — 7 newsroom personas with system prompt templates
- [x] `apps/ingestion-api` scaffold — FastAPI with stub endpoints
- [x] `apps/newsroom-director` scaffold — Morning Press pipeline outline
- [x] `@nxlv/python` plugin registered, all projects lint/typecheck/test green

---

## Phase 2: World Lore & Prompt Engineering

- [ ] Author the initial WorldLedger — populate the template with founding lore (nations, alliances, economic blocs, tech landscape, environmental state, seed history)
- [ ] Write a `WorldLedger → synopsis` serialiser that compresses the ledger into a text block for `{{WORLD_LEDGER_SYNOPSIS}}`
- [ ] Write a `WorldLedger + event → updated WorldLedger` mutation function
- [ ] Add `packages/prompt-engine` library with template interpolation utilities
- [ ] Refine persona system prompt templates — test each against sample events, tune voice/bias fidelity
- [ ] Write integration tests: template interpolation → valid prompt string for each persona

---

## Phase 3: Prompt Categorisation & Ingestion API

- [ ] Design PostgreSQL schema: `prompts`, `categorised_prompts`, `payment_refs`, `world_ledger`, `editions`
- [ ] Set up PostgreSQL (Cloud SQL or Supabase) and database migrations
- [ ] Implement `POST /prompts/quote` — accept draft prompt, run local LLM categoriser, return cost estimate
- [ ] Implement `CategoriserStrategy` interface and Gemini Flash implementation — classify prompt into 1–6 newspaper categories
- [ ] Implement `POST /payments/braintree-webhook` — on payment success: save prompt, categorise, publish to Pub/Sub
- [ ] Implement `GET /editions` — list editions from R2 index
- [ ] Set up Braintree sandbox integration
- [ ] Add input validation and content moderation for prompts
- [ ] Add rate limiting
- [ ] Write API tests for all endpoints

---

## Phase 4: Newsroom Director Implementation

- [ ] Implement batch job entry point (Cloud Run Job trigger)
- [ ] Implement: pull unprocessed categorised prompts from PostgreSQL
- [ ] Implement: load WorldLedger from PostgreSQL
- [ ] Implement Vertex AI context cache creation from WorldLedger synopsis
- [ ] Implement world coherence validation (Pro model) — accept/reject prompts against current world state
- [ ] Implement per-newspaper model tier config map (Pro vs Flash per persona)
- [ ] Implement per-newspaper Gemini calls — only for newspapers with accepted, matched prompts; merge multiple prompts per newspaper into single event briefing
- [ ] Implement Curator synthesis (Pro model) — input: generated articles, output: meta-analysis
- [ ] Implement WorldLedger mutation (Pro model) — apply consequences, write back to PostgreSQL transactionally
- [ ] Implement R2 write — store edition articles as JSON
- [ ] Implement context cache force-deletion
- [ ] Add retry logic and error handling for Gemini API failures
- [ ] Add structured logging (edition ID, persona ID, model tier, latency, token usage)
- [ ] Write end-to-end test: sample event → full edition output

---

## Phase 5: Gazette — Static Site Generator

- [ ] Scaffold `apps/gazette` with 11ty
- [ ] Design newspaper page templates (edition index, per-newspaper article, Curator synthesis)
- [ ] Build persona identity cards (ideology, biases, blindspots) into article templates
- [ ] Build world timeline page from WorldLedger history
- [ ] Build edition archive with pagination
- [ ] Mobile-first responsive design, WCAG 2.2 AA
- [ ] Set up Cloudflare Pages deployment for gazette output
- [ ] Automate: morning run completes → gazette rebuild → deploy

---

## Phase 6: Frontend — Prompt Submission UI

- [ ] Remove NxWelcome boilerplate, establish app shell
- [ ] Build prompt submission form — event description textarea + weight slider
- [ ] Build cost calculator — show estimated cost based on category count (calls `/prompts/quote`)
- [ ] Integrate Braintree Drop-in UI for payment
- [ ] Build confirmation view — payment success, prompt queued for next morning edition
- [ ] Mobile-first layout, WCAG 2.2 AA compliance
- [ ] Keyboard navigation and screen reader testing
- [ ] Loading states, error boundaries, empty states
- [ ] Deploy to Cloudflare Pages

---

## Phase 7: Integration & DevOps

- [ ] Set up CI/CD pipeline (GitHub Actions) — lint, typecheck, test on PR
- [ ] Configure Cloudflare R2 bucket and access credentials
- [ ] Set up Vertex AI project, service account, and API keys
- [ ] Set up GCP Pub/Sub topic and subscription
- [ ] Configure Cloud Scheduler for daily morning trigger
- [ ] Containerise Python apps (Dockerfile per app)
- [ ] Deploy ingestion-api to Cloud Run
- [ ] Deploy newsroom-director as Cloud Run Job
- [ ] Set up environment variable management (secrets for API keys, Braintree keys)
- [ ] Configure CORS between prompt UI and API
- [ ] Set up monitoring and alerting (error rates, API latency, Gemini token spend)

---

## Phase 8: Hardening & Launch Prep

- [ ] Security audit — OWASP top 10 review, dependency scanning
- [ ] Verify zero PII — audit all database tables, logs, and error reports for personal data leakage
- [ ] Performance testing — Gemini call latency, categorisation throughput
- [ ] Cost modelling — Gemini token usage per edition, R2 storage growth, Pub/Sub costs
- [ ] User acceptance testing with sample world events
- [ ] Set up error tracking (Sentry or similar)
- [ ] Define and implement backup strategy for WorldLedger in PostgreSQL
- [ ] Launch checklist: DNS, SSL, rate limits, monitoring dashboards

---

## Resolved Decisions

1. **Trigger model** — daily batch ("morning press"). Strictly once daily.
2. **World state** — single canonical ledger in PostgreSQL, no branching.
3. **Language** — English only.
4. **Monetisation** — per-prompt payment via Braintree. Cost scales with number of newspaper categories activated.
5. **User data** — zero PII stored. Braintree owns identity.
6. **Reading experience** — static HTML via 11ty + Cloudflare Pages. Free, no registration.
7. **Prompt UI** — separate React SPA (`apps/imbryk`).
8. **Categorisation model** — Gemini Flash via `CategoriserStrategy` interface (swappable to local model later).
9. **Per-newspaper model tiers** — Pro for Herald, Market Wire, Curator, validation, ledger mutation. Flash for People's Dispatch, Sovereign Standard, Green Pulse, Oracle Network. Configurable via map.
10. **Content moderation** — the Newsroom Director (Pro model with full world context) validates prompt coherence before article generation. The categoriser does not gate content. Payment itself filters casual abuse.
11. **Prompt merging** — multiple prompts landing in the same newspaper category for one morning run are merged into a single event briefing for that persona.

## Open Questions

None currently blocking. Model tier assignments (decision 9) can be tuned after initial testing.
