"""Regenerate Day 15 evidence (deterministic; byte-reproducible in CI).

Writes under day15/evidence/:
  q2_results.json     per-class confusion + Wilson intervals + groups + no-hiding
                      reconciliation, for the full labelled set AND the test split
  q2_failures.json    every false positive / false negative, with why + observable
  Q2_FINDINGS.md      the Q2 tables with links to each failing example
  traces/<id>.json    one Day-4 trace per failing sample
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in ("", "../day04", "../day08", "../day09", "../day10", "../day11", "../day13", "../day14"):
    sys.path.insert(0, str((ROOT / rel).resolve()))

from faultline_q2 import build_report, collect_failures, render_q2_markdown, run_outcomes  # noqa: E402

EVIDENCE = ROOT / "evidence"
TRACES = EVIDENCE / "traces"


def _dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, sort_keys=True, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8")


def main() -> None:
    EVIDENCE.mkdir(exist_ok=True)
    TRACES.mkdir(exist_ok=True)

    report_all = build_report(split="all")
    report_test = build_report(split="test")
    _dump(EVIDENCE / "q2_results.json", {"full_labelled_set": report_all, "held_out_test": report_test})

    outcomes = run_outcomes(split="all")
    failures = collect_failures(outcomes)
    # per-failure trace files; the failures index references them by path
    for f in failures:
        _dump(TRACES / f"{f['sample_id']}.json",
              {k: f[k] for k in ("sample_id", "modality", "kind", "severity", "seed",
                                 "outcome", "why", "observable", "trace")})
    _dump(EVIDENCE / "q2_failures.json", {
        "dataset_version": report_all["dataset_version"],
        "false_positives": report_all["no_hiding"]["total_false_positives"],
        "false_negatives": report_all["no_hiding"]["total_false_negatives"],
        "fn_taxonomy": report_all["no_hiding"]["fn_taxonomy"],
        "failures": [{k: f[k] for k in ("sample_id", "modality", "kind", "severity",
                                        "seed", "outcome", "why", "observable",
                                        "trace_artifact")} for f in failures],
    })
    (EVIDENCE / "Q2_FINDINGS.md").write_text(
        render_q2_markdown(report_all, failures), encoding="utf-8")

    r = report_all
    print("Day 15 evidence written:")
    print(f"  dataset_version   : {r['dataset_version']}  (n={r['n_samples']}, full set)")
    print(f"  per-class recall  : "
          f"{ {m: c['recall'] for m, c in r['per_class_confusion'].items()} }")
    print(f"  micro / macro     : {r['aggregation_warning']['micro_recall']} / "
          f"{r['aggregation_warning']['macro_recall']}")
    print(f"  false positives   : {r['no_hiding']['total_false_positives']}")
    print(f"  false negatives   : {r['no_hiding']['total_false_negatives']} "
          f"({r['no_hiding']['fn_taxonomy']})")
    print(f"  reconciled        : {r['no_hiding']['reconciled']}")


if __name__ == "__main__":
    main()
