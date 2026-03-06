# Imbryk

Imbryk ("the teapot") is an AI-powered newspaper generation platform. Users submit world-altering event prompts (paid via Stripe), and a daily batch job produces news articles written by 6 ideologically distinct AI newspaper personas, plus a Curator synthesis. Generated editions are published as free static HTML — no registration required.

The 6 newspapers are audience archetypes inspired by the *Yes Minister* observation about who reads which paper: The Sovereign (establishment), The Aspirant (idealist), The Owner (financial), The Moralist (traditionalist), The Radical (anti-establishment), and The Hedonist (entertainment).

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
