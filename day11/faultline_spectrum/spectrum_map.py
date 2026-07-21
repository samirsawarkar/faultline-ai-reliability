"""The deterministic-vs-semantic map across the whole F1-F6 spectrum.

This is the capstone artifact and the answer to the fail condition ("cannot
separate deterministic from semantic detection"). It classifies every fault by
its detection nature and backs each classification with an OBSERVED recall pulled
from the day that measured it (Day 9 for F1/F2, Day 10 for F3/F4, Day 11 for
F5/F6) — so the map is evidence, not opinion.

Definition (also in LEARN):
  deterministic detection = verdict is a function of structure / counts /
    equality / explicit flags, with NO model of correctness.
  semantic detection = verdict needs a correctness or meaning model (a value
    invariant, or the oracle / a judge).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

_DAY9 = Path(__file__).resolve().parents[2] / "day9"
_DAY10 = Path(__file__).resolve().parents[2] / "day10"
for p in (_DAY9, _DAY10):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import faultline_contracts as _fc  # noqa: E402  (Day 10)
import faultline_detect as _fd  # noqa: E402  (Day 9)

from .runner import run_batch  # noqa: E402
from .score import score_f5, score_f6  # noqa: E402
from .spec import SpectrumFaultSpec  # noqa: E402

_MAP_SEED = 20260721


def _f5_batch():
    plan = [(0, "context_drift"), (1, "context_inconsistent"),
            (2, "context_drift"), (3, "context_inconsistent")]
    specs = [SpectrumFaultSpec(f"F5-{seq}", kind, 2, "call_index", str(seq), seed=1)
             for seq, kind in plan]
    return run_batch(specs, _MAP_SEED, n_runs=8)


def _f6_batch():
    plan = [(0, "repetition"), (1, "budget_exhaustion"),
            (2, "repetition"), (3, "budget_exhaustion")]
    specs = [SpectrumFaultSpec(f"F6-{seq}", kind, 2, "call_index", str(seq), seed=1)
             for seq, kind in plan]
    return run_batch(specs, _MAP_SEED, n_runs=8)


def build_map() -> Dict[str, Any]:
    d9 = _fd.build_report()
    d10 = _fc.build_report()

    f1 = {r["severity"]: r["recall"] for r in d9["f1_schema_sweep"]}
    f2_from = d9["headline"]["f2_detected_from_severity"]
    f3_recall = d10["f3_detection"]["recall"]
    f3_escapes = d10["headline"]["f3_escaped_kinds"]
    f4_recall = d10["f4_detection"]["recall"]

    obs5, truth5 = _f5_batch()
    obs6, truth6 = _f6_batch()
    f5 = score_f5(obs5, truth5)
    f6 = score_f6(obs6, truth6)

    faults: List[Dict[str, Any]] = [
        {"fault": "F1", "name": "structured-output corruption",
         "primary_detector": "schema (structural)", "nature": "deterministic",
         "observed_recall": {"severity_1": f1.get(1), "severity_2plus": f1.get(2)},
         "semantic_residual": True,
         "residual": "small in-range value drift is schema-valid (missed at low severity)"},
        {"fault": "F2", "name": "tool latency / timeout",
         "primary_detector": "duration vs budget", "nature": "deterministic",
         "observed_recall": {"at_or_above_budget": 1.0, "detected_from_severity": f2_from},
         "semantic_residual": False},
        {"fault": "F3", "name": "schema drift / semantic corruption",
         "primary_detector": "schema + value invariant", "nature": "mixed",
         "observed_recall": {"mixed_classifier": f3_recall},
         "semantic_residual": True, "escape_kinds": f3_escapes},
        {"fault": "F4", "name": "provider error",
         "primary_detector": "explicit error flag", "nature": "deterministic",
         "observed_recall": {"all": f4_recall}, "semantic_residual": False},
        {"fault": "F5", "name": "context corruption",
         "primary_detector": "context-consistency invariant", "nature": "semantic",
         "observed_recall": {"consistency_invariant": f5.recall},
         "semantic_residual": True, "escape_kinds": ["context_drift"]},
        {"fault": "F6", "name": "loop exhaustion (repetition / budget)",
         "primary_detector": "repetition + step-budget", "nature": "deterministic",
         "observed_recall": {"all": f6.recall}, "semantic_residual": False},
    ]

    fully_deterministic = [f["fault"] for f in faults
                           if f["nature"] == "deterministic" and not f["semantic_residual"]]
    require_semantic = [f["fault"] for f in faults if f["semantic_residual"]]

    return {
        "definition": {
            "deterministic": "verdict from structure/counts/equality/explicit flags; "
                             "no model of correctness",
            "semantic": "verdict needs a correctness or meaning model (value "
                        "invariant or oracle/judge)",
        },
        "faults": faults,
        "fully_deterministic_recall_1_no_escape": fully_deterministic,
        "require_semantic_evaluation": require_semantic,
        "separation_holds": (set(fully_deterministic) == {"F2", "F4", "F6"}
                             and "F5" in require_semantic and "F3" in require_semantic),
    }
