#!/usr/bin/env python3
"""Regenerate Q1 evidence (all deterministic; CI byte-diffs these).

  evidence/q1_results.json      the Q1 finding: curve + per-hop + intervals + gate
  evidence/measured_vs_naive.svg the measured-vs-naive figure with CI bands
  evidence/investigation.json    divergence + trace-gap investigation
  evidence/example_fail_trace.json a concrete failing run, fully traced (no gaps)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from faultline_hops import (  # noqa: E402
    SweepConfig,
    build_curves,
    build_q1,
    investigate_divergence,
    render_svg,
    run_sweep,
)

EVID = ROOT / "evidence"


def _write(path: Path, data: bytes) -> None:
    path.write_bytes(data)
    print(f"wrote {len(data):6d} B -> {path.relative_to(ROOT)}")


def _json_bytes(obj) -> bytes:
    return (json.dumps(obj, indent=2, sort_keys=True) + "\n").encode()


def main() -> int:
    EVID.mkdir(exist_ok=True)
    config = SweepConfig()

    q1 = build_q1(config)
    _write(EVID / "q1_results.json", _json_bytes(q1))
    _write(EVID / "measured_vs_naive.svg", render_svg(q1).encode())

    sweep = run_sweep(config)
    curves = build_curves(sweep)
    inv = investigate_divergence(sweep, curves)
    example_trace = inv.pop("example_fail_trace")
    _write(EVID / "investigation.json", _json_bytes(inv))
    _write(EVID / "example_fail_trace.json", _json_bytes(example_trace))

    print(f"\nfinding: {q1['finding']}")
    print(f"observability gate passed: {q1['observability_gate']['gate_passed']}")
    ok = q1["observability_gate"]["gate_passed"] and q1["first_divergence_hop"]
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
