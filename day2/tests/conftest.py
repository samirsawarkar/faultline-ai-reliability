import sys
from pathlib import Path

# Make `faultline_agent` importable when pytest is run from anywhere.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def entities(env, k=None):
    """Entity display names in deterministic corpus order (fact docs only)."""
    suffixes = ("Labs", "Works", "Foundry", "Collective", "Systems", "Union")
    names = [d["title"] for d in env["documents"] if d["title"].endswith(suffixes)]
    return names if k is None else names[:k]
