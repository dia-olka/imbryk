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

- [ ] Author the initial WorldLedger — populate `WORLD_LEDGER_TEMPLATE` with the founding lore (nations, alliances, economic blocs, tech landscape, environmental state, and seed history)
- [ ] Write a `WorldLedger → synopsis` serialiser that compresses the ledger into a concise text block for the `{{WORLD_LEDGER_SYNOPSIS}}` placeholder
- [ ] Write a `WorldLedger + event → updated WorldLedger` mutation function that applies an event's consequences to the ledger
- [ ] Refine persona system prompt templates — test each against sample events, tune voice/bias fidelity
- [ ] Add a `packages/prompt-engine` library with template interpolation utilities (fill `{{WORLD_LEDGER_SYNOPSIS}}`, `{{EVENT_DESCRIPTION}}`, `{{SIX_ARTICLES}}`)
- [ ] Write integration tests: template interpolation → valid prompt string for each persona

---

## Phase 3: Newsroom Director Implementation

- [ ] Implement Vertex AI context cache creation from WorldLedger synopsis
- [ ] Implement parallel 6-persona Gemini calls with structured output (article title, body, pull quotes, bias disclosure)
- [ ] Implement Curator synthesis call — input: 6 articles, output: consensus/disagreement map + meta-analysis
- [ ] Implement WorldLedger mutation — apply event consequences after article generation
- [ ] Implement R2 write — store edition (articles + curator + updated ledger snapshot)
- [ ] Implement context cache cleanup
- [ ] Add retry logic and error handling for Gemini API failures
- [ ] Add structured logging (edition ID, persona ID, latency, token usage)
- [ ] Write end-to-end test: sample event → full edition output

---

## Phase 4: Ingestion API Implementation

- [ ] Design and implement user authentication (likely OAuth2 / JWT)
- [ ] Implement credit/payment system (Stripe or similar)
- [ ] Implement `POST /prompts` — validate input, deduct credits, enqueue event
- [ ] Implement `GET /prompts/:id` — poll processing status
- [ ] Implement `GET /editions` — list editions with pagination
- [ ] Implement `GET /editions/:id` — fetch full edition (articles + curator + ledger snapshot)
- [ ] Implement `POST /payments/webhook` — handle payment processor callbacks
- [ ] Add rate limiting and abuse prevention
- [ ] Add input validation and content moderation for user prompts
- [ ] Write API tests for all endpoints (auth, payment, CRUD)

---

## Phase 5: Frontend — Newspaper Reader UI

- [ ] Remove NxWelcome boilerplate, establish app shell with routing
- [ ] Design mobile-first layout system (responsive grid, touch-friendly)
- [ ] Implement accessibility foundations (skip links, ARIA landmarks, focus management, colour contrast)
- [ ] Build newspaper edition reader — display all 6 articles + Curator synthesis
- [ ] Build individual article view with persona identity card (ideology, biases, blindspots)
- [ ] Build world timeline / history view — visualise the WorldLedger history
- [ ] Build prompt submission form — event description input with credit balance display
- [ ] Build edition archive / browse view with pagination
- [ ] Implement keyboard navigation and screen reader testing
- [ ] Add loading states, error boundaries, and empty states
- [ ] Add dark mode / theme support

---

## Phase 6: Integration & DevOps

- [ ] Set up CI/CD pipeline (GitHub Actions) — lint, typecheck, test on PR
- [ ] Configure Cloudflare R2 bucket and access credentials
- [ ] Set up Vertex AI project, service account, and API keys
- [ ] Containerise Python apps (Dockerfile per app)
- [ ] Deploy frontend to Cloudflare Pages (or similar)
- [ ] Deploy ingestion-api and newsroom-director to Cloud Run (or similar)
- [ ] Set up environment variable management (secrets for API keys, payment keys)
- [ ] Configure CORS between frontend and API
- [ ] Set up monitoring and alerting (error rates, API latency, Gemini token spend)

---

## Phase 7: Hardening & Launch Prep

- [ ] Security audit — OWASP top 10 review, dependency scanning
- [ ] Performance testing — Gemini call latency, concurrent edition generation
- [ ] Cost modelling — Gemini token usage per edition, R2 storage growth
- [ ] User acceptance testing with sample world events
- [ ] Write user-facing documentation (how it works, what the personas are)
- [ ] Set up error tracking (Sentry or similar)
- [ ] Define and implement backup strategy for WorldLedger state
- [ ] Launch checklist: DNS, SSL, rate limits, monitoring dashboards

---

## Open Questions

1. **Trigger model** — Should editions be generated on-demand per user prompt, or batched on a schedule (e.g., "morning press" daily)?
2. **World state branching** — If multiple prompts arrive concurrently, do they share the same world state or create divergent timelines?
3. **Gemini model selection** — Which Gemini model variant balances quality vs. cost for 6 parallel persona calls?
4. **Content moderation** — How aggressively should user prompts be filtered? What about generated content?
5. **Monetisation** — Credit-based? Subscription? Free tier with limits?
6. **Multi-language** — Should articles be generated in multiple languages from the start, or English-only for MVP?
