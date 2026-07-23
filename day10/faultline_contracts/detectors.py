"""Mixed, deterministic detectors + the classifier that defines the boundaries.

Three cheap detectors, layered from most to least explicit:

  provider_error_detect  the call raised an explicit error -> unambiguous.
  schema (Day 9)         the output is malformed -> structural.
  invariant_detect       the output breaks a SEMANTIC invariant that is weaker
                         than the oracle (here: "value is a round ten"). It
                         catches *some* schema-valid corruption, never all of it.

`classify` composes them into one label per call. The classes it can emit define
the CLASSIFIER BOUNDARY: PROVIDER_ERROR, MALFORMED, and INVARIANT_VIOLATION are
separable from observables; a schema-valid, invariant-respecting, non-erroring
output is classified OK even when it is wrong. That last case is exactly the
false negative this mission refuses to hide — `classify` cannot and does not
pretend to detect it. Only the oracle (truth layer) knows it is wrong.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional

_DAY9 = Path(__file__).resolve().parents[2] / "day09"
if str(_DAY9) not in sys.path:
    sys.path.insert(0, str(_DAY9))

from faultline_detect.schema import validate_output  # noqa: E402

# Classifier boundary — the only labels a deterministic classifier can emit.
OK = "ok"
PROVIDER_ERROR = "provider_error"
MALFORMED = "malformed"
INVARIANT_VIOLATION = "invariant_violation"
CLASSES = (OK, PROVIDER_ERROR, MALFORMED, INVARIANT_VIOLATION)

# The semantic invariant(s) beyond the schema. Kept deliberately partial: a
# stronger invariant tying every field to the request would just be the oracle.
def _value_is_round_ten(out: dict) -> bool:
    v = out.get("value")
    return isinstance(v, int) and not isinstance(v, bool) and v % 10 == 0


@dataclass(frozen=True)
class InvariantSignal:
    ok: bool
    violated: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"ok": self.ok, "violated": list(self.violated)}


def invariant_detect(output: Any) -> InvariantSignal:
    """Check semantic invariants that a schema does not enforce."""
    if not isinstance(output, dict):
        return InvariantSignal(ok=False, violated=["not_object"])
    violated: List[str] = []
    if not _value_is_round_ten(output):
        violated.append("value_not_round_ten")
    return InvariantSignal(ok=not violated, violated=violated)


def provider_error_detect(raised: bool) -> bool:
    """The explicit signal: did the provider hand back an error instead of a value."""
    return bool(raised)


def classify(raised: bool, output: Any) -> str:
    """The mixed classifier. Precedence: explicit error > malformed > invariant."""
    if provider_error_detect(raised):
        return PROVIDER_ERROR
    if validate_output(output):            # non-empty violation list => malformed
        return MALFORMED
    if not invariant_detect(output).ok:
        return INVARIANT_VIOLATION
    return OK


def detected_faulty(cls: str) -> bool:
    """A class other than OK means the classifier flagged the call."""
    return cls != OK
