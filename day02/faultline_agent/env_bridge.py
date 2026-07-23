"""Consume Day 1's frozen, deterministic environment as Day 2's ground truth.

Day 2 does not re-implement the corpus. It imports Day 1's `build_env` so the
agent is exercised against the exact same seeded environment the oracle was
built for. Coupling here is intentional and one-directional (Day 2 -> Day 1).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

_DAY1 = Path(__file__).resolve().parents[2] / "day01"
if str(_DAY1) not in sys.path:
    sys.path.insert(0, str(_DAY1))

from faultline import build_env  # noqa: E402  (path set above)


def load_env(seed: int) -> Dict[str, Any]:
    return build_env(seed)
