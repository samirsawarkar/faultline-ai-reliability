"""Import Day 2's agent as Day 3's measured subject.

Day 3 measures the *baseline* behavior of the Day-2 deterministic agent. It does
not re-implement the agent; it imports it, so the zero point is measured on the
exact code the earlier day froze. Coupling is one-directional (Day 3 -> Day 2).
"""
from __future__ import annotations

import sys
from pathlib import Path

_DAY2 = Path(__file__).resolve().parents[2] / "day2"
if str(_DAY2) not in sys.path:
    sys.path.insert(0, str(_DAY2))

from faultline_agent import (  # noqa: E402
    Agent,
    ArchiveSumTask,
    OutcomeStatus,
    load_env,
    verdict,
)

_SUFFIXES = ("Labs", "Works", "Foundry", "Collective", "Systems", "Union")


def entity_names(env) -> list:
    """Entity display names in deterministic corpus order (fact docs only)."""
    return [d["title"] for d in env["documents"] if d["title"].endswith(_SUFFIXES)]


__all__ = [
    "Agent",
    "ArchiveSumTask",
    "OutcomeStatus",
    "load_env",
    "verdict",
    "entity_names",
]
