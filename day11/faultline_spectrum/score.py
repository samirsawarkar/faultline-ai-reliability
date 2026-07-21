"""Score F5/F6 detectors against injection truth + isolate the semantic escapes.

Reuses Day 9's confusion machinery. The point of the day is the SEPARATION:
  * F6 (deterministic detectors) close every injected loop fault — recall 1.0,
    no escape set.
  * F5 (semantic detector) catches only the incoherent corruption; the coherent
    `context_drift` escapes and must be isolated as requiring semantic evaluation
    (the oracle), which is exactly the Q2 split.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Set

_DAY9 = Path(__file__).resolve().parents[2] / "day9"
if str(_DAY9) not in sys.path:
    sys.path.insert(0, str(_DAY9))

from faultline_detect.score import Confusion, score  # noqa: E402

from . import task  # noqa: E402
from .detectors import context_integrity_detect, loop_detect
from .runner import RunObservation
from .spec import F5_LABEL_PREFIX, F6_LABEL_PREFIX


def truth_is_f5(e) -> bool:
    return e.fired and e.label.startswith(F5_LABEL_PREFIX)


def truth_is_f6(e) -> bool:
    return e.fired and e.label.startswith(F6_LABEL_PREFIX)


def f5_positives(obs: List[RunObservation]) -> Set[int]:
    return {o.seq for o in obs if context_integrity_detect(o.result).fired}


def f6_positives(obs: List[RunObservation]) -> Set[int]:
    return {o.seq for o in obs if loop_detect(o.result).fired}


def score_f5(obs: List[RunObservation], truth) -> Confusion:
    return score(f5_positives(obs), truth, truth_is_f5)


def score_f6(obs: List[RunObservation], truth) -> Confusion:
    return score(f6_positives(obs), truth, truth_is_f6)


def semantic_escapes(obs: List[RunObservation], truth) -> List[Dict[str, Any]]:
    """F5 runs that are wrong (oracle) yet pass the deterministic/consistency
    detectors — the faults that REQUIRE semantic evaluation. With evidence."""
    caught = f5_positives(obs)
    rows: List[Dict[str, Any]] = []
    for o in obs:
        e = truth.entries[o.seq]
        wrong = not task.is_correct(o.result)
        if truth_is_f5(e) and wrong and o.seq not in caught:
            rows.append({
                "seq": o.seq,
                "injected_kind": e.mode,
                "consistency_check": "passed",       # deterministic/consistency missed it
                "oracle_verdict": "wrong",
                "needs_semantic_eval": True,
                "expected_context": task.EXPECTED_CONTEXT,
                "got_context": o.result.context,
                "expected_final": task.EXPECTED_FINAL,
                "got_final": o.result.final,
            })
    return rows
