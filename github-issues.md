# GitHub Issues for Claude Code (GitHub App)

These issues are scoped for code analysis and can be completed by the GitHub Claude app via PR.

---

## Issue 1: Security audit — OWASP Top 10 review

**Title:** Security audit: OWASP Top 10 review across all apps

**Labels:** `security`, `phase-10`

**Body:**

### Context

Imbryk handles payment flows (Braintree) and user-submitted prompts. Before launch we need an OWASP Top 10 review of all application code.

### Scope

Review the following for security vulnerabilities:

1. **Injection** — `apps/ingestion-api/ingestion_api/` (SQL via SQLAlchemy, prompt text handling)
2. **Broken Authentication** — Braintree webhook signature validation in `main.py:braintree_webhook`
3. **Sensitive Data Exposure** — ensure no secrets, API keys, or credentials are hardcoded anywhere in the repo
4. **XML External Entities** — check any XML parsing (Braintree webhook payloads)
5. **Broken Access Control** — verify endpoints that should be restricted are (webhook endpoint especially)
6. **Security Misconfiguration** — CORS config in `ingestion_api/config.py`, rate limiting in `main.py`, debug modes
7. **XSS** — `apps/imbryk/src/` React frontend (user input rendering, `dangerouslySetInnerHTML` usage)
8. **Insecure Deserialization** — Pydantic model validation in `schemas.py`, any `pickle` usage in newsroom-director
9. **Using Components with Known Vulnerabilities** — run `npm audit` and `pip audit` equivalent
10. **Insufficient Logging & Monitoring** — verify error paths don't leak sensitive data in logs

### Key files

- `apps/ingestion-api/ingestion_api/main.py` — all API endpoints
- `apps/ingestion-api/ingestion_api/config.py` — environment variable handling
- `apps/ingestion-api/ingestion_api/database.py` — SQLAlchemy setup
- `apps/imbryk/src/app/api/client.ts` — frontend fetch calls
- `apps/imbryk/src/app/hooks/useBraintree.ts` — payment handling
- `apps/newsroom-director/newsroom_director/main.py` — batch job entry point

### Deliverable

Open a PR that fixes any vulnerabilities found and documents the audit results as comments on this issue.

---

## Issue 2: Zero PII audit

**Title:** Verify zero PII: audit all code for personal data leakage

**Labels:** `security`, `privacy`, `phase-10`

**Body:**

### Context

Imbryk's core design principle is **zero PII** — Braintree owns all user identity. Our database should store only transaction reference IDs, prompt text, weights, and categories. No names, emails, IP addresses, or personal data should touch our code.

### Audit scope

1. **Database models** — `apps/ingestion-api/ingestion_api/models.py`: verify no PII columns exist in `prompts`, `categorised_prompts`, `payment_refs`, `editions`, `edition_articles` tables
2. **API request handling** — `main.py`: check that request bodies, headers, and IP addresses are not persisted beyond rate limiting
3. **Logging** — search all Python and TypeScript files for `logging`, `console.log`, `print` statements that might log user data, IP addresses, or payment details
4. **Braintree webhook** — `main.py:braintree_webhook`: verify we only extract `transaction_id`, `amount`, and `prompt_text` from the webhook payload — no customer info
5. **Frontend** — `apps/imbryk/src/`: verify no analytics, tracking pixels, or user fingerprinting
6. **Error responses** — verify error messages don't leak internal state or user data
7. **Alembic migrations** — `apps/ingestion-api/alembic/`: verify migration history doesn't contain PII columns that were later removed

### Deliverable

Open a PR documenting the audit findings. Fix any PII leakage found. Add a comment in `config.py` or a `PRIVACY.md` documenting the zero-PII invariant and what each table stores.

---

## Issue 3: Dependency vulnerability scan

**Title:** Scan and fix vulnerable dependencies across all packages

**Labels:** `security`, `dependencies`, `phase-10`

**Body:**

### Context

The project has multiple dependency trees: npm (frontend + packages), Python (ingestion-api, newsroom-director). We need to identify and address known vulnerabilities before launch.

### Tasks

