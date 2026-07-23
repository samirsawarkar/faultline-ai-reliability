"""The mission gate: raise mid-tool exceptions and demand a complete error span
in every one of 100 runs. A single incomplete trace fails the mission.
"""
from __future__ import annotations

import pytest

from faultline_trace import (
    RiskyToolError,
    STEPS,
    Tracer,
    audit_failed_trace,
    audit_ok_trace,
    run_pipeline,
)

N = 100


def test_100_forced_failures_all_produce_complete_error_spans():
    for seed in range(N):
        fail_at = STEPS[seed % len(STEPS)]  # rotate the injection point
        tracer = Tracer(seed)
        with pytest.raises(RiskyToolError):
            run_pipeline(tracer, task=f"task-{seed}", fail_at=fail_at, secret="hunter2")

        # No failure without a complete error span.
        report = audit_failed_trace(tracer.spans)
        assert report["complete"] is True
        assert report["open_spans"] == 0
        assert tracer.open_spans() == []

        # The failing tool span itself is a complete error span.
        failing = [s for s in tracer.spans if s.name == f"tool.{fail_at}"]
        assert len(failing) == 1 and failing[0].status == "error"


def test_secret_never_leaks_in_failed_trace():
    tracer = Tracer(42)
    with pytest.raises(RiskyToolError):
        run_pipeline(tracer, task="leak-check", fail_at="sum", secret="hunter2")
    blob = tracer.to_json().decode()
    assert "hunter2" not in blob, "secret leaked into the trace"
    # and the error message was still captured (redacted)
    err = [s for s in tracer.spans if s.status == "error"][0].error
    assert err is not None and err.type == "RiskyToolError"
    assert "***REDACTED***" in err.message


def test_normal_run_is_clean_and_complete():
    for seed in range(N):
        tracer = Tracer(seed)
        run_pipeline(tracer, task=f"ok-{seed}", fail_at=None)
        audit_ok_trace(tracer.spans)
        assert tracer.open_spans() == []
        assert len(tracer.spans) == 1 + 1 + len(STEPS)  # agent + model + tools
