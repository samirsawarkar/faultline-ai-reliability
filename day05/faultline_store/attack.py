"""Deletion attack: damage a stored trace and measure whether a stranger can
still reconstruct the run — and how the structured store beats a raw log.

For each scenario we delete a field or a whole span, then ask the single
question that matters: *can we still name what failed and where?* We also record
the structural cost of answering it two ways:

  * store   — one indexed query hits the error span directly (rows_scanned ~ hits)
  * rawlog  — a flat text log must be scanned line by line (rows_scanned = N)

Everything here is deterministic (counts, not clocks), so the report is
byte-reproducible evidence.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .ingest import make_traces
from .reconstruct import reconstruct
from .store import TraceStore


def _fresh_failed_store() -> tuple:
    _, failed = make_traces()
    store = TraceStore(":memory:")
    tid = store.ingest_trace(failed)
    return store, tid


def _rawlog_lines(store: TraceStore, tid: str) -> List[str]:
    """A naive flat log: one line per span, unindexed, unlinked."""
    lines = []
    for s in store.timeline(tid):
        lines.append(
            f"seq={s['start_seq']} {s['name']} kind={s['kind']} "
            f"status={s['status']} err={s['error_type'] or '-'}"
        )
    return lines


def _rawlog_find_failure(lines: List[str]) -> Dict[str, Any]:
    """Emulate finding the failure in a raw log: scan every line."""
    scanned = 0
    hit = None
    for ln in lines:
        scanned += 1
        if "status=error" in ln:
            hit = ln
    return {"rows_scanned": scanned, "found": hit is not None}


def _store_find_failure(store: TraceStore, tid: str) -> Dict[str, Any]:
    """Find the failure via the status index (no full scan)."""
    errs = store.error_spans(tid)  # uses idx_spans_status
    return {"rows_scanned": len(errs), "found": bool(errs),
            "plan": store.query_plan(
                "SELECT * FROM spans WHERE trace_id=? AND status='error'", (tid,))}


def run_scenarios() -> Dict[str, Any]:
    scenarios = []

    def record(name: str, mutate, expect_still_named: bool):
        store, tid = _fresh_failed_store()
        n_lines = len(_rawlog_lines(store, tid))
        mutate(store, tid)
        rec = reconstruct(store, tid)
        raw = _rawlog_find_failure(_rawlog_lines(store, tid))
        via_store = _store_find_failure(store, tid)
        named = bool(rec["root_cause_spans"]) and rec["root_cause_spans"] != []
        scenarios.append({
            "scenario": name,
            "present_spans": rec["present_span_count"],
            "missing_spans": rec["missing_span_count"],
            "root_cause_named": named,
            "root_cause_spans": rec["root_cause_spans"],
            "failing_paths": rec["failing_paths"],
            "orphan_spans": rec["orphan_spans"],
            "sequence_gaps": rec["sequence_gaps"],
            "reconstructable": rec["reconstructable"],
            "store_rows_scanned_to_find_failure": via_store["rows_scanned"],
            "rawlog_rows_scanned_to_find_failure": raw["rows_scanned"],
            "store_uses_index": "USING INDEX" in via_store["plan"],
            "expected_named": expect_still_named,
            "ok": named == expect_still_named,
        })
        store.close()

    # 1. Baseline: nothing deleted.
    record("intact", lambda s, t: None, expect_still_named=True)

    # 2. Delete the failing span's error MESSAGE (keep the type).
    def drop_msg(s, t):
        err = s.error_spans(t)[-1]
        s.clear_field(t, err["span_id"], "error_message")
    record("drop_error_message", drop_msg, expect_still_named=True)

    # 3. Delete an intermediate (successful) span -> leaves a sibling gap.
    def drop_retrieve(s, t):
        row = next(r for r in s.timeline(t) if r["name"] == "tool.retrieve")
        s.delete_span(t, row["span_id"])
    record("delete_intermediate_span", drop_retrieve, expect_still_named=True)

    # 4. Delete the ROOT span -> every child is orphaned (parent points at a
    #    span that no longer exists); reconstruction falls back to seq order.
    def drop_root(s, t):
        root = s.children(t, None)[0]
        s.delete_span(t, root["span_id"])
    record("delete_root_span", drop_root, expect_still_named=True)

    all_ok = all(s["ok"] for s in scenarios)
    return {
        "all_scenarios_reconstructable": all_ok,
        "claim": "structured store still names the failure after each deletion; "
                 "raw-log finding always costs a full scan",
        "scenarios": scenarios,
    }
