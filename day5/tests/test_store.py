"""Store: ingest, derived status, and index-backed queries (no full scans)."""
from __future__ import annotations

from faultline_store import build_store


def test_ingest_counts_and_derived_status():
    store, ok_id, fail_id = build_store()
    ok = store.get_trace(ok_id)
    failed = store.get_trace(fail_id)
    assert ok["status"] == "ok"
    assert failed["status"] == "error"
    assert failed["span_count"] == len(store.timeline(fail_id))


def test_failed_traces_uses_status_index():
    store, ok_id, fail_id = build_store()
    failed = store.failed_traces()
    assert [r["trace_id"] for r in failed] == [fail_id]
    plan = store.query_plan("SELECT * FROM traces WHERE status='error'")
    assert "USING" in plan and "idx_traces_status" in plan


def test_timeline_ordered_and_indexed():
    store, ok_id, fail_id = build_store()
    seqs = [s["start_seq"] for s in store.timeline(fail_id)]
    assert seqs == sorted(seqs)
    plan = store.query_plan(
        "SELECT * FROM spans WHERE trace_id=? ORDER BY start_seq", (fail_id,))
    assert "idx_spans_trace_start" in plan


def test_children_and_error_queries_indexed():
    store, ok_id, fail_id = build_store()
    root = store.children(fail_id, None)[0]
    assert root["kind"] == "agent"
    kids = store.children(fail_id, root["span_id"])
    assert {k["kind"] for k in kids} <= {"model", "tool"}
    assert "idx_spans_parent" in store.query_plan(
        "SELECT * FROM spans WHERE trace_id=? AND parent_span_id=?", (fail_id, root["span_id"]))

    errs = store.error_spans(fail_id)
    assert any(e["name"] == "tool.sum" for e in errs)
    assert "idx_spans_status" in store.query_plan(
        "SELECT * FROM spans WHERE trace_id=? AND status='error'", (fail_id,))


def test_secret_not_in_store():
    store, ok_id, fail_id = build_store()
    dump = "\n".join(str(dict(s)) for s in store.timeline(fail_id))
    assert "hunter2" not in dump
