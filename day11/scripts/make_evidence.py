"""Regenerate Day 11 evidence (deterministic; byte-reproducible in CI).

Writes under day11/evidence/:
  fault_cards.json                 F5/F6 datasheets
  spectrum_report.json             F5/F6 detection + escapes + map + Q2 hypothesis
  deterministic_vs_semantic_map.json  the F1-F6 map (the required artifact)
  q2_split_hypothesis.json         the Q2 split hypothesis with supporting numbers
  escape_examples.json             F5 context_drift runs that need semantic eval
  trace_f5_context.json            an F5 batch run, traced (Day 4) + verdicts
  trace_f6_loop.json               an F6 batch run, traced + verdicts
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in ("", "../day8", "../day9", "../day10", "../day4"):
    sys.path.insert(0, str((ROOT / rel).resolve()))

import faultline_trace as ft  # noqa: E402

from faultline_spectrum import (  # noqa: E402
    build_map,
    build_report,
    context_integrity_detect,
    fault_cards,
    is_correct,
    loop_detect,
    run_batch,
    score_f5,
    score_f6,
    semantic_escapes,
)
from faultline_spectrum.experiment import f5_specs, f6_specs, q2_split_hypothesis  # noqa: E402

EVIDENCE = ROOT / "evidence"
SEED = 20260721


def _dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, sort_keys=True, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8")


def _traced_batch(specs, family):
    """Run a batch and emit a Day-4 trace (one span per run) + per-run verdicts."""
    obs, truth = run_batch(specs, SEED, n_runs=8)
    tracer = ft.Tracer(SEED)
    rows = []
    for o in obs:
        e = truth.entries[o.seq]
        rr = o.result
        with tracer.span(f"run.{o.seq}", "agent",
                         payload={"seq": o.seq, "steps": rr.steps_used}) as h:
            h.set_output({"completed": rr.completed, "final": rr.final})
        rows.append({
            "seq": o.seq, "injected": e.mode or "clean",
            "result": rr.to_dict(),
            "loop_detected": loop_detect(rr).fired,
            "context_integrity_violation": context_integrity_detect(rr).fired,
            "oracle_correct": is_correct(rr),
        })
    conf = (score_f5 if family == "F5" else score_f6)(obs, truth)
    return {"seed": SEED, "family": family,
            "confusion_vs_injection_truth": conf.to_dict(),
            "verdicts": rows, "trace": tracer.to_dict()}


def main() -> None:
    EVIDENCE.mkdir(exist_ok=True)
    report = build_report(seed=SEED)
    det_map = build_map()

    _dump(EVIDENCE / "fault_cards.json", {"cards": fault_cards()})
    _dump(EVIDENCE / "spectrum_report.json", report)
    _dump(EVIDENCE / "deterministic_vs_semantic_map.json", det_map)
    _dump(EVIDENCE / "q2_split_hypothesis.json", report["q2_split_hypothesis"])

    obs5, truth5 = run_batch(f5_specs(), SEED, n_runs=8)
    _dump(EVIDENCE / "escape_examples.json", {
        "note": "F5 context_drift: coherent, well-formed, consistent — yet wrong. "
                "Passed every deterministic/consistency check; only the oracle "
                "catches it. Isolated here as REQUIRING semantic evaluation.",
        "f5_consistency_confusion": score_f5(obs5, truth5).to_dict(),
        "escapes": semantic_escapes(obs5, truth5),
    })

    _dump(EVIDENCE / "trace_f5_context.json", _traced_batch(f5_specs(), "F5"))
    _dump(EVIDENCE / "trace_f6_loop.json", _traced_batch(f6_specs(), "F6"))

    h = report["headline"]
    print("Day 11 evidence written:")
    print(f"  F6 loop recall (deterministic) : {h['f6_loop_recall']}  escapes={h['f6_escapes']}")
    print(f"  F5 consistency recall          : {h['f5_consistency_recall']}")
    print(f"  F5 semantic escape kinds       : {h['f5_semantic_escape_kinds']}")
    print(f"  fully deterministic faults     : {det_map['fully_deterministic_recall_1_no_escape']}")
    print(f"  require semantic evaluation    : {det_map['require_semantic_evaluation']}")
    print(f"  separation holds               : {h['separation_holds']}")


if __name__ == "__main__":
    main()
