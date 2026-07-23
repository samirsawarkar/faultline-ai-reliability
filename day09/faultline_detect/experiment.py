"""The attack: sweep severity, score detector precision/recall against truth.

Two families, scored independently, plus two specificity checks that prove each
detector is blind to the OTHER family (a schema detector cannot see latency; a
duration detector cannot see corruption). Every number is a confusion matrix
against the Day-8 injection log — the mission's fail condition made concrete.

Scenario (fixed, deterministic): 12 calls, the fault fires on every 2nd call
(seqs 0,2,4,6,8,10), the other six are clean negatives. So precision, recall AND
true-negative rate are all well-defined at every severity.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .detectors import duration_detect, schema_detect
from .injectors import f1_corruption_spec, f2_latency_spec
from .latency import DEFAULT_BUDGET
from .runner import run
from .score import (
    Confusion,
    duration_positives,
    schema_positives,
    score,
    truth_is_f1,
    truth_is_f2,
)

SWEEP_SEVERITIES = [1, 2, 3, 4, 5]
FIRE_EVERY = "2"                 # fault fires on every 2nd call
DEFAULT_SEED = 20260719


def _f1_confusion(severity: int, seed: int, calls, mode: str) -> Confusion:
    spec = f1_corruption_spec("*", severity, mode=mode,
                              trigger="every_n", trigger_value=FIRE_EVERY, seed=seed)
    obs, truth, _ = run([spec], seed, calls)
    sigs = [schema_detect(o.seq, o.output) for o in obs]
    return score(schema_positives(sigs), truth, truth_is_f1)


def _f2_confusion(severity: int, seed: int, calls, budget: int) -> Confusion:
    spec = f2_latency_spec("*", severity, trigger="every_n",
                           trigger_value=FIRE_EVERY, seed=seed)
    obs, truth, _ = run([spec], seed, calls)
    sigs = [duration_detect(o.seq, o.duration, budget) for o in obs]
    return score(duration_positives(sigs), truth, truth_is_f2)


def sweep_f1(seed: int = DEFAULT_SEED, calls=None, mode: str = "corrupt",
             severities: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    out = []
    for s in (severities or SWEEP_SEVERITIES):
        out.append({"severity": s, **_f1_confusion(s, seed, calls, mode).to_dict()})
    return out


def sweep_f2(seed: int = DEFAULT_SEED, calls=None, budget: int = DEFAULT_BUDGET,
             severities: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    out = []
    for s in (severities or SWEEP_SEVERITIES):
        out.append({"severity": s, **_f2_confusion(s, seed, calls, budget).to_dict()})
    return out


def f2_budget_sensitivity(severity: int = 4, seed: int = DEFAULT_SEED, calls=None,
                          budgets: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    """Same latency fault, different budgets: detection is budget-gated."""
    budgets = budgets or [30, 45, 50, 60]
    out = []
    for b in budgets:
        c = _f2_confusion(severity, seed, calls, b)
        out.append({"budget": b, "severity": severity, **c.to_dict()})
    return out


def specificity(seed: int = DEFAULT_SEED, calls=None,
                budget: int = DEFAULT_BUDGET) -> Dict[str, Any]:
    """Cross-checks: each detector is scored against the OTHER family's truth.
    Both should score recall 0 — a detector catches only its own fault family."""
    # F2 latency run graded with the SCHEMA detector against F2 truth.
    f2_spec = f2_latency_spec("*", 5, trigger="every_n", trigger_value=FIRE_EVERY, seed=seed)
    obs2, truth2, _ = run([f2_spec], seed, calls)
    schema_pos = schema_positives(schema_detect(o.seq, o.output) for o in obs2)
    schema_vs_f2 = score(schema_pos, truth2, truth_is_f2)

    # F1 corruption run graded with the DURATION detector against F1 truth.
    f1_spec = f1_corruption_spec("*", 5, mode="corrupt",
                                 trigger="every_n", trigger_value=FIRE_EVERY, seed=seed)
    obs1, truth1, _ = run([f1_spec], seed, calls)
    dur_pos = duration_positives(duration_detect(o.seq, o.duration, budget) for o in obs1)
    dur_vs_f1 = score(dur_pos, truth1, truth_is_f1)

    return {
        "schema_detector_vs_latency_truth": schema_vs_f2.to_dict(),
        "duration_detector_vs_corruption_truth": dur_vs_f1.to_dict(),
        "each_detector_blind_to_other_family": (
            schema_vs_f2.recall in (0.0, None) and dur_vs_f1.recall in (0.0, None)),
    }


def build_report(seed: int = DEFAULT_SEED, budget: int = DEFAULT_BUDGET
                 ) -> Dict[str, Any]:
    f1 = sweep_f1(seed=seed)
    f2 = sweep_f2(seed=seed, budget=budget)
    spec = specificity(seed=seed, budget=budget)
    return {
        "seed": seed,
        "budget": budget,
        "scenario": {"calls": 12, "fires_on": "every 2nd call (seqs 0,2,4,6,8,10)",
                     "clean_negatives": 6},
        "scored_against": "day08 GroundTruthLog (injection truth), joined by seq",
        "f1_schema_sweep": f1,
        "f2_latency_sweep": f2,
        "f2_budget_sensitivity": f2_budget_sensitivity(seed=seed),
        "specificity": spec,
        "headline": {
            "f1_recall_at_severity_1": next(r["recall"] for r in f1 if r["severity"] == 1),
            "f1_recall_at_severity_2plus": next(r["recall"] for r in f1 if r["severity"] == 2),
            "f2_detected_from_severity": next(
                (r["severity"] for r in f2 if r["recall"] == 1.0), None),
            "f1_precision_min": min(r["precision"] for r in f1 if r["precision"] is not None),
        },
    }
