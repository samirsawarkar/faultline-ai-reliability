"""Attack: score F5/F6, isolate the semantic-eval faults, state the Q2 split.

F6 is closed by deterministic detectors (recall 1.0, no escape). F5's coherent
context drift escapes the consistency invariant and is isolated as requiring
semantic evaluation. Combined with Days 9-10 via the spectrum map, this yields the
Q2 SPLIT HYPOTHESIS: detection accuracy bifurcates by detection nature.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .runner import run_batch
from .score import score_f5, score_f6, semantic_escapes
from .spec import SpectrumFaultSpec
from .spectrum_map import build_map

DEFAULT_SEED = 20260721

F5_PLAN = [(0, "context_drift"), (1, "context_inconsistent"),
           (2, "context_drift"), (3, "context_inconsistent")]
F6_PLAN = [(0, "repetition"), (1, "budget_exhaustion"),
           (2, "repetition"), (3, "budget_exhaustion")]


def f5_specs() -> List[SpectrumFaultSpec]:
    return [SpectrumFaultSpec(f"F5-{seq}", kind, 2, "call_index", str(seq), seed=1)
            for seq, kind in F5_PLAN]


def f6_specs() -> List[SpectrumFaultSpec]:
    return [SpectrumFaultSpec(f"F6-{seq}", kind, 2, "call_index", str(seq), seed=1)
            for seq, kind in F6_PLAN]


def q2_split_hypothesis(det_map: Dict[str, Any], f5, f6) -> Dict[str, Any]:
    return {
        "question": "Q2 — how does detection accuracy split across the fault spectrum?",
        "hypothesis": (
            "Detection accuracy bifurcates by DETECTION NATURE, not by fault "
            "severity. Deterministic faults (F2 latency, F4 provider error, F6 "
            "loop exhaustion) are detected at recall 1.0 by cheap structural/"
            "counting detectors with NO residual escape. Semantic faults (F3 "
            "schema-valid drift, F5 context corruption) leave an irreducible "
            "escape set under ANY deterministic detector; closing them requires "
            "semantic evaluation (an oracle or a validated judge). Q2 (Mission 15) "
            "will measure this split with confidence intervals."),
        "supporting": {
            "fully_deterministic_faults": det_map["fully_deterministic_recall_1_no_escape"],
            "require_semantic_evaluation": det_map["require_semantic_evaluation"],
            "f6_deterministic_recall": f6.recall,          # expect 1.0
            "f6_escape_set_size": f6.fn,                     # expect 0
            "f5_consistency_recall": f5.recall,             # expect < 1.0
            "f5_escape_needs_semantic_eval": f5.fn,          # the drift runs
        },
        "falsifiable_by": (
            "a deterministic detector that closes F5 context_drift or F3 "
            "drift_value/offbase_tokens without any correctness model would refute "
            "the split. None exists by construction: those corruptions are "
            "structurally identical to correct outputs."),
    }


def build_report(seed: int = DEFAULT_SEED) -> Dict[str, Any]:
    obs5, truth5 = run_batch(f5_specs(), seed, n_runs=8)
    obs6, truth6 = run_batch(f6_specs(), seed, n_runs=8)
    f5 = score_f5(obs5, truth5)
    f6 = score_f6(obs6, truth6)
    escapes = semantic_escapes(obs5, truth5)
    det_map = build_map()

    return {
        "seed": seed,
        "scored_against": "day8 GroundTruthLog (injection truth) + day11 oracle",
        "f5_context_detection": f5.to_dict(),
        "f6_loop_detection": f6.to_dict(),
        "f5_semantic_escapes": escapes,
        "f5_escape_count": len(escapes),
        "deterministic_vs_semantic_map": det_map,
        "q2_split_hypothesis": q2_split_hypothesis(det_map, f5, f6),
        "headline": {
            "f6_loop_recall": f6.to_dict()["recall"],
            "f6_escapes": f6.to_dict()["fn"],
            "f5_consistency_recall": f5.to_dict()["recall"],
            "f5_semantic_escape_kinds": sorted({r["injected_kind"] for r in escapes}),
            "separation_holds": det_map["separation_holds"],
        },
    }
