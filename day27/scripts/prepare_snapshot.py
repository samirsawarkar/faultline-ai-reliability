"""Create a tagged source snapshot containing the candidate worktree."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "day27"))

from faultline_cold_repro import prepare_snapshot  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination")
    args = parser.parse_args()
    destination = Path(args.destination).resolve()
    prepare_snapshot(destination)
    print(destination.as_uri())


if __name__ == "__main__":
    main()
