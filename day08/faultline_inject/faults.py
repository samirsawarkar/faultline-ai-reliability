"""The WHAT and HOW MUCH — mode + severity turned into a deterministic effect.

Each mode is a pure transform of the boundary's *clean* output into its *faulted*
output; `severity` (1..5) scales the magnitude on a fixed, documented schedule so
"severity 4 corrupt" means the same thing on every machine and in every replay.

Two invariants the tests pin down:
  * Determinism: `apply_fault` is a pure function of (mode, severity, clean
    output). No RNG, no clock.
  * No self-labelling: a faulted output NEVER contains the ground-truth label or
    any "this is a fault" marker. Corruption looks like a plausible-but-wrong
    value, a drop looks like an empty-but-well-formed result. The truth lives
    only in the out-of-band GroundTruthLog (see truth.py). This is what keeps a
    downstream detector honest — it cannot read the answer off the sample.
"""
from __future__ import annotations

import copy
import math
from typing import Any, Dict, Optional, Tuple


class InjectedFaultError(RuntimeError):
    """Raised by the `error` mode: a hard boundary failure, injected on purpose.

    The message is deliberately generic (no label, no severity word a detector
    could key on) so that `error` faults are not trivially distinguishable from
    organic failures by string-matching the exception.
    """


def _first_numeric_key(d: Dict[str, Any]) -> Optional[str]:
    for k, v in d.items():
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return k
    return None


def _first_list_key(d: Dict[str, Any]) -> Optional[str]:
    for k, v in d.items():
        if isinstance(v, list):
            return k
    return None


def apply_fault(mode: str, severity: int, clean: Dict[str, Any]
                ) -> Tuple[Dict[str, Any], int]:
    """Return (faulted_output, cost_units). Raises InjectedFaultError for `error`.

    `cost_units` is a side-channel cost (the `stall` mode's only observable
    effect); it is 0 for every content-mutating mode. Content faults never touch
    cost, and the cost fault never touches content — so the two observation
    channels are independent, which the no-leakage argument leans on.
    """
    if mode == "error":
        raise InjectedFaultError("boundary call did not complete")

    out = copy.deepcopy(clean)

    if mode == "stall":
        # Output content is IDENTICAL to clean; only the cost meter moves.
        return out, severity * 10

    if mode == "corrupt":
        k = _first_numeric_key(out)
        if k is not None:
            # A plausible-but-wrong value: a fixed offset, not a random one.
            out[k] = out[k] + severity * 111
        return out, 0

    if mode == "drop":
        lk = _first_list_key(out)
        if lk is not None:
            out[lk] = []
        nk = _first_numeric_key(out)
        if nk is not None:
            out[nk] = 0
        return out, 0

    if mode == "truncate":
        lk = _first_list_key(out)
        if lk is not None and out[lk]:
            keep = math.ceil(len(out[lk]) * (1.0 - 0.15 * severity))
            keep = max(0, min(len(out[lk]) - 1, keep))  # always drop >= 1 element
            out[lk] = out[lk][:keep]
        return out, 0

    if mode == "duplicate":
        lk = _first_list_key(out)
        if lk is not None and out[lk]:
            n = min(severity, len(out[lk]))
            out[lk] = out[lk][:n] + out[lk]
        return out, 0

    raise ValueError(f"unknown mode {mode!r}")
