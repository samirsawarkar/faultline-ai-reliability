"""Regenerate Day 18 evidence (deterministic; byte-reproducible in CI).

Writes under day18/evidence/:
  recovery_report.json   configs + paired experiments + exhaustion attack + new-failure
  recovery_traces.json   Day-4 traces of a recovered and an exhausted run (M1 + M2)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in ("", "../day04", "../day08", "../day09", "../day14"):
    sys.path.insert(0, str((ROOT / rel).resolve()))

import faultline_trace as ft  # noqa: E402 (Day 4)

from faultline_recovery import (  # noqa: E402
    M1_POLICY, M2_POLICY, build_report, make_producer, make_slow_tool,
    persistent_slow, transient_slow,
)

EVIDENCE = ROOT / "evidence"
SEED = 20260728


def _dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, sort_keys=True, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8")


def _trace_m1(clears_after: int, policy):
    """Trace a repair-retry: one span per bounded attempt, error span if invalid."""
    tracer = ft.Tracer(SEED)
    attempt_fn = make_producer(clears_after)
    with tracer.span("repair_retry", "agent", payload={"max": policy.max_attempts}) as a:
        recovered = False
        for i in range(policy.max_attempts):
            with tracer.span(f"attempt.{i}", "tool", payload={"i": i}) as h:
                ok, lat, out = attempt_fn(i)
                if ok:
                    h.set_output({"valid": True, "latency": lat}); recovered = True; break
                h.set_output({"valid": False, "latency": lat})
        a.set_output({"recovered": recovered})
    return tracer.to_dict()


def _trace_m2(duration_fn, timeout, policy):
    tracer = ft.Tracer(SEED)
    attempt_fn = make_slow_tool(duration_fn, timeout)
    with tracer.span("timeout_retry", "agent", payload={"timeout": timeout}) as a:
        recovered = False
        for i in range(policy.max_attempts):
            with tracer.span(f"attempt.{i}", "tool", payload={"i": i}) as h:
                ok, lat, dur = attempt_fn(i)
                h.set_output({"completed": ok, "waited": lat, "duration": dur})
                if ok:
                    recovered = True; break
        a.set_output({"recovered": recovered})
    return tracer.to_dict()


def main() -> None:
    EVIDENCE.mkdir(exist_ok=True)
    report = build_report()
    _dump(EVIDENCE / "recovery_report.json", report)
    _dump(EVIDENCE / "recovery_traces.json", {
        "m1_recovered": _trace_m1(2, M1_POLICY),
        "m1_exhausted": _trace_m1(99, M1_POLICY),
        "m2_recovered": _trace_m2(transient_slow(60, 20), 30, M2_POLICY),
        "m2_exhausted": _trace_m2(persistent_slow(90), 30, M2_POLICY),
    })

    ex = report["exhaustion_attack"]["checks"]
    print("Day 18 evidence written:")
    print(f"  M1 recovery: no-recov {report['paired_m1']['no_recovery_success']} -> "
          f"recov {report['paired_m1']['recovery_success']} "
          f"(McNemar p={report['paired_m1']['mcnemar']['p_value']:.5f}, "
          f"sig={report['paired_m1']['mcnemar']['significant_at_0.05']})")
    print(f"  M2 recovery: no-recov {report['paired_m2']['no_recovery_success']} -> "
          f"recov {report['paired_m2']['recovery_success']} "
          f"(McNemar p={report['paired_m2']['mcnemar']['p_value']:.5f})")
    print(f"  all ceilings hold: {ex['all_ceilings_hold']}")
    print(f"  safe to repeat (idempotent): {report['new_failure_analysis']['idempotency']['safe_to_repeat']}")


if __name__ == "__main__":
    main()
