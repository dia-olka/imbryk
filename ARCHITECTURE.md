# Imbryk — System Architecture

## Overview

Imbryk ("the teapot") is an AI-powered newspaper generation platform. Users submit world-altering event prompts (paid via Braintree), and a daily batch job produces news articles written in English by 6 ideologically distinct AI newspaper personas, plus a 7th "Curator" synthesis. Generated editions are published as static HTML sites — freely accessible to everyone, no registration required.

**Zero PII principle:** Imbryk stores no personal user data. Braintree owns identity and payment. The database holds only transaction references, prompt text, weights, and categories.

## High-Level Data Flow

```text
User Prompt + Weight
    │
    ▼
┌───────────────────────┐
│  Imbryk Frontend      │
│  (React 19 / Vite)    │
│  - Prompt submission  │
│  - Braintree Checkout │
│  - Cost calculator    │
└──────────┬────────────┘
           │ Braintree Payment
           ▼
┌───────────────────────┐     ┌─────────────────────────┐
│  Ingestion API        │────▶│   PostgreSQL             │
│  (FastAPI)            │     │   - prompts (raw)        │
│  - Payment webhook    │     │   - prompts (categorised)│
│  - Prompt validation  │     │   - payment refs         │
│  - Local LLM classify │     │   - WorldLedger          │
└───────────────────────┘     └──────────┬──────────────┘
                                         │
           ┌─────────────────────────────┘
           │ GCP Pub/Sub
           ▼ (morning trigger)
┌──────────────────────────────────────────────┐
│  Newsroom Director                           │
│  (Cloud Run Job — daily batch)               │
│                                              │
│  1. Pull categorised prompts from DB         │
│  2. Load WorldLedger from DB                 │
│  3. Cache context (Vertex AI)                │
│  4. Per-newspaper persona prompts (Gemini)   │
│     — only newspapers with matching prompts  │
│  5. Curator synthesis                        │
│  6. Update WorldLedger in DB                 │
│  7. Write edition articles to R2             │
│  8. Force-delete context cache               │
└──────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│  Gazette (11ty)                              │
│  - Reads articles from R2                    │
│  - Builds static HTML newspaper site         │
│  - Deploys to Cloudflare Pages               │
└──────────────────────────────────────────────┘
```

## Prompt Categorisation Pipeline

A user's raw prompt is categorised by a cheap LLM (Gemini Flash via the ingestion API) into one or more newspaper personas. This determines which newspapers cover the event. The categoriser is implemented behind a `CategoriserStrategy` interface so the backing model can be swapped (e.g., to a local Ollama model) without changing the rest of the pipeline.

```text
"Global water crisis triggers mass migration"
    │
    Categoriser (Gemini Flash, swappable)
    │
    ├─▶ The Global Herald     (geopolitical angle)
    ├─▶ The People's Dispatch (humanitarian angle)
    ├─▶ The Green Pulse       (environmental angle)
    └─▶ The Market Wire       (commodity markets angle)

Cost to user = f(number of categories)
```

A prompt touching all 6 newspapers costs more than one touching 2. The Curator always runs (synthesising whichever newspapers were activated), so its cost is fixed per edition.

## World Coherence Gate

The Newsroom Director — not the categoriser — decides whether a prompt actually enters the world. Before generating any articles, the director runs a **validation step** using a Pro-tier model with full WorldLedger context:

