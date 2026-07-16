"""Reconstruction: the stranger's-eye view is correct and deterministic."""
from __future__ import annotations

from faultline_store import build_store, reconstruct, render_timeline


def test_failed_run_names_root_cause_and_path():
    store, ok_id, fail_id = build_store()
    r = reconstruct(store, fail_id)
    assert r["trace_status"] == "error"
    assert r["root_cause_spans"] == ["tool.sum"]
    assert r["failing_paths"] == [["agent", "tool.sum"]]
    assert r["reconstructable"] is True
    assert r["sequence_gaps"] == []      # intact trace has no false gaps
    assert r["orphan_spans"] == []


def test_ok_run_has_no_failing_path():
    store, ok_id, fail_id = build_store()
    r = reconstruct(store, ok_id)
    assert r["trace_status"] == "ok"
    assert r["failing_paths"] == []
    assert r["reconstructable"] is True


def test_viewer_is_deterministic_and_shows_failure():
    store, ok_id, fail_id = build_store()
    a = render_timeline(store, fail_id)
    b = render_timeline(store, fail_id)
    assert a == b
    assert "status=ERROR" in a
    assert "tool.sum" in a
    assert "failing path: agent > tool.sum" in a
    assert "hunter2" not in a


def test_depth_reflects_tree():
    store, ok_id, fail_id = build_store()
    r = reconstruct(store, fail_id)
    by_name = {s["name"]: s for s in r["spans"]}
    assert by_name["agent"]["depth"] == 0
    assert by_name["tool.sum"]["depth"] == 1
