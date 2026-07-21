import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in ("", "../day8", "../day9", "../day10"):
    sys.path.insert(0, str((ROOT / rel).resolve()))
