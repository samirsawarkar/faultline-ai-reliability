"""Expose the Day 28 package from an isolated per-day test run."""
import sys
from pathlib import Path

DAY = Path(__file__).resolve().parents[1]
if str(DAY) not in sys.path:
    sys.path.insert(0, str(DAY))
