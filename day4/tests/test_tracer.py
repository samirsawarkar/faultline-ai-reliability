"""Tracer structural behavior: links, determinism, always-closed spans."""
from __future__ import annotations

import pytest

from faultline_trace import RiskyToolError, STEPS, Tracer, run_pipeline
from faultline_trace.schema import assert_links_intact


def test_parent_child_links():
    tracer = Tracer(1)
    run_pipeline(tracer, task="t", fail_at=None)
    spans = tracer.spans
    assert_links_intact(spans)
    agent = next(s for s in spans if s.kind == "agent")
    assert agent.parent_span_id is None
    for s in spans:
        if s is agent:
            continue
        assert s.parent_span_id == agent.span_id  # model + tools are agent's kids


def test_same_seed_byte_identical_trace():
    a = Tracer(7)
    run_pipeline(a, task="x", fail_at=None)
    b = Tracer(7)
    run_pipeline(b, task="x", fail_at=None)
    assert a.to_json() == b.to_json()


def test_failed_trace_is_reproducible():
    a = Tracer(7)
    with pytest.raises(RiskyToolError):
        run_pipeline(a, task="x", fail_at="verify")
    b = Tracer(7)
    with pytest.raises(RiskyToolError):
        run_pipeline(b, task="x", fail_at="verify")
    assert a.to_json() == b.to_json()


def test_span_closed_even_on_raise():
    tracer = Tracer(3)
    with pytest.raises(ValueError):
        with tracer.span("agent", "agent") as _:
            raise ValueError("boom")
    span = tracer.spans[0]
    assert span.end_seq is not None and span.status == "error"
    assert tracer.open_spans() == []


def test_monotonic_clock_orders_spans():
    tracer = Tracer(2)
    run_pipeline(tracer, task="t", fail_at=None)
    for s in tracer.spans:
        assert s.end_seq > s.start_seq
    starts = [s.start_seq for s in tracer.spans]
    assert starts == sorted(starts)  # created in entry order
