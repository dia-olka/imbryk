"""Convert WorldLedger dataclasses to/from plain dicts for JSON storage."""

from __future__ import annotations

from dataclasses import asdict

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


def ledger_to_dict(ledger: WorldLedger) -> dict:
    """Serialize a WorldLedger dataclass to a plain dict (snake_case)."""
    return asdict(ledger)


def _snake_to_camel(key: str) -> str:
    head, *tail = key.split("_")
    return head + "".join(part.title() for part in tail)


def _camelize(value):
    if isinstance(value, dict):
        return {_snake_to_camel(k): _camelize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_camelize(item) for item in value]
    return value


def ledger_to_camel_dict(ledger: WorldLedger) -> dict:
    """Serialize a WorldLedger as camelCase — the shape the TS WorldLedgerSchema
    expects. Used when mirroring to R2 so the gazette build can validate and
    consume the live ledger instead of silently falling back to the initial lore.
    """
    return _camelize(asdict(ledger))


def ledger_from_dict(data: dict) -> WorldLedger:
    """Deserialize a plain dict into a WorldLedger dataclass."""
    geo = data.get("geopolitics", {})
    econ = data.get("economics", {})
    tech = data.get("technology", {})
    cult = data.get("culture", {})
    mil = data.get("military", {})
    env = data.get("environment", {})

    return WorldLedger(
        epoch=data.get("epoch", ""),
        synopsis=data.get("synopsis", ""),
        geopolitics=GeopoliticsState(
            nations=[Nation(**n) for n in geo.get("nations", [])],
            alliances=[Alliance(**a) for a in geo.get("alliances", [])],
            conflicts=[Conflict(**c) for c in geo.get("conflicts", [])],
        ),
        economics=EconomicsState(
            currencies=[Currency(**c) for c in econ.get("currencies", [])],
            trading_blocs=[
                TradingBloc(**t) for t in econ.get("trading_blocs", [])
            ],
            scarcities=[Scarcity(**s) for s in econ.get("scarcities", [])],
            global_gdp_trend=econ.get("global_gdp_trend", ""),
        ),
        technology=TechnologyState(
            ai=_tech_domain(tech.get("ai", {}), "Artificial Intelligence"),
            energy=_tech_domain(tech.get("energy", {}), "Energy"),
            biotech=_tech_domain(tech.get("biotech", {}), "Biotechnology"),
            other=[TechDomain(**t) for t in tech.get("other", [])],
        ),
        culture=CultureState(
            dominant_narratives=cult.get("dominant_narratives", []),
            movements=[
                CulturalMovement(**m) for m in cult.get("movements", [])
            ],
            media_landscape=cult.get("media_landscape", ""),
        ),
        military=MilitaryState(
            forces=[MilitaryForce(**f) for f in mil.get("forces", [])],
            arms_races=mil.get("arms_races", []),
            doctrine_shifts=mil.get("doctrine_shifts", []),
        ),
        environment=EnvironmentState(
            global_temperature_anomaly=env.get(
                "global_temperature_anomaly", 0.0
            ),
            crises=[
                EnvironmentalCrisis(**c) for c in env.get("crises", [])
            ],
            mitigation_efforts=env.get("mitigation_efforts", []),
        ),
        story_threads=[
            StoryThread(**t) for t in data.get("story_threads", [])
        ],
        history=[
            HistoricalEvent(**e) for e in data.get("history", [])
        ],
    )


def _tech_domain(data: dict, default_name: str) -> TechDomain:
    if not data:
        return TechDomain(
            name=default_name,
            maturity_level="emerging",
            key_players=[],
            description="",
        )
    return TechDomain(
        name=data.get("name", default_name),
        maturity_level=data.get("maturity_level", "emerging"),
        key_players=data.get("key_players", []),
        description=data.get("description", ""),
    )
