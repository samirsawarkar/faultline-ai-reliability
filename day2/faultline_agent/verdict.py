"""Semantic-correctness judge for an ArchiveSumTask outcome.

This is the Day-2 analogue of Day 1's oracle, and it is deliberately SEPARATE
from Pydantic validation. Pydantic answers "is this outcome well-formed?"
(schema validity). This function answers "is this outcome right?" (semantic
correctness). An outcome can pass the first and fail the second — that gap is
the whole subject of LEARN.md.

Mirroring Day 1's stance, a task passes only when it is BOTH:
  1. correct  -> the numeric answer equals the true sum, and
  2. grounded -> every required fact document was cited.
"""
from __future__ import annotations

from typing import Any, Dict, Set, Tuple

from .contracts import AgentOutcome, ArchiveSumTask, OutcomeStatus


def ground_truth(env: Dict[str, Any], task: ArchiveSumTask) -> Tuple[int, Set[str]]:
    """The independently computed correct sum and the required source doc ids."""
    by_name = {e_doc["title"]: e_doc for e_doc in env["documents"]}
    facts_by_name = _facts_by_name(env)
    total = 0
    required: Set[str] = set()
    for name in task.entities:
        if name not in facts_by_name:
            raise KeyError(f"entity not in environment: {name!r}")
        token = facts_by_name[name]["archival_reference"]  # e.g. "Rune-4016"
        total += int(token.split("-")[1])
        required.add(by_name[name]["id"])
    return total, required


def verdict(env: Dict[str, Any], task: ArchiveSumTask, outcome: AgentOutcome) -> Dict[str, Any]:
    truth_total, required = ground_truth(env, task)
    if outcome.status is not OutcomeStatus.SOLVED:
        return {
            "task_id": task.task_id,
            "passed": False,
            "correct": False,
            "grounded": False,
            "status": outcome.status.value,
            "expected_answer": str(truth_total),
            "reason": f"outcome status is {outcome.status.value}",
        }
    correct = outcome.answer == str(truth_total)
    grounded = required.issubset(set(outcome.cited_sources))
    return {
        "task_id": task.task_id,
        "passed": correct and grounded,
        "correct": correct,
        "grounded": grounded,
        "status": outcome.status.value,
        "expected_answer": str(truth_total),
        "got_answer": outcome.answer,
        "required_sources": sorted(required),
        "cited_sources": list(outcome.cited_sources),
    }


def _facts_by_name(env: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """Reconstruct each entity's facts by parsing its own fact document.

    We parse rather than reach into an internal structure so the judge depends
    only on the public, serialized environment — the same bytes the oracle sees.
    """
    import re

    fact_re = re.compile(r"The (?P<label>[a-z ]+) of (?P<ent>.+?) is (?P<val>\S+?)\.")
    out: Dict[str, Dict[str, str]] = {}
    for d in env["documents"]:
        for m in fact_re.finditer(d["text"]):
            ent = m.group("ent")
            key = m.group("label").strip().replace(" ", "_")
            out.setdefault(ent, {})[key] = m.group("val")
    return out
