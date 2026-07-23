#!/usr/bin/env python3
"""Capture a run, replay it, and print the difference (should be zero).

    python scripts/replay_demo.py                 # simulator: exact
    python scripts/replay_demo.py --provider flaky # real-provider stand-in
    python scripts/replay_demo.py --bundle evidence/bundle_simulator.json
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from faultline_replay import capture_run, diff_summary, load, replay_bundle  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", default="simulator", choices=["simulator", "flaky"])
    ap.add_argument("--bundle", type=str, help="replay an existing bundle file")
    ap.add_argument("--seed", type=int, default=6)
    args = ap.parse_args()

    if args.bundle:
        bundle = load(args.bundle)
        print(f"loaded bundle: {args.bundle} (provider={bundle['provider']})")
    else:
        bundle = capture_run(args.provider, args.seed, "sum the archive")
        print(f"captured live run (provider={args.provider}, seed={args.seed})")

    replayed = replay_bundle(bundle)
    d = diff_summary(bundle["trace"], replayed["trace"])
    print(f"replay vs captured trace: equal={d['equal']} diff_count={d['diff_count']}")
    print(f"calls replayed: {replayed['calls_consumed']}")

    if args.provider == "flaky" and not args.bundle:
        reexec = capture_run("flaky", args.seed, "sum the archive")
        rd = diff_summary(bundle["trace"], reexec["trace"])
        print(f"\nlive RE-EXECUTION vs captured: equal={rd['equal']} "
              f"diff_count={rd['diff_count']}  <- real providers cannot reproduce")
    return 0 if d["equal"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
