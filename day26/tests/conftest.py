"""Day-26 package path."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
path = str(ROOT / "day26")
if path not in sys.path:
    sys.path.insert(0, path)
