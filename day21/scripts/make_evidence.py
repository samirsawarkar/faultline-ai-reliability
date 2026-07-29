"""Regenerate Day 21's deterministic Q4 evidence."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in ("", "../day01", "../day14", "../day16", "../day20"):
    sys.path.insert(0, str((ROOT / rel).resolve()))

from faultline_fallback_quality import build_report, render_findings  # noqa: E402

EVIDENCE = ROOT / "evidence"


def _dump(path: Path, obj) -> None:
    path.write_text(
        json.dumps(obj, sort_keys=True, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    EVIDENCE.mkdir(exist_ok=True)
    report = build_report()
    _dump(
        EVIDENCE / "availability_quality_comparison.json",
        {
            "params": report["params"],
            "metric_definitions": report["metric_definitions"],
            "comparison": report["comparison"],
            "fail_condition_guard": report["fail_condition_guard"],
        },
    )
    _dump(EVIDENCE / "degradation_detector.json", report["degradation_detector"])
    _dump(
        EVIDENCE / "silent_degradation_attack.json",
        {
            **report["silent_degradation_attack"],
            "evidence_sample": report["evidence_sample"],
        },
    )
    (EVIDENCE / "Q4_FINDINGS.md").write_text(
        render_findings(report), encoding="utf-8"
    )

    effects = report["comparison"]["effects"]
    detector = report["degradation_detector"]
    print("Day 21 evidence written:")
    print(
        "  availability gain "
        f"{effects['availability_gain']:+}; strict answer-quality change "
        f"{effects['strict_quality_given_answered_change']:+}"
    )
    print(
        "  detector TP/FN "
        f"{detector['confusion']['tp']}/{detector['confusion']['fn']}; "
        f"recall {detector['recall']['rate']}"
    )
    print(
        "  fail condition respected: "
        f"{report['fail_condition_guard']['passed']}"
    )


if __name__ == "__main__":
    main()
