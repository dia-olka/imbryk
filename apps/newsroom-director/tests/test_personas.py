"""Tests for persona definitions."""

from newsroom_director.personas import (
    _PREAMBLE,
    ALL_PERSONAS,
    CURATOR_PERSONA,
    MODEL_TIER_MAP,
    NEWSPAPER_PERSONAS,
)
from newsroom_director.taxonomy import NEWSPAPER_SUBSCRIPTIONS


class TestPersonaDefinitions:
    def test_six_newspapers_defined(self):
        assert len(NEWSPAPER_PERSONAS) == 6

    def test_curator_defined(self):
        assert CURATOR_PERSONA.id == "curator"
        assert CURATOR_PERSONA.model_tier == "flash"

    def test_all_personas_includes_curator(self):
        assert len(ALL_PERSONAS) == 7
        ids = {p.id for p in ALL_PERSONAS}
        assert "curator" in ids

    def test_newspaper_ids(self):
        ids = {p.id for p in NEWSPAPER_PERSONAS}
        expected = {
            "sovereign", "aspirant", "owner",
            "moralist", "radical", "hedonist",
        }
        assert ids == expected

    def test_subscribed_categories_match_taxonomy(self):
        for persona in NEWSPAPER_PERSONAS:
            taxonomy_cats = set(
                NEWSPAPER_SUBSCRIPTIONS.get(persona.id, [])
            )
            persona_cats = set(persona.subscribed_categories)
            assert persona_cats == taxonomy_cats, (
                f"{persona.id}: persona categories {persona_cats} "
                f"!= taxonomy categories {taxonomy_cats}"
            )

    def test_system_prompts_have_placeholders(self):
        for persona in NEWSPAPER_PERSONAS:
            assert "{{WORLD_LEDGER_SYNOPSIS}}" in persona.system_prompt_template
            assert "{{CLUSTER_DIGESTS}}" in persona.system_prompt_template

    def test_curator_prompt_has_articles_placeholder(self):
        assert "{{ALL_ARTICLES}}" in CURATOR_PERSONA.system_prompt_template

    def test_model_tier_map(self):
        assert MODEL_TIER_MAP["sovereign"] == "pro"
        assert MODEL_TIER_MAP["aspirant"] == "flash"
        assert MODEL_TIER_MAP["owner"] == "pro"
        assert MODEL_TIER_MAP["moralist"] == "flash"
        assert MODEL_TIER_MAP["radical"] == "flash"
        assert MODEL_TIER_MAP["hedonist"] == "flash"
        assert MODEL_TIER_MAP["curator"] == "flash"

    def test_each_persona_has_biases_and_blindspots(self):
        for persona in ALL_PERSONAS:
            assert len(persona.biases) > 0
            assert len(persona.blindspots) > 0


class TestPreambleLanguageInstructions:
    def test_preamble_instructs_english_output(self):
        assert "LANGUAGE:" in _PREAMBLE
        assert "English" in _PREAMBLE

    def test_preamble_handles_encrypted_prompts(self):
        assert "ENCRYPTED PROMPTS:" in _PREAMBLE
        assert "encrypted" in _PREAMBLE.lower()

    def test_newspaper_system_prompts_contain_language_instruction(self):
        for persona in NEWSPAPER_PERSONAS:
            assert "LANGUAGE:" in persona.system_prompt_template

    def test_curator_prompt_instructs_english_output(self):
        assert "English" in CURATOR_PERSONA.system_prompt_template
