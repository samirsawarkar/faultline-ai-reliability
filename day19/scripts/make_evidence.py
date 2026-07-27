"""Regenerate Day 19 evidence (deterministic; byte-reproducible in CI).

Writes under day19/evidence/:
  retry_sweep.json     the full sweep (both scenarios): success+CI, cost, tail latency
  crossover.json       crossover + recommended region + fail-condition guard
  crossover_curve.svg  success (solid) vs p99 latency (dashed) by K, both scenarios
  q3_conclusion.json   the defensible recommended retry region + conclusion
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in ("", "../day08", "../day09", "../day14", "../day18"):
    sys.path.insert(0, str((ROOT / rel).resolve()))

from faultline_retry import build_report, render_svg  # noqa: E402

EVIDENCE = ROOT / "evidence"


def _dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, sort_keys=True, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8")


def main() -> None:
    EVIDENCE.mkdir(exist_ok=True)
    r = build_report()
    _dump(EVIDENCE / "retry_sweep.json",
          {"params": r["params"], "ceilings": r["ceilings"],
           "independent": r["sweep_independent"], "correlated": r["sweep_correlated"]})
    _dump(EVIDENCE / "crossover.json",
          {"independent": r["crossover_independent"], "correlated": r["crossover_correlated"],
           "fail_condition_guard": r["fail_condition_guard"],
           "paired_correlation_effect": r["paired_correlation_effect_at_recommended_K"]})
    (EVIDENCE / "crossover_curve.svg").write_text(
        render_svg(r["sweep_independent"], r["sweep_correlated"],
                   r["crossover_independent"]["recommended_max_attempts"]), encoding="utf-8")
    _dump(EVIDENCE / "q3_conclusion.json", r["q3_conclusion"])

    q = r["q3_conclusion"]
    print("Day 19 evidence written:")
    print(f"  recommended budget: independent K={q['recommended_region']['independent_max_attempts']}, "
          f"correlated K={q['recommended_region']['correlated_max_attempts']}")
    print(f"  crossover K: independent {q['crossover_K']['independent']}, correlated {q['crossover_K']['correlated']}")
    corr = r["sweep_correlated"]
    print(f"  correlated amplification 1x -> {max(p['amplification'] for p in corr)}x, "
          f"p99 {corr[0]['p99_latency']} -> {max(p['p99_latency'] for p in corr)}")
    print(f"  fail_condition_respected: {q['fail_condition_respected']}")


if __name__ == "__main__":
    main()
