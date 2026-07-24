"""Investigate every false positive and false negative — trace by trace.

The mission's fail condition is that FPs/FNs get hidden by aggregate metrics. This
module does the opposite: for each failing sample it re-runs the exact unit through
the owning day's runner with a Day-4 tracer, and returns the observable the detector
saw, the detector's verdict, the oracle's verdict, and a full trace. So every miss
is a concrete, reproducible example a reviewer can open — not a number.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

_ROOT = Path(__file__).resolve().parents[2]
for rel in ("day04", "day08", "day09", "day10", "day11"):
    p = _ROOT / rel
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import faultline_trace as ft  # noqa: E402

import faultline_contracts as fc  # noqa: E402
import faultline_detect as fd  # noqa: E402
import faultline_spectrum as fsp  # noqa: E402
from faultline_contracts import ContractFaultSpec, classify, detected_faulty  # noqa: E402
from faultline_spectrum import SpectrumFaultSpec, context_integrity_detect, loop_detect  # noqa: E402

_ONE_CALL = [{"component": "tool.retrieve", "step": "retrieve", "index": 0}]
_SEMANTIC_ESCAPE_KINDS = ("drift_value", "offbase_tokens", "context_drift")


def trace_sample(modality: str, is_fault: bool, kind: str, severity: int, seed: int
                 ) -> Dict[str, Any]:
    """Reproduce one unit with a Day-4 trace; return observable + verdict + trace."""
    if modality in ("F1", "F2"):
        tr = ft.Tracer(seed)
        specs = ([fd.f1_corruption_spec("*", severity, mode=kind, trigger="call_index",
                                        trigger_value="0", seed=seed)] if modality == "F1"
                 else [fd.f2_latency_spec("*", severity, trigger="call_index",
                                          trigger_value="0", seed=seed)]) if is_fault else []
        obs, _, _ = fd.run(specs, seed, calls=_ONE_CALL, tracer=tr)
        o = obs[0]
        predicted = (fd.schema_detect(o.seq, o.output).repair_signal if modality == "F1"
                     else fd.duration_detect(o.seq, o.duration).timeout_signal)
        observable = {"output": o.output, "duration": o.duration, "raised": o.raised}
        trace = tr.to_dict()

    elif modality in ("F3", "F4"):
        tr = ft.Tracer(seed)
        specs = ([ContractFaultSpec("S", "*", kind, severity, "call_index", "0", seed=seed)]
                 if is_fault else [])
        obs, _, _ = fc.run_contracts(specs, seed, calls=_ONE_CALL, tracer=tr)
        o = obs[0]
        predicted = detected_faulty(classify(o.raised, o.output))
        observable = {"output": o.output, "raised": o.raised, "error_code": o.error_code}
        trace = tr.to_dict()

    elif modality in ("F5", "F6"):
        specs = ([SpectrumFaultSpec("S", kind, severity, "call_index", "0", seed=seed)]
                 if is_fault else [])
        obs, _ = fsp.run_batch(specs, seed, n_runs=1)
        rr = obs[0].result
        tr = ft.Tracer(seed)
        with tr.span("run.0", "agent", payload={"steps": rr.steps_used}) as h:
            h.set_output({"completed": rr.completed, "final": rr.final})
        predicted = (context_integrity_detect(rr).fired if modality == "F5"
                     else loop_detect(rr).fired)
        observable = rr.to_dict()
        trace = tr.to_dict()
    else:
        raise ValueError(f"unknown modality {modality!r}")

    return {"modality": modality, "is_fault": is_fault, "kind": kind,
            "severity": severity, "seed": seed,
            "predicted_faulty": predicted, "observable": observable, "trace": trace}


def _why(outcome: str, kind: str) -> str:
    if outcome == "FP":
        return "false positive: detector flagged a clean sample"
    if kind in _SEMANTIC_ESCAPE_KINDS:
        return ("irreducible semantic escape: schema-valid, invariant-respecting, "
                "structurally identical to a correct output — only the oracle knows")
    return ("threshold-reducible: the fault is below the detector's threshold "
            "(schema value range / latency budget); tightening it would catch this")


def collect_failures(outcomes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """For each FP/FN row, attach the observable, verdict, reason, and trace."""
    failures: List[Dict[str, Any]] = []
    for o in outcomes:
        if o["outcome"] not in ("FP", "FN"):
            continue
        t = trace_sample(o["modality"], o["is_fault"], o["kind"], o["severity"], o["seed"])
        failures.append({
            "sample_id": o["sample_id"], "modality": o["modality"], "kind": o["kind"],
            "severity": o["severity"], "seed": o["seed"], "outcome": o["outcome"],
            "expected_faulty": o["expected_faulty"], "predicted_faulty": o["predicted_faulty"],
            "why": _why(o["outcome"], o["kind"]),
            "observable": t["observable"],
            "trace_artifact": f"evidence/traces/{o['sample_id']}.json",
            "trace": t["trace"],
        })
    return failures
