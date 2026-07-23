"""Regenerate Day 10 evidence (deterministic; byte-reproducible in CI).

Writes under day10/evidence/:
  fault_cards.json           F3/F4 datasheets
  contract_report.json       detection vs injection truth, per-kind, severity
                             invariance, classifier boundaries, breaker
  false_negatives.json       the escape set: schema-valid semantic corruption that
                             is wrong (oracle) yet classified OK — with evidence
  classifier_boundaries.json which classes are separable and which are not
  trace_f3_mixed.json        a mixed F3 run as a Day-4 trace + per-call verdicts
  trace_f4_provider.json     a provider-error run as a Day-4 trace + breaker
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "day08"))
sys.path.insert(0, str(ROOT.parent / "day09"))
sys.path.insert(0, str(ROOT.parent / "day04"))

import faultline_trace as ft  # noqa: E402

from faultline_contracts import (  # noqa: E402
    build_report,
    classify,
    classifier_boundaries,
    escaped_false_negatives,
    fault_cards,
    oracle,
    run_breaker,
    run_contracts,
    score_detection,
)
from faultline_contracts.experiment import f3_specs, f4_specs  # noqa: E402

EVIDENCE = ROOT / "evidence"
SEED = 20260720


def _dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, sort_keys=True, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8")


def _verdict_rows(obs, truth):
    rows = []
    for o in obs:
        e = truth.entries[o.seq]
        rows.append({
            "seq": o.seq, "component": o.component,
            "injected": e.mode or "clean", "raised": o.raised,
            "output": o.output,
            "classifier_class": classify(o.raised, o.output),
            "oracle_correct": (not o.raised) and oracle.is_correct(
                o.component, o.payload, o.output),
        })
    return rows


def main() -> None:
    EVIDENCE.mkdir(exist_ok=True)

    _dump(EVIDENCE / "fault_cards.json", {"cards": fault_cards()})
    _dump(EVIDENCE / "contract_report.json", build_report(seed=SEED))
    _dump(EVIDENCE / "classifier_boundaries.json", classifier_boundaries())

    # F3 mixed run, fully traced (Day 4) + per-call verdicts + the escape set.
    tracer3 = ft.Tracer(SEED)
    obs3, truth3, _ = run_contracts(f3_specs(), SEED, tracer=tracer3)
    _dump(EVIDENCE / "false_negatives.json", {
        "scored_against": "day08 GroundTruthLog + day10 oracle",
        "note": "schema-valid semantic corruption: wrong per oracle, classified OK. "
                "Reported as MISSED, never as detected.",
        "f3_detection_confusion": score_detection(obs3, truth3, "F3").to_dict(),
        "escaped": escaped_false_negatives(obs3, truth3),
    })
    _dump(EVIDENCE / "trace_f3_mixed.json", {
        "seed": SEED, "family": "F3",
        "confusion_vs_injection_truth": score_detection(obs3, truth3, "F3").to_dict(),
        "verdicts": _verdict_rows(obs3, truth3),
        "trace": tracer3.to_dict(),
    })

    # F4 provider-error run, traced + circuit-breaker trace.
    tracer4 = ft.Tracer(SEED)
    obs4, truth4, ef4 = run_contracts(f4_specs(), SEED, tracer=tracer4)
    _dump(EVIDENCE / "trace_f4_provider.json", {
        "seed": SEED, "family": "F4",
        "confusion_vs_injection_truth": score_detection(obs4, truth4, "F4").to_dict(),
        "circuit_breaker": run_breaker(ef4).to_dict(),
        "verdicts": _verdict_rows(obs4, truth4),
        "trace": tracer4.to_dict(),
    })

    rep = build_report(seed=SEED)
    print("Day 10 evidence written:")
    print(f"  F3 wrong-data recall  : {rep['headline']['f3_wrong_data_recall']} "
          f"(precision {rep['headline']['f3_precision']})")
    print(f"  F3 escaped kinds      : {rep['headline']['f3_escaped_kinds']} "
          f"({rep['escape_count']} escapes)")
    print(f"  F4 provider recall    : {rep['headline']['f4_provider_error_recall']}")
    print(f"  circuit breaker opens : seq {rep['headline']['circuit_breaker_opened_at']}")
    print(f"  escape severity-inv.  : {rep['headline']['escape_is_severity_invariant']}")


if __name__ == "__main__":
    main()
