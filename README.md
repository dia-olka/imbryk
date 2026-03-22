# Imbryk

Imbryk ("the teapot") is an AI-powered newspaper generation platform. Every morning, a batch pipeline automatically gathers real-world news via web search and hands it to 6 ideologically distinct AI newspaper personas. Each persona writes a full edition — same world, same day, six completely different front pages — plus a Curator synthesis. Editions are published as free static HTML, no registration required.

**Paid human prompts are optional steering, not the source of content.** Without any submissions the newspapers still publish, driven entirely by AI-sourced news. When a reader pays to submit a world-altering event, that prompt is folded into the day's content alongside the AI-gathered news, weighted by payment amount — pushing a story to a front-page feature rather than an in-brief mention.

The 6 newspapers are audience archetypes inspired by the *Yes Minister* observation about who reads which paper:

| Newspaper | Real-world model | Motto | Audience | Style |
|---|---|---|---|---|
| **The Sovereign** | *The Economist* | "The view from the situation room" | Senior officials, policy analysts, diplomats | Measured broadsheet prose. Institutional voice, geopolitical chess, realpolitik. |
| **The Aspirant** | *The Guardian* | "A better world is possible" | Educated progressives, students, NGO workers, union organisers | Passionate, solidarity-driven. Class analysis, structural critique, human-first. |
| **The Owner** | *Financial Times* | "The bottom line, above all" | Financial professionals, investors, C-suite | Data-driven, precise, unsentimental. Numbers first, market impact, incentive structures. |
| **The Moralist** | *Daily Telegraph* | "Decency still matters" | Middle-class families, churchgoers, small-business owners | Morally grounded, direct, forceful. Family values, faith, law and order. |
| **The Radical** | *The Intercept* | "They don't want you to read this" | Working-class readers, grassroots activists, disillusioned voters | Aggressive, skeptical, punchy. Follow the money, challenge every narrative. |
| **The Hedonist** | *Daily Mail / NY Post* | "Life is too short for boring news" | General public, commuters, social media scrollers | Tabloid energy, celebrity-driven. Short sentences, bold claims, vivid drama. |

A seventh persona, **The Curator**, synthesises all six editions into a single balanced briefing — highlighting consensus, fault lines, uncovered angles, and what to watch next.

## Workspace

| App / Package | What it does |
|---|---|
| `apps/imbryk` | React prompt submission UI with Stripe Checkout |
| `apps/ingestion-api` | FastAPI backend — payment webhooks, prompt categorisation |
| `apps/newsroom-director` | Python batch job — distillation pipeline, Gemini generation, WorldLedger |
| `apps/gazette` | 11ty static site — renders editions as browsable HTML |
| `packages/world-state` | WorldLedger schema and initial world lore |
| `packages/ai-personas` | 6 newspaper personas + Curator definitions |
| `packages/taxonomy` | 30-category taxonomy, routing, pricing |

## Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** — system design, data flow, project descriptions, infrastructure, and key design decisions
- **[PLAN.md](PLAN.md)** — phased release plan with task checklists and current progress
- **[DEPLOYMENT.md](DEPLOYMENT.md)** — infrastructure setup, containerisation, and deployment procedures

## Local Development

### Prerequisites

- Node.js 20+
- Python 3.9+
- [uv](https://docs.astral.sh/uv/) (Python package manager)

### Setup

```sh
# Install JS dependencies (workspace root)
npm install

# Install Python dependencies for each app
npx nx install ingestion-api
npx nx install newsroom-director
```

### Running Apps Locally

**Ingestion API** — runs on port 8000 with SQLite and a stub categoriser (no Gemini key needed):

```sh
npx nx serve ingestion-api
# API available at http://localhost:8000/docs (Swagger UI)
```

**Gazette** — serves on port 8080 with hot-reload, using the sample edition fixture:

```sh
npx nx serve gazette
# Site available at http://localhost:8080
```

**Newsroom Director** — runs the full pipeline locally with stub LLM and in-memory storage. No cloud credentials required:

```sh
cd apps/newsroom-director
DATABASE_URL="sqlite:///./local.db" uv run python -m newsroom_director.main
```

Without `VERTEX_AI_PROJECT` set, the director automatically uses `StubGenerationStrategy` (returns placeholder articles) and `StubEditionStorage` (in-memory). This exercises the entire pipeline — DB access, taxonomy routing, distillation, coherence validation, and edition assembly — without any API calls.

To run with real Gemini generation, set `VERTEX_AI_PROJECT` and authenticate:

```sh
gcloud auth application-default login
VERTEX_AI_PROJECT=your-project DATABASE_URL="sqlite:///./local.db" \
  uv run python -m newsroom_director.main
```

### Testing

```sh
# All tests across the workspace
npx nx run-many -t test

# Individual apps
npx nx test newsroom-director    # 130 tests, uses SQLite + stubs
npx nx test ingestion-api        # uses SQLite + stubs

# Lint
npx nx run-many -t lint

# Visualise project graph
npx nx graph
```

All Python tests use in-memory SQLite and stub strategies — no cloud services, no API keys, no network access required.
