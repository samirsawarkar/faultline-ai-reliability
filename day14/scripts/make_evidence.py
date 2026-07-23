"""Regenerate Day 14 evidence (deterministic; byte-reproducible in CI).

Writes under day14/evidence/:
  stats_verification.json  independent verification of every utility (all_passed)
  edge_cases.json          known cases + adversarial edge samples and their outputs
  paired_comparison.json   the grounded paired experiment (Wilson CIs + McNemar)
  INTERPRETATION.md        plain-English guide to reading intervals + McNemar
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in ("", "../day8", "../day9", "../day10"):
    sys.path.insert(0, str((ROOT / rel).resolve()))

from faultline_stats import (  # noqa: E402
    bootstrap_ci,
    build_report,
    interpret_interval,
    interpret_mcnemar,
    mcnemar_test,
    verify_all,
    wilson_interval,
)

EVIDENCE = ROOT / "evidence"


def _dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, sort_keys=True, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8")


def _edge_cases():
    return {
        "wilson": {
            "n=0 (no data)": list(wilson_interval(0, 0)),
            "0/1": [round(x, 4) for x in wilson_interval(0, 1)],
            "1/1 (p=1)": [round(x, 4) for x in wilson_interval(1, 1)],
            "0/10 (p=0)": [round(x, 4) for x in wilson_interval(0, 10)],
            "10/10 (p=1)": [round(x, 4) for x in wilson_interval(10, 10)],
            "1/1000 (tiny rate)": [round(x, 6) for x in wilson_interval(1, 1000)],
        },
        "bootstrap": {
            "degenerate all-ones (n=20)": list(bootstrap_ci([1.0] * 20, seed=0)),
            "single sample n=1": list(bootstrap_ci([1.0], seed=0)),
        },
        "mcnemar": {
            "no discordant (0,0)": {k: mcnemar_test(0, 0)[k] for k in ("p_value", "significant_at_0.05")},
            "symmetric (6,6)": {k: mcnemar_test(6, 6)[k] for k in ("p_value", "significant_at_0.05")},
            "one-sided small (0,6)": {k: mcnemar_test(0, 6)[k] for k in ("p_value", "recommended", "significant_at_0.05")},
            "large (30,5)": {k: mcnemar_test(30, 5)[k] for k in ("p_value", "recommended", "significant_at_0.05")},
        },
    }


INTERP = """# Interpreting FAULTLINE intervals and paired tests

A plain-English guide to reading the two things this project reports for every
comparison: a **confidence interval** on a rate, and a **McNemar test** on a paired
comparison.

## Confidence intervals (Wilson)

Every rate we report (a detector's recall, an accuracy) is an estimate from a
finite sample, so it comes with a **95% Wilson interval**. Read it like this:

- The point value (e.g. "recall 0.75") is the best single guess.
- The interval (e.g. "[0.65, 0.83]") is the range of true rates consistent with the
  data. **It is not a probability about this one interval**; it means a procedure
  that produces such intervals contains the truth 95% of the time.
- **Two rates whose intervals overlap are not distinguishable at this sample size.**
  A higher point estimate with an overlapping interval is not evidence of a real
  difference — collect more samples to narrow the bands.
- Smaller n → wider interval. At n=0 the interval is [0, 1]: no data, no claim.
- Wilson is used (not the normal approximation) because it stays inside [0, 1] and
  is correct at the extremes (p near 0 or 1) and for small n.

## Paired comparisons (McNemar)

To compare two systems fairly we run them on the **same seeded samples** (a paired
design). This cancels sample-to-sample difficulty, so the only evidence about a
difference lives in the **discordant pairs** — samples where exactly one system was
right.

- McNemar looks only at the two discordant counts (A-right/B-wrong and
  A-wrong/B-right). Pairs where both agree carry no information and are correctly
  ignored.
- Small discordant counts use the **exact binomial** p; larger counts use the
  continuity-corrected **chi-square**. We report both and mark which to trust.
- p < 0.05 means the difference is unlikely under "the two systems are equally
  good." **A significant McNemar result says the systems differ, not by how much** —
  pair it with the accuracy intervals to see the size.
- Watch the counts: 5 one-directional discordant pairs give p = 0.0625 (not
  significant); it takes 6 (p = 0.03125) to cross 0.05. Significance needs enough
  discordant evidence, not just a clean direction.

## The rule of thumb

Never report a bare number. Report the estimate, its interval, and — when comparing
— the paired test. A difference is only real if the paired test says so; a rate is
only precise if its interval is narrow.
"""


def main() -> None:
    EVIDENCE.mkdir(exist_ok=True)
    verification = verify_all()
    _dump(EVIDENCE / "stats_verification.json", verification)
    _dump(EVIDENCE / "edge_cases.json", _edge_cases())
    _dump(EVIDENCE / "paired_comparison.json", build_report())
    (EVIDENCE / "INTERPRETATION.md").write_text(INTERP, encoding="utf-8")

    rep = build_report()
    print("Day 14 evidence written:")
    print(f"  verification all_passed : {verification['all_passed']}")
    print(f"  paired A acc / CI       : {rep['system_a']['accuracy']} {rep['system_a']['wilson_ci95']}")
    print(f"  paired B acc / CI       : {rep['system_b']['accuracy']} {rep['system_b']['wilson_ci95']}")
    print(f"  McNemar p / significant : {rep['mcnemar']['p_value']:.2e} "
          f"/ {rep['mcnemar']['significant_at_0.05']}")


if __name__ == "__main__":
    main()
