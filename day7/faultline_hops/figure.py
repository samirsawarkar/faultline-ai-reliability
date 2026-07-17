"""Deterministic, dependency-free SVG of the measured-vs-naive curve.

Measured curve with a Wilson CI band, the naive p1**n curve with its propagated
band, and a marker at the first divergence hop. Regenerates byte-for-byte.
"""
from __future__ import annotations

from typing import Any, Dict, List

_W, _H = 720, 460
_ML, _MR, _MT, _MB = 70, 30, 50, 55
_PLOT_W = _W - _ML - _MR
_PLOT_H = _H - _MT - _MB
_MEASURED = "#1565c0"
_NAIVE = "#c62828"
_BAND_M = "#1565c0"
_BAND_N = "#c62828"


def _x(n: int, max_n: int) -> float:
    return _ML + (n - 1) / max(max_n - 1, 1) * _PLOT_W


def _y(p: float) -> float:
    return _MT + (1.0 - p) * _PLOT_H


def _esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _band(points: List[Dict[str, Any]], key: str, max_n: int) -> str:
    top = [f"{_x(p['hops'], max_n):.1f},{_y(p[key][1]):.1f}" for p in points]
    bot = [f"{_x(p['hops'], max_n):.1f},{_y(p[key][0]):.1f}" for p in reversed(points)]
    return " ".join(top + bot)


def _line(points: List[Dict[str, Any]], key: str, max_n: int) -> str:
    return " ".join(f"{_x(p['hops'], max_n):.1f},{_y(p[key]):.1f}" for p in points)


def render_svg(q1: Dict[str, Any]) -> str:
    pts = q1["curve"]
    max_n = pts[-1]["hops"]
    div = q1["first_divergence_hop"]

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_W}" height="{_H}" '
        f'font-family="sans-serif" font-size="12">',
        f'<rect width="{_W}" height="{_H}" fill="white"/>',
        f'<text x="{_ML}" y="26" font-size="15" font-weight="bold">'
        f'Q1: end-to-end reliability vs required tool hops</text>',
    ]

    # gridlines + y labels (0..1)
    for i in range(0, 6):
        p = i / 5
        y = _y(p)
        out.append(f'<line x1="{_ML}" y1="{y:.1f}" x2="{_ML+_PLOT_W}" y2="{y:.1f}" '
                   f'stroke="#eee"/>')
        out.append(f'<text x="{_ML-8}" y="{y+4:.1f}" text-anchor="end" fill="#666">'
                   f'{p:.1f}</text>')
    # x labels
    for p in pts:
        x = _x(p["hops"], max_n)
        out.append(f'<text x="{x:.1f}" y="{_MT+_PLOT_H+18:.1f}" text-anchor="middle" '
                   f'fill="#666">{p["hops"]}</text>')
    out.append(f'<text x="{_ML+_PLOT_W/2:.0f}" y="{_H-12}" text-anchor="middle" '
               f'fill="#333">required tool hops (n)</text>')

    # bands
    out.append(f'<polygon points="{_band(pts, "naive_ci95", max_n)}" '
               f'fill="{_BAND_N}" fill-opacity="0.12"/>')
    out.append(f'<polygon points="{_band(pts, "measured_ci95", max_n)}" '
               f'fill="{_BAND_M}" fill-opacity="0.15"/>')
    # lines
    out.append(f'<polyline points="{_line(pts, "naive", max_n)}" fill="none" '
               f'stroke="{_NAIVE}" stroke-width="2" stroke-dasharray="6 4"/>')
    out.append(f'<polyline points="{_line(pts, "measured", max_n)}" fill="none" '
               f'stroke="{_MEASURED}" stroke-width="2.5"/>')
    # points
    for p in pts:
        x, y = _x(p["hops"], max_n), _y(p["measured"])
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{_MEASURED}"/>')

    # divergence marker
    if div is not None:
        x = _x(div, max_n)
        out.append(f'<line x1="{x:.1f}" y1="{_MT}" x2="{x:.1f}" y2="{_MT+_PLOT_H}" '
                   f'stroke="#999" stroke-dasharray="3 3"/>')
        out.append(f'<text x="{x+5:.1f}" y="{_MT+14}" fill="#555" font-size="11">'
                   f'naive falsified at n={div}</text>')

    # legend
    lx, ly = _ML + _PLOT_W - 210, _MT + 6
    out.append(f'<rect x="{lx}" y="{ly}" width="200" height="46" fill="white" '
               f'stroke="#ddd"/>')
    out.append(f'<line x1="{lx+10}" y1="{ly+16}" x2="{lx+34}" y2="{ly+16}" '
               f'stroke="{_MEASURED}" stroke-width="2.5"/>')
    out.append(f'<text x="{lx+40}" y="{ly+20}">measured (95% CI)</text>')
    out.append(f'<line x1="{lx+10}" y1="{ly+34}" x2="{lx+34}" y2="{ly+34}" '
               f'stroke="{_NAIVE}" stroke-width="2" stroke-dasharray="6 4"/>')
    out.append(f'<text x="{lx+40}" y="{ly+38}">naive p1^n</text>')

    out.append("</svg>")
    return "\n".join(out) + "\n"
