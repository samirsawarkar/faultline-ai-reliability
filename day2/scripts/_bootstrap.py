"""Shared path + helpers for the Day-2 scripts."""
import sys
from pathlib import Path

_DAY2 = Path(__file__).resolve().parents[1]
if str(_DAY2) not in sys.path:
    sys.path.insert(0, str(_DAY2))


def entity_names(env):
    suffixes = ("Labs", "Works", "Foundry", "Collective", "Systems", "Union")
    return [d["title"] for d in env["documents"] if d["title"].endswith(suffixes)]
