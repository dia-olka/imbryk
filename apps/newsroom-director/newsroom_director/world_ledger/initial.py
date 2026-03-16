"""Initial WorldLedger state — loaded from generated data.

DO NOT EDIT — edit data/world-state.json and run codegen instead.
"""

from ._generated_world_state import WORLD_STATE_DATA
from .serialise_dict import ledger_from_dict

INITIAL_WORLD_LEDGER = ledger_from_dict(WORLD_STATE_DATA)
