"""Deterministic, dependency-free SVG render of a trace timeline.

This is the committed *visual* a stranger opens (a rendered snapshot of the
viewer, not a photographed screen — so it regenerates byte-for-byte in CI).
Failed spans are red with the error under the bar; a missing/gap is annotated.
"""
from __future__ import annotations

from .reconstruct import reconstruct
from .store import TraceStore

_ROW_H = 34
_PAD = 16
_LABEL_W = 210
_BAR_W = 460
_OK = "#2e7d32"
_ERR = "#c62828"
_UNSET = "#9e9e9e"
_GRID = "#e0e0e0"


def _esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def render_svg(store: TraceStore, trace_id: str) -> str:
    r = reconstruct(store, trace_id)
    rows = r["spans"]
    lo = min((s["start_seq"] for s in rows), default=0)
    hi = max(((s["end_seq"] or s["start_seq"]) for s in rows), default=1)
    span = max(hi - lo, 1)

    def x(seq: int) -> float:
        return _LABEL_W + (seq - lo) / span * _BAR_W

    height = _PAD * 2 + (len(rows) + 2) * _ROW_H + 40
    width = _LABEL_W + _BAR_W + _PAD * 2 + 40
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'font-family="monospace" font-size="13">',
        f'<rect width="{width}" height="{height}" fill="white"/>',
    ]
    status = r["trace_status"].upper()
    title = f"{trace_id}   status={status}   spans={r['present_span_count']}"
    if r["missing_span_count"]:
        title += f"  ({r['missing_span_count']} MISSING of {r['recorded_span_count']})"
    out.append(f'<text x="{_PAD}" y="{_PAD + 14}" font-weight="bold">{_esc(title)}</text>')

    y0 = _PAD + _ROW_H
    for i, s in enumerate(rows):
        y = y0 + i * _ROW_H
        color = {"error": _ERR, "ok": _OK}.get(s["status"], _UNSET)
        out.append(f'<line x1="{_LABEL_W}" y1="{y-4}" x2="{_LABEL_W+_BAR_W}" '
                   f'y2="{y-4}" stroke="{_GRID}"/>')
        label = "  " * s["depth"] + f'{s["name"]} [{s["kind"]}]'
        out.append(f'<text x="{_PAD}" y="{y+10}">{_esc(label[:30])}</text>')
        x1 = x(s["start_seq"])
        x2 = x(s["end_seq"] if s["end_seq"] is not None else s["start_seq"])
        x2 = max(x2, x1 + 6)
        out.append(f'<rect x="{x1:.1f}" y="{y}" width="{x2-x1:.1f}" height="14" '
                   f'rx="3" fill="{color}"/>')
        if s["status"] == "error":
            msg = f'→ {s["name"]}: {s["error_type"]}: {s["error_message"]}'
            # anchored at the label column so long messages never clip off-canvas
            out.append(f'<text x="{_PAD}" y="{y+27}" fill="{_ERR}" '
                       f'font-size="11">{_esc(msg[:78])}</text>')
        if s["orphan"]:
            out.append(f'<text x="{x2+6:.1f}" y="{y+11}" fill="{_UNSET}" '
                       f'font-size="11">orphan</text>')

    fy = y0 + len(rows) * _ROW_H + 18
    footer = ("failing: " + " &gt; ".join(r["failing_paths"][0])
              if r["failing_paths"] else "run succeeded")
    out.append(f'<text x="{_PAD}" y="{fy}" fill="{_ERR if r["failing_paths"] else _OK}">'
               f'{_esc(footer) if not r["failing_paths"] else footer}</text>')
    if r["sequence_gaps"] or r["orphan_spans"]:
        note = f'gaps={r["sequence_gaps"]} orphans={r["orphan_spans"]}'
        out.append(f'<text x="{_PAD}" y="{fy+18}" fill="{_UNSET}" font-size="11">'
                   f'{_esc(note)}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"
