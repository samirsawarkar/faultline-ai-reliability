"""Observability gate + divergence/trace-gap investigation.

The gate (Evidence block, "pass the observability gate"): every counted run must
leave a complete, gap-free record — reached-hop count consistent, hop outcomes
present and contiguous, and the end-to-end verdict consistent with the hops. If
any run is unbacked, the numbers are not trustworthy and the gate fails.

Investigation (Attack block): for the divergence hop, rebuild concrete runs as
Day-4 traces (a failing one and a passing one) to show the failure is real and
observable — no trace gaps — and that the divergence is explained by declining
per-hop reliability, not a measurement artifact.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

from .simulator import hop_probability, run_once
from .sweep import SweepResult

_DAY4 = Path(__file__).resolve().parents[2] / "day04"
if str(_DAY4) not in sys.path:
    sys.path.insert(0, str(_DAY4))


class ObservabilityGateError(AssertionError):
    pass


def check_gate(sweep: SweepResult) -> Dict[str, Any]:
    """Assert every run is completely and consistently recorded. Raises on any gap."""
    cfg = sweep.config
    expected_runs = cfg.max_hops * cfg.trials
    if len(sweep.runs) != expected_runs:
        raise ObservabilityGateError(
            f"run count {len(sweep.runs)} != expected {expected_runs}")

    gaps: List[str] = []
    for r in sweep.runs:
        # per-hop record present for every reached hop (no missing hop)
        if len(r.hop_success) != r.hops_reached:
            gaps.append(f"n={r.n_hops} trial={r.trial}: hop record length gap")
        # a run either reached all n (and all succeeded) or stopped at a failure
        if r.success:
            if r.hops_reached != r.n_hops or not all(r.hop_success):
                gaps.append(f"n={r.n_hops} trial={r.trial}: success/hops inconsistent")
        else:
            if r.hop_success and r.hop_success[-1] is True and r.hops_reached == r.n_hops:
                gaps.append(f"n={r.n_hops} trial={r.trial}: failure verdict inconsistent")

    if gaps:
        raise ObservabilityGateError(f"{len(gaps)} trace gap(s): {gaps[:3]}")

    return {
        "runs": len(sweep.runs),
        "runs_expected": expected_runs,
        "trace_gaps": 0,
        "every_run_backed_by_record": True,
        "gate_passed": True,
    }


def _trace_run(master_seed: int, n: int, trial: int) -> Dict[str, Any]:
    """Rebuild one run as a Day-4 trace (agent -> per-hop tool spans)."""
    import faultline_trace as ft  # Day 4

    r = run_once(master_seed, n, trial)
    tracer = ft.Tracer(trial)
    try:
        with tracer.span("agent", "agent", payload={"n_hops": n}) as agent:
            for k in range(1, r.hops_reached + 1):
                with tracer.span(f"hop.{k}", "tool", payload={"hop": k}) as hop:
                    if not r.hop_success[k - 1]:
                        raise ft.RiskyToolError(f"hop {k} failed (p_k={hop_probability(k):.3f})")
                    hop.set_output({"hop": k, "ok": True})
            agent.set_output({"success": True, "hops": n})
    except ft.RiskyToolError:
        pass

    spans = tracer.to_dict()["spans"]
    return {
        "n_hops": n, "trial": trial, "success": r.success,
        "hops_reached": r.hops_reached,
        "trace": tracer.to_dict(),
        "spans_complete": all(s["end_seq"] is not None for s in spans),
        "span_count": len(spans),
    }


def investigate_divergence(sweep: SweepResult, curves: Dict[str, Any]) -> Dict[str, Any]:
    """Explain the divergence hop and prove the runs are observable (no gaps)."""
    n = curves["first_divergence_hop"]
    findings: Dict[str, Any] = {"divergence_hop": n}

    if n is None:
        findings["explanation"] = "naive band never separated from measured band"
        return findings

    # find a failing and a passing trial at the divergence hop
    fail_ex = pass_ex = None
    for trial in range(sweep.config.trials):
        r = run_once(sweep.config.master_seed, n, trial)
        if not r.success and fail_ex is None:
            fail_ex = _trace_run(sweep.config.master_seed, n, trial)
        if r.success and pass_ex is None:
            pass_ex = _trace_run(sweep.config.master_seed, n, trial)
        if fail_ex and pass_ex:
            break

    pt = next(p for p in curves["points"] if p["hops"] == n)
    findings.update({
        "measured": pt["measured"],
        "measured_ci95": pt["measured_ci95"],
        "naive": pt["naive"],
        "naive_ci95": pt["naive_ci95"],
        "measured_minus_naive": pt["measured_minus_naive"],
        "explanation": (
            f"At n={n} the naive constant-per-step prediction ({pt['naive']}) lies "
            f"above the measured 95% CI {pt['measured_ci95']}. Per-hop reliability "
            f"declines with depth (hop1={curves['per_hop'][0]['rate']} -> "
            f"hop{n}={curves['per_hop'][n-1]['rate']}), so end-to-end reliability "
            f"compounds faster downward than p1**n predicts."
        ),
        "example_fail": {k: fail_ex[k] for k in
                         ("n_hops", "trial", "success", "hops_reached",
                          "spans_complete", "span_count")} if fail_ex else None,
        "example_pass": {k: pass_ex[k] for k in
                         ("n_hops", "trial", "success", "hops_reached",
                          "spans_complete", "span_count")} if pass_ex else None,
        "trace_gaps_in_examples": 0 if (
            (not fail_ex or fail_ex["spans_complete"]) and
            (not pass_ex or pass_ex["spans_complete"])) else 1,
        "example_fail_trace": fail_ex["trace"] if fail_ex else None,
    })
    return findings
