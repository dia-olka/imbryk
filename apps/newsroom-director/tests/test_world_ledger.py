"""Tests for WorldLedger types, serialiser, and mutator."""

from newsroom_director.world_ledger import (
    INITIAL_WORLD_LEDGER,
    LedgerMutation,
    apply_mutation,
    serialize_ledger_to_synopsis,
)
from newsroom_director.world_ledger.serialise_dict import (
    ledger_from_dict,
    ledger_to_dict,
)
from newsroom_director.world_ledger.types import (
    Conflict,
    CulturalMovement,
    HistoricalEvent,
    Nation,
    WorldLedger,
)


class TestSerializer:
    def test_produces_epoch_header(self):
        text = serialize_ledger_to_synopsis(INITIAL_WORLD_LEDGER)
        assert "EPOCH: Year Zero" in text

    def test_contains_section_headers(self):
        text = serialize_ledger_to_synopsis(INITIAL_WORLD_LEDGER)
        assert "--- GEOPOLITICS ---" in text
        assert "--- ECONOMICS ---" in text
        assert "--- TECHNOLOGY ---" in text
        assert "--- CULTURE ---" in text
        assert "--- MILITARY ---" in text
        assert "--- ENVIRONMENT ---" in text
        assert "--- RECENT HISTORY ---" in text

    def test_contains_nation_data(self):
        text = serialize_ledger_to_synopsis(INITIAL_WORLD_LEDGER)
        assert "Atlantic Republic" in text
        assert "President Elena Marsh" in text
        assert "stability: 72/100" in text

    def test_contains_conflict_data(self):
        text = serialize_ledger_to_synopsis(INITIAL_WORLD_LEDGER)
        assert "Caspian Basin Standoff" in text
        assert "(frozen)" in text

    def test_contains_currency_data(self):
        text = serialize_ledger_to_synopsis(INITIAL_WORLD_LEDGER)
        assert "Atlantic Dollar" in text
        assert "Meridian" in text

    def test_contains_temperature(self):
        text = serialize_ledger_to_synopsis(INITIAL_WORLD_LEDGER)
        assert "+1.8" in text

    def test_contains_history(self):
        text = serialize_ledger_to_synopsis(INITIAL_WORLD_LEDGER)
        assert "Fracture Accords signed" in text

    def test_empty_ledger(self):
        text = serialize_ledger_to_synopsis(WorldLedger())
        assert "EPOCH:" in text
        assert "--- GEOPOLITICS ---" in text


class TestMutator:
    def test_add_nation(self):
        mutation = LedgerMutation(
            add_nations=[
                Nation(
                    name="New Nation",
                    government_type="Democracy",
                    leader="Leader X",
                    stability=60,
                    description="A new nation",
                )
            ]
        )
        result = apply_mutation(INITIAL_WORLD_LEDGER, mutation)
        names = [n.name for n in result.geopolitics.nations]
        assert "New Nation" in names
        assert len(result.geopolitics.nations) == 7

    def test_update_nation(self):
        mutation = LedgerMutation(
            update_nations=[{"name": "Atlantic Republic", "stability": 50}]
        )
        result = apply_mutation(INITIAL_WORLD_LEDGER, mutation)
        ar = next(
            n for n in result.geopolitics.nations
            if n.name == "Atlantic Republic"
        )
        assert ar.stability == 50

    def test_update_synopsis(self):
        mutation = LedgerMutation(synopsis="New synopsis")
        result = apply_mutation(INITIAL_WORLD_LEDGER, mutation)
        assert result.synopsis == "New synopsis"

    def test_add_conflict(self):
        mutation = LedgerMutation(
            add_conflicts=[
                Conflict(
                    name="New Conflict",
                    parties=["A", "B"],
                    status="active",
                    description="A new conflict",
                )
            ]
        )
        result = apply_mutation(INITIAL_WORLD_LEDGER, mutation)
        names = [c.name for c in result.geopolitics.conflicts]
        assert "New Conflict" in names

    def test_add_historical_event(self):
        mutation = LedgerMutation(
            add_historical_events=[
                HistoricalEvent(
                    date="Year Zero, Day 2",
                    headline="Test Event",
                    description="Something happened",
                    impact="Big impact",
                    sectors=["geopolitics"],
                )
            ]
        )
        result = apply_mutation(INITIAL_WORLD_LEDGER, mutation)
        assert len(result.history) == 6
        assert result.history[-1].headline == "Test Event"

    def test_add_movement(self):
        mutation = LedgerMutation(
            add_movements=[
                CulturalMovement(
                    name="New Movement",
                    reach="global",
                    description="A new movement",
                )
            ]
        )
        result = apply_mutation(INITIAL_WORLD_LEDGER, mutation)
        names = [m.name for m in result.culture.movements]
        assert "New Movement" in names

    def test_update_temperature(self):
        mutation = LedgerMutation(update_temperature_anomaly=2.1)
        result = apply_mutation(INITIAL_WORLD_LEDGER, mutation)
        assert result.environment.global_temperature_anomaly == 2.1

    def test_empty_mutation_preserves_ledger(self):
        mutation = LedgerMutation()
        result = apply_mutation(INITIAL_WORLD_LEDGER, mutation)
        assert result.epoch == INITIAL_WORLD_LEDGER.epoch
        assert len(result.geopolitics.nations) == len(
            INITIAL_WORLD_LEDGER.geopolitics.nations
        )


class TestDictRoundTrip:
    def test_roundtrip(self):
        d = ledger_to_dict(INITIAL_WORLD_LEDGER)
        restored = ledger_from_dict(d)
        assert restored.epoch == INITIAL_WORLD_LEDGER.epoch
        assert len(restored.geopolitics.nations) == 6
        assert restored.geopolitics.nations[0].name == "Atlantic Republic"
        assert len(restored.history) == 5

    def test_serialise_roundtrip_text(self):
        """Serialise → dict → deserialise → serialise produces same text."""
        text1 = serialize_ledger_to_synopsis(INITIAL_WORLD_LEDGER)
        d = ledger_to_dict(INITIAL_WORLD_LEDGER)
        restored = ledger_from_dict(d)
        text2 = serialize_ledger_to_synopsis(restored)
        assert text1 == text2
