"""Shared sys.path bootstrap for Day-3 scripts."""
import sys
from pathlib import Path

_DAY3 = Path(__file__).resolve().parents[1]
if str(_DAY3) not in sys.path:
    sys.path.insert(0, str(_DAY3))
