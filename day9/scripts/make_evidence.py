"""Regenerate Day 9 evidence (deterministic; byte-reproducible in CI).

Writes under day9/evidence/:
  fault_cards.json      the F1/F2 datasheets (market/evidence)
  detector_sweep.json   severity sweep + budget sensitivity + specificity,
                        every score a confusion matrix vs the injection log
  scored_runs.json      two representative runs, per-call: output, duration,
                        detector signals, and the joined ground truth + confusion
  trace_f1_corrupt.json representative F1 run as a Day-4 trace + its confusion
  trace_f2_latency.json representative F2 run as a Day-4 trace + its confusion
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "day8"))
sys.path.insert(0, str(ROOT.parent / "day4"))

import faultline_trace as ft  # noqa: E402

from faultline_detect import (  # noqa: E402
    DEFAULT_BUDGET,
    build_report,
    duration_detect,
    duration_positives,
    f1_corruption_spec,
    f2_latency_spec,
    fault_cards,
    run,
    schema_detect,
    schema_positives,
    score,
    truth_is_f1,
    truth_is_f2,
)

EVIDENCE = ROOT / "evidence"
SEED = 20260719


def _dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, sort_keys=True, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8")


def scored_run(specs, family: str, budget: int = DEFAULT_BUDGET):
    tracer = ft.Tracer(SEED)
    obs, truth, cost = run(specs, SEED, tracer=tracer)
    rows = []
    for o in obs:
        e = truth.entries[o.seq]
        rows.append({
            "seq": o.seq,
            "component": o.component,
            "output": o.output,
            "duration": o.duration,
            "raised": o.raised,
            "schema_signal": schema_detect(o.seq, o.output).to_dict(),
            "duration_signal": duration_detect(o.seq, o.duration, budget).to_dict(),
            "ground_truth": {"fired": e.fired, "label": e.label,
                             "mode": e.mode, "severity": e.severity},
        })
    if family == "F1":
        conf = score(schema_positives(schema_detect(o.seq, o.output) for o in obs),
                     truth, truth_is_f1)
    else:
        conf = score(duration_positives(
            duration_detect(o.seq, o.duration, budget) for o in obs), truth, truth_is_f2)
    return {
        "family": family, "seed": SEED, "budget": budget, "total_cost": cost,
        "specs": [s.to_dict() for s in specs],
        "confusion_vs_injection_truth": conf.to_dict(),
        "calls": rows,
        "trace": tracer.to_dict(),
    }


def main() -> None:
    EVIDENCE.mkdir(exist_ok=True)

    _dump(EVIDENCE / "fault_cards.json", {"cards": fault_cards()})
    _dump(EVIDENCE / "detector_sweep.json", build_report(seed=SEED))

    # Representative F1: severity 1 corruption — deliberately shows the schema
    # detector MISSING small (in-range) corruption (recall < 1), the honest case.
    f1_specs = [f1_corruption_spec("*", 1, mode="corrupt",
                                   trigger="every_n", trigger_value="2", seed=SEED)]
    run_f1 = scored_run(f1_specs, "F1")

    # Representative F2: severity 4 latency — duration 50 breaches the default
    # budget 45, so the duration detector trips a timeout signal.
    f2_specs = [f2_latency_spec("*", 4, trigger="every_n", trigger_value="2", seed=SEED)]
    run_f2 = scored_run(f2_specs, "F2")

    _dump(EVIDENCE / "scored_runs.json", {
        "scored_against": "day8 GroundTruthLog (injection truth), joined by seq",
        "runs": [{k: v for k, v in r.items() if k != "trace"}
                 for r in (run_f1, run_f2)],
    })
    _dump(EVIDENCE / "trace_f1_corrupt.json", run_f1)
    _dump(EVIDENCE / "trace_f2_latency.json", run_f2)

    rep = build_report(seed=SEED)
    print("Day 9 evidence written:")
    print(f"  F1 schema recall @sev1 : {rep['headline']['f1_recall_at_severity_1']} "
          f"(precision {rep['headline']['f1_precision_min']})")
    print(f"  F2 latency detected from severity : {rep['headline']['f2_detected_from_severity']} "
          f"(budget {DEFAULT_BUDGET})")
    print(f"  specificity (each detector blind to other family): "
          f"{rep['specificity']['each_detector_blind_to_other_family']}")
    print(f"  F1 rep confusion : {run_f1['confusion_vs_injection_truth']}")
    print(f"  F2 rep confusion : {run_f2['confusion_vs_injection_truth']}")


if __name__ == "__main__":
    main()
