"""Assemble the Day-26 audit report and Checkpoint 26."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "day26"))

from faultline_repro import build_report, render_checkpoint  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-missing-container", action="store_true")
    args = parser.parse_args()
    report = build_report(require_container=not args.allow_missing_container)
    evidence = ROOT / "day26/evidence"
    evidence.mkdir(exist_ok=True)
    (evidence / "reproduction_report.json").write_text(
        json.dumps(report, sort_keys=True, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (evidence / "CHECKPOINT-26.md").write_text(
        render_checkpoint(report), encoding="utf-8"
    )
    if not report["checkpoint_26"]["passed"]:
        raise SystemExit("Checkpoint 26 failed")
    print(
        f"Checkpoint 26 green; "
        f"release={report['checkpoint_26']['release_candidate']}"
    )


if __name__ == "__main__":
    main()
