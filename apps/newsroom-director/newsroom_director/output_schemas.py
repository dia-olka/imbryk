"""Dataclass schemas for structured LLM output.

Passed to Gemini's response_schema to enforce exact field names and
structure in the generated JSON, preventing field name deviations
(e.g. "title"/"content"/"fullArticles") that cause gazette parse errors.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Literal

from .world_ledger.types import (
    Alliance,
    Conflict,
    CulturalMovement,
    Currency,
    EnvironmentalCrisis,
    HistoricalEvent,
    MilitaryForce,
    Nation,
    Scarcity,
    StoryThread,
    TechDomain,
    TradingBloc,
)


@dataclass
class ArticleOutput:
    headline: str
    body: str
    weight: float | None = None
    clusters: list[int] | None = None
    imagePrompt: str | None = None


@dataclass
class InBriefOutput:
    headline: str
    summary: str
    clusters: list[int] | None = None


@dataclass
class NewspaperOutput:
    newspaper_name: str
    frontPageImagePrompt: str
    articles: list[ArticleOutput]
    in_brief: list[InBriefOutput] | None = None
    editors_note: str | None = None
    metadata: dict | None = field(default=None)


@dataclass
class CuratorOutput:
    """Structured curator synthesis V1 — plain string lists."""
    consensus: list[str]
    fault_lines: list[str]
    uncovered_angles: list[str]
    what_to_watch: list[str]


# ─── Curator V2: structured analysis with spectrum data ──────────────────────


@dataclass
class FaultLineStance:
    """A newspaper's position on a fault line axis (0 = left label, 100 = right label)."""
    newspaper_id: str
    score: int


@dataclass
class FaultLineItem:
    """A fault line with opposing labels and per-newspaper stance scores."""
    topic: str
    label_left: str
    label_right: str
    stances: list[FaultLineStance]
    summary: str


@dataclass
class ConsensusItem:
    """A consensus point with participating newspaper voices."""
    text: str
    voices: list[str]


@dataclass
class GapItem:
    """A topic or angle that no newspaper covered."""
    topic: str
    description: str


@dataclass
class CuratorOutputV2:
    """Structured curator synthesis V2 — spectrum analysis with stance scores.

    The ``version`` field distinguishes V2 from V1 at parse time.
    """
    version: int  # always 2
    consensus: list[ConsensusItem]
    fault_lines: list[FaultLineItem]
    gaps: list[GapItem]
    what_to_watch: list[str]


# ─── World-ledger mutation: partial-update sub-schemas ───────────────────────

# Add-* lists reuse the world_ledger dataclasses directly — their required
# fields (e.g. Scarcity.resource, EnvironmentalCrisis.severity enum) become
# schema constraints Gemini must satisfy, so the `KeyError: 'resource'` class
# of drift cannot recur.
#
# Update-* lists cannot reuse those dataclasses: a partial update must carry
# only the fields that should change, so every field except the identifier
# (name / entity) is optional. These sub-schemas make that explicit.


@dataclass
class NationUpdate:
    name: str
    government_type: str | None = None
    leader: str | None = None
    stability: int | None = None
    description: str | None = None


@dataclass
class ConflictUpdate:
    name: str
    parties: list[str] | None = None
    status: Literal["active", "frozen", "resolved"] | None = None
    description: str | None = None


@dataclass
class MilitaryForceUpdate:
    entity: str
    conventional_strength: int | None = None
    nuclear_capable: bool | None = None
    special_capabilities: list[str] | None = None


@dataclass
class StoryThreadUpdate:
    name: str
    status: Literal["developing", "ongoing", "resolved"] | None = None
    started: str | None = None
    last_covered: str | None = None
    summary: str | None = None
    related_nations: list[str] | None = None
    sectors: list[str] | None = None


@dataclass
class TechDomainUpdate:
    name: str | None = None
    maturity_level: Literal["emerging", "growth", "mature", "declining"] | None = None
    key_players: list[str] | None = None
    description: str | None = None


@dataclass
class LedgerMutationOutput:
    """Schema for a single LLM-generated world-ledger mutation.

    Mirrors LedgerMutation (world_ledger.mutator) field-by-field so Gemini's
    controlled generation emits exactly what _dict_to_mutation expects. Every
    field is optional — the model only fills in what should change.
    """
    epoch: str | None = None
    synopsis: str | None = None

    add_nations: list[Nation] | None = None
    update_nations: list[NationUpdate] | None = None
    add_alliances: list[Alliance] | None = None
    add_conflicts: list[Conflict] | None = None
    update_conflicts: list[ConflictUpdate] | None = None

    add_currencies: list[Currency] | None = None
    add_trading_blocs: list[TradingBloc] | None = None
    add_scarcities: list[Scarcity] | None = None
    update_global_gdp_trend: str | None = None

    update_ai: TechDomainUpdate | None = None
    update_energy: TechDomainUpdate | None = None
    update_biotech: TechDomainUpdate | None = None
    add_tech_domains: list[TechDomain] | None = None

    add_dominant_narratives: list[str] | None = None
    add_movements: list[CulturalMovement] | None = None
    update_media_landscape: str | None = None

    add_forces: list[MilitaryForce] | None = None
    update_forces: list[MilitaryForceUpdate] | None = None
    add_arms_races: list[str] | None = None
    add_doctrine_shifts: list[str] | None = None

    update_temperature_anomaly: float | None = None
    add_crises: list[EnvironmentalCrisis] | None = None
    add_mitigation_efforts: list[str] | None = None

    add_story_threads: list[StoryThread] | None = None
    update_story_threads: list[StoryThreadUpdate] | None = None

    add_historical_events: list[HistoricalEvent] | None = None


# ─── Output validation ────────────────────────────────────────────────────────

def is_valid_newspaper(raw: str) -> bool:
    """Return True if *raw* parses as a newspaper with at least one usable article."""
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return False
    articles = parsed.get("articles") or []
    return (
        isinstance(articles, list)
        and len(articles) > 0
        and any(a.get("headline") and a.get("body") for a in articles)
    )


def is_valid_curator(raw: str) -> bool:
    """Return True if *raw* parses as a non-empty curator synthesis (V1, V2, or legacy)."""
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return False

    version = parsed.get("version")

    # V2 structured format — validate stance scores and nested objects
    if version == 2:
        consensus = parsed.get("consensus")
        fault_lines = parsed.get("fault_lines")
        if not isinstance(consensus, list) or not isinstance(fault_lines, list):
            return False
        # At least one consensus or fault line
        if len(consensus) == 0 and len(fault_lines) == 0:
            return False
        # Validate fault line structure
        for fl in fault_lines:
            if not isinstance(fl, dict):
                return False
            if not fl.get("label_left") or not fl.get("label_right"):
                return False
            stances = fl.get("stances")
            if not isinstance(stances, list) or len(stances) == 0:
                return False
            for s in stances:
                if not isinstance(s, dict) or "newspaper_id" not in s:
                    return False
                score = s.get("score")
                if not isinstance(score, (int, float)) or score < 0 or score > 100:
                    return False
        return True

    # V1 structured format — plain string lists
    consensus = parsed.get("consensus")
    if isinstance(consensus, list) and len(consensus) > 0:
        return True

    # Legacy text format
    text = parsed.get("text", "")
    return isinstance(text, str) and len(text.strip()) > 100
