"""Apply structured mutations to a WorldLedger.

Python port of world-ledger.mutator.ts — same merge/append logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .types import (
    Alliance,
    Conflict,
    CulturalMovement,
    CultureState,
    Currency,
    EconomicsState,
    EnvironmentalCrisis,
    EnvironmentState,
    GeopoliticsState,
    HistoricalEvent,
    MilitaryForce,
    MilitaryState,
    Nation,
    Scarcity,
    StoryThread,
    TechDomain,
    TechnologyState,
    TradingBloc,
    WorldLedger,
)


@dataclass
class LedgerMutation:
    synopsis: str | None = None

    # Geopolitics
    add_nations: list[Nation] = field(default_factory=list)
    update_nations: list[dict[str, Any]] = field(default_factory=list)
    add_alliances: list[Alliance] = field(default_factory=list)
    add_conflicts: list[Conflict] = field(default_factory=list)
    update_conflicts: list[dict[str, Any]] = field(default_factory=list)

    # Economics
    add_currencies: list[Currency] = field(default_factory=list)
    add_trading_blocs: list[TradingBloc] = field(default_factory=list)
    add_scarcities: list[Scarcity] = field(default_factory=list)
    update_global_gdp_trend: str | None = None

    # Technology
    update_ai: dict[str, Any] | None = None
    update_energy: dict[str, Any] | None = None
    update_biotech: dict[str, Any] | None = None
    add_tech_domains: list[TechDomain] = field(default_factory=list)

    # Culture
    add_dominant_narratives: list[str] = field(default_factory=list)
    add_movements: list[CulturalMovement] = field(default_factory=list)
    update_media_landscape: str | None = None

    # Military
    add_forces: list[MilitaryForce] = field(default_factory=list)
    update_forces: list[dict[str, Any]] = field(default_factory=list)
    add_arms_races: list[str] = field(default_factory=list)
    add_doctrine_shifts: list[str] = field(default_factory=list)

    # Environment
    update_temperature_anomaly: float | None = None
    add_crises: list[EnvironmentalCrisis] = field(default_factory=list)
    add_mitigation_efforts: list[str] = field(default_factory=list)

    # Story Threads
    add_story_threads: list[StoryThread] = field(default_factory=list)
    update_story_threads: list[dict[str, Any]] = field(default_factory=list)

    # History
    add_historical_events: list[HistoricalEvent] = field(default_factory=list)


def apply_mutation(
    ledger: WorldLedger, mutation: LedgerMutation
) -> WorldLedger:
    return WorldLedger(
        epoch=ledger.epoch,
        synopsis=(
            mutation.synopsis
            if mutation.synopsis is not None
            else ledger.synopsis
        ),
        geopolitics=GeopoliticsState(
            nations=_merge_by_key(
                ledger.geopolitics.nations,
                mutation.add_nations,
                mutation.update_nations,
                "name",
            ),
            alliances=_append(
                ledger.geopolitics.alliances, mutation.add_alliances
            ),
            conflicts=_merge_by_key(
                ledger.geopolitics.conflicts,
                mutation.add_conflicts,
                mutation.update_conflicts,
                "name",
            ),
        ),
        economics=EconomicsState(
            currencies=_append(
                ledger.economics.currencies, mutation.add_currencies
            ),
            trading_blocs=_append(
                ledger.economics.trading_blocs, mutation.add_trading_blocs
            ),
            scarcities=_append(
                ledger.economics.scarcities, mutation.add_scarcities
            ),
            global_gdp_trend=(
                mutation.update_global_gdp_trend
                if mutation.update_global_gdp_trend is not None
                else ledger.economics.global_gdp_trend
            ),
        ),
        technology=TechnologyState(
            ai=_merge_tech_domain(ledger.technology.ai, mutation.update_ai),
            energy=_merge_tech_domain(
                ledger.technology.energy, mutation.update_energy
            ),
            biotech=_merge_tech_domain(
                ledger.technology.biotech, mutation.update_biotech
            ),
            other=_append(ledger.technology.other, mutation.add_tech_domains),
        ),
        culture=CultureState(
            dominant_narratives=_append(
                ledger.culture.dominant_narratives,
                mutation.add_dominant_narratives,
            ),
            movements=_append(
                ledger.culture.movements, mutation.add_movements
            ),
            media_landscape=(
                mutation.update_media_landscape
                if mutation.update_media_landscape is not None
                else ledger.culture.media_landscape
            ),
        ),
        military=MilitaryState(
            forces=_merge_by_key(
                ledger.military.forces,
                mutation.add_forces,
                mutation.update_forces,
                "entity",
            ),
            arms_races=_append(
                ledger.military.arms_races, mutation.add_arms_races
            ),
            doctrine_shifts=_append(
                ledger.military.doctrine_shifts, mutation.add_doctrine_shifts
            ),
        ),
        environment=EnvironmentState(
            global_temperature_anomaly=(
                mutation.update_temperature_anomaly
                if mutation.update_temperature_anomaly is not None
                else ledger.environment.global_temperature_anomaly
            ),
            crises=_append(ledger.environment.crises, mutation.add_crises),
            mitigation_efforts=_append(
                ledger.environment.mitigation_efforts,
                mutation.add_mitigation_efforts,
            ),
        ),
        story_threads=_merge_by_key(
            ledger.story_threads,
            mutation.add_story_threads,
            mutation.update_story_threads,
            "name",
        ),
        history=_append(ledger.history, mutation.add_historical_events),
    )


def _append(existing: list, additions: list) -> list:
    if not additions:
        return list(existing)
    return [*existing, *additions]


def _merge_by_key(
    existing: list,
    additions: list,
    updates: list[dict[str, Any]],
    key: str,
) -> list:
    result = list(existing)

    if additions:
        result = [*result, *additions]

    if updates:
        for item in result:
            key_val = getattr(item, key)
            for update in updates:
                if update.get(key) == key_val:
                    for attr, val in update.items():
                        if attr != key:
                            setattr(item, attr, val)
                    break

    return result


def _merge_tech_domain(
    existing: TechDomain, update: dict[str, Any] | None
) -> TechDomain:
    if not update:
        return TechDomain(
            name=existing.name,
            maturity_level=existing.maturity_level,
            key_players=list(existing.key_players),
            description=existing.description,
        )
    return TechDomain(
        name=update.get("name", existing.name),
        maturity_level=update.get("maturity_level", existing.maturity_level),
        key_players=update.get("key_players", list(existing.key_players)),
        description=update.get("description", existing.description),
    )
