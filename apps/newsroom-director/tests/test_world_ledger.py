"""Tests for WorldLedger types, serialiser, and mutator."""

from newsroom_director.world_ledger import (
    INITIAL_WORLD_LEDGER,
    LedgerMutation,
    apply_mutation,
    serialize_ledger_to_synopsis,
)
from newsroom_director.world_ledger.serialise_dict import (
    ledger_from_dict,
    ledger_to_camel_dict,
    ledger_to_dict,
)
from newsroom_director.world_ledger.types import (
    Conflict,
    CulturalMovement,
    HistoricalEvent,
    Nation,
    StoryThread,
    WorldLedger,
)


class TestSerializer:
    def test_produces_epoch_header(self):
        text = serialize_ledger_to_synopsis(INITIAL_WORLD_LEDGER)
        # epoch may change over time; just make sure the header matches the
        # ledger value rather than hard-coding a string.
        assert f"EPOCH: {INITIAL_WORLD_LEDGER.epoch}" in text

    def test_contains_section_headers(self):
        text = serialize_ledger_to_synopsis(INITIAL_WORLD_LEDGER)
        assert "--- GEOPOLITICS ---" in text
        assert "--- ECONOMICS ---" in text
        assert "--- TECHNOLOGY ---" in text
        assert "--- CULTURE ---" in text
        assert "--- MILITARY ---" in text
        assert "--- ENVIRONMENT ---" in text
        assert "--- STORY THREADS ---" in text
        assert "--- RECENT HISTORY ---" in text

    def test_contains_nation_data(self):
        text = serialize_ledger_to_synopsis(INITIAL_WORLD_LEDGER)
        # pick a real nation from the initial ledger; the list is long but the
        # first entry should be stable.
        first_name = INITIAL_WORLD_LEDGER.geopolitics.nations[0].name
        assert first_name in text
        # also check that stability score appears somewhere
        assert "stability" in text

    def test_contains_conflict_data(self):
        text = serialize_ledger_to_synopsis(INITIAL_WORLD_LEDGER)
        # just make sure at least one conflict name is rendered
        if INITIAL_WORLD_LEDGER.geopolitics.conflicts:
            name = INITIAL_WORLD_LEDGER.geopolitics.conflicts[0].name
            assert name in text

    def test_contains_currency_data(self):
        text = serialize_ledger_to_synopsis(INITIAL_WORLD_LEDGER)
        # assert at least one currency string shows up
        if INITIAL_WORLD_LEDGER.economics.currencies:
            assert INITIAL_WORLD_LEDGER.economics.currencies[0].name in text

    def test_contains_temperature(self):
        text = serialize_ledger_to_synopsis(INITIAL_WORLD_LEDGER)
        # temperature anomaly is a float; ensure its string form appears
        temp = INITIAL_WORLD_LEDGER.environment.global_temperature_anomaly
        assert str(temp) in text

    def test_contains_history(self):
        text = serialize_ledger_to_synopsis(INITIAL_WORLD_LEDGER)
        # there should be at least one historical event rendered
        if INITIAL_WORLD_LEDGER.history:
            assert INITIAL_WORLD_LEDGER.history[0].headline in text

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
        assert len(result.geopolitics.nations) == len(
            INITIAL_WORLD_LEDGER.geopolitics.nations
        ) + 1

    def test_update_nation(self):
        # pick a nation that exists in the ledger so the update actually takes
        # effect.  using the first entry keeps the test data-agnostic.
        existing = INITIAL_WORLD_LEDGER.geopolitics.nations[0].name
        mutation = LedgerMutation(
            update_nations=[{"name": existing, "stability": 50}]
        )
        result = apply_mutation(INITIAL_WORLD_LEDGER, mutation)
        ar = next(n for n in result.geopolitics.nations if n.name == existing)
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
        assert len(result.history) == len(INITIAL_WORLD_LEDGER.history) + 1
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

    def test_add_story_thread(self):
        mutation = LedgerMutation(
            add_story_threads=[
                StoryThread(
                    name="Test Thread",
                    status="developing",
                    started="2026-03-16",
                    last_covered="2026-03-16",
                    summary="A test story thread.",
                    related_nations=["United States"],
                    sectors=["geopolitics"],
                )
            ]
        )
        result = apply_mutation(INITIAL_WORLD_LEDGER, mutation)
        names = [t.name for t in result.story_threads]
        assert "Test Thread" in names
        assert len(result.story_threads) == len(
            INITIAL_WORLD_LEDGER.story_threads
        ) + 1

    def test_update_story_thread(self):
        existing = INITIAL_WORLD_LEDGER.story_threads[0].name
        mutation = LedgerMutation(
            update_story_threads=[
                {"name": existing, "status": "resolved", "summary": "Updated."}
            ]
        )
        result = apply_mutation(INITIAL_WORLD_LEDGER, mutation)
        updated = next(t for t in result.story_threads if t.name == existing)
        assert updated.status == "resolved"
        assert updated.summary == "Updated."

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
        assert len(restored.geopolitics.nations) == len(
            INITIAL_WORLD_LEDGER.geopolitics.nations
        )
        if restored.geopolitics.nations:
            assert restored.geopolitics.nations[0].name == INITIAL_WORLD_LEDGER.geopolitics.nations[0].name
        assert len(restored.history) == len(INITIAL_WORLD_LEDGER.history)
        assert len(restored.story_threads) == len(INITIAL_WORLD_LEDGER.story_threads)
        if restored.story_threads:
            assert restored.story_threads[0].name == INITIAL_WORLD_LEDGER.story_threads[0].name

    def test_serialise_roundtrip_text(self):
        """Serialise → dict → deserialise → serialise produces same text."""
        text1 = serialize_ledger_to_synopsis(INITIAL_WORLD_LEDGER)
        d = ledger_to_dict(INITIAL_WORLD_LEDGER)
        restored = ledger_from_dict(d)
        text2 = serialize_ledger_to_synopsis(restored)
        assert text1 == text2


class TestLedgerToCamelDict:
    """The gazette validates the R2-mirrored ledger with a camelCase Zod
    schema; a silent fallback to INITIAL_WORLD_LEDGER broke the timeline
    for weeks. These tests lock in the key-casing contract."""

    def test_top_level_keys_are_camel_case(self):
        d = ledger_to_camel_dict(INITIAL_WORLD_LEDGER)
        assert "storyThreads" in d
        assert "story_threads" not in d

    def test_nested_keys_are_camel_case(self):
        d = ledger_to_camel_dict(INITIAL_WORLD_LEDGER)
        if d["geopolitics"]["nations"]:
            nation = d["geopolitics"]["nations"][0]
            assert "governmentType" in nation
            assert "government_type" not in nation
        assert "globalTemperatureAnomaly" in d["environment"]
        assert "globalGdpTrend" in d["economics"]
        assert "tradingBlocs" in d["economics"]
        assert "dominantNarratives" in d["culture"]
        assert "mediaLandscape" in d["culture"]
        assert "armsRaces" in d["military"]
        assert "doctrineShifts" in d["military"]
        assert "mitigationEfforts" in d["environment"]
        assert "maturityLevel" in d["technology"]["ai"]
        assert "keyPlayers" in d["technology"]["ai"]

    def test_values_preserved(self):
        d = ledger_to_camel_dict(INITIAL_WORLD_LEDGER)
        assert d["epoch"] == INITIAL_WORLD_LEDGER.epoch
        assert len(d["history"]) == len(INITIAL_WORLD_LEDGER.history)
        assert len(d["storyThreads"]) == len(
            INITIAL_WORLD_LEDGER.story_threads
        )
