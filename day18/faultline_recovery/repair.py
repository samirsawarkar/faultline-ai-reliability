"""M1 — bounded schema repair-retry for invalid outputs (F1).

When a tool returns a schema-invalid structured output, we retry a bounded number
of times, re-validating each attempt against the Day-9 schema. A transient
corruption clears after a few attempts (recovered); a persistent one never clears
(exhausted — cleanly, within the budget). On success the result is committed once
through an idempotency ledger, so re-running the whole recovery is safe to repeat.

No LLM: the "repair" is modelled as a deterministic producer whose output becomes
valid after `clears_after` attempts. A real repair prompt slots in as the producer;
the bounding, budgeting, and idempotency are unchanged.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable, Optional, Tuple

_DAY09 = Path(__file__).resolve().parents[2] / "day09"
if str(_DAY09) not in sys.path:
    sys.path.insert(0, str(_DAY09))

from faultline_detect import validate_output  # noqa: E402 (Day 9 schema)

from .engine import RecoveryResult, run_bounded_retry
from .idempotency import IdempotencyLedger
from .policy import RetryPolicy

ATTEMPT_LATENCY = 5            # virtual cost of one produce+validate attempt

_CLEAN = {"step": "retrieve", "value": 10, "tokens": [0, 1, 2, 3]}
_CORRUPT = {"step": "retrieve", "value": 999, "tokens": [0, 1, 2, 3]}  # value out of range


def make_producer(clears_after: int) -> Callable[[int], Tuple[bool, int, Any]]:
    """attempt_fn: output is corrupt until attempt `clears_after`, then clean.
    clears_after > max_attempts models a PERSISTENT corruption (never clears)."""
    def attempt(i: int) -> Tuple[bool, int, Any]:
        out = dict(_CLEAN) if i >= clears_after else dict(_CORRUPT)
        valid = (validate_output(out) == [])
        return valid, ATTEMPT_LATENCY, out
    return attempt


def schema_repair_retry(clears_after: int, policy: RetryPolicy, *,
                        request_id: str = "req", ledger: Optional[IdempotencyLedger] = None
                        ) -> Tuple[RecoveryResult, Any]:
    """Run bounded repair-retry; commit a recovered output once via the ledger."""
    ledger = ledger if ledger is not None else IdempotencyLedger()
    result = run_bounded_retry(make_producer(clears_after), policy)
    committed = None
    if result.recovered:
        committed = ledger.execute(request_id, lambda: {"committed": request_id,
                                                        "output": result.payload})
    return result, committed
