# Imbryk — System Architecture

## Overview

Imbryk ("the teapot") is an AI-powered newspaper generation platform. Users submit world-altering event prompts (paid via Braintree), and a daily batch job produces news articles written in English by 6 ideologically distinct AI newspaper personas, plus a Curator synthesis. Each newspaper publishes exactly one edition per day. Generated editions are published as static HTML sites — freely accessible to everyone, no registration required.

The 6 newspapers are audience archetypes — inspired by the classic observation about who reads which paper (cf. *Yes Minister*). Each represents a distinct worldview and readership, not a topic silo.

**Zero PII principle:** Imbryk stores no personal user data. Braintree owns identity and payment. The database holds only transaction references, prompt text, weights, and categories.

## High-Level Data Flow

```text
User Prompt
    |
    v
+-------------------------+
|  Imbryk Frontend        |
|  (React 19 / Vite)      |
|  - Prompt submission    |
|  - Braintree Checkout   |
|  - Cost calculator      |
+----------+--------------+
           | Braintree Payment
           v
+-------------------------+     +---------------------------+
|  Ingestion API          |---->|   PostgreSQL               |
|  (FastAPI)              |     |   - prompts (raw)          |
|  - Payment webhook      |     |   - prompts (categorised)  |
|  - Prompt validation    |     |   - payment refs           |
|  - Category classifier  |     |   - WorldLedger            |
+-------------------------+     |   - taxonomy (categories,  |
                                |     newspaper subscriptions)|
                                +------------+--------------+
                                             |
           +---------------------------------+
           | GCP Pub/Sub
           v (morning trigger)
+------------------------------------------------+
|  Newsroom Director                             |
|  (Cloud Run Job -- daily batch)                |
|                                                |
|  1. Pull categorised prompts from DB           |
|  2. Route prompts to newspapers via taxonomy   |
|  3. Load WorldLedger from DB                   |
|  4. Validate prompts (world coherence gate)    |
|  5. Per-newspaper distillation pipeline:       |
|     a. Embed prompts (local sentence-transformers)|
|     b. Cluster via HDBSCAN                     |
|     c. Build weighted cluster digests          |
|     d. Allocate token budget                   |
|     e. Single Gemini call per newspaper        |
|  6. Curator synthesis                          |
|  7. Update WorldLedger in DB                   |
|  8. Write edition articles to R2               |
|  9. Force-delete context cache                 |
+------------------------------------------------+
           |
           v
+------------------------------------------------+
|  Gazette (11ty)                                |
|  - Reads articles from R2                      |
|  - Builds static HTML newspaper site           |
|  - Deploys to Cloudflare Pages                 |
+------------------------------------------------+
```

## Two-Level Taxonomy: Categories & Newspapers

Categories and newspapers are different kinds of things. Categories are routing labels; newspapers are pipeline units.

| Level | What it is | How many | Role in pipeline |
|---|---|---|---|
| Category | A curated topic label (Finance, AI, Climate...) | 30 | Routing only — determines which newspapers receive a prompt |
| Newspaper | An editorial product subscribing to a set of categories | 6 | Pipeline unit — has its own prompt pool, clustering, Gemini call, and one daily edition |

**Categories are not pipelines — newspapers are.** A category like "Finance" never runs a Gemini call. The Owner newspaper runs a Gemini call, using all prompts tagged Finance, Markets, Banking, or Trade that arrived today.

### The 30-Category Taxonomy

30 categories across 6 groups, tuned for the 6 newspaper audiences. Every category has at least one newspaper that cares about it; no dead-weight labels.

| Group | Categories |
|---|---|
| Power & Governance (6) | Geopolitics, Domestic Politics, Military & Defence, Law & Justice, Immigration, Intelligence & Surveillance |
| Finance & Economy (5) | Finance & Markets, Trade & Commerce, Real Estate & Property, Cryptocurrency, Labour & Employment |
| Science & Technology (4) | Technology & Innovation, Artificial Intelligence, Science & Research, Energy |
| Society & Values (5) | Social Issues, Education, Religion & Faith, Crime & Public Safety, Health & Medicine |
| Environment (2) | Climate & Environment, Food & Agriculture |
| Culture & Entertainment (8) | Entertainment, Celebrity & Personalities, Culture & Arts, Sports, Fashion & Style, Food & Lifestyle, Travel, Corruption & Scandal |

