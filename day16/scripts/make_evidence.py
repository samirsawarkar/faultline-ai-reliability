"""Regenerate Day 16 evidence (deterministic; byte-reproducible in CI).

Writes under day16/evidence/:
  judge_rubric.md       the narrow fallback-quality rubric
  validation_set.json   the blinded human-labelled set (+ second rater)
  agreement_report.json agreement + Cohen's kappa + positional bias + slices + verdict
  JUDGE_CARD.md         the judge card; forbids the judge from core success scoring
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in ("", "../day14"):
    sys.path.insert(0, str((ROOT / rel).resolve()))

from faultline_judge import RUBRIC_TEXT, build_report, items, judge_card  # noqa: E402

EVIDENCE = ROOT / "evidence"


def _dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, sort_keys=True, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8")


def main() -> None:
    EVIDENCE.mkdir(exist_ok=True)
    report = build_report()

    (EVIDENCE / "judge_rubric.md").write_text(RUBRIC_TEXT, encoding="utf-8")
    _dump(EVIDENCE / "validation_set.json", {
        "n": len(items()),
        "note": "trusted human labels, hand-authored by applying the rubric strictly; "
                "the judge never sees these. rater_b is a second human for inter-rater kappa.",
        "items": items(),
    })
    _dump(EVIDENCE / "agreement_report.json", report)
    (EVIDENCE / "JUDGE_CARD.md").write_text(judge_card(report), encoding="utf-8")

    jvh = report["judge_vs_human"]
    print("Day 16 evidence written:")
    print(f"  judge vs human   : agreement {jvh['raw_agreement']} "
          f"(CI {jvh['raw_agreement_ci95']}), kappa {jvh['cohen_kappa']} ({jvh['kappa_label']})")
    print(f"  human ceiling    : kappa {report['human_ceiling_inter_rater']['cohen_kappa']}")
    print(f"  failure slices   : {report['failure_slices']}")
    print(f"  positional bias  : {report['positional_bias']['judge_under_test']['positional_bias_rate']} "
          f"(close pairs {report['positional_bias']['judge_under_test']['by_kind']['close']['bias_rate']})")
    print(f"  validated stand. : {report['verdict']['validated_for_standalone_use']}")
    print(f"  forbidden core   : {report['verdict']['forbidden_from_core_success_scoring']}")


if __name__ == "__main__":
    main()
