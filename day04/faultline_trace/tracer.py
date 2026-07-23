"""Tracer — creates linked spans that survive failures.

The load-bearing guarantee (mission fail condition: 'a failure can occur
without a complete error span'):

    Every span is appended to the trace at ENTRY, and its end/status/error are
    set in a `finally`. So no matter how the body exits -- return, `raise`, or
    an exception thrown by a child that propagates through -- the span is left
    closed (end_seq set) with a terminal status, and a failing span is left as a
    complete error span. There is no code path that opens a span without closing
    it.

Determinism: one Tracer instance == one trace. IDs derive from the seed and a
counter; the clock is a logical monotonic sequence. Same seed + same calls =>
byte-identical trace. (Single trace is single-threaded by construction.)
"""
from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any, Iterator, List, Optional

from . import redaction
from .schema import Span, validate_span


class SpanHandle:
    """Handed to the `with` body so it can attach output and attributes.
    All values pass through the redaction policy before storage."""

    def __init__(self, span: Span):
        self._span = span

    def set_output(self, payload: Any) -> None:
        self._span.output_ref = redaction.reference(payload)

    def set_attribute(self, key: str, value: Any) -> None:
        # attributes are redacted strings; keep them small and safe
        self._span.attributes[str(key)] = redaction.redact(str(value))

    @property
    def span_id(self) -> str:
        return self._span.span_id


class Tracer:
    def __init__(self, seed: int):
        if not isinstance(seed, int):
            raise TypeError("seed must be int")
        self.seed = seed
        self.trace_id = f"trace-{seed:08d}"
        self.spans: List[Span] = []
        self._stack: List[Span] = []
        self._counter = 0
        self._clock = 0

    def _tick(self) -> int:
        self._clock += 1
        return self._clock

    def _next_id(self) -> str:
        sid = f"{self.trace_id}-span-{self._counter:04d}"
        self._counter += 1
        return sid

    @contextmanager
    def span(self, name: str, kind: str, payload: Any = None) -> Iterator[SpanHandle]:
        parent = self._stack[-1] if self._stack else None
        span = Span(
            trace_id=self.trace_id,
            span_id=self._next_id(),
            parent_span_id=parent.span_id if parent else None,
            name=name,
            kind=kind,
            start_seq=self._tick(),
        )
        if payload is not None:
            span.input_ref = redaction.reference(payload)
        # Record at ENTRY: the span exists before the risky body runs.
        self.spans.append(span)
        self._stack.append(span)
        try:
            yield SpanHandle(span)
        except BaseException as exc:  # noqa: BLE001 - we re-raise after recording
            span.status = "error"
            span.error = redaction.error_of(exc)
            raise
        finally:
            # Runs on EVERY exit path -> the span is never left open.
            if span.status == "unset":
                span.status = "ok"
            span.end_seq = self._tick()
            self._stack.pop()

    # --- serialization (deterministic) ---
    def to_dict(self) -> dict:
        for s in self.spans:
            validate_span(s)
        return {
            "trace_id": self.trace_id,
            "seed": self.seed,
            "span_count": len(self.spans),
            "spans": [s.to_dict() for s in self.spans],
        }

    def to_json(self) -> bytes:
        text = json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=True, indent=2)
        return (text + "\n").encode("utf-8")

    def open_spans(self) -> List[Span]:
        """Spans still open (end_seq is None). Must be empty after a trace ends;
        a non-empty result means a failure escaped without a closed span."""
        return [s for s in self.spans if s.end_seq is None]
