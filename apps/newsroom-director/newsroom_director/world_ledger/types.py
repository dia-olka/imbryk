"""WorldLedger dataclasses — Python port of world-ledger.types.ts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Nation:
    name: str
    government_type: str
    leader: str
    stability: int
    description: str


@dataclass
class Alliance:
    name: str
    members: list[str]
    purpose: str


@dataclass
class Conflict:
    name: str
    parties: list[str]
    status: Literal["active", "frozen", "resolved"]
    description: str


@dataclass
class GeopoliticsState:
    nations: list[Nation] = field(default_factory=list)
    alliances: list[Alliance] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)


@dataclass
class Currency:
    name: str
    issuing_entity: str
    strength: int
    description: str


@dataclass
class TradingBloc:
    name: str
    members: list[str]
    focus: str


@dataclass
class Scarcity:
    resource: str
    severity: Literal["low", "moderate", "critical"]
    affected_regions: list[str]
    description: str


@dataclass
class EconomicsState:
    currencies: list[Currency] = field(default_factory=list)
    trading_blocs: list[TradingBloc] = field(default_factory=list)
    scarcities: list[Scarcity] = field(default_factory=list)
    global_gdp_trend: str = ""


@dataclass
class TechDomain:
    name: str
    maturity_level: Literal["emerging", "growth", "mature", "declining"]
    key_players: list[str]
    description: str


@dataclass
class TechnologyState:
    ai: TechDomain = field(
        default_factory=lambda: TechDomain(
            "Artificial Intelligence", "emerging", [], ""
        )
    )
    energy: TechDomain = field(
        default_factory=lambda: TechDomain("Energy", "emerging", [], "")
    )
    biotech: TechDomain = field(
        default_factory=lambda: TechDomain("Biotechnology", "emerging", [], "")
    )
    other: list[TechDomain] = field(default_factory=list)


@dataclass
class CulturalMovement:
    name: str
    reach: Literal["local", "regional", "global"]
    description: str


@dataclass
class CultureState:
    dominant_narratives: list[str] = field(default_factory=list)
    movements: list[CulturalMovement] = field(default_factory=list)
    media_landscape: str = ""


@dataclass
class MilitaryForce:
    entity: str
    conventional_strength: int
    nuclear_capable: bool
    special_capabilities: list[str]


@dataclass
class MilitaryState:
    forces: list[MilitaryForce] = field(default_factory=list)
    arms_races: list[str] = field(default_factory=list)
    doctrine_shifts: list[str] = field(default_factory=list)


@dataclass
class EnvironmentalCrisis:
    name: str
    severity: Literal["low", "moderate", "severe", "catastrophic"]
    affected_regions: list[str]
    description: str


@dataclass
class EnvironmentState:
    global_temperature_anomaly: float = 0.0
    crises: list[EnvironmentalCrisis] = field(default_factory=list)
    mitigation_efforts: list[str] = field(default_factory=list)


@dataclass
class HistoricalEvent:
    date: str
    headline: str
    description: str
    impact: str
    sectors: list[str]


@dataclass
class StoryThread:
    name: str
    status: Literal["developing", "ongoing", "resolved"]
    started: str
    last_covered: str
    summary: str
    related_nations: list[str] = field(default_factory=list)
    sectors: list[str] = field(default_factory=list)


@dataclass
class WorldLedger:
    epoch: str = ""
    synopsis: str = ""
    geopolitics: GeopoliticsState = field(default_factory=GeopoliticsState)
    economics: EconomicsState = field(default_factory=EconomicsState)
    technology: TechnologyState = field(default_factory=TechnologyState)
    culture: CultureState = field(default_factory=CultureState)
    military: MilitaryState = field(default_factory=MilitaryState)
    environment: EnvironmentState = field(default_factory=EnvironmentState)
    story_threads: list[StoryThread] = field(default_factory=list)
    history: list[HistoricalEvent] = field(default_factory=list)
