"""Contract tests — verify newsroom output_schemas stay in sync with the
shared contract files in data/contracts/.

The contract JSONs are the single source of truth for what the newsroom
LLM produces.  These tests fail if:
  - A required field is removed from NewspaperOutput / CuratorOutput
  - A field present in the contract is missing from the dataclasses
  - The contract sample fails is_valid_newspaper / is_valid_curator

The gazette side (loadEditions.spec.js) has matching tests that validate
the same contract files pass the Zod schemas used to consume the data.
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from newsroom_director.output_schemas import (
    ArticleOutput,
    CuratorOutput,
    InBriefOutput,
    NewspaperOutput,
    is_valid_curator,
    is_valid_newspaper,
)

CONTRACTS_DIR = Path(__file__).parents[3] / "data" / "contracts"


@pytest.fixture(scope="module")
def newspaper_contract() -> dict:
    return json.loads((CONTRACTS_DIR / "newspaper-output.json").read_text())


@pytest.fixture(scope="module")
def curator_contract() -> dict:
    return json.loads((CONTRACTS_DIR / "curator-output.json").read_text())


# ─── NewspaperOutput ─────────────────────────────────────────────────────────

class TestNewspaperContract:
    def test_contract_file_exists(self):
        assert (CONTRACTS_DIR / "newspaper-output.json").exists(), (
            "data/contracts/newspaper-output.json is missing"
        )

    def test_contract_passes_is_valid_newspaper(self, newspaper_contract):
        """The contract sample must satisfy the same validation gate used in
        the generation retry loop."""
        raw = json.dumps(newspaper_contract)
        assert is_valid_newspaper(raw), (
            "Contract sample failed is_valid_newspaper — check output_schemas.py"
        )

    def test_newspaper_output_fields_cover_contract(self, newspaper_contract):
        """Every top-level key in the contract must be a field on NewspaperOutput
        (excluding metadata-only keys like _comment)."""
        dataclass_fields = {f.name for f in dataclasses.fields(NewspaperOutput)}
        contract_keys = {k for k in newspaper_contract if not k.startswith("_")}
        missing = contract_keys - dataclass_fields
        assert not missing, (
            f"Contract keys not present in NewspaperOutput: {missing}. "
            "Add them to output_schemas.NewspaperOutput or remove from contract."
        )

    def test_article_output_fields_cover_contract(self, newspaper_contract):
        """Every key in a contract article must be a field on ArticleOutput."""
        dataclass_fields = {f.name for f in dataclasses.fields(ArticleOutput)}
        for article in newspaper_contract.get("articles", []):
            contract_keys = {k for k in article if not k.startswith("_")}
            missing = contract_keys - dataclass_fields
            assert not missing, (
                f"Article contract keys not in ArticleOutput: {missing}"
            )

    def test_in_brief_output_fields_cover_contract(self, newspaper_contract):
        """Every key in a contract in_brief item must be a field on InBriefOutput."""
        dataclass_fields = {f.name for f in dataclasses.fields(InBriefOutput)}
        for item in newspaper_contract.get("in_brief", []):
            contract_keys = {k for k in item if not k.startswith("_")}
            missing = contract_keys - dataclass_fields
            assert not missing, (
                f"in_brief contract keys not in InBriefOutput: {missing}"
            )

    def test_required_newspaper_fields_present_in_contract(self, newspaper_contract):
        """Required fields on NewspaperOutput must exist in the contract."""
        required = {
            f.name for f in dataclasses.fields(NewspaperOutput)
            if f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING  # type: ignore[misc]
        }
        contract_keys = set(newspaper_contract.keys())
        missing = required - contract_keys
        assert not missing, (
            f"Required NewspaperOutput fields missing from contract: {missing}. "
            "Update data/contracts/newspaper-output.json."
        )


# ─── CuratorOutput ───────────────────────────────────────────────────────────

class TestCuratorContract:
    def test_contract_file_exists(self):
        assert (CONTRACTS_DIR / "curator-output.json").exists(), (
            "data/contracts/curator-output.json is missing"
        )

    def test_contract_passes_is_valid_curator(self, curator_contract):
        """The contract sample must satisfy the curator validation gate."""
        raw = json.dumps(curator_contract)
        assert is_valid_curator(raw), (
            "Contract sample failed is_valid_curator — check output_schemas.py"
        )

    def test_curator_output_fields_cover_contract(self, curator_contract):
        """Every key in the curator contract must be a field on CuratorOutput."""
        dataclass_fields = {f.name for f in dataclasses.fields(CuratorOutput)}
        contract_keys = {k for k in curator_contract if not k.startswith("_")}
        missing = contract_keys - dataclass_fields
        assert not missing, (
            f"Curator contract keys not in CuratorOutput: {missing}"
        )

    def test_required_curator_fields_present_in_contract(self, curator_contract):
        """Required fields on CuratorOutput must exist in the contract."""
        required = {
            f.name for f in dataclasses.fields(CuratorOutput)
            if f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING  # type: ignore[misc]
        }
        missing = required - set(curator_contract.keys())
        assert not missing, (
            f"Required CuratorOutput fields missing from contract: {missing}. "
            "Update data/contracts/curator-output.json."
        )
