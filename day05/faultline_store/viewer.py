"""Terminal timeline viewer — the thing a stranger actually reads.

Renders one trace as an indented, time-ordered timeline with a seq bar, status,
and (for failures) the error and the reconstructed failing path. Output is
deterministic: no clocks, no colors that depend on a terminal.
"""
from __future__ import annotations

from .reconstruct import MISSING, reconstruct
from .store import TraceStore

_BAR_WIDTH = 24


def _bar(start: int, end, lo: int, hi: int) -> str:
    if end is None:
        end = start
    span = max(hi - lo, 1)
    a = int((start - lo) / span * _BAR_WIDTH)
    b = max(int((end - lo) / span * _BAR_WIDTH), a + 1)
    b = min(b, _BAR_WIDTH)
    return " " * a + "#" * (b - a) + " " * (_BAR_WIDTH - b)


def render_timeline(store: TraceStore, trace_id: str) -> str:
    r = reconstruct(store, trace_id)
    rows = r["spans"]
    if not rows:
        return f"trace {trace_id}: no spans found (nothing to reconstruct)"

    lo = min(s["start_seq"] for s in rows)
    hi = max((s["end_seq"] or s["start_seq"]) for s in rows)

    out = []
    status = r["trace_status"].upper()
    hdr = (f"TRACE {trace_id}   status={status}   "
           f"spans={r['present_span_count']}")
    if r["missing_span_count"]:
        hdr += f"   (recorded {r['recorded_span_count']}, {r['missing_span_count']} MISSING)"
    out.append(hdr)
    out.append("seq " + "".ljust(_BAR_WIDTH) + "  span")
    for s in rows:
        bar = _bar(s["start_seq"], s["end_seq"], lo, hi)
        indent = "  " * s["depth"]
        mark = {"error": "X", "ok": ".", "unset": "?"}.get(s["status"], "?")
        end = s["end_seq"] if s["end_seq"] is not None else MISSING
        line = (f"{s['start_seq']:>2}-{str(end):<3}|{bar}| {mark} "
                f"{indent}{s['name']} [{s['kind']}]")
        if s["orphan"]:
            line += "  (orphan: parent missing)"
        out.append(line)
        if s["status"] == "error":
            out.append(f"        {indent}  -> {s['error_type']}: {s['error_message']}")

    out.append("")
    if r["trace_status"] == "error":
        for p in r["failing_paths"]:
            out.append("failing path: " + " > ".join(p))
        out.append("root-cause span(s): " + ", ".join(r["root_cause_spans"]))
    else:
        out.append("run succeeded; no failing path")
    if r["sequence_gaps"]:
        out.append(f"sequence gaps (deleted spans?): {r['sequence_gaps']}")
    if r["orphan_spans"]:
        out.append(f"orphan spans (broken links): {r['orphan_spans']}")
    return "\n".join(out) + "\n"
