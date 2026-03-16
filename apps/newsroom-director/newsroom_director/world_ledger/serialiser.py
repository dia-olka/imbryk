"""Serialize a WorldLedger to a human-readable synopsis text.

Python port of world-ledger.serialiser.ts — produces the same text format.
"""

from __future__ import annotations

from .types import WorldLedger


def serialize_ledger_to_synopsis(ledger: WorldLedger) -> str:
    sections: list[str] = []

    sections.append(f"EPOCH: {ledger.epoch}")
    if ledger.synopsis:
        sections.append(ledger.synopsis)

    sections.append(_serialize_geopolitics(ledger))
    sections.append(_serialize_economics(ledger))
    sections.append(_serialize_technology(ledger))
    sections.append(_serialize_culture(ledger))
    sections.append(_serialize_military(ledger))
    sections.append(_serialize_environment(ledger))
    sections.append(_serialize_story_threads(ledger))
    sections.append(_serialize_history(ledger))

    return "\n\n".join(s for s in sections if s)


def _serialize_geopolitics(ledger: WorldLedger) -> str:
    geo = ledger.geopolitics
    lines: list[str] = ["--- GEOPOLITICS ---"]

    if geo.nations:
        lines.append("Nations:")
        for n in geo.nations:
            lines.append(
                f"- {n.name} ({n.government_type}, leader: {n.leader}, "
                f"stability: {n.stability}/100): {n.description}"
            )

    if geo.alliances:
        lines.append("Alliances:")
        for a in geo.alliances:
            members = ", ".join(a.members)
            lines.append(f"- {a.name} [{members}]: {a.purpose}")

    if geo.conflicts:
        lines.append("Conflicts:")
        for c in geo.conflicts:
            parties = " vs ".join(c.parties)
            lines.append(
                f"- {c.name} ({c.status}) [{parties}]: {c.description}"
            )

    return "\n".join(lines)


def _serialize_economics(ledger: WorldLedger) -> str:
    econ = ledger.economics
    lines: list[str] = ["--- ECONOMICS ---"]

    if econ.currencies:
        lines.append("Currencies:")
        for c in econ.currencies:
            lines.append(
                f"- {c.name} (issuer: {c.issuing_entity}, "
                f"strength: {c.strength}/100): {c.description}"
            )

    if econ.trading_blocs:
        lines.append("Trading Blocs:")
        for t in econ.trading_blocs:
            members = ", ".join(t.members)
            lines.append(f"- {t.name} [{members}]: {t.focus}")

    if econ.scarcities:
        lines.append("Scarcities:")
        for s in econ.scarcities:
            regions = ", ".join(s.affected_regions)
            lines.append(
                f"- {s.resource} ({s.severity}, regions: {regions}): "
                f"{s.description}"
            )

    if econ.global_gdp_trend:
        lines.append(f"GDP Trend: {econ.global_gdp_trend}")

    return "\n".join(lines)


def _serialize_technology(ledger: WorldLedger) -> str:
    tech = ledger.technology
    lines: list[str] = ["--- TECHNOLOGY ---"]

    for domain in [tech.ai, tech.energy, tech.biotech, *tech.other]:
        lines.append(
            f"{domain.name} ({domain.maturity_level}): {domain.description}"
        )
        if domain.key_players:
            players = "; ".join(domain.key_players)
            lines.append(f"  Key players: {players}")

    return "\n".join(lines)


def _serialize_culture(ledger: WorldLedger) -> str:
    culture = ledger.culture
    lines: list[str] = ["--- CULTURE ---"]

    if culture.dominant_narratives:
        lines.append("Dominant Narratives:")
        for n in culture.dominant_narratives:
            lines.append(f"- {n}")

    if culture.movements:
        lines.append("Movements:")
        for m in culture.movements:
            lines.append(f"- {m.name} ({m.reach}): {m.description}")

    if culture.media_landscape:
        lines.append(f"Media Landscape: {culture.media_landscape}")

    return "\n".join(lines)


def _serialize_military(ledger: WorldLedger) -> str:
    mil = ledger.military
    lines: list[str] = ["--- MILITARY ---"]

    if mil.forces:
        lines.append("Forces:")
        for f in mil.forces:
            nuclear = ", nuclear-capable" if f.nuclear_capable else ""
            caps = ", ".join(f.special_capabilities)
            lines.append(
                f"- {f.entity} (strength: "
                f"{f.conventional_strength}/100{nuclear}): {caps}"
            )

    if mil.arms_races:
        lines.append("Arms Races:")
        for r in mil.arms_races:
            lines.append(f"- {r}")

    if mil.doctrine_shifts:
        lines.append("Doctrine Shifts:")
        for d in mil.doctrine_shifts:
            lines.append(f"- {d}")

    return "\n".join(lines)


def _serialize_environment(ledger: WorldLedger) -> str:
    env = ledger.environment
    lines: list[str] = ["--- ENVIRONMENT ---"]

    lines.append(
        f"Global Temperature Anomaly: +{env.global_temperature_anomaly}\u00b0C"
    )

    if env.crises:
        lines.append("Crises:")
        for c in env.crises:
            regions = ", ".join(c.affected_regions)
            lines.append(
                f"- {c.name} ({c.severity}, regions: {regions}): "
                f"{c.description}"
            )

    if env.mitigation_efforts:
        lines.append("Mitigation Efforts:")
        for e in env.mitigation_efforts:
            lines.append(f"- {e}")

    return "\n".join(lines)


def _serialize_story_threads(ledger: WorldLedger) -> str:
    threads = [t for t in ledger.story_threads if t.status != "resolved"]
    if not threads:
        return ""

    lines: list[str] = ["--- STORY THREADS ---"]
    for t in threads:
        nations = (
            f" [{', '.join(t.related_nations)}]" if t.related_nations else ""
        )
        lines.append(
            f"- {t.name} ({t.status}, since {t.started}){nations}: "
            f"{t.summary}"
        )

    return "\n".join(lines)


def _serialize_history(ledger: WorldLedger) -> str:
    events = ledger.history[-10:]
    if not events:
        return ""

    lines: list[str] = ["--- RECENT HISTORY ---"]
    for e in events:
        lines.append(
            f"[{e.date}] {e.headline}: {e.description} "
            f"(Impact: {e.impact})"
        )

    return "\n".join(lines)