1. **npm** — analyse `package-lock.json` output from `npm audit`. Categorise findings by severity. Fix or document acceptable risk for each.
2. **Python (ingestion-api)** — review `apps/ingestion-api/pyproject.toml` dependencies. Check for known CVEs in FastAPI, SQLAlchemy, Braintree SDK, slowapi, Pydantic.
3. **Python (newsroom-director)** — review `apps/newsroom-director/pyproject.toml` dependencies. Check for known CVEs in torch, sentence-transformers, hdbscan, boto3, google-cloud-aiplatform.
4. **Version pinning** — verify all production dependencies have minimum version constraints. Flag any unpinned or overly broad version ranges.
5. **Transitive dependencies** — check for vulnerable transitive dependencies that may not be directly listed.

### Deliverable

Open a PR that:
- Updates dependency versions to fix critical/high vulnerabilities
- Documents accepted risks for vulnerabilities that can't be fixed (e.g., torch ecosystem)
- Adds version lower bounds where missing

---

## Issue 4: Persona system prompt quality review

**Title:** Review and refine AI persona system prompt templates

**Labels:** `ai`, `quality`, `phase-10`

**Body:**

### Context

Each of the 6 newspaper personas + The Curator has a `systemPromptTemplate` in `packages/ai-personas/src/lib/personas.ts`. These templates define the editorial voice, biases, and output format for each newspaper. Quality of these prompts directly determines article quality.

### Review criteria

1. **Voice consistency** — does each persona's system prompt produce a distinctly recognisable voice? Compare The Sovereign (institutional) vs The Radical (aggressive) vs The Hedonist (tabloid).
2. **Bias fidelity** — do the declared `biases` and `blindspots` arrays actually manifest in the system prompt instructions?
3. **Output format compliance** — do prompts clearly instruct the model to produce: full articles, In Brief section, Editor's note, and metadata block?
4. **Weighting instructions** — do prompts correctly explain how to interpret `aggregate_weight` and verbatim markers `[w:XXXX]`?
5. **Placeholder usage** — verify `{{WORLD_LEDGER_SYNOPSIS}}` and `{{CLUSTER_DIGESTS}}` placeholders are correctly positioned
6. **Curator template** — verify it uses `{{ALL_ARTICLES}}` and correctly instructs cross-article synthesis
7. **Edge cases** — what happens with very few prompts? With only one cluster? The prompts should handle gracefully.
8. **Token efficiency** — are prompts unnecessarily verbose? Every token in the system prompt is a token not available for output.

### Key files

- `packages/ai-personas/src/lib/personas.ts` — all persona definitions
- `packages/ai-personas/src/lib/persona.types.ts` — NewsroomPersona interface
- `packages/prompt-engine/src/` — template interpolation

### Deliverable

Open a PR with refined system prompt templates. Document the rationale for each change.

---

## Issue 5: Error handling and failure behaviour review

**Title:** Define and implement failure behaviour across the pipeline

**Labels:** `reliability`, `phase-10`

**Body:**

### Context

The system has multiple failure points: API errors, Gemini failures, database issues, R2 write failures. We need consistent failure behaviour and clear documentation of what happens when things go wrong.

### Review scope

1. **Ingestion API** (`apps/ingestion-api/ingestion_api/main.py`)
   - What happens if the categoriser fails mid-request?
   - What happens if the database is unreachable during webhook processing?
   - Are partial writes rolled back correctly (prompt saved but categorisation failed)?
   - Is the Braintree webhook idempotent (duplicate delivery)?

2. **Newsroom Director** (`apps/newsroom-director/newsroom_director/main.py`)
   - If one newspaper's Gemini call fails, do the others still proceed?
   - If WorldLedger mutation fails after articles are written, what state are we in?
   - If R2 write fails, are articles lost?
   - What happens if the context cache can't be created or deleted?

3. **Frontend** (`apps/imbryk/src/`)
   - Does the ErrorBoundary catch all failure modes?
   - What happens if the quote API is down? Braintree is down?
   - Are there appropriate loading/error states for every async operation?

4. **Pipeline-level**
   - If the morning batch fails entirely, should we publish nothing, the last successful edition, or a stub?
   - Should failed prompts be retried in the next run or marked as permanently failed?

