"""Regenerate Day 17 evidence (deterministic; byte-reproducible in CI).

Writes under day17/evidence/:
  subgroup_report.json  the full sliced report (fault/severity/hops/outcome) + gate
  evaluation_audit.json the audit: no contradiction ignored, reversal detector verified
  SUBGROUP_FINDINGS.md  the findings, with known limitations up front
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in ("", "../day08", "../day09", "../day10", "../day11", "../day13", "../day14", "../day15"):
    sys.path.insert(0, str((ROOT / rel).resolve()))

from faultline_subgroups import build_report, render_findings, run_audit  # noqa: E402

EVIDENCE = ROOT / "evidence"


def _dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, sort_keys=True, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8")


def main() -> None:
    EVIDENCE.mkdir(exist_ok=True)
    report = build_report()
    audit = run_audit(report)

    _dump(EVIDENCE / "subgroup_report.json", report)
    _dump(EVIDENCE / "evaluation_audit.json", audit)
    (EVIDENCE / "SUBGROUP_FINDINGS.md").write_text(render_findings(report), encoding="utf-8")

    d = report["detection"]
    rev = d["deterministic_vs_semantic_reversal"]
    print("Day 17 evidence written:")
    print(f"  detection headline accuracy : {d['headline_rate']} (n={d['n']})")
    print(f"  contradictions detected     : {len(report['contradictions_detected'])} "
          f"(significant after Holm: {len(report['significant_contradictions'])})")
    print(f"  det-vs-sem reversal slices  : {[s['slice'] for s in rev['reversal_slices']]}")
    print(f"  hop headline fails at hops  : {[c['hops'] for c in report['hops'].get('headline_contradictions', [])]}")
    print(f"  measurement gate passed     : {report['measurement_gate']['passed']}")
    print(f"  evaluation audit passed     : {audit['audit_passed']}")


if __name__ == "__main__":
    main()
