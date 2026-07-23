"""A grounded paired comparison: schema-only vs schema+invariant detection.

Two systems are compared on IDENTICAL seeded F3 samples (the paired design):
  System A — schema only: predict faulty iff the output fails the schema.
  System B — schema + invariant: predict faulty iff schema fails OR the value
             invariant fails (Day 10's classifier).

Because they see the same samples, the comparison is paired and McNemar applies.
The expected finding: B strictly dominates A on `nonmultiple` corruption (schema
valid but not a round ten), neither catches coherent `drift_value`, and both catch
`malformed_range` and pass `clean` — a real, defensible improvement with a p-value.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

_ROOT = Path(__file__).resolve().parents[2]
for rel in ("day08", "day09", "day10"):
    p = _ROOT / rel
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from faultline_contracts import ContractFaultSpec, classify, detected_faulty, run_contracts  # noqa: E402
from faultline_detect import validate_output  # noqa: E402

from .interpret import interpret_interval, interpret_mcnemar
from .intervals import wilson_interval
from .paired import mcnemar_from_pairs

_CATEGORIES = [("malformed_range", True), ("nonmultiple", True),
               ("drift_value", True), ("clean", False)]
_SEEDS = list(range(1, 21))


def _pair_outcomes():
    a_correct: List[bool] = []
    b_correct: List[bool] = []
    for seed in _SEEDS:
        idx = seed % 6                          # vary the sample so data has variety
        call = [{"component": "tool.retrieve", "step": "retrieve", "index": idx}]
        for kind, is_fault in _CATEGORIES:
            specs = ([ContractFaultSpec("S", "*", kind, 3, "call_index", "0", seed=seed)]
                     if is_fault else [])
            obs, _, _ = run_contracts(specs, seed, calls=call)
            o = obs[0]
            schema_faulty = len(validate_output(o.output)) > 0
            classify_faulty = detected_faulty(classify(o.raised, o.output))
            a_correct.append(schema_faulty == is_fault)
            b_correct.append(classify_faulty == is_fault)
    return a_correct, b_correct


def build_report() -> Dict[str, Any]:
    a, b = _pair_outcomes()
    n = len(a)
    ka, kb = sum(a), sum(b)
    ci_a = wilson_interval(ka, n)
    ci_b = wilson_interval(kb, n)
    mc = mcnemar_from_pairs(a, b)

    return {
        "design": "paired: System A (schema only) vs System B (schema+invariant) on "
                  "identical seeded F3 samples",
        "n_paired_samples": n,
        "system_a": {"name": "schema-only", "correct": ka, "accuracy": round(ka / n, 4),
                     "wilson_ci95": [round(ci_a[0], 4), round(ci_a[1], 4)]},
        "system_b": {"name": "schema+invariant", "correct": kb, "accuracy": round(kb / n, 4),
                     "wilson_ci95": [round(ci_b[0], 4), round(ci_b[1], 4)]},
        "mcnemar": mc,
        "interpretation": {
            "system_a": interpret_interval(ka, n),
            "system_b": interpret_interval(kb, n),
            "paired": interpret_mcnemar(mc, "schema-only", "schema+invariant"),
        },
    }