### Newspaper Subscriptions

Each newspaper is defined by its category subscription set. With 6 newspapers and 30 categories, each newspaper subscribes to 8-12 categories. Some categories are owned by a single newspaper (e.g. only The Hedonist covers Sports) while others are shared across 2-4 newspapers, creating the editorial overlap that makes the same event produce genuinely different coverage.

| Newspaper | Subscribed categories |
|---|---|
| The Sovereign | Geopolitics, Domestic Politics, Military & Defence, Law & Justice, Immigration, Intelligence & Surveillance, Trade & Commerce, Energy, Technology & Innovation |
| The Aspirant | Geopolitics, Social Issues, Climate & Environment, Health & Medicine, Education, Immigration, Science & Research, Food & Agriculture, Culture & Arts |
| The Owner | Finance & Markets, Trade & Commerce, Real Estate & Property, Cryptocurrency, Labour & Employment, Technology & Innovation, Artificial Intelligence, Energy |
| The Moralist | Domestic Politics, Religion & Faith, Education, Crime & Public Safety, Health & Medicine, Immigration, Law & Justice, Social Issues, Entertainment |
| The Radical | Domestic Politics, Labour & Employment, Corruption & Scandal, Intelligence & Surveillance, Cryptocurrency, Social Issues, Immigration, Geopolitics, Climate & Environment |
| The Hedonist | Entertainment, Celebrity & Personalities, Culture & Arts, Sports, Fashion & Style, Food & Lifestyle, Travel, Corruption & Scandal |

**Overlap is a feature, not a bug.** When The Sovereign and The Owner both receive a "central bank rate decision" prompt, they write about it from entirely different angles — The Sovereign through state power implications, The Owner through market impact. Independent pipelines and distinct editorial voices guarantee genuinely different articles from the same underlying event.

### Routing Math

With 30 categories, 6 newspapers, and avg 8 subscriptions per newspaper:

| Prompt categories | Expected newspapers reached (of 6) | Example |
|---|---|---|
| 1 category | 1-2 | Very niche prompt |
| 2-3 categories | 2-3 | Typical prompt |
| 4-5 categories | 3-4 | Broader event |
| 6+ categories | 4-6 | Major cross-cutting event |

The system prices reach automatically — the classification determines how many newspapers cover the prompt, and pricing follows. Most prompts will reach 2-4 newspapers; only truly world-shaking events hit all 6.

## Prompt Categorisation Pipeline

A user's raw prompt is categorised by a cheap LLM (Gemini Flash via the ingestion API) into 1-K categories from the 30-category taxonomy. The categoriser is implemented behind a `CategoriserStrategy` interface so the backing model can be swapped (e.g., to a local Ollama model) without changing the rest of the pipeline.

```text
"Fed raises rates 0.5%"
    |
    Categoriser (Gemini Flash, swappable)
    |
    +-> [Finance & Markets, Trade & Commerce]
    |
    Routing (zero cost, set intersection)
    |
    +-> The Sovereign  (Geopolitics+Politics+Military+...+Trade & Commerce)  YES
    +-> The Aspirant   (Social Issues+Climate+Health+...)                    NO
    +-> The Owner      (Finance & Markets+Trade & Commerce+Crypto+...)       YES
    +-> The Moralist   (Politics+Religion+Education+Crime+...)               NO
    +-> The Radical    (Politics+Labour+Corruption+...)                      NO
    +-> The Hedonist   (Entertainment+Celebrity+Culture+...)                 NO

Cost to user = base x newspapers_reached (2 in this case)
```

## World Coherence Gate

The Newsroom Director — not the categoriser — decides whether a prompt actually enters the world. Before generating any articles, the director runs a **validation step** using a Pro-tier model with full WorldLedger context:

