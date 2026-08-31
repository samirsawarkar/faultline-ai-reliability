"""Expose Day 29 and its Day 25 replay dependency."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for relative in ("day29", "day25", "day04"):
    path = str(ROOT / relative)
    if path not in sys.path:
        sys.path.insert(0, path)
