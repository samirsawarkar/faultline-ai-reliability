"""Regenerate Day 8 evidence (deterministic; byte-reproducible in CI).

Writes three artifacts under day8/evidence/:
  injector_spec.json     the example fault-spec set (the API's input contract)
  integrity_report.json  cross-seed attack: identical triggers + no leakage
  fault_trace.json       ONE reproducible fault trace with its ground-truth labels

Everything is a pure function of the fixed seeds/specs below — no wall clock, no
default RNG — so re-running reproduces the bytes and CI can `git diff --exit-code`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "day4"))

import faultline_trace as ft  # noqa: E402

from faultline_inject import (  # noqa: E402
    FaultSpec,
    SPEC_VERSION,
    build_report,
    default_calls,
    leakage_scan,
    run_boundary,
)

EVIDENCE = ROOT / "evidence"
TRACE_SEED = 20260718
SEEDS = [20260718, 1, 42, 777, 100000]


def scenario():
    """A representative spec set: one of each trigger family, mixed modes."""
    return [
        FaultSpec("F-idx-corrupt", "*", "corrupt", 3, "call_index", "4", 1, 1.0,
                  "fault:corrupt", SPEC_VERSION),
        FaultSpec("F-evn-truncate", "tool.verify", "truncate", 2, "every_n", "2",
                  2, 1.0, "fault:truncate", SPEC_VERSION),
        FaultSpec("F-prb-stall", "tool.retrieve", "stall", 4, "probabilistic", "",
                  9, 0.5, "fault:stall", SPEC_VERSION),
        FaultSpec("F-idx-error", "tool.sum", "error", 5, "call_index", "7", 3, 1.0,
                  "fault:error", SPEC_VERSION),
    ]


def _dump(path: Path, obj) -> None:
    text = json.dumps(obj, sort_keys=True, ensure_ascii=True, indent=2)
    path.write_text(text + "\n", encoding="utf-8")


def main() -> None:
    EVIDENCE.mkdir(exist_ok=True)
    specs = scenario()

    # 1. The input contract: the fault specs, exactly as the API consumes them.
    _dump(EVIDENCE / "injector_spec.json", {
        "spec_version": SPEC_VERSION,
        "fields": list(FaultSpec.FIELDS),
        "specs": [s.validate().to_dict() for s in specs],
    })

    # 2. The attack: identical triggers across seeds + no label leakage.
    report = build_report(specs, SEEDS)
    _dump(EVIDENCE / "integrity_report.json", report)

    # 3. One reproducible fault trace, with its independent ground-truth labels.
    calls = default_calls()
    tracer = ft.Tracer(TRACE_SEED)
    outputs, truth, cost = run_boundary(specs, TRACE_SEED, calls, tracer=tracer)
    trace = tracer.to_dict()
    leaks = leakage_scan(outputs, truth, trace=trace)
    # outputs may contain the sentinel "<error>"; keep it as-is (JSON-safe).
    _dump(EVIDENCE / "fault_trace.json", {
        "run_seed": TRACE_SEED,
        "spec_version": SPEC_VERSION,
        "specs": [s.to_dict() for s in specs],
        "calls": calls,
        "cost_units": cost,
        "faults_fired": truth.fired_seqs(),
        "no_label_leakage": leaks == [],
        "outputs": outputs,
        "ground_truth": truth.to_dict(),
        "trace": trace,
    })

    print("Day 8 evidence written:")
    print(f"  seeds tested            : {SEEDS}")
    print(f"  all seeds reproducible  : {report['all_seeds_reproducible']}")
    print(f"  det. triggers seed-indep: {report['deterministic_triggers_seed_independent']}")
    print(f"  prob. trigger varies    : {report['probabilistic_trigger_varies_across_seeds']}")
    print(f"  label leaks (total)     : {report['label_leaks_total']}")
    print(f"  trace faults fired      : {truth.fired_seqs()}  cost={cost}")


if __name__ == "__main__":
    main()