1. Does this event make sense given the current world state?
2. Is it coherent, non-contradictory, and meaningful?
3. If **yes** -> proceed to article generation and ledger mutation
4. If **no** -> mark prompt as rejected (user's payment still consumed — they paid for the attempt)

This ensures world coherence is maintained by the model with the deepest context, not a cheap classifier.

## Prompt Distillation Pipeline

The newspaper quality ceiling is set by how well we distill prompts before the LLM sees them — not by the LLM itself. The pipeline invests engineering effort in distillation (cheap local compute) and keeps the LLM as a pure writer/editor at the end.

### Stage 1 — Weighted Clustering (local, ~$0)

Group each newspaper's daily prompt pool into topically coherent clusters without touching the LLM.

1. **Embed** all prompts using a local sentence transformer model (e.g. `all-MiniLM-L6-v2` or `BAAI/bge-small-en`). No API calls.
2. **Compute weight** for each prompt: `weight = payment_amount_norm x uniqueness_bonus`. Payment amount is the primary signal. Uniqueness (inverse of near-duplicate count) gives rare ideas a bonus.
3. **Cluster** via HDBSCAN — finds variable-density clusters, marks noise points, doesn't require specifying K upfront. Produces more natural topic groups than k-means.
4. **Rank clusters** by `aggregate_weight` (sum of member prompt weights). This establishes editorial hierarchy before any LLM is involved.

### Stage 2 — Cluster Digest Construction (local, ~$0)

Transform each cluster into a rich text digest that preserves the actual language of high-value prompts while compressing the redundant long tail.

Per-cluster algorithm:
1. Sort prompts by weight descending
2. Select top K prompts verbatim (K = min(20, cluster_size)) — preserves actual user language
3. For remaining prompts, run extractive summarisation (LexRank or similar) in batches — captures texture without verbatim repetition
4. Assemble digest: cluster_size, aggregate_weight, verbatim prompts, long-tail summary, dominant keywords

```text
CLUSTER #3 | aggregate_weight: 847,200 | prompt_count: 142,500
High-value verbatim prompts:
  [w:9820] "Solar panel output dropping in winter even on clear days"
  [w:7440] "Best battery storage options for off-grid solar under $5000"
Long-tail summary (139,480 prompts):
  Most prompts asked about cost, efficiency, and installation. Common concerns
  included grid tie-in regulations and net metering policies.
Keywords: solar, battery, off-grid, efficiency, ROI, winter, storage
```

### Stage 3 — Token Budget Allocation (local, ~$0)

The context window is a finite resource. Allocate tokens proportionally to cluster importance.

| Parameter | Value |
|---|---|
| Total budget | ~800,000 tokens (reserve 200K for system prompt, instructions, output) |
| Allocation | `tokens_per_cluster = (cluster_weight / total_weight) x 800,000` |
| Minimum floor | 500 tokens per cluster (header + a few verbatim prompts) |
| Maximum cap | 150,000 tokens per cluster (prevents one topic from dominating) |
| Low-volume day | Remaining budget filled with richer verbatim inclusion |
| High-volume day | Merge lowest-weight clusters into "Other Topics" group |

### Stage 4 — Gemini Generation (one call per newspaper)

One expensive, high-quality LLM call per newspaper edition. Multiple calls would lose cross-cluster synthesis — the ability to notice that two clusters are the same story from different angles, or that a small high-value cluster deserves front-page treatment over a massive low-value one.

**System prompt includes:**
- Role definition: newspaper editor with full editorial authority and the newspaper's ideological lens
- Weighting instructions: how to interpret aggregate_weight and verbatim markers
- Output schema: newspaper structure with sections, article slots, "In Brief" for minor clusters
- Editorial directives: find cross-cluster narratives, surface novelty, decide placement by weight not count
- WorldLedger synopsis for world context

**Extended thinking mode** is used for the editorial reasoning phase — cross-cluster synthesis, importance calibration, story angle selection, narrative cohesion. Article prose generation follows from that plan with less thinking.

**Output format:**
- Full articles (8-18): top clusters by aggregate_weight, ~400-600 words each, grounded in verbatim prompts
- In Brief section: remaining clusters, 2-3 sentences each
- Editor's note: cross-cluster observations, what defined the day
- Metadata block: article-to-cluster mapping, weights used, generation timestamp

## Projects

### `apps/imbryk` — Prompt Submission UI ("The Orb")

| Aspect | Detail |
|---|---|
| Framework | React 19, Vite 7 |
| Styling | Tailwind CSS v4 + shadcn/ui (mobile-first, WCAG 2.2 AA) |
| Test | Vitest + @testing-library/react |
| Port | 4200 (dev) |

The prompt submission and payment interface, built around a central metaphor: **the Orb**. Inspired by the Interstate 60 magic ball — users hold a glowing sphere, type a world-altering event into it, and release it into the world. The orb pulses with a warm rust glow while idle, intensifies on focus, and plays a release animation on submission.

The UX flow: users type an event prompt inside the orb, see a live cost estimate (based on how many newspapers the event would trigger), review which newspapers will cover it, pay via Braintree Drop-in, and receive confirmation. No account creation — Braintree handles identity.

Tailwind CSS v4 handles layout, spacing, and typography. shadcn/ui provides polished accessible components (Card, Button, Badge, Label, Textarea, Alert). The orb glow and animation effects use custom CSS keyframes layered on top.

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
- `POST /prompts/quote` — accepts draft prompt, runs categoriser, returns cost estimate (newspapers_reached x base price)
- `POST /payments/braintree-webhook` — Braintree callback; on success, commits prompt to DB and triggers categorisation
- `GET /editions` — list generated editions (reads from R2 index)

**Categorisation flow (post-payment):**
1. Raw prompt saved to `prompts` table with Braintree transaction ref
2. Categoriser (Gemini Flash, behind `CategoriserStrategy` interface) classifies prompt into 1-K categories from the 30-category taxonomy
3. Categorised entries saved to `categorised_prompts` table (category tags, not newspaper assignments)
4. Newspaper routing computed via set intersection (category tags vs newspaper subscriptions)
5. Message published to Pub/Sub for the morning batch

**Note:** The categoriser does **not** decide whether a prompt enters the world. It only assigns category labels. Newspaper routing is a deterministic set intersection. World coherence validation happens in the Newsroom Director.

### `apps/newsroom-director` — AI Orchestrator

| Aspect | Detail |
|---|---|
| Runtime | Python 3.9+ |
| Compute | Google Cloud Run Job (scheduled daily) |
| AI Provider | Google Vertex AI (Gemini) |
| Embedding | Local sentence-transformers (all-MiniLM-L6-v2 or similar) |
| Clustering | HDBSCAN |
| Test | pytest |

The core intelligence layer. Runs as a daily batch job:

1. **Pull categorised prompts** — reads all unprocessed categorised prompts from PostgreSQL
2. **Route to newspapers** — for each newspaper, collect prompts whose categories intersect the newspaper's subscription set
3. **Load WorldLedger** — reads the canonical ledger from PostgreSQL
4. **Create Vertex AI context cache** — uploads the ledger once, shares across all persona calls
5. **Validate prompts (Pro model)** — for each prompt, the director decides whether the event is coherent and meaningful in the current world context. Rejected prompts are marked as such; accepted prompts proceed.
6. **Per-newspaper distillation pipeline** — for each newspaper with accepted prompts:
   - Embed the newspaper's prompt pool (local sentence-transformers)
   - Cluster via HDBSCAN
   - Build weighted cluster digests (verbatim top prompts + extractive summaries)
   - Allocate token budget proportional to cluster importance
   - Single Gemini call with persona system prompt, ledger context, and allocated digests
7. **Run Curator synthesis (Pro model)** — The Curator reads all generated articles and produces a meta-analysis
8. **Update WorldLedger (Pro model)** — applies the event consequences to the ledger and writes back to PostgreSQL transactionally
9. **Write to R2** — stores edition articles as JSON for the Gazette to consume
10. **Force-delete context cache** — drops the Vertex AI cache immediately to avoid idle costs

### Per-Newspaper Model Tier Map

Each newspaper persona is assigned a Gemini model tier. Pro-tier models are used where complex reasoning, factual analysis, or synthesis is required. Flash-tier models handle voice-driven stylistic writing.

| Newspaper | Model | Rationale |
|---|---|---|
| The Sovereign | **Gemini Pro** | Complex geopolitical analysis, institutional nuance |
| The Aspirant | Gemini Flash | Academic/idealist voice, structural framing |
| The Owner | **Gemini Pro** | Data-driven financial reasoning |
| The Moralist | Gemini Flash | Emotive, traditionalist rhetoric |
| The Radical | Gemini Flash | Aggressive/skeptical voice, style-heavy |
| The Hedonist | Gemini Flash | Punchy, vibrant tabloid energy |
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

Defines the 6 AI newspaper personas plus the Curator. Each newspaper represents a distinct audience archetype — not a topic silo, but a worldview. Inspired by the classic *Yes Minister* observation about who reads which paper.

| # | Paper | Regional Bias | Tone | Who reads it |
|---|---|---|---|---|
| 1 | The Sovereign | Global / US Elite | Institutional American English. Focus on "The State." | People who actually run the country |
| 2 | The Aspirant | Internationalist | Academic English. Focus on "Global Justice" and "Humanity." | People who think they ought to run the country |
| 3 | The Owner | Wall Street / The City | Financial English. Focus on "Global Markets" and "The Dollar." | People who own the country |
| 4 | The Moralist | Middle-America / Middle-England | Traditionalist. Focus on "Family" and "Decency." | The wives of the people who run the country |
| 5 | The Radical | Anti-Globalist | Aggressive/Skeptical. Focus on "The Deep State" and "The People." | People who think the country should be run by another country |
| 6 | The Hedonist | Hollywood / West End | Punchy/Vibrant. Focus on "Stardom" and "Spectacle." | People who don't care who runs the country |
| 7 | The Curator | Meta-journalist | Analytical synthesis (no ideology) | — |

Each persona carries:
- `systemPromptTemplate` with `{{WORLD_LEDGER_SYNOPSIS}}` and `{{CLUSTER_DIGESTS}}` placeholders
- Explicit `biases` and `blindspots` that shape their coverage
- `regionalBias` and `toneAdjustment` — the editorial lens and voice register
- `subscribedCategories` — list of categories from the taxonomy this newspaper covers
- `modelTier` — Flash or Pro assignment
- The Curator uses `{{ALL_ARTICLES}}` to synthesise whichever newspapers were activated

All output is strictly English-language.

### `packages/taxonomy` — Category & Routing System (new)

Defines the 30-category taxonomy, newspaper-to-category subscription mappings, and the routing function.

- **Category registry** — the 30 curated topic labels, grouped into 6 domains
- **Subscription map** — which categories each newspaper subscribes to (6-12 per newspaper)
- **Router** — given a prompt's assigned categories, returns the set of newspapers whose subscriptions intersect
- **Pricing helper** — `newspapers_reached` count for cost calculation

The taxonomy is managed by editorial configuration, not code changes. Categories are stable; the newspaper count (6) is fixed by design.

## Pricing Model

```
price = base x newspapers_reached
```

| Component | Value |
|---|---|
| `base` | Fixed per-submission base price |
| `newspapers_reached` | Auto-calculated from category classification (set intersection with newspaper subscriptions) |

A niche prompt reaching 1-2 newspapers costs less than a cross-cutting event reaching 5-6. The classification system determines reach, and pricing follows automatically.

## Cost Model

Each active newspaper runs exactly one Gemini call per day. Cost scales with active newspapers, not prompt volume. Local compute (embedding, clustering, digests) is effectively free.

| Component | Cost |
|---|---|
| Embedding (local sentence-transformers) | ~$0 |
| HDBSCAN clustering | ~$0 |
| Extractive summarisation | ~$0 |
| Token budget allocation | ~$0 |
| Gemini call per newspaper | ~$3 |
| Daily cost at 6 newspapers | ~$18 |

The per-newspaper verbatim breakpoint (all prompts included raw without summarisation) is ~22,900 prompts/day per newspaper. Below that, every newspaper runs fully verbatim. Above it, high-volume newspapers start summarising while niche ones may stay verbatim indefinitely.

## Infrastructure & Storage

| Component | Technology | Purpose |
|---|---|---|
| Database | PostgreSQL (Cloud SQL) | Canonical WorldLedger, prompts, categorised prompts, taxonomy, payment refs. Single source of truth. |
| Event Queue | Google Cloud Pub/Sub | Triggers morning batch job, absorbs traffic spikes. |
| Object Storage | Cloudflare R2 | Edition article JSON (consumed by Gazette for static build). |
| AI Inference | Google Vertex AI / Gemini | Article generation (Flash + Pro tiers), validation, ledger mutation, context caching. |
| Categorisation | Gemini Flash (swappable) | Prompt categorisation into taxonomy categories. Runs behind `CategoriserStrategy` interface for future swap to local model. |
| Embedding | Local sentence-transformers | Prompt embedding for clustering. Runs on the same compute as the Newsroom Director. No API calls. |
| Clustering | HDBSCAN | Groups prompts into topically coherent clusters per newspaper. Local compute. |
| Static Hosting | Cloudflare Pages | Generated newspaper HTML (public, no auth). |
| Prompt UI Hosting | Cloudflare Pages | React SPA for prompt submission. |
| Payments | Braintree | Payment processing. No user data stored on our side. |

## Key Design Decisions

1. **Zero PII** — Braintree owns all user identity and payment data. Our database stores only transaction reference IDs, prompt text, weights, and categories. No names, emails, or personal data touch our servers.

2. **Two-level taxonomy** — Categories (30 curated topic labels) route prompts. Newspapers (6 audience-archetype editorial products) subscribe to categories and run independent pipelines. This separates classification granularity from editorial identity.

3. **Four-stage distillation pipeline** — Embed, cluster, digest, allocate (all local, ~$0) before a single expensive Gemini call per newspaper. The newspaper quality ceiling is set by distillation quality, not LLM capability. Invest engineering effort in the pipeline, keep the LLM as a pure writer/editor.

4. **Reach-based pricing** — The number of newspapers a prompt reaches (determined automatically by category classification and subscription intersection) determines its cost. Transparent and fair — users pay for the actual editorial footprint of their idea.

5. **PostgreSQL for transactional safety** — Payment-linked prompts require ACID guarantees. The WorldLedger requires atomic read-modify-write between morning runs. R2 cannot provide either.

6. **Pub/Sub for scale** — Decouples prompt ingestion from batch processing. Absorbs viral traffic spikes without database pressure.

7. **Vertex AI context caching with explicit destruction** — Cache the WorldLedger once per batch run, share across all persona calls, then force-delete immediately. Zero idle cost.

8. **Static site generation** — Generated newspapers are pre-rendered HTML via 11ty. No server needed to read news, no JavaScript required, instant global delivery via Cloudflare CDN.

9. **Separate prompt UI from reading experience** — `apps/imbryk` (React SPA) handles the interactive payment flow. `apps/gazette` (11ty) produces the static reading experience. Different tools for different jobs.

10. **Single canonical WorldLedger** — One copy in PostgreSQL, updated transactionally. No branching, no eventual consistency. Each morning run reads, modifies, and writes back atomically.

11. **World coherence gate** — The director (Pro model with full ledger context) decides whether a prompt enters the world, not the categoriser. This prevents nonsensical or contradictory events from corrupting the world state.

12. **Swappable categoriser** — The categorisation step is behind an interface (`CategoriserStrategy`). Ships with Gemini Flash, can be swapped to Ollama/local model without touching the rest of the pipeline.

13. **Configurable model tiers** — Each newspaper persona maps to a model tier (Flash or Pro) via configuration. Pro is used for reasoning-heavy newspapers, the Curator, validation, and ledger mutation. Flash handles stylistic voice work.

14. **Local embedding + HDBSCAN clustering** — Prompts are embedded with a local sentence transformer (no API cost) and clustered with HDBSCAN (finds natural topic groups without requiring a preset K). This transforms an unmanageable prompt volume into structured topic groups before any LLM is invoked.

15. **Weighted cluster digests** — High-value prompts (by payment amount, uniqueness) are included verbatim in digests. The long tail is extractively summarised. This preserves the actual language of important prompts while compressing redundancy.

16. **One Gemini call per newspaper per day** — Cost scales linearly with active newspapers, not with prompt volume. At ~$3 per newspaper edition, 6 newspapers cost ~$18/day.

17. **Overlap between newspapers is a feature** — When multiple newspapers receive the same prompt via shared category subscriptions, they produce genuinely distinct articles because each sees a different prompt pool composition and has a different editorial lens.
