# Imbryk — System Architecture

## Overview

Imbryk ("the teapot") is an AI-powered newspaper generation platform. Users submit world-altering event prompts, and the system produces a full set of news articles written by 6 ideologically distinct AI newspaper personas, plus a 7th "Curator" synthesis. The result is a rich, multi-perspective media experience set in a persistent fictional world.

## High-Level Data Flow

```
User Prompt
    │
    ▼
┌─────────────────┐     ┌──────────────────────┐
│  Ingestion API   │────▶│   Event Queue (R2)    │
│  (FastAPI)       │     └──────────┬───────────┘
│  - auth/payment  │               │
│  - validation    │               ▼
└─────────────────┘     ┌──────────────────────┐
                        │  Newsroom Director    │
                        │  (Python orchestrator)│
                        │                      │
                        │  1. Load WorldLedger  │
                        │  2. Cache context     │
                        │     (Vertex AI)       │
                        │  3. 6 persona prompts │
                        │     (Gemini, parallel)│
                        │  4. Curator synthesis │
                        │  5. Write to R2       │
                        │  6. Cleanup cache     │
                        └──────────┬───────────┘
                                   │
                                   ▼
                        ┌──────────────────────┐
                        │  R2 Object Storage    │
                        │  - articles JSON      │
                        │  - updated ledger     │
                        └──────────┬───────────┘
                                   │
                                   ▼
                        ┌──────────────────────┐
                        │  Imbryk Frontend      │
                        │  (React 19 / Vite)    │
                        │  - newspaper reader   │
                        │  - prompt submission  │
                        │  - world timeline     │
                        └──────────────────────┘
```

## Projects

### `apps/imbryk` — React Frontend

| Aspect | Detail |
|---|---|
| Framework | React 19, Vite 7 |
| Styling | CSS Modules (mobile-first, accessible) |
| Test | Vitest + @testing-library/react |
| Port | 4200 (dev) |

The frontend is the public face of Imbryk. It renders the generated newspapers, allows users to submit event prompts, and visualises the world timeline. Design is mobile-first with WCAG 2.2 AA compliance as the accessibility baseline.

### `apps/ingestion-api` — FastAPI Backend

| Aspect | Detail |
|---|---|
| Runtime | Python 3.9+ |
| Framework | FastAPI + Pydantic |
| Server | Uvicorn (port 8000) |
| Test | pytest |

Receives user prompts and manages the payment/credit gate. Validates input, deducts credits, and enqueues the event for the Newsroom Director to process.

**Endpoints (current stubs):**
- `GET /health` — liveness check
- `POST /prompts` — submit an event prompt

**Planned endpoints:**
- `POST /auth/login` — user authentication
- `GET /prompts/:id` — poll prompt processing status
- `GET /editions` — list generated newspaper editions
- `GET /editions/:id` — fetch a specific edition
- `POST /payments/webhook` — payment processor callback

### `apps/newsroom-director` — AI Orchestrator

| Aspect | Detail |
|---|---|
| Runtime | Python 3.9+ |
| AI Provider | Google Vertex AI (Gemini) |
| Test | pytest |

The core intelligence layer. Triggered per accepted prompt, it:

1. **Loads the WorldLedger** — the current state of the fictional world
2. **Creates a Vertex AI context cache** — avoids re-uploading the full ledger per persona
3. **Runs 6 persona prompts in parallel** — each newspaper writes its take on the event
4. **Runs the Curator synthesis** — The Curator reads all 6 articles and produces a meta-analysis
5. **Writes results to R2** — articles, updated ledger, edition metadata
6. **Deletes the context cache** — cost management

### `packages/world-state` — World Ledger Schema

The WorldLedger is the persistent state of the fictional world. It is a structured JSON document covering 7 domains:

| Domain | Key Types | Purpose |
|---|---|---|
| Geopolitics | `Nation`, `Alliance`, `Conflict` | Political landscape, power structures |
| Economics | `Currency`, `TradingBloc`, `Scarcity` | Markets, trade, resource dynamics |
| Technology | `TechDomain` (AI, energy, biotech) | Innovation state, key players |
| Culture | `CulturalMovement` | Narratives, media, social movements |
| Military | `MilitaryForce` | Force projection, arms dynamics |
| Environment | `EnvironmentalCrisis` | Climate state, mitigation efforts |
| History | `HistoricalEvent[]` | Timeline of past events and their impact |

The ledger evolves with each processed prompt — the Newsroom Director updates it after generating articles.

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
- The Curator uses `{{SIX_ARTICLES}}` to synthesise the other six

## Infrastructure & Storage

| Component | Technology | Purpose |
|---|---|---|
| Object storage | Cloudflare R2 | Articles, ledger snapshots, editions |
| AI inference | Google Vertex AI / Gemini | Article generation, context caching |
| Hosting (frontend) | TBD (Cloudflare Pages likely) | Static React app |
| Hosting (APIs) | TBD (Cloud Run likely) | FastAPI + orchestrator |
| Auth/Payments | TBD | User accounts, credit system |

## Key Design Decisions

1. **Vertex AI context caching** — The WorldLedger is large. Caching it once per edition run and sharing across 6 parallel persona calls saves tokens and latency.

2. **Parallel persona execution** — All 6 newspaper prompts are independent and run concurrently. Only the Curator depends on their output.

3. **Structured WorldLedger** — Using typed schemas (not free-form text) ensures the world state is machine-readable, diffable, and validatable between editions.

4. **Separate ingestion from orchestration** — The API handles user-facing concerns (auth, payment, rate limiting). The director handles AI concerns (prompting, caching, output). They communicate via an event queue.

5. **Python for both backends** — Keeps the AI/ML ecosystem consistent. FastAPI for the web layer, plain Python for the orchestrator.

6. **TypeScript libraries shared at source** — Using TS Solution Mode with `customConditions: ["@org/source"]`, libraries resolve directly to `.ts` source at dev time. No build step needed for library consumers.