1. Does this event make sense given the current world state?
2. Is it coherent, non-contradictory, and meaningful?
3. If **yes** → proceed to article generation and ledger mutation
4. If **no** → mark prompt as rejected (user's payment still consumed — they paid for the attempt)

This ensures world coherence is maintained by the model with the deepest context, not a cheap classifier.

## Projects

### `apps/imbryk` — Prompt Submission UI

| Aspect | Detail |
|---|---|
| Framework | React 19, Vite 7 |
| Styling | CSS Modules (mobile-first, WCAG 2.2 AA) |
| Test | Vitest + @testing-library/react |
| Port | 4200 (dev) |

The prompt submission and payment interface. Users write an event prompt, see a cost estimate (based on how many newspapers it would trigger), pay via Braintree, and receive confirmation. No account creation — Braintree handles identity.

This app does **not** display generated newspapers. Those are static HTML on a separate domain.

### `apps/gazette` — Static Site Generator (planned)

| Aspect | Detail |
|---|---|
| Framework | 11ty (Eleventy) |
| Output | Static HTML |
| Hosting | Cloudflare Pages |

Reads article JSON from R2 and builds a browsable, static newspaper site. Each edition gets its own page set. The world timeline, persona identity cards, and archive are all pre-rendered HTML — no JavaScript required to read the news.

### `apps/ingestion-api` — FastAPI Backend

| Aspect | Detail |
|---|---|
| Runtime | Python 3.9+ |
| Framework | FastAPI + Pydantic |
| Server | Uvicorn |
| Test | pytest |

Handles the payment-gated prompt flow and prompt categorisation.

**Endpoints:**
- `GET /health` — liveness check
- `POST /prompts/quote` — accepts draft prompt, runs categoriser, returns cost estimate (number of categories × base price)
- `POST /payments/braintree-webhook` — Braintree callback; on success, commits prompt to DB and triggers categorisation
- `GET /editions` — list generated editions (reads from R2 index)

**Categorisation flow (post-payment):**
1. Raw prompt saved to `prompts` table with Braintree transaction ref
2. Categoriser (Gemini Flash, behind `CategoriserStrategy` interface) classifies prompt into 1–6 newspaper categories
3. Categorised entries saved to `categorised_prompts` table
4. Message published to Pub/Sub for the morning batch

**Note:** The categoriser does **not** decide whether a prompt enters the world. It only labels which newspapers would cover it. World coherence validation happens in the Newsroom Director.

### `apps/newsroom-director` — AI Orchestrator

| Aspect | Detail |
|---|---|
| Runtime | Python 3.9+ |
| Compute | Google Cloud Run Job (scheduled daily) |
| AI Provider | Google Vertex AI (Gemini) |
| Test | pytest |

The core intelligence layer. Runs as a daily batch job:

1. **Pull categorised prompts** — reads all unprocessed categorised prompts from PostgreSQL
2. **Load WorldLedger** — reads the canonical ledger from PostgreSQL
3. **Create Vertex AI context cache** — uploads the ledger once, shares across all persona calls
4. **Validate prompts (Pro model)** — for each prompt, the director decides whether the event is coherent and meaningful in the current world context. Rejected prompts are marked as such in the DB; accepted prompts proceed.
5. **Run persona prompts** — for each newspaper with accepted prompts, runs a Gemini call with the persona's system prompt, ledger context, and matched prompts. Newspapers with no prompts are skipped.
6. **Run Curator synthesis (Pro model)** — The Curator reads all generated articles and produces a meta-analysis
7. **Update WorldLedger (Pro model)** — applies the event consequences to the ledger and writes back to PostgreSQL transactionally
8. **Write to R2** — stores edition articles as JSON for the Gazette to consume
9. **Force-delete context cache** — drops the Vertex AI cache immediately to avoid idle costs

### Per-Newspaper Model Tier Map

Each newspaper persona is assigned a Gemini model tier. Pro-tier models are used where complex reasoning, factual analysis, or synthesis is required. Flash-tier models handle voice-driven stylistic writing.

| Newspaper | Model | Rationale |
|---|---|---|
| The Global Herald | **Gemini Pro** | Complex geopolitical analysis, institutional nuance |
| The People's Dispatch | Gemini Flash | Voice-driven, structural framing |
| The Sovereign Standard | Gemini Flash | Emotive, rhetorical style |
| The Market Wire | **Gemini Pro** | Data-driven economic reasoning |
| The Green Pulse | Gemini Flash | Urgent ecological voice |
| The Oracle Network | Gemini Flash | Futurist speculation, style-heavy |
| The Curator | **Gemini Pro** | Cross-article synthesis, hardest reasoning task |
| Validation step | **Gemini Pro** | World coherence requires full context |
| Ledger mutation | **Gemini Pro** | Accurate world-state updates |

This map is stored as configuration and can be adjusted without code changes.

### `packages/world-state` — World Ledger Schema

The WorldLedger is the persistent state of the fictional world, stored as a structured document in PostgreSQL. It covers 7 domains:

| Domain | Key Types | Purpose |
|---|---|---|
| Geopolitics | `Nation`, `Alliance`, `Conflict` | Political landscape, power structures |
| Economics | `Currency`, `TradingBloc`, `Scarcity` | Markets, trade, resource dynamics |
| Technology | `TechDomain` (AI, energy, biotech) | Innovation state, key players |
| Culture | `CulturalMovement` | Narratives, media, social movements |
| Military | `MilitaryForce` | Force projection, arms dynamics |
| Environment | `EnvironmentalCrisis` | Climate state, mitigation efforts |
| History | `HistoricalEvent[]` | Timeline of past events and their impact |

The ledger is a **single canonical copy** in PostgreSQL, updated transactionally after each morning run.

### `packages/ai-personas` — Newsroom Personas

Defines the 7 AI journalist personas, each with a distinct ideological lens:

| # | Paper | Ideology | Leaning |
|---|---|---|---|
| 1 | The Global Herald | Centrist establishment | Centre |
| 2 | The People's Dispatch | Democratic socialist | Left |
| 3 | The Sovereign Standard | National conservative | Right |
| 4 | The Market Wire | Libertarian / free-market | Centre-right |
| 5 | The Green Pulse | Eco-socialist / deep ecology | Far left / Green |
| 6 | The Oracle Network | Techno-utopian / accelerationist | Post-political |
| 7 | The Curator | Meta-journalist (no ideology) | None |

Each persona carries:
- `systemPromptTemplate` with `{{WORLD_LEDGER_SYNOPSIS}}` and `{{EVENT_DESCRIPTION}}` placeholders
- Explicit `biases` and `blindspots` that shape their coverage
- The Curator uses `{{SIX_ARTICLES}}` to synthesise whichever newspapers were activated

All output is strictly English-language.

## Infrastructure & Storage

| Component | Technology | Purpose |
|---|---|---|
| Database | PostgreSQL (Cloud SQL) | Canonical WorldLedger, prompts, categorised prompts, payment refs. Single source of truth. |
| Event Queue | Google Cloud Pub/Sub | Triggers morning batch job, absorbs traffic spikes. |
| Object Storage | Cloudflare R2 | Edition article JSON (consumed by Gazette for static build). |
| AI Inference | Google Vertex AI / Gemini | Article generation (Flash + Pro tiers), validation, ledger mutation, context caching. |
| Categorisation | Gemini Flash (swappable) | Prompt categorisation into newspaper personas. Runs behind `CategoriserStrategy` interface for future swap to local model. |
| Static Hosting | Cloudflare Pages | Generated newspaper HTML (public, no auth). |
| Prompt UI Hosting | Cloudflare Pages | React SPA for prompt submission. |
| Payments | Braintree | Payment processing. No user data stored on our side. |

## Key Design Decisions

1. **Zero PII** — Braintree owns all user identity and payment data. Our database stores only transaction reference IDs, prompt text, weights, and categories. No names, emails, or personal data touch our servers.

2. **Three-stage LLM pipeline** — Gemini Flash categorises prompts (cheap). Gemini Pro validates world coherence and gates entry. Per-newspaper models (Flash or Pro, configurable) generate articles. This keeps costs proportional to the reasoning required at each stage.

3. **Category-based pricing** — The number of newspapers a prompt activates determines its cost. A narrow prompt (2 newspapers) is cheap; a world-shaking event (all 6) costs more. Transparent and fair.

4. **PostgreSQL for transactional safety** — Payment-linked prompts require ACID guarantees. The WorldLedger requires atomic read-modify-write between morning runs. R2 cannot provide either.

5. **Pub/Sub for scale** — Decouples prompt ingestion from batch processing. Absorbs viral traffic spikes without database pressure.

6. **Vertex AI context caching with explicit destruction** — Cache the WorldLedger once per batch run, share across all persona calls, then force-delete immediately. Zero idle cost.

7. **Static site generation** — Generated newspapers are pre-rendered HTML via 11ty. No server needed to read news, no JavaScript required, instant global delivery via Cloudflare CDN.

8. **Separate prompt UI from reading experience** — `apps/imbryk` (React SPA) handles the interactive payment flow. `apps/gazette` (11ty) produces the static reading experience. Different tools for different jobs.

9. **Single canonical WorldLedger** — One copy in PostgreSQL, updated transactionally. No branching, no eventual consistency. Each morning run reads, modifies, and writes back atomically.

10. **World coherence gate** — The director (Pro model with full ledger context) decides whether a prompt enters the world, not the categoriser. This prevents nonsensical or contradictory events from corrupting the world state.

11. **Swappable categoriser** — The categorisation step is behind an interface (`CategoriserStrategy`). Ships with Gemini Flash, can be swapped to Ollama/local model without touching the rest of the pipeline.

12. **Configurable model tiers** — Each newspaper persona maps to a model tier (Flash or Pro) via configuration. Pro is used for reasoning-heavy tasks (Herald, Market Wire, Curator, validation, ledger mutation). Flash handles stylistic voice work.
