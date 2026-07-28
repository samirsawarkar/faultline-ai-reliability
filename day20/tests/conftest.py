import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in ("", "../day04", "../day08", "../day09", "../day14"):
    sys.path.insert(0, str((ROOT / rel).resolve()))
