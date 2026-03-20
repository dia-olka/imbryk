# Submission Pivot — From World-Altering Events to Topic Requests

## Summary

User-submitted prompts currently enter the distillation pipeline **verbatim** — their raw text appears in cluster digests and is fed directly to the article-writing LLM. The WorldLedger provides a fictional world context, and a coherence gate filters prompts against it.

This plan pivots to **real-world news**: prompts become topic requests that trigger Tavily research during the daily batch. The article-writing LLM receives researched news articles, never the user's original text. The WorldLedger transforms from fictional world state into **World History** — a factual record of real-world events over time, received by all LLMs. The economy ($1/newspaper, weight multiplier, categories, routing) is preserved unchanged.

### Design Decisions

- **Real-world news**, not fiction — articles report on actual events
- **Research during batch pipeline**, not at submission time — keeps submission fast and cheap
- **Topic steering only** — user prompt text never reaches the article-writing LLM; it controls *what* is researched, not *what is written*

---

## Phase 1: Topic Research Step

**Goal:** Each paid prompt triggers Tavily research during the morning batch, producing real news articles that enter the existing distillation pipeline.

### New Module

Create `apps/newsroom-director/newsroom_director/topic_researcher.py` — a new pipeline step that runs after prompt fetch and before distillation.

### Design

Reuse the existing `news_scout/searcher.py` (`TavilySearcher`, `SearchResult`) and follow the `query_generator.py` pattern (Gemini Flash for query formulation, structured output, retry logic).

For each unprocessed paid prompt:

1. **Generate 1–3 search queries** via Gemini Flash. The prompt text is the input; the model produces targeted, temporal-anchored queries (same style as `query_generator.py`).
2. **Execute Tavily searches** using the existing `TavilySearcher`. Deduplicate results by URL across all prompts.
3. **Return research results** as a list that maps back to the originating prompt (for weight inheritance).

### Weight Inheritance

Each prompt's payment weight is distributed across its research results:

```
weight_per_result = prompt.payment_amount / num_results
```

This preserves the economic signal: a $3 prompt producing 3 results yields 3 items at $1 weight each. The distillation pipeline's existing weight-based ranking (scorer, clustering, digest construction) handles priority naturally.

### Feature Flag

```python
# config.py
TOPIC_RESEARCH_ENABLED = os.getenv("TOPIC_RESEARCH_ENABLED", "false").lower() == "true"
```

When `false` (default), prompts enter the pipeline verbatim as today. When `true`, prompts are researched and only the research results enter distillation. Safe rollout: enable per-environment, compare edition quality.

### Integration Point

In `main.py`, after Step 2 (fetch prompts) and before Step 6 (route to newspapers):

```python
if TOPIC_RESEARCH_ENABLED and prompt_records:
    from .topic_researcher import research_prompts
    research_results = research_prompts(prompt_records, searcher, gen)
    # Replace prompt_records with research-derived DistillationPrompts
    # that carry inherited weights and original category assignments
```

### Files Changed

| File | Change |
|------|--------|
| `newsroom_director/topic_researcher.py` | **New** — query generation, search execution, weight distribution |
| `newsroom_director/main.py` | Insert topic research step between fetch and routing |
| `newsroom_director/config.py` | Add `TOPIC_RESEARCH_ENABLED` flag |
| `newsroom_director/distillation/types.py` | Add optional `source_url` field to `Prompt` dataclass (for citation) |

---

## Phase 2: Digest Reform

**Goal:** Cluster digests contain researched news (headline, snippet, source URL) instead of verbatim user prompt text.

### Current State

