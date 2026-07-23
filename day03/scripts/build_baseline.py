"""Build the committed baseline: baseline.json + success_vs_hops.svg.

Runs the full config (500 tasks/tier by default) and writes both artifacts. Re-
running with the committed config MUST reproduce byte-identical files — that is
the Day-3 pass/fail condition, enforced by CI (`git diff --exit-code`).
"""
import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401

from faultline_baseline import BaselineConfig, build_baseline, render_success_vs_hops

EVIDENCE = Path(__file__).resolve().parents[1] / "evidence"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=None, help="override n_per_tier")
    args = ap.parse_args()

    config = BaselineConfig(n_per_tier=args.n) if args.n else BaselineConfig()
    baseline, _records = build_baseline(config)

    # Canonical JSON: sorted keys + trailing newline -> stable diffs.
    baseline_json = json.dumps(baseline.model_dump(mode="json"),
                               indent=2, sort_keys=True) + "\n"
    (EVIDENCE / "baseline.json").write_text(baseline_json)

    svg = render_success_vs_hops(baseline.success_vs_hops, config)
    (EVIDENCE / "success_vs_hops.svg").write_text(svg)

    print(f"master_seed={config.master_seed}  n_per_tier={config.n_per_tier}  "
          f"step_cap={config.step_cap}")
    print(f"content_hash={baseline.content_hash}\n")
    hdr = f"{'tier':<8}{'n':>5}{'succ':>6}{'rate':>8}{'wilson 95% CI':>22}{'steps':>7}{'cost$':>9}{'lat_ms':>9}"
    print(hdr)
    print("-" * len(hdr))
    for t in baseline.tiers:
        ci = f"[{t.wilson_low:.3f}, {t.wilson_high:.3f}]"
        print(f"{t.tier.value:<8}{t.n:>5}{t.successes:>6}{t.success_rate:>8.3f}"
              f"{ci:>22}{t.steps_mean:>7.1f}{t.cost_usd_mean:>9.4f}{t.latency_ms_mean:>9.1f}")
    print(f"\nwrote {(EVIDENCE / 'baseline.json').relative_to(EVIDENCE.parents[2])}")
    print(f"wrote {(EVIDENCE / 'success_vs_hops.svg').relative_to(EVIDENCE.parents[2])}")


if __name__ == "__main__":
    main()
