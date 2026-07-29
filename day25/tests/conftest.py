"""Day-25 import paths and one replay-backed report fixture."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for rel in ("day25", "day04"):
    path = str(ROOT / rel)
    if path not in sys.path:
        sys.path.insert(0, path)


@pytest.fixture(scope="session")
def postmortem_report():
    from faultline_postmortem import build_report

    return build_report(repetitions=4, include_cross_process=True)
