"""Newspaper persona definitions.

Data generated from data/personas.json — single source of truth.
Run `npx nx run newsroom-director:generate-data` to regenerate.
"""

from __future__ import annotations

from dataclasses import dataclass

from newsroom_director._generated_data import PERSONAS_DATA as _raw_file
from newsroom_director.taxonomy import NEWSPAPER_SUBSCRIPTIONS

_PREAMBLE: str = _raw_file["preamble"]


@dataclass
class PersonaConfig:
    id: str
    paper_name: str
    tagline: str
    ideology: str
    political_leaning: str
    writing_style: str
    biases: list[str]
    blindspots: list[str]
    regional_bias: str
    tone_adjustment: str
    subscribed_categories: list[str]
    model_tier: str  # "pro" | "flash"
    negative_prompt: str  # Imagen negative prompt (plain nouns)
    system_prompt_template: str


def _serialize_exemplars(exemplars: list[dict]) -> str:
    """Serialize exemplar objects into an XML-tagged block for the prompt."""
    if not exemplars:
        return ""
    blocks = []
    for ex in exemplars:
        blocks.append(
            f'<example author="{ex["author"]}" source="{ex["source"]}">\n'
            f"  <passage>{ex['passage']}</passage>\n"
            f"  <note>{ex['note']}</note>\n"
            f"</example>"
        )
    return (
        "<exemplars>\n"
        "Each exemplar represents a distinct voice on your editorial team. "
        "Study the prose style — absorb it, do not copy.\n\n"
        + "\n\n".join(blocks)
        + "\n</exemplars>"
    )


def _build_prompt(raw: dict) -> str:
    """Build the full system prompt from preamble + persona suffix + exemplars."""
    curator_prompt = raw.get("curatorPrompt")
    if curator_prompt:
        return curator_prompt
    suffix = raw.get("promptSuffix")
    if not suffix:
        return ""
    exemplars_block = _serialize_exemplars(raw.get("exemplars", []))
    suffix = suffix.replace("{{EXEMPLARS}}", exemplars_block)
    return f"{_PREAMBLE}\n\n{suffix}"


def _to_persona(raw: dict) -> PersonaConfig:
    persona_id = raw["id"]
    subs = NEWSPAPER_SUBSCRIPTIONS.get(persona_id, [])
    return PersonaConfig(
        id=persona_id,
        paper_name=raw["paperName"],
        tagline=raw["tagline"],
        ideology=raw["ideology"],
        political_leaning=raw["politicalLeaning"],
        writing_style=raw["writingStyle"],
        biases=raw["biases"],
        blindspots=raw["blindspots"],
        regional_bias=raw["regionalBias"],
        tone_adjustment=raw["toneAdjustment"],
        subscribed_categories=subs,
        model_tier=raw["modelTier"],
        negative_prompt=raw.get("negativePrompt", ""),
        system_prompt_template=_build_prompt(raw),
    )


def _find_persona(by_id: dict[str, PersonaConfig], persona_id: str) -> PersonaConfig:
    try:
        return by_id[persona_id]
    except KeyError:
        raise ValueError(
            f"Persona '{persona_id}' not found in personas.json. "
            "Run `npx nx run newsroom-director:generate-data` to regenerate."
        ) from None


_ALL = [_to_persona(p) for p in _raw_file["personas"]]
_BY_ID: dict[str, PersonaConfig] = {p.id: p for p in _ALL}

SOVEREIGN = _find_persona(_BY_ID, "sovereign")
ASPIRANT = _find_persona(_BY_ID, "aspirant")
OWNER = _find_persona(_BY_ID, "owner")
MORALIST = _find_persona(_BY_ID, "moralist")
RADICAL = _find_persona(_BY_ID, "radical")
HEDONIST = _find_persona(_BY_ID, "hedonist")
CURATOR = _find_persona(_BY_ID, "curator")

NEWSPAPER_PERSONAS: list[PersonaConfig] = [
    SOVEREIGN,
    ASPIRANT,
    OWNER,
    MORALIST,
    RADICAL,
    HEDONIST,
]

CURATOR_PERSONA: PersonaConfig = CURATOR

ALL_PERSONAS: list[PersonaConfig] = [*NEWSPAPER_PERSONAS, CURATOR]

MODEL_TIER_MAP: dict[str, str] = {p.id: p.model_tier for p in ALL_PERSONAS}

