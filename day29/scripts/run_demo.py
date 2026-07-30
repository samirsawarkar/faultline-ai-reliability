"""Run the live compact Day 29 staff-engineer demo."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "day29"))

from faultline_brief.demo import build_demo, compact_screen  # noqa: E402


def main() -> None:
    print(compact_screen(build_demo()))


if __name__ == "__main__":
    main()
