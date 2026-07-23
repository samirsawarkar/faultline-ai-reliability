"""Span schema — the essential fields every recorded operation carries.

Design stance (see SPAN_SCHEMA.md):
  * A span is the record of ONE risky operation. It is created the moment the
    operation begins and mutated in place as it ends, so a span always exists
    even if the operation crashes before returning.
  * Payloads are never embedded raw. A span holds a PayloadRef (content hash +
    size + redacted preview) produced by the redaction policy. See REDACTION.md.
  * Times are a logical monotonic sequence (start_seq / end_seq), not wall clock,
    so traces are byte-reproducible and orderable without a real clock.

'Complete span' is defined precisely by `is_complete`; 'complete error span'
(the mission's fail condition target) by `is_complete_error`.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Enumerations kept as plain str sets: cheap to validate, trivial to serialize.
KINDS = ("agent", "model", "tool")
STATUSES = ("unset", "ok", "error")


@dataclass
class PayloadRef:
    """A reference to a payload, never the payload itself.

    sha256/size/preview are all derived from the *redacted* canonical form, so
    nothing sensitive is recoverable from a span, and the ref is stable.
    """
    sha256: str
    size_bytes: int
    preview: str
    redacted: bool


@dataclass
class SpanError:
    """Captured failure. `message` has already passed the redaction policy."""
    type: str
    message: str


@dataclass
class Span:
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    name: str
    kind: str                       # one of KINDS
    start_seq: int                  # logical clock at entry (always set)
    end_seq: Optional[int] = None   # logical clock at exit (None => still open)
    status: str = "unset"           # one of STATUSES
    error: Optional[SpanError] = None
    attributes: Dict[str, str] = field(default_factory=dict)
    input_ref: Optional[PayloadRef] = None
    output_ref: Optional[PayloadRef] = None

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


def is_complete(span: Span) -> bool:
    """A span is complete iff it was both opened and closed with a terminal
    status. An open span (end_seq is None / status 'unset') is an incomplete
    record and, for a failed operation, a mission failure."""
    return (
        span.start_seq is not None
        and span.end_seq is not None
        and span.end_seq >= span.start_seq
        and span.status in ("ok", "error")
    )


def is_complete_error(span: Span) -> bool:
    """The record a failure MUST leave behind: complete, status 'error', with a
    non-empty error type and message."""
    return (
        is_complete(span)
        and span.status == "error"
        and span.error is not None
        and bool(span.error.type)
        and bool(span.error.message)
    )


def validate_span(span: Span) -> None:
    """Structural validation. Raises ValueError on any schema violation."""
    if not span.trace_id:
        raise ValueError("span.trace_id is required")
    if not span.span_id:
        raise ValueError("span.span_id is required")
    if not span.name:
        raise ValueError("span.name is required")
    if span.kind not in KINDS:
        raise ValueError(f"span.kind {span.kind!r} not in {KINDS}")
    if span.status not in STATUSES:
        raise ValueError(f"span.status {span.status!r} not in {STATUSES}")
    if span.start_seq is None:
        raise ValueError("span.start_seq is required (span must record its entry)")
    if span.status == "error" and span.error is None:
        raise ValueError("error span must carry a SpanError")
    if span.parent_span_id == span.span_id:
        raise ValueError("span cannot be its own parent")


def assert_links_intact(spans: List[Span]) -> None:
    """Every non-root parent_span_id must resolve to a span in the same trace,
    and there is exactly one root (parent_span_id is None)."""
    ids = {s.span_id for s in spans}
    roots = [s for s in spans if s.parent_span_id is None]
    if len(roots) != 1:
        raise ValueError(f"expected exactly one root span, found {len(roots)}")
    for s in spans:
        if s.parent_span_id is not None and s.parent_span_id not in ids:
            raise ValueError(f"span {s.span_id} references missing parent {s.parent_span_id}")
