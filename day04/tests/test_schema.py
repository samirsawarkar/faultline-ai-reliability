"""Span schema tests: validation and the completeness predicates."""
from __future__ import annotations

import pytest

from faultline_trace.schema import (
    Span,
    SpanError,
    is_complete,
    is_complete_error,
    validate_span,
)


def _span(**kw):
    base = dict(trace_id="t", span_id="s", parent_span_id=None,
                name="agent", kind="agent", start_seq=1)
    base.update(kw)
    return Span(**base)


def test_validate_rejects_bad_kind():
    with pytest.raises(ValueError):
        validate_span(_span(kind="wizard"))


def test_validate_rejects_error_status_without_error():
    with pytest.raises(ValueError):
        validate_span(_span(status="error", end_seq=2))


def test_validate_rejects_self_parent():
    with pytest.raises(ValueError):
        validate_span(_span(parent_span_id="s"))


def test_open_span_is_incomplete():
    s = _span(status="unset", end_seq=None)
    assert is_complete(s) is False


def test_complete_error_requires_error_object():
    s = _span(status="error", end_seq=2, error=None)
    assert is_complete_error(s) is False
    s.error = SpanError(type="X", message="m")
    assert is_complete_error(s) is True


def test_ok_span_complete_not_error():
    s = _span(status="ok", end_seq=2)
    assert is_complete(s) is True
    assert is_complete_error(s) is False
