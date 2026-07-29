"""Run the non-mutating Day-27 document and saved-evidence audit."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "day27"))

from faultline_cold_repro import build_report  # noqa: E402


def main() -> None:
    report = build_report(require_peer=True)
    if not report["checkpoint_27"]["passed"]:
        raise SystemExit("Checkpoint 27 audit failed")
    print("Day 27 audit green: cold reader required zero improvisations")


if __name__ == "__main__":
    main()
