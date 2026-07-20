"""Scoring + the false-negative analysis — against injection truth and the oracle.

Detection is scored with Day 9's confusion machinery (`faultline_detect.score`):
predicted-positive = the classifier flagged the call (class != OK); truth-positive
= the injection log says an F3 (or F4) fault fired. So the numbers are joined to
the Day-8 `GroundTruthLog`, per seq, exactly as the fail condition demands.

The mission's real deliverable is the ESCAPE SET: calls that are genuinely wrong
(the oracle says so) yet classified OK. `escaped_false_negatives` returns those
with expected-vs-got evidence, so a schema-valid semantic corruption is recorded
as a *missed detection with proof*, never as a detection.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Set

_DAY9 = Path(__file__).resolve().parents[2] / "day9"
if str(_DAY9) not in sys.path:
    sys.path.insert(0, str(_DAY9))

from faultline_detect.score import Confusion, score  # noqa: E402 (reuse Day 9)

from . import oracle  # noqa: E402
from .detectors import classify, detected_faulty, invariant_detect  # noqa: E402
from .runner import Observation
from .spec import F3_LABEL_PREFIX, F4_LABEL_PREFIX


def truth_is_f3(e) -> bool:
    return e.fired and e.label.startswith(F3_LABEL_PREFIX)


def truth_is_f4(e) -> bool:
    return e.fired and e.label.startswith(F4_LABEL_PREFIX)


def classifier_positives(observations: List[Observation]) -> Set[int]:
    return {o.seq for o in observations if detected_faulty(classify(o.raised, o.output))}


def score_detection(observations: List[Observation], truth, family: str) -> Confusion:
    """Confusion of classifier-flagged vs injected, for family 'F3' or 'F4'."""
    predicate = truth_is_f4 if family == "F4" else truth_is_f3
    return score(classifier_positives(observations), truth, predicate)


def escaped_false_negatives(observations: List[Observation], truth
                            ) -> List[Dict[str, Any]]:
    """Calls that are actually wrong (oracle) but classified OK — with evidence.

    This is the committed proof that schema-valid semantic corruption is MISSED,
    not detected. Each row shows the injected kind, the classifier's OK verdict,
    and the oracle's expected-vs-got diff."""
    rows: List[Dict[str, Any]] = []
    for o in observations:
        e = truth.entries[o.seq]
        cls = classify(o.raised, o.output)
        wrong = not o.raised and not oracle.is_correct(o.component, o.payload, o.output)
        if wrong and cls == "ok":
            rows.append({
                "seq": o.seq,
                "component": o.component,
                "injected_kind": e.mode,
                "injected_label": e.label,
                "classifier_class": cls,          # "ok" — the miss
                "schema_valid": True,             # OK implies schema valid
                "invariant_ok": invariant_detect(o.output).ok,
                "oracle_verdict": "wrong",
                "diff": oracle.diff(o.component, o.payload, o.output),
            })
    return rows


def per_kind_detection(observations: List[Observation], truth) -> Dict[str, Any]:
    """For each injected kind: how many fired, how many the classifier caught,
    how many escaped (classified OK), and the detection rate."""
    by_kind: Dict[str, Dict[str, int]] = {}
    for o in observations:
        e = truth.entries[o.seq]
        if not e.fired:
            continue
        kind = e.mode
        cls = classify(o.raised, o.output)
        b = by_kind.setdefault(kind, {"fired": 0, "detected": 0, "escaped": 0})
        b["fired"] += 1
        if detected_faulty(cls):
            b["detected"] += 1
        else:
            b["escaped"] += 1
    for kind, b in by_kind.items():
        b["detection_rate"] = round(b["detected"] / b["fired"], 6) if b["fired"] else None
    return by_kind
