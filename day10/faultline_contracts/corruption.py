"""F3 corruptions (WHAT goes wrong) + the F4 provider-error signal.

Each F3 corruption is a pure, deterministic transform of the clean output. Two
are malformed (they break the Day-9 schema); three are SCHEMA-VALID but wrong —
they return a well-typed object that a contract validator happily accepts. Those
three are the whole point of the mission, so the code makes their validity
explicit and testable.

Severity scales magnitude but — unlike Day 9's F1/F2 — does NOT change
detectability for the schema-valid kinds: a big wrong-but-valid value is exactly
as invisible to the schema as a small one. That invariance is a finding, not an
oversight (see LEARN-semantic-invariants.md).
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any, Dict

_DAY9 = Path(__file__).resolve().parents[2] / "day9"
if str(_DAY9) not in sys.path:
    sys.path.insert(0, str(_DAY9))

from faultline_detect.schema import TOKENS_LEN, VALUE_MAX, VALUE_MIN  # noqa: E402

_MULTIPLES = list(range(VALUE_MIN, VALUE_MAX + 1, 10))   # the legal round tens


class ProviderError(RuntimeError):
    """F4: an explicit provider failure envelope (a 5xx-style hard error).

    Carries a code so a classifier can be shown to key on the explicit signal,
    not on any content (there is no content — the call did not return a value).
    """
    def __init__(self, code: str = "provider_unavailable"):
        super().__init__(f"provider error: {code}")
        self.code = code


def apply_corruption(kind: str, severity: int, clean: Dict[str, Any]) -> Dict[str, Any]:
    """Return the corrupted output for an F3 `kind`. Raises for unknown kinds."""
    out = copy.deepcopy(clean)

    if kind == "malformed_range":
        # value pushed clearly out of the schema range -> schema catches it.
        out["value"] = VALUE_MAX + 10 * severity
        return out

    if kind == "malformed_tokens":
        # wrong-length token list -> schema catches it.
        keep = max(0, TOKENS_LEN - severity)
        out["tokens"] = out["tokens"][:keep]
        return out

    if kind == "nonmultiple":
        # in-range but NOT a round ten -> passes schema, fails the value invariant.
        out["value"] = out["value"] + severity          # severity 1..5 -> last digit != 0
        return out

    if kind == "drift_value":
        # a DIFFERENT legal round ten, in range -> passes schema AND the value
        # invariant, yet is wrong. This is a pure escape.
        base = out["value"]
        others = [m for m in _MULTIPLES if m != base]
        out["value"] = others[(base // 10 + severity) % len(others)]
        return out

    if kind == "offbase_tokens":
        # a shifted-but-still-consecutive run -> passes schema and every value
        # invariant (value untouched), yet the tokens are wrong. Another escape.
        out["tokens"] = [t + severity for t in out["tokens"]]
        return out

    raise ValueError(f"unknown F3 kind {kind!r}")
