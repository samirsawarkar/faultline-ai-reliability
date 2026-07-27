"""Idempotency ledger — makes retries SAFE TO REPEAT.

A retry (or a re-delivered request) that re-applies a side effect — a write, a
charge, a send — turns recovery into a NEW fault: the operation happens N times.
The ledger keys each logical operation by an idempotency key; the first execution
applies the side effect and records the result, and every repeat returns the cached
result WITHOUT re-applying the side effect. This is what makes bounded recovery
correct, not merely bounded.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict


@dataclass
class IdempotencyLedger:
    _results: Dict[str, Any] = field(default_factory=dict)
    side_effects: int = 0        # count of side effects ACTUALLY applied

    def execute(self, key: str, op: Callable[[], Any]) -> Any:
        if key in self._results:
            return self._results[key]        # replay — no side effect re-applied
        result = op()                        # first time only: side effect happens
        self.side_effects += 1
        self._results[key] = result
        return result

    def seen(self, key: str) -> bool:
        return key in self._results


@dataclass
class NaiveNoLedger:
    """The UNSAFE baseline: every call re-applies the side effect. Used only to
    show, by contrast, what the ledger prevents."""
    side_effects: int = 0

    def execute(self, key: str, op: Callable[[], Any]) -> Any:
        self.side_effects += 1
        return op()

    def seen(self, key: str) -> bool:
        return False