`distillation/digest.py` builds digests with:
- Verbatim high-value prompts: `[w:9820] "Solar panel output dropping..."` (user's raw text)
- Long-tail extractive summary of remaining prompts
- Keywords extracted from prompt text

### New Behaviour

When topic research is active, the `Prompt.text` field already contains the research result (headline + snippet) rather than user text — this happens in Phase 1 when research results replace raw prompts. The digest machinery (`build_digest`, `serialize_digest`) works unchanged because it operates on `Prompt.text` regardless of content.

The key change is in `serialize_digest`: add source URL attribution when available.

```
CLUSTER #3 | aggregate_weight: 847 | prompt_count: 5
High-value researched articles:
  [w:333] "Three Nations Seize River Dams" — Water wars escalate as...
          Source: https://example.com/water-wars
```

### User Prompt Isolation

User prompt text never enters digests. The transformation chain is:

```
User prompt → Gemini Flash queries → Tavily results → Prompt(text=headline+snippet) → digest
```

The user's original text is consumed by the query generator and discarded from the pipeline.

### Files Changed

| File | Change |
|------|--------|
| `newsroom_director/distillation/digest.py` | Add source URL to serialized digest format when `Prompt.source_url` is set |
| `newsroom_director/distillation/types.py` | `Prompt.source_url` field (added in Phase 1) |
| `newsroom_director/main.py` | No change (Phase 1 already replaces prompts with research results) |

---

## Phase 3: WorldLedger → World History Transformation

**Goal:** Transform the fictional WorldLedger into **World History** — a factual record of real-world events over time. All LLMs (personas, News Scout, mutation) receive the world history as context. The infrastructure (DB, load/save, synopsis injection, mutation step) stays; the framing shifts from fiction to fact.

### Why Keep It

- **Temporal context**: Knowing what happened last week/month helps personas write better, more contextual articles
- **Autonomous fallback**: When no paid prompts arrive, the News Scout uses world history to decide what topics to research
- **Factual record**: Accumulating a structured timeline of real-world events has standalone value

### What Changes

| Component | Location | Change |
|-----------|----------|--------|
| `NEWS_MUTATES_LEDGER` config flag | `config.py` | **Remove** — mutation always runs (factual history should always be updated) |
| Mutation prompt | `main.py` `_build_mutation_prompt()` | **Reframe**: "Record new real-world facts from today's articles" instead of "Evolve the fictional world state" |
| News Scout query generator | `news_scout/query_generator.py` | **Reframe**: Remove fictional-world framing from system prompt; keep world history as context for editorial decisions |
| News Scout WorldLedger loading | `news_scout/main.py` | **Keep** — still loads world history and passes synopsis to query generator |
| Synopsis injection in `main.py` | `main.py` `.replace("{{WORLD_LEDGER_SYNOPSIS}}", synopsis)` | **Keep** — all personas receive world history |
| `packages/world-state/` | package | **Rename/reframe** types: `WorldLedger` → keep class name but update docstrings from "fictional world" to "factual history" |

### What Stays Unchanged

| Component | Reason |
|-----------|--------|
| `world_ledger` DB table + load/save functions | Infrastructure stays; data is now factual |
| `load_world_ledger`, `save_world_ledger` | Still needed — just records facts now |
| `serialize_ledger_to_synopsis` | Still serializes world history for LLM context |
| `apply_mutation` | Still applies daily updates |
| `{{WORLD_LEDGER_SYNOPSIS}}` placeholder | All LLMs receive world history |
| Steps 3–4 in `main.py` (ledger load) | Still needed |
| Step 9 in `main.py` (mutation) | Still needed — always runs now (no flag check) |

### Gazette Changes

| File | Change |
|------|--------|
| `apps/gazette/src/timeline.njk` | **Keep** — now displays real-world history timeline. Update header copy from fictional to factual framing |
| `apps/gazette/src/about.njk` | Update copy: remove fictional-world references, reframe as real-world AI newspaper platform with historical record |

### News Scout Adaptation

The News Scout continues to load world history and pass it to the query generator. The query generation prompt shifts from "what would a journalist in this fictional world investigate?" to "what real-world developments are most editorially relevant, given this history of recent events?" The editorial journal and reader metrics remain as context inputs alongside the world history.

### Files Changed

| File | Change |
|------|--------|
| `newsroom_director/main.py` | Remove `NEWS_MUTATES_LEDGER` flag check (always mutate); reframe `_build_mutation_prompt()` for factual recording |
| `newsroom_director/config.py` | Remove `NEWS_MUTATES_LEDGER` flag |
| `newsroom_director/news_scout/query_generator.py` | Reframe system prompt: fictional world → real-world context; keep `synopsis` parameter |
| `apps/gazette/src/timeline.njk` | Update copy for real-world framing |
| `apps/gazette/src/about.njk` | Rewrite copy for real-world framing |

---

## Phase 4: Persona Prompt Updates

**Goal:** Update persona definitions to reflect real-world news reporting instead of fictional world simulation. The `{{WORLD_LEDGER_SYNOPSIS}}` placeholder **stays** — all LLMs receive world history.

### Preamble Changes (`data/personas.json`)

The `preamble` field (shared across all personas) needs these edits:

| Section | Current | New |
|---------|---------|-----|
| Role description | "Use the world context provided to ground your reporting" | "You produce a full newspaper edition based on real-world news articles provided in the cluster digests below. The WORLD HISTORY section provides a factual record of recent events for context." |
| ENCRYPTED PROMPTS section | Full paragraph about gibberish/encrypted submissions | **Remove entirely** — prompts no longer reach the LLM |
| Source citation | Not present | Add: "CITATION: When an article's source cluster includes source URLs, cite them naturally within the article body" |

### Per-Persona `promptSuffix` Changes

Every persona's `promptSuffix` contains:

```
WORLD CONTEXT:
{{WORLD_LEDGER_SYNOPSIS}}
```

**Keep this block but rename the header** from `WORLD CONTEXT` to `WORLD HISTORY` across all 6 newspaper personas. The `{{WORLD_LEDGER_SYNOPSIS}}` placeholder remains — it will be populated with the factual world history. The `{{EDITORIAL_JOURNAL}}` and `{{CLUSTER_DIGESTS}}` placeholders also remain.

### What Stays Unchanged

- All persona voices, ideologies, biases, and blindspots
- Headline rules, image prompt rules, output format
- Model tier assignments
- The Curator's `curatorPrompt` (operates on generated articles, not prompts)
- `{{EDITORIAL_JOURNAL}}` placeholder
- `{{CLUSTER_DIGESTS}}` placeholder
- `{{WORLD_LEDGER_SYNOPSIS}}` placeholder (now carries factual world history)
- Synopsis replacement in `main.py` (keeps working as-is)

### Codegen

After editing `data/personas.json`, run:

```sh
node scripts/generate-data.mjs
```

This regenerates `_generated_data.ts` and `_generated_data.py` across all consuming packages.

### Files Changed

| File | Change |
|------|--------|
| `data/personas.json` | Rename `WORLD CONTEXT` → `WORLD HISTORY` in all `promptSuffix` fields; update preamble for real-world framing; remove ENCRYPTED PROMPTS section; add citation instructions |
| Generated outputs | `_generated_data.ts`, `_generated_data.py` regenerated via codegen |

---

## Phase 5: Validation Removal

**Goal:** Remove the coherence validation step. With real-world news, there is no fictional world to validate against.

### Current State

`main.py` Step 5 (lines 217–242) runs `validate_prompts()` from `validation.py` — a Pro-tier Gemini call that checks each user prompt against the WorldLedger for coherence. This costs ~$3/day in Pro model tokens.

### Why It's Safe to Remove

1. **No fictional world** — coherence against what?
2. **Payment is the abuse filter** — users pay before submitting; economic friction prevents spam
3. **Prompt text never reaches article LLM** — even a malicious prompt only affects Gemini Flash query generation, which produces search queries (not articles)
4. **Saves ~$3/day** in Pro model costs

### What Changes

- Remove the `enable_validation` parameter from `run_morning_press()`
- Remove the validation step (lines 217–242) from `main.py`
- Remove `from .validation import validate_prompts` import
- Deprecate `validation.py` — keep `sanitize_prompt_text()` (used by `digest.py`) but remove `validate_prompts()` and `_VALIDATION_SYSTEM_PROMPT`

Note: `sanitize_prompt_text()` is imported by `distillation/digest.py` and should be moved to a shared utils module or kept in `validation.py` with a deprecation note.

### Files Changed

| File | Change |
|------|--------|
| `newsroom_director/main.py` | Remove validation step, `enable_validation` parameter, validation import |
| `newsroom_director/validation.py` | Remove `validate_prompts()`, keep `sanitize_prompt_text()` |
| `newsroom_director/config.py` | Remove `ENABLE_VALIDATION` env var handling in `cli_main()` (line 1307) |

---

## Phase 6: UI Reframing

**Goal:** Update user-facing copy from "world-altering events" to "topic requests."

### Frontend Changes

| File | Current Copy | New Copy |
|------|-------------|----------|
| `src/app/components/OrbInput.tsx` (line 96) | `"Describe a world-altering event"` | `"Request coverage of a topic"` |
| `apps/imbryk/src/app/components/OrbFrontFace.tsx` | Check for event/world references | Update to topic/coverage language |
| `apps/imbryk/src/app/components/Confirmation.tsx` | Check for event references | Update to topic language |

### Gazette Changes

| File | Change |
|------|--------|
| `apps/gazette/src/about.njk` (line 37) | "Submit a world-altering event" → "Request topic coverage" |
| `apps/gazette/src/about.njk` | Full copy rewrite (covered in Phase 3) |

### Tone Shift

- "world-altering event" → "topic" or "topic request"
- "submit an event" → "request coverage"
- "your event will be covered by..." → "your topic will be researched and covered by..."
- "the orb receives your event" → "the orb receives your request"

---

## Phase 7: Testing & Migration

### Feature Flag Rollout Strategy

1. **Deploy all code** with `TOPIC_RESEARCH_ENABLED=false` (default) — zero behaviour change
2. **Enable in staging** — run parallel editions (flag on vs off) and compare quality
3. **Enable in production** — flip flag, monitor edition quality and costs
4. **Remove flag** — once stable, remove the flag and the old code paths

### Test Updates Per Phase

| Phase | Test Changes |
|-------|-------------|
| Phase 1 | Unit tests for `topic_researcher.py`: query generation, weight inheritance math, Tavily integration. Integration test: prompt → research results → DistillationPrompt conversion |
| Phase 2 | Update `digest.py` tests: verify source URL appears in serialized digests. Verify user text never appears in digest output when research is active |
| Phase 3 | Update mutation prompt tests for factual framing. Remove `NEWS_MUTATES_LEDGER` flag from test fixtures. Update News Scout query generator tests for real-world framing |
| Phase 4 | Snapshot tests for generated persona prompts — verify `{{WORLD_LEDGER_SYNOPSIS}}` placeholder is present (world history). Verify `WORLD HISTORY` header replaces `WORLD CONTEXT`. Verify codegen output matches `data/personas.json` |
| Phase 5 | Remove validation step tests. Verify `sanitize_prompt_text()` tests still pass |
| Phase 6 | Update e2e tests (`apps/imbryk-e2e/`) — check for new copy text. Update gazette e2e for removed timeline page |

### Economy Preservation Tests

Critical invariants that must hold across the pivot:

```python
def test_pricing_unchanged():
    """Price = base × newspapers_reached. Category routing unchanged."""

def test_weight_inheritance():
    """Sum of research result weights == original prompt payment."""

def test_routing_unchanged():
    """Category → newspaper routing via set intersection is identical."""

def test_news_items_still_fill_gaps():
    """News Scout items still enter pipeline at low weight."""
```

### Rollback Strategy

Each phase is independently deployable and reversible:

- **Phase 1:** Set `TOPIC_RESEARCH_ENABLED=false` → immediate rollback to verbatim prompts
- **Phase 2:** Digest format is backward-compatible (source URL is additive)
- **Phase 3:** Prompt reframing is cosmetic — revert mutation/query-generator prompts to restore fictional framing; re-add `NEWS_MUTATES_LEDGER` flag
- **Phase 4:** Revert `data/personas.json` and re-run codegen
- **Phase 5:** Re-enable validation flag in `cli_main()`
- **Phase 6:** Revert copy changes (cosmetic only)

---

## Economy Impact Analysis

### What's Preserved

| Component | Status |
|-----------|--------|
| Pricing: `base × newspapers_reached` | Unchanged |
| 30-category taxonomy | Unchanged |
| Category → newspaper routing (set intersection) | Unchanged |
| Weight-based distillation (scorer, clustering, digest ranking) | Unchanged |
| Payment amount as primary weight signal | Unchanged — distributed across research results |
| News Scout gap-filling at low weight | Unchanged |
| Per-newspaper model tier assignments | Unchanged |

### Cost Impact

| Item | Current | After Pivot | Delta |
|------|---------|-------------|-------|
| Coherence validation (Pro) | ~$3/day | $0 | -$3/day |
| World History mutation (Pro) | ~$3/day | ~$3/day | $0 (kept) |
| Topic research queries (Flash) | $0 | ~$0.50/day | +$0.50/day |
| Topic research Tavily searches | $0 | ~$0.50–1.00/day | +$0.50–1.00/day |
| **Net daily change** | | | **-$1.50 to -$2.00/day** |

The pivot is cost-negative: removing the Pro validation call saves more than the new Flash + Tavily costs. The World History mutation cost stays (factual history recording is valuable).

### No More "Paid But Rejected" Prompts

Currently, the coherence gate can reject paid prompts — users pay but their event doesn't enter the world. After the pivot, every paid prompt triggers research. If research returns zero results, the prompt still contributed payment weight to the system (see Open Questions).

---

## Open Questions

### 1. Empty Research Results

**Scenario:** A prompt's Tavily search returns zero relevant results.

**Options:**
- **Drop silently** — the prompt's weight is lost. Payment was consumed but nothing enters the pipeline. This mirrors the current "rejected by coherence gate" behaviour but is less likely (search rarely returns nothing).
- **Fallback to prompt text** — if research fails, include the prompt text itself as a low-weight item. Breaks the "user text never reaches article LLM" guarantee.
- **Recommended: Drop with refund eligibility** — drop from pipeline, flag in DB as `research_empty`. Build a future refund/credit mechanism for these cases. In practice, this should be rare (<5% of prompts).

### 2. Source Citation in Articles

**Scenario:** Should generated articles cite the Tavily source URLs?

**Recommended: Yes.** Add citation instructions to the persona preamble (Phase 4). Benefits:
- Adds credibility to AI-generated articles
- Readers can verify claims
- Differentiates from pure AI hallucination

### 3. Timeline Page Fate

**Scenario:** The gazette's `timeline.njk` displays WorldLedger history.

**Decision: Keep.** The timeline now displays real-world history — a factual record of events over time. Update the page header and copy from fictional to factual framing. This is a differentiating feature: readers can see the accumulating historical context that informs each edition.

---

## Key Files Reference

| File | Role in Pivot |
|------|--------------|
| `apps/newsroom-director/newsroom_director/main.py` | Pipeline orchestrator — central integration point for all phases |
| `apps/newsroom-director/newsroom_director/topic_researcher.py` | **New** — topic research step (Phase 1) |
| `apps/newsroom-director/newsroom_director/config.py` | Feature flags, removed configs |
| `apps/newsroom-director/newsroom_director/distillation/types.py` | `Prompt` dataclass — add `source_url` field |
| `apps/newsroom-director/newsroom_director/distillation/digest.py` | Digest serialization — add source URL output |
| `apps/newsroom-director/newsroom_director/distillation/scorer.py` | Weight computation — unchanged but verify with inherited weights |
| `apps/newsroom-director/newsroom_director/news_scout/searcher.py` | `TavilySearcher` — reused by topic researcher |
| `apps/newsroom-director/newsroom_director/news_scout/query_generator.py` | Pattern to follow; also reframed from fictional to real-world context |
| `apps/newsroom-director/newsroom_director/news_scout/main.py` | News Scout entry point — keeps WorldLedger loading (now world history) |
| `apps/newsroom-director/newsroom_director/validation.py` | Coherence gate — deprecate `validate_prompts()` |
| `data/personas.json` | Persona prompts — keep `{{WORLD_LEDGER_SYNOPSIS}}`, rename header to `WORLD HISTORY`, update preamble |
| `scripts/generate-data.mjs` | Codegen — regenerate after persona changes |
| `src/app/components/OrbInput.tsx` | Frontend copy — "world-altering event" text |
| `apps/imbryk/src/app/components/OrbFrontFace.tsx` | Frontend copy |
| `apps/imbryk/src/app/components/Confirmation.tsx` | Frontend copy |
| `apps/gazette/src/timeline.njk` | Keep — update copy for real-world history framing |
| `apps/gazette/src/about.njk` | Rewrite copy for real-world framing |

---

## Phase Dependency Graph

```
Phase 1 (Topic Research) ──► Phase 2 (Digest Reform)
                                     │
Phase 3 (World History Reframe) ◄────┘
        │
        ├──► Phase 4 (Persona Updates)
        │
        └──► Phase 5 (Validation Removal)

Phase 6 (UI Reframing) — independent, can ship anytime

Phase 7 (Testing) — parallel with each phase
```

Phases 1→2→3 are sequential. Phases 4 and 5 depend on Phase 3. Phase 6 is independent. Phase 7 runs alongside each phase.
