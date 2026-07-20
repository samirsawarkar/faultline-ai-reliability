"""The attack: measure which wrong values escape contract validation.

A single mixed run exercises all five F3 kinds and one F4 provider error on
distinct calls, so one trace shows the whole boundary: schema catches the
malformed, the invariant catches the non-round-ten, the provider-error detector
catches the explicit failure — and two schema-valid semantic corruptions ESCAPE.

A second sweep shows the escape is severity-INVARIANT: a big wrong-but-valid value
is exactly as invisible as a small one, unlike Day 9's F1/F2 whose detection rose
with severity.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .breaker import run_breaker
from .detectors import classify
from .runner import run_contracts
from .score import (
    escaped_false_negatives,
    per_kind_detection,
    score_detection,
)
from .spec import F3_KINDS, ContractFaultSpec

DEFAULT_SEED = 20260720
SWEEP_SEVERITIES = [1, 2, 3, 4, 5]

# One kind per call, on distinct indices, so a single run covers the boundary.
MIXED_PLAN = [
    (0, "malformed_range"), (1, "malformed_tokens"), (2, "nonmultiple"),
    (3, "drift_value"), (4, "offbase_tokens"), (5, "provider_error"),
]
# F3-only plan (no provider error) — used for the F3 precision/recall so a
# provider-error flag is never miscounted as an F3 false positive.
F3_PLAN = [p for p in MIXED_PLAN if p[1] != "provider_error"]


def mixed_specs(severity: int = 2) -> List[ContractFaultSpec]:
    return [ContractFaultSpec(f"C{seq}", "*", kind, severity, "call_index",
                              str(seq), seed=1) for seq, kind in MIXED_PLAN]


def f3_specs(severity: int = 2) -> List[ContractFaultSpec]:
    return [ContractFaultSpec(f"C{seq}", "*", kind, severity, "call_index",
                              str(seq), seed=1) for seq, kind in F3_PLAN]


def f4_specs(severity: int = 2) -> List[ContractFaultSpec]:
    return [ContractFaultSpec("F4", "*", "provider_error", severity,
                              "every_n", "2", seed=1)]


def _single_kind_specs(kind: str, severity: int) -> List[ContractFaultSpec]:
    return [ContractFaultSpec(f"K-{kind}", "*", kind, severity, "every_n", "2", seed=1)]


def severity_invariance() -> Dict[str, Any]:
    """Detection rate per F3 kind across severities 1..5."""
    table: Dict[str, Dict[int, float]] = {}
    for kind in F3_KINDS:
        row: Dict[int, float] = {}
        for s in SWEEP_SEVERITIES:
            obs, truth, _ = run_contracts(_single_kind_specs(kind, s), DEFAULT_SEED)
            row[s] = per_kind_detection(obs, truth)[kind]["detection_rate"]
        table[kind] = row
    return table


def build_report(seed: int = DEFAULT_SEED) -> Dict[str, Any]:
    # F3 scored on an F3-only run; F4 on an F4-only run — so a flag for one family
    # is never a false positive against the other.
    obs3, truth3, _ = run_contracts(f3_specs(), seed)
    obs4, truth4, ef4 = run_contracts(f4_specs(), seed)

    f3 = score_detection(obs3, truth3, "F3")
    f4 = score_detection(obs4, truth4, "F4")
    escapes = escaped_false_negatives(obs3, truth3)
    per_kind = per_kind_detection(obs3, truth3)
    breaker = run_breaker(ef4)

    # A combined run purely to ILLUSTRATE the classifier boundary per call.
    obsm, truthm, _ = run_contracts(mixed_specs(), seed)
    verdicts = [{"seq": o.seq, "injected": truthm.entries[o.seq].mode or "clean",
                 "classifier_class": classify(o.raised, o.output)} for o in obsm]

    return {
        "seed": seed,
        "scored_against": "day8 GroundTruthLog (injection truth) + day10 oracle",
        "mixed_run_verdicts": verdicts,
        "f3_detection": f3.to_dict(),
        "f4_detection": f4.to_dict(),
        "per_kind_detection": per_kind,
        "escaped_false_negatives": escapes,
        "escape_count": len(escapes),
        "severity_invariance": severity_invariance(),
        "circuit_breaker": breaker.to_dict(),
        "classifier_boundaries": classifier_boundaries(),
        "headline": {
            "f3_wrong_data_recall": f3.to_dict()["recall"],
            "f3_precision": f3.to_dict()["precision"],
            "f3_escaped_kinds": sorted({r["injected_kind"] for r in escapes}),
            "f4_provider_error_recall": f4.to_dict()["recall"],
            "circuit_breaker_opened_at": breaker.opened_at,
            "escape_is_severity_invariant": _escape_invariant(),
        },
    }


def _escape_invariant() -> bool:
    """True iff the schema-valid escaping kinds detect at rate 0 for every severity."""
    inv = severity_invariance()
    return all(inv[k][s] == 0.0 for k in ("drift_value", "offbase_tokens")
               for s in SWEEP_SEVERITIES)


def classifier_boundaries() -> Dict[str, Any]:
    """Which truth classes a deterministic classifier can and cannot separate."""
    return {
        "separable": {
            "provider_error": "explicit error flag (recall 1.0)",
            "malformed": "schema violation (structural)",
            "invariant_violation": "value not a round ten (semantic invariant)",
        },
        "not_separable": {
            "schema_valid_semantic_wrong": (
                "drift_value / offbase_tokens: schema-valid, invariant-respecting, "
                "non-erroring -> classified OK. Only the oracle knows it is wrong. "
                "Reported as a missed detection with evidence, never as detected."),
        },
    }
