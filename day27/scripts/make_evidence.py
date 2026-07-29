"""Assemble the stable Day-27 report and rendered checkpoint."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "day27"))

from faultline_cold_repro import build_report, render_checkpoint  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-missing-peer", action="store_true")
    args = parser.parse_args()
    report = build_report(require_peer=not args.allow_missing_peer)
    evidence = ROOT / "day27/evidence"
    evidence.mkdir(exist_ok=True)
    (evidence / "checkpoint_27.json").write_text(
        json.dumps(report["checkpoint_27"], sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (evidence / "reproduction_audit.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (evidence / "CHECKPOINT-27.md").write_text(
        render_checkpoint(report), encoding="utf-8"
    )
    if not report["checkpoint_27"]["passed"]:
        raise SystemExit("Checkpoint 27 failed")
    print("Checkpoint 27 green")


if __name__ == "__main__":
    main()
