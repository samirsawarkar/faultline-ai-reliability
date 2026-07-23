"""One canonical, labelled trace per fault — regenerated from the owning day.

Nothing here re-implements a fault; each trace is produced by the exact runner
that owns the family (Day 9 for F1/F2, Day 10 for F3/F4, Day 11 for F5/F6) plus
the Day-4 tracer, and paired with its Day-8 ground-truth log. So a catalog trace
is the same artifact the mission days already trust, collected in one place.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

_ROOT = Path(__file__).resolve().parents[2]
for rel in ("day04", "day08", "day09", "day10", "day11"):
    p = _ROOT / rel
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import faultline_trace as ft  # noqa: E402

import faultline_contracts as fc  # noqa: E402 (day10)
import faultline_detect as fd  # noqa: E402 (day09)
import faultline_spectrum as fsp  # noqa: E402 (day11)
from faultline_contracts import ContractFaultSpec  # noqa: E402
from faultline_spectrum import SpectrumFaultSpec  # noqa: E402

SEED = 20260722


def _pack(fault_id: str, trace: Dict[str, Any], truth,
          summary: Dict[str, Any]) -> Dict[str, Any]:
    return {"fault_id": fault_id, "summary": summary,
            "ground_truth": truth.to_dict(), "trace": trace}


def _day09_trace(fault_id: str, spec) -> Dict[str, Any]:
    tr = ft.Tracer(SEED)
    obs, truth, cost = fd.run([spec], SEED, tracer=tr)
    fired = truth.fired_seqs()
    return _pack(fault_id, tr.to_dict(), truth,
                 {"calls": len(obs), "faults_fired": fired, "cost": cost})


def _day10_trace(fault_id: str, spec) -> Dict[str, Any]:
    tr = ft.Tracer(SEED)
    obs, truth, errs = fc.run_contracts([spec], SEED, tracer=tr)
    return _pack(fault_id, tr.to_dict(), truth,
                 {"calls": len(obs), "faults_fired": truth.fired_seqs(),
                  "provider_errors": sum(errs)})


def _day11_trace(fault_id: str, spec) -> Dict[str, Any]:
    obs, truth = fsp.run_batch([spec], SEED, n_runs=8)
    tr = ft.Tracer(SEED)
    for o in obs:
        rr = o.result
        with tr.span(f"run.{o.seq}", "agent",
                     payload={"seq": o.seq, "steps": rr.steps_used}) as h:
            h.set_output({"completed": rr.completed, "final": rr.final})
    return _pack(fault_id, tr.to_dict(), truth,
                 {"runs": len(obs), "faults_fired": truth.fired_seqs()})


def canonical_trace(fault_id: str) -> Dict[str, Any]:
    if fault_id == "F1":
        return _day09_trace("F1", fd.f1_corruption_spec(
            "*", 3, mode="corrupt", trigger="every_n", trigger_value="2", seed=1))
    if fault_id == "F2":
        return _day09_trace("F2", fd.f2_latency_spec(
            "*", 4, trigger="every_n", trigger_value="2", seed=1))
    if fault_id == "F3":
        return _day10_trace("F3", ContractFaultSpec(
            "F3", "*", "drift_value", 3, "call_index", "3", seed=1))
    if fault_id == "F4":
        return _day10_trace("F4", ContractFaultSpec(
            "F4", "*", "provider_error", 5, "every_n", "2", seed=1))
    if fault_id == "F5":
        return _day11_trace("F5", SpectrumFaultSpec(
            "F5", "context_drift", 2, "call_index", "0", seed=1))
    if fault_id == "F6":
        return _day11_trace("F6", SpectrumFaultSpec(
            "F6", "repetition", 2, "call_index", "0", seed=1))
    raise ValueError(f"unknown fault id {fault_id!r}")


def all_traces() -> Dict[str, Dict[str, Any]]:
    return {fid: canonical_trace(fid) for fid in ("F1", "F2", "F3", "F4", "F5", "F6")}
