"""Attack: after each deletion the stranger can STILL reconstruct the run.

This is the mission's fail condition, negated and enforced: a damaged trace must
not become unreconstructable.
"""
from __future__ import annotations

from faultline_store import build_store, reconstruct, render_timeline
from faultline_store.attack import run_scenarios


def test_every_deletion_scenario_still_names_the_failure():
    report = run_scenarios()
    assert report["all_scenarios_reconstructable"] is True
    for s in report["scenarios"]:
        assert s["root_cause_named"] is True, s["scenario"]
        assert s["ok"] is True, s["scenario"]
        # structured store always beats raw-log scanning for locating the fault
        assert s["store_uses_index"] is True
        assert s["store_rows_scanned_to_find_failure"] <= s["rawlog_rows_scanned_to_find_failure"]


def test_drop_error_message_degrades_gracefully():
    store, ok_id, fail_id = build_store()
    err = store.error_spans(fail_id)[-1]
    store.clear_field(fail_id, err["span_id"], "error_message")
    r = reconstruct(store, fail_id)
    # still names where it failed, message shown as explicit placeholder
    assert r["root_cause_spans"] == ["tool.sum"]
    row = next(s for s in r["spans"] if s["name"] == "tool.sum")
    assert row["error_message"] == "<missing>"
    assert row["error_type"] == "RiskyToolError"


def test_delete_intermediate_span_shows_gap_but_reconstructs():
    store, ok_id, fail_id = build_store()
    retrieve = next(s for s in store.timeline(fail_id) if s["name"] == "tool.retrieve")
    store.delete_span(fail_id, retrieve["span_id"])
    r = reconstruct(store, fail_id)
    assert r["missing_span_count"] == 1
    assert r["sequence_gaps"], "a deleted sibling should surface as a gap"
    assert r["root_cause_spans"] == ["tool.sum"]


def test_delete_root_orphans_children_but_still_reconstructs():
    store, ok_id, fail_id = build_store()
    root = store.children(fail_id, None)[0]
    store.delete_span(fail_id, root["span_id"])
    r = reconstruct(store, fail_id)
    assert r["orphan_spans"], "children of a deleted root are orphans"
    assert r["root_cause_spans"] == ["tool.sum"]
    view = render_timeline(store, fail_id)
    assert "orphan" in view
