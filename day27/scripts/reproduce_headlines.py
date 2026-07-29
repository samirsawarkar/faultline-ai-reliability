"""Run inside the pinned image and print the verified headline results."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "day27"))

from faultline_cold_repro import (  # noqa: E402
    build_headline_result,
    render_headline_result,
)


def main() -> None:
    report = build_headline_result(run_generators=True)
    print(render_headline_result(report))
    if not report["passed"]:
        raise SystemExit("headline reproduction failed")


if __name__ == "__main__":
    main()
