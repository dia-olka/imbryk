"""World coherence validation — filter prompts against current world state."""

from __future__ import annotations

import json
import logging

from .db import PromptRecord
from .generation import GenerationStrategy

logger = logging.getLogger(__name__)

# Maximum prompts per validation call to stay within context limits.
BATCH_SIZE = 50

_VALIDATION_SYSTEM_PROMPT = """\
You are a world-coherence validator for a fictional newspaper simulation.

You will be given:
1. A synopsis of the current world state.
2. A batch of user-submitted prompts, each identified by an ID.

Your job: determine which prompts are coherent with the current world state.
A prompt is coherent if the people, nations, events, or concepts it references
either exist in the world state or are plausible extensions of it.  Reject
prompts that reference real-world entities not present in the fiction, or that
contradict established facts in the world state.

Respond with ONLY a JSON object: {"accepted": ["id1", "id2", ...]}
Include only the IDs of prompts that pass validation."""


def validate_prompts(
    prompts: list[PromptRecord],
    synopsis: str,
    generation_strategy: GenerationStrategy,
) -> list[PromptRecord]:
    """Filter *prompts* to those coherent with the current world state.

    Sends batches of prompts + the world synopsis to a Pro-tier model and
    keeps only the prompts the model marks as accepted.
    """
    if not prompts:
        return []

    accepted_ids: set[str] = set()

    for batch_start in range(0, len(prompts), BATCH_SIZE):
        batch = prompts[batch_start : batch_start + BATCH_SIZE]
        prompt_list = "\n".join(
            f"- [{pr.prompt_id}] {pr.text}" for pr in batch
        )

        user_prompt = (
            f"WORLD STATE SYNOPSIS:\n{synopsis}\n\n"
            f"PROMPTS TO VALIDATE:\n{prompt_list}"
        )

        system_prompt = _VALIDATION_SYSTEM_PROMPT
        response = generation_strategy.generate(
            system_prompt + "\n\n" + user_prompt, "pro"
        )

        batch_accepted = _parse_validation_response(
            response, {pr.prompt_id for pr in batch}
        )
        accepted_ids.update(batch_accepted)

        rejected = [pr for pr in batch if pr.prompt_id not in batch_accepted]
        if rejected:
            logger.info(
                "Prompts rejected by coherence validation",
                extra={
                    "step": "validation",
                    "rejected_count": len(rejected),
                    "rejected_ids": [pr.prompt_id for pr in rejected],
                },
            )

    result = [pr for pr in prompts if pr.prompt_id in accepted_ids]
    logger.info(
        "Coherence validation complete",
        extra={
            "step": "validation",
            "total": len(prompts),
            "accepted": len(result),
            "rejected": len(prompts) - len(result),
        },
    )
    return result


def _parse_validation_response(
    response: str, valid_ids: set[str]
) -> set[str]:
    """Extract accepted prompt IDs from the LLM response.

    Falls back to accepting all prompts if parsing fails — we prefer
    false positives over silently dropping user prompts.
    """
    try:
        text = response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)

        data = json.loads(text)
        accepted = set(data.get("accepted", []))
        # Only return IDs that are actually in the batch
        return accepted & valid_ids
    except (json.JSONDecodeError, TypeError, AttributeError):
        logger.warning(
            "Failed to parse validation response, accepting all prompts"
        )
        return valid_ids
