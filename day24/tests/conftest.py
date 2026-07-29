"""Day-24 import paths and one shared measured report fixture."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for rel in ("day24", "day14", "day23"):
    path = str(ROOT / rel)
    if path not in sys.path:
        sys.path.insert(0, path)


@pytest.fixture(scope="session")
def q5_report():
    from faultline_q5 import build_report

    return build_report()
