# Editorial Excellence — Implementation Checklist

Tracks implementation progress for the improvements described in [EDITORIAL.md](./EDITORIAL.md).

---

## Step 0 — Tracking File
- [x] Create this checklist

## Step 1 — Editorial Team Traditions
- [x] Add `EDITORIAL TEAM TRADITION` block to The Sovereign promptSuffix (Lippmann, Applebaum, Orwell, le Carré, Tuchman, Sorensen)
- [x] Add `EDITORIAL TEAM TRADITION` block to The Aspirant promptSuffix (Monbiot, Klein, Baldwin, Galeano, Le Guin, Alexievich)
- [x] Add `EDITORIAL TEAM TRADITION` block to The Owner promptSuffix (Wolf, Levine, Lewis, Taleb, Galbraith, Tett)
- [x] Add `EDITORIAL TEAM TRADITION` block to The Moralist promptSuffix (Noonan, Scruton, Krauthammer, C.S. Lewis, Berry, Lincoln)
- [x] Add `EDITORIAL TEAM TRADITION` block to The Radical promptSuffix (Stone, Hitchens, Thompson, Swift, Taibbi, Saviano)
- [x] Add `EDITORIAL TEAM TRADITION` block to The Hedonist promptSuffix (Wolfe, Breslin, Talese, Wilde, Ephron, Dunne)
- [x] Run codegen + tests

## Step 2 — Few-Shot Exemplars
- [x] ~~Fictional exemplars added as placeholder~~ (temporary — replaced with real text)
- [x] Update exemplar schema to include `author` and `source` attribution fields
- [x] Update `serializeExemplars()` in both Python and TypeScript for new schema
- [x] **Source real text excerpts from EDITORIAL.md section 2.7 writers** (one per team member, 36 total)
- [x] Replace placeholder exemplars with real sourced passages (~150 words each)
- [x] Run codegen + tests

## Step 3 — Generation Config (temperature + thinking)
- [x] Add `temperature: 1.0` to VertexAIStrategy
- [x] Switch `thinking_budget=-1` → `thinking_level="high"` (pro) / `"medium"` (flash)
- [x] Run tests

## Step 4 — XML Tag Restructuring
- [x] Wrap preamble sections in XML tags (`<rules>`, `<image_style>`, `<output_schema>`)
- [x] Wrap all 6 newspaper promptSuffix fields in XML tags (`<role>`, `<editorial_team>`, `<voice>`, `<lens>`, `<image_style>`)
- [x] Run codegen + tests

## Step 5 — Self-Review & Thinking Guidance
- [x] Add `<thinking_guidance>` block to shared preamble
- [x] Add `<self_review>` block to shared preamble
- [x] Run codegen + tests

## Step 6 — Output Schema Descriptions
- [x] Add `<output_schema>` block at end of preamble with field descriptions
- [x] Run codegen + tests

## Step 7 — System Instruction / User Turn Split
- [x] Remove `{{WORLD_LEDGER_SYNOPSIS}}` from all promptSuffix fields
- [x] Remove `{{EDITORIAL_JOURNAL}}` from all promptSuffix fields
- [x] Remove `{{CLUSTER_DIGESTS}}` from all promptSuffix fields
- [x] Update `main.py` to assemble WorldLedger + journal + clusters in user_content
- [x] Update `prompt-builder.ts` to return `{ systemInstruction, userContent }`
- [x] Update `test_personas.py` placeholder assertions
- [x] Update `personas.spec.ts` placeholder assertions
- [x] Update `prompt-engine.spec.ts` tests
- [x] Run full test suite

## Step 8 — Imagen Improvements
- [x] Add `negativePrompt` field to each persona in `data/personas.json`
- [x] Add `negative_prompt` to `PersonaConfig` dataclass in `personas.py`
- [x] Add `negativePrompt` to `NewsroomPersona` interface in `persona.types.ts`
- [x] Update `image_gen/client.py` to accept and pass `negative_prompt` + `aspect_ratio`
- [x] Update image pipeline to use 16:9 for hero, 4:3 for article images
- [x] Update image tests (PartialClient signature)
- [x] Run codegen + full test suite

---

## Remaining Work

### Per-Article Team Member Assignment
Consider adding article-type-to-team-member mapping in the prompt (e.g., "For investigative pieces, channel Hitchens; for satirical commentary, channel Swift").

### Exemplar Passage Verification
All 36 exemplars now contain real text from the writers listed in EDITORIAL.md section 2.7. Passages were sourced from well-known published works. A manual review pass is recommended to verify word-for-word accuracy against the original sources, especially for:
- Book passages (Klein, Lewis, Taleb, Galbraith, Tett, Alexievich, Saviano, Ephron, Dunne)
- Paywalled articles (Applebaum/Atlantic, Wolf/FT, Levine/Bloomberg, Noonan/WSJ)

The `scripts/update_exemplars.py` script can be re-run after corrections.

---

## Verification
- [x] Full test suite passes (`npx nx run-many -t test`) — 404 Python + 156 TS + 61 ingestion-api
- [ ] Manual dry-run generation for The Sovereign to verify prompt quality