### Deliverable

Open a PR that:
- Adds missing error handling where gaps are found
- Documents the failure behaviour decision in ARCHITECTURE.md
- Adds retry logic or graceful degradation where appropriate

---

## Issue 6: Accessibility audit of frontend components

**Title:** WCAG 2.2 AA accessibility audit of the Imbryk prompt UI

**Labels:** `accessibility`, `frontend`, `phase-10`

**Body:**

### Context

The Imbryk frontend (`apps/imbryk`) must meet WCAG 2.2 AA. The implementation includes ARIA landmarks, skip links, focus rings, labels, and `prefers-reduced-motion` support, but needs a thorough code-level audit.

### Audit checklist

1. **Colour contrast** — verify all text/background combinations meet 4.5:1 (text) and 3:1 (UI components) against the theme in `src/styles.css` (especially the orb's white-on-dark text)
2. **Keyboard navigation** — trace the tab order through all interactive elements in `PromptFlow.tsx`. Verify no keyboard traps exist, especially in the Braintree Drop-in.
3. **Screen reader** — verify all form inputs have associated labels (`OrbInput.tsx`), all dynamic content uses `aria-live` (`QuotePreview.tsx`, `Confirmation.tsx`), and the orb visual is hidden from AT (`aria-hidden="true"`)
4. **Focus management** — when state transitions occur in PromptFlow (input → payment → confirmed), does focus move to a logical target?
5. **Touch targets** — verify all buttons and interactive elements meet 44x44px minimum (`Button` component `min-h-[44px] min-w-[44px]`)
6. **Error messages** — verify validation errors are linked to inputs via `aria-describedby` and announced via `role="alert"`
7. **Reduced motion** — verify `orb.css` `@media (prefers-reduced-motion: reduce)` disables all animations

### Key files

- `src/app/components/OrbInput.tsx` + `orb.css`
- `src/app/components/PromptFlow.tsx`
- `src/app/components/PaymentForm.tsx`
- `src/app/components/Confirmation.tsx`
- `src/components/ui/*.tsx` — all shadcn/ui components
- `src/styles.css` — theme tokens

### Deliverable

Open a PR fixing any accessibility gaps found. Add automated accessibility tests where possible.

---

## Issue 7: Code quality review of distillation pipeline

**Title:** Review distillation pipeline for correctness and edge cases

**Labels:** `quality`, `ai`, `phase-10`

**Body:**

### Context

The 4-stage distillation pipeline (embed → cluster → digest → budget) in `apps/newsroom-director/newsroom_director/distillation/` processes raw user prompts before they reach the LLM. Pipeline quality sets the article quality ceiling. We need to review for correctness, edge cases, and numerical stability.

### Review scope

1. **Embedder** (`distillation/embedder.py`) — does it handle empty input, single-prompt input, very long prompts, and non-ASCII text correctly?
2. **Scorer** (`distillation/scorer.py`) — is the `weight = payment_amount_norm × uniqueness_bonus` formula numerically stable? What happens with zero payments? Division by zero? All-identical prompts?
3. **Clusterer** (`distillation/clusterer.py`) — HDBSCAN with very few prompts (1-5)? All prompts identical? `min_cluster_size` and `min_samples` defaults — are they sensible for expected data volumes?
4. **Digest** (`distillation/digest.py`) — does extractive summarisation (LexRank) degrade gracefully with very short or very long prompts? Are verbatim selections representative?
5. **Budget** (`distillation/budget.py`) — does proportional allocation handle edge cases: single cluster, all equal weights, zero total weight? Does `merge_low_weight_clusters` preserve important information?
6. **Integration** — does the full pipeline handle: 0 prompts, 1 prompt, 1000 prompts, prompts with only noise clusters (no clean clusters)?

### Key files

- `apps/newsroom-director/newsroom_director/distillation/` — all pipeline stages
- `apps/newsroom-director/tests/` — existing test coverage

### Deliverable

Open a PR adding tests for edge cases found and fixing any bugs. Document recommended HDBSCAN parameter ranges for different data volumes.
