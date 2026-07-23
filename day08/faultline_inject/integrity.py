"""Injection integrity — the properties that make a fault a measurement.

Three claims, all machine-checkable and all exercised by the Day-8 test gate and
the evidence script:

  * DETERMINISTIC / IDENTICAL TRIGGERS — re-running the same specs at the same
    run seed injects on byte-identically the same calls, with byte-identical
    outputs and truth. Across a set of seeds, the *deterministic* triggers fire
    on the same calls regardless of seed, while the *probabilistic* trigger's
    pattern varies by seed yet is reproducible within each seed.
  * INDEPENDENT TRUTH / NO LABEL LEAKAGE — no ground-truth label (or fault id or
    mode word) appears anywhere in what the system under test can observe: not in
    an output payload, not in a trace span. The label lives only in the log.
  * COMPLETE LABELLING — every call is labelled exactly once, contiguously, so
    the truth log is a full dataset, not a lossy sample.

`build_report` returns a JSON-able summary used as committed evidence.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .boundary import DemoChannel, InjectingChannel, digest
from .spec import FaultSpec
from .truth import GroundTruthLog

_DAY4 = Path(__file__).resolve().parents[2] / "day04"
if str(_DAY4) not in sys.path:
    sys.path.insert(0, str(_DAY4))


Call = Dict[str, Any]


def default_calls(n: int = 12) -> List[Call]:
    """A fixed, deterministic call sequence over three tool components."""
    names = ("retrieve", "sum", "verify")
    calls: List[Call] = []
    for i in range(n):
        name = names[i % len(names)]
        calls.append({"component": f"tool.{name}", "step": name, "index": i})
    return calls


def run_boundary(specs: List[FaultSpec], run_seed: int, calls: List[Call],
                 tracer=None) -> Tuple[List[Any], GroundTruthLog, int]:
    """Drive `calls` through an InjectingChannel over a clean DemoChannel.

    Returns (outputs, truth_log, cost_units). An `error`-mode fault surfaces as
    the sentinel "RAISED" in the outputs list (a neutral marker chosen NOT to
    contain any mode word), so the sequence stays aligned with the truth log for
    comparison without itself looking like a leak.
    """
    from .faults import InjectedFaultError
    ch = InjectingChannel(DemoChannel(), specs, run_seed, tracer=tracer)
    outputs: List[Any] = []
    for c in calls:
        payload = {k: v for k, v in c.items() if k != "component"}
        try:
            outputs.append(ch.call(c["component"], payload))
        except InjectedFaultError:
            outputs.append("RAISED")
    return outputs, ch.truth, ch.cost_units


def _outputs_digest(outputs: List[Any]) -> str:
    return digest(outputs)


def leakage_scan(outputs: List[Any], truth: GroundTruthLog,
                 trace: Optional[Dict[str, Any]] = None) -> List[str]:
    """Return the list of leaks: label strings found in observable surfaces.
    An empty list means no leakage."""
    needles = truth.label_strings()
    haystacks = [json.dumps(outputs, sort_keys=True, ensure_ascii=True)]
    if trace is not None:
        haystacks.append(json.dumps(trace, sort_keys=True, ensure_ascii=True))
    leaks: List[str] = []
    for needle in needles:
        if any(needle in hay for hay in haystacks):
            leaks.append(needle)
    return leaks


def assert_deterministic(specs: List[FaultSpec], run_seed: int,
                         calls: List[Call], repeats: int = 3) -> None:
    """Same specs + same seed => identical fire pattern, outputs, and truth."""
    base_out, base_truth, base_cost = run_boundary(specs, run_seed, calls)
    for _ in range(repeats - 1):
        out, truth, cost = run_boundary(specs, run_seed, calls)
        assert _outputs_digest(out) == _outputs_digest(base_out), "outputs drift"
        assert truth.to_json() == base_truth.to_json(), "truth drift"
        assert cost == base_cost, "cost drift"


def build_report(specs: List[FaultSpec], seeds: List[int],
                 calls: Optional[List[Call]] = None) -> Dict[str, Any]:
    """Cross-seed attack: prove identical/deterministic triggers and no leakage."""
    calls = calls or default_calls()
    det_triggers = {"call_index", "every_n", "input_match"}
    det_ids = [s.fault_id for s in specs if s.trigger in det_triggers]
    prob_ids = [s.fault_id for s in specs if s.trigger == "probabilistic"]

    per_seed: List[Dict[str, Any]] = []
    det_fire_signatures = set()
    prob_fire_by_seed: Dict[int, str] = {}
    all_leaks: List[str] = []

    for seed in seeds:
        # reproducibility within a seed (identical triggers on repeat)
        out1, truth1, cost1 = run_boundary(specs, seed, calls)
        out2, truth2, cost2 = run_boundary(specs, seed, calls)
        reproducible = (truth1.to_json() == truth2.to_json()
                        and _outputs_digest(out1) == _outputs_digest(out2)
                        and cost1 == cost2)

        # separate the fire pattern into deterministic vs probabilistic specs
        det_fires = tuple(
            (e.seq, e.fault_id) for e in truth1.entries
            if e.fired and e.fault_id in det_ids)
        prob_fires = tuple(
            (e.seq, e.fault_id) for e in truth1.entries
            if e.fired and e.fault_id in prob_ids)
        det_fire_signatures.add(det_fires)
        prob_fire_by_seed[seed] = json.dumps(prob_fires)

        leaks = leakage_scan(out1, truth1)
        all_leaks.extend(leaks)

        per_seed.append({
            "seed": seed,
            "calls": len(calls),
            "faults_fired": len(truth1.fired_seqs()),
            "fired_seqs": truth1.fired_seqs(),
            "cost_units": cost1,
            "reproducible_on_repeat": reproducible,
            "truth_sha256": digest(truth1.to_dict()),
            "outputs_sha256": _outputs_digest(out1),
            "leaks": leaks,
        })

    det_seed_independent = len(det_fire_signatures) == 1 and bool(det_ids)
    prob_varies = len(set(prob_fire_by_seed.values())) > 1 if prob_ids else False

    return {
        "seeds": seeds,
        "spec_count": len(specs),
        "deterministic_fault_ids": det_ids,
        "probabilistic_fault_ids": prob_ids,
        "all_seeds_reproducible": all(p["reproducible_on_repeat"] for p in per_seed),
        "deterministic_triggers_seed_independent": det_seed_independent,
        "probabilistic_trigger_varies_across_seeds": prob_varies,
        "label_leaks_total": len(all_leaks),
        "no_label_leakage": len(all_leaks) == 0,
        "per_seed": per_seed,
    }
