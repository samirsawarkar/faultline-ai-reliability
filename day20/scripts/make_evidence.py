"""Regenerate Day 20 evidence (deterministic; byte-reproducible in CI).

Writes under day20/evidence/:
  breaker_report.json    false-open, flapping, fallback-failure + paired outage configs
  state_diagram.svg      the circuit-breaker state-transition diagram
  transitions_trace.json a canonical outage run: transition timeline + per-request
                         provenance + the Day-4 trace (both traceable, the fail cond.)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in ("", "../day04", "../day08", "../day09", "../day14"):
    sys.path.insert(0, str((ROOT / rel).resolve()))

import faultline_trace as ft  # noqa: E402 (Day 4)

from faultline_breaker import (BreakerConfig, CircuitBreaker, build_report,  # noqa: E402
                               render_state_diagram, render_timeline, run_stream)

EVIDENCE = ROOT / "evidence"
SEED = 20260730


def _dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, sort_keys=True, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8")


def main() -> None:
    EVIDENCE.mkdir(exist_ok=True)
    report = build_report()
    _dump(EVIDENCE / "breaker_report.json", report)
    (EVIDENCE / "state_diagram.svg").write_text(render_state_diagram(), encoding="utf-8")

    # canonical traced run: primary down for ticks [20,40)
    tr = ft.Tracer(SEED)
    r = run_stream(60, lambda t: 20 <= t < 40, CircuitBreaker(BreakerConfig(3, 5, 10, 2)),
                   use_fallback=True, tracer=tr)
    _dump(EVIDENCE / "transitions_trace.json", {
        "metrics": r["metrics"],
        "transition_timeline": render_timeline(r["transitions"]),
        "transitions": r["transitions"],
        "provenance_sample": r["outcomes"][18:44],   # around the outage
        "trace": r["trace"],
    })

    p = report["paired_outage"]
    print("Day 20 evidence written:")
    print(f"  transitions (canonical run): {render_timeline(r['transitions'])}")
    print(f"  false open — twitchy blocked {report['false_open']['twitchy_threshold1']['healthy_blocked']} "
          f"healthy vs tuned {report['false_open']['tuned_threshold3_of_5']['healthy_blocked']}")
    print(f"  flapping — eager {report['flapping']['eager']['transitions']} vs damped "
          f"{report['flapping']['damped']['transitions']} transitions")
    print(f"  fallback failure — availability {report['fallback_failure']['availability']} "
          f"({report['fallback_failure']['served_degraded']} degraded, 0 hidden)")
    print(f"  paired — naive avail {p['naive_no_breaker_no_fallback']['availability']} -> "
          f"breaker+fb {p['breaker_plus_fallback']['availability']}; "
          f"primary calls saved {p['primary_calls_saved_by_breaker']}")


if __name__ == "__main__":
    main()
