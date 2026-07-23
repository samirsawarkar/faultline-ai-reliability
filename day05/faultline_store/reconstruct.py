"""Reconstruct a run from the store alone — the answer to 'what failed, where?'

Designed to degrade gracefully: missing fields become explicit placeholders and
a missing parent link falls back to sequence order, so a stranger still gets a
coherent story from a damaged trace instead of a dead end.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .store import TraceStore

MISSING = "<missing>"


def _depth(span_by_id: Dict[str, Any], span: Any) -> int:
    """Depth from root via parent links; falls back safely on broken links."""
    depth, node, seen = 0, span, set()
    while node is not None and node["parent_span_id"] is not None:
        pid = node["parent_span_id"]
        if pid in seen or pid not in span_by_id:  # orphan / cycle guard
            break
        seen.add(pid)
        node = span_by_id[pid]
        depth += 1
    return depth


def reconstruct(store: TraceStore, trace_id: str) -> Dict[str, Any]:
    """Return a structured incident reconstruction. Pure function of the store."""
    trace = store.get_trace(trace_id)
    spans = store.timeline(trace_id)  # ordered by start_seq (indexed)
    span_by_id = {s["span_id"]: s for s in spans}
    present_ids = set(span_by_id)

    # Failing path: each error leaf up to its root.
    errors = [s for s in spans if s["status"] == "error"]
    child_error_parents = {s["parent_span_id"] for s in errors}
    leaves = [s for s in errors if s["span_id"] not in child_error_parents]

    def path_to_root(leaf: Any) -> List[str]:
        out, node, seen = [], leaf, set()
        while node is not None:
            out.append(node["name"] or MISSING)
            pid = node["parent_span_id"]
            if pid is None or pid in seen or pid not in span_by_id:
                break
            seen.add(pid)
            node = span_by_id[pid]
        return list(reversed(out))

    # Orphans: spans whose parent link points at a span that is gone.
    orphans = [s["span_id"] for s in spans
               if s["parent_span_id"] is not None and s["parent_span_id"] not in present_ids]

    # Gaps: a deleted span leaves a hole between two SIBLINGS. Under one parent,
    # consecutive children tile the tick sequence (child.end_seq + 1 ==
    # next.start_seq); a break means a sibling was removed. Comparing siblings
    # (not raw start_seqs) avoids false positives from the start/end tick scheme.
    by_parent: Dict[Optional[str], List[Any]] = {}
    for s in spans:
        by_parent.setdefault(s["parent_span_id"], []).append(s)
    gaps = []
    for kids in by_parent.values():
        kids = sorted(kids, key=lambda s: s["start_seq"])
        for a, b in zip(kids, kids[1:]):
            a_end = a["end_seq"] if a["end_seq"] is not None else a["start_seq"]
            if b["start_seq"] - a_end > 1:
                gaps.append([a_end, b["start_seq"]])
    gaps.sort()

    rows = []
    for s in spans:
        rows.append({
            "span_id": s["span_id"],
            "name": s["name"] or MISSING,
            "kind": s["kind"],
            "depth": _depth(span_by_id, s),
            "start_seq": s["start_seq"],
            "end_seq": s["end_seq"],
            "status": s["status"],
            "error_type": s["error_type"] or (MISSING if s["status"] == "error" else None),
            "error_message": s["error_message"] or (MISSING if s["status"] == "error" else None),
            "orphan": s["parent_span_id"] is not None and s["parent_span_id"] not in present_ids,
        })

    return {
        "trace_id": trace_id,
        "trace_status": trace["status"] if trace else MISSING,
        "recorded_span_count": trace["span_count"] if trace else None,
        "present_span_count": len(spans),
        "root_cause_spans": [leaf["name"] or MISSING for leaf in leaves],
        "failing_paths": [path_to_root(leaf) for leaf in leaves],
        "orphan_spans": orphans,
        "sequence_gaps": gaps,
        "missing_span_count": (trace["span_count"] - len(spans)) if trace else None,
        "reconstructable": bool(leaves) or (trace and trace["status"] == "ok"),
        "spans": rows,
    }
