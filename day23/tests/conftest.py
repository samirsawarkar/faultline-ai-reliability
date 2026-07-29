import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in ("", "../day04", "../day14", "../day16", "../day20", "../day21"):
    sys.path.insert(0, str((ROOT / rel).resolve()))
