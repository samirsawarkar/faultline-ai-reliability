"""Trace audits — the definition of 'no failure without a complete error span'.

`audit_failed_trace` is the checker the forced-failure experiment and its test
both call. It encodes the mission's fail condition as an assertion.
"""
from __future__ import annotations

from typing import List

from .schema import Span, assert_links_intact, is_complete, is_complete_error


class IncompleteTraceError(AssertionError):
    """A failure was recorded without a complete error span."""


def _by_id(spans: List[Span]):
    return {s.span_id: s for s in spans}


def audit_failed_trace(spans: List[Span]) -> dict:
    """Assert that a trace which ended in failure honours the guarantee.

    Requirements:
      1. Links intact, exactly one root.
      2. NO span left open (every span has end_seq).
      3. At least one complete error span exists.
      4. The error propagates: from every error leaf up to the root, the whole
         ancestor chain is complete error spans (a failure is never silently
         swallowed inside the trace).
    """
    assert_links_intact(spans)

    open_spans = [s.span_id for s in spans if s.end_seq is None]
    if open_spans:
        raise IncompleteTraceError(f"open spans left after failure: {open_spans}")

    error_spans = [s for s in spans if s.status == "error"]
    if not error_spans:
        raise IncompleteTraceError("failure occurred but no error span recorded")

    for s in error_spans:
        if not is_complete_error(s):
            raise IncompleteTraceError(f"span {s.span_id} is an incomplete error span")

    # Error propagation up the ancestor chain.
    by_id = _by_id(spans)
    children_error = {s.parent_span_id for s in error_spans}
    leaves = [s for s in error_spans if s.span_id not in children_error]
    for leaf in leaves:
        node = leaf
        while node is not None:
            if not is_complete_error(node):
                raise IncompleteTraceError(
                    f"ancestor {node.span_id} of failing {leaf.span_id} is not a complete error span"
                )
            node = by_id.get(node.parent_span_id) if node.parent_span_id else None

    return {
        "spans": len(spans),
        "error_spans": len(error_spans),
        "open_spans": 0,
        "complete": True,
    }


def audit_ok_trace(spans: List[Span]) -> dict:
    """A successful trace: links intact, all spans complete and 'ok'."""
    assert_links_intact(spans)
    for s in spans:
        if not is_complete(s):
            raise IncompleteTraceError(f"span {s.span_id} incomplete")
        if s.status != "ok":
            raise IncompleteTraceError(f"span {s.span_id} status {s.status!r}, expected ok")
    return {"spans": len(spans), "error_spans": 0, "open_spans": 0, "complete": True}
