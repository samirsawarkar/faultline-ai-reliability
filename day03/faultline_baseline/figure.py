"""Render the success-vs-hops figure as a dependency-free, deterministic SVG.

No plotting library, no fonts to embed, no rasterization: the output is text
built from the data, so it is byte-reproducible and diffs cleanly in git. Each
hop shows its success rate with a Wilson 95% interval; the budget cliff (where a
task needs more steps than the cap allows) is annotated.
"""
from __future__ import annotations

from typing import List

from .records import BaselineConfig, HopPoint

_W, _H = 760, 440
_ML, _MR, _MT, _MB = 70, 30, 60, 60  # margins


def _x(hops: int, hmin: int, hmax: int) -> float:
    span = max(hmax - hmin, 1)
    return _ML + (hops - hmin) / span * (_W - _ML - _MR)


def _y(rate: float) -> float:
    return _MT + (1.0 - rate) * (_H - _MT - _MB)


def render_success_vs_hops(points: List[HopPoint], config: BaselineConfig) -> str:
    if not points:
        raise ValueError("no hop points to plot")
    hmin, hmax = points[0].hops, points[-1].hops
    # First hop count whose step demand (2*h + 1) exceeds the cap: the cliff.
    cliff = next((p.hops for p in points if 2 * p.hops + 1 > config.step_cap), None)

    el: List[str] = []
    el.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_W}" height="{_H}" '
        f'viewBox="0 0 {_W} {_H}" font-family="ui-sans-serif,Segoe UI,Helvetica,Arial">'
    )
    el.append(f'<rect width="{_W}" height="{_H}" fill="#ffffff"/>')
    el.append(
        f'<text x="{_W/2:.0f}" y="30" text-anchor="middle" font-size="18" '
        f'font-weight="700" fill="#111827">FAULTLINE baseline — success vs. hops '
        f'(deterministic agent, step cap {config.step_cap})</text>'
    )

    # y gridlines + labels
    for t in (0.0, 0.25, 0.5, 0.75, 1.0):
        y = _y(t)
        el.append(f'<line x1="{_ML}" y1="{y:.1f}" x2="{_W-_MR}" y2="{y:.1f}" '
                  f'stroke="#e5e7eb" stroke-width="1"/>')
        el.append(f'<text x="{_ML-10}" y="{y+4:.1f}" text-anchor="end" '
                  f'font-size="12" fill="#6b7280">{t:.2f}</text>')

    # axes
    el.append(f'<line x1="{_ML}" y1="{_MT}" x2="{_ML}" y2="{_H-_MB}" stroke="#9ca3af"/>')
    el.append(f'<line x1="{_ML}" y1="{_H-_MB}" x2="{_W-_MR}" y2="{_H-_MB}" stroke="#9ca3af"/>')
    el.append(f'<text x="20" y="{_H/2:.0f}" transform="rotate(-90 20 {_H/2:.0f})" '
              f'text-anchor="middle" font-size="13" fill="#374151">success rate</text>')
    el.append(f'<text x="{_W/2:.0f}" y="{_H-18}" text-anchor="middle" '
              f'font-size="13" fill="#374151">hops (entities to retrieve and sum)</text>')

    # budget-cliff shading + line
    if cliff is not None:
        cx = _x(cliff, hmin, hmax)
        el.append(f'<rect x="{cx:.1f}" y="{_MT}" width="{_W-_MR-cx:.1f}" '
                  f'height="{_H-_MT-_MB}" fill="#fca5a5" opacity="0.12"/>')
        el.append(f'<line x1="{cx:.1f}" y1="{_MT}" x2="{cx:.1f}" y2="{_H-_MB}" '
                  f'stroke="#dc2626" stroke-width="1.5" stroke-dasharray="5 4"/>')
        el.append(f'<text x="{cx+6:.1f}" y="{_MT+16:.1f}" font-size="12" '
                  f'fill="#b91c1c">over budget (needs &gt; {config.step_cap} steps)</text>')

    # x ticks
    for p in points:
        x = _x(p.hops, hmin, hmax)
        el.append(f'<text x="{x:.1f}" y="{_H-_MB+18:.1f}" text-anchor="middle" '
                  f'font-size="12" fill="#6b7280">{p.hops}</text>')

    # connecting line
    pts = " ".join(f"{_x(p.hops,hmin,hmax):.1f},{_y(p.success_rate):.1f}" for p in points)
    el.append(f'<polyline points="{pts}" fill="none" stroke="#2563eb" stroke-width="2"/>')

    # Wilson intervals + markers
    for p in points:
        x = _x(p.hops, hmin, hmax)
        ylo, yhi = _y(p.wilson_low), _y(p.wilson_high)
        el.append(f'<line x1="{x:.1f}" y1="{yhi:.1f}" x2="{x:.1f}" y2="{ylo:.1f}" '
                  f'stroke="#1e3a8a" stroke-width="1.5"/>')
        for yy in (ylo, yhi):
            el.append(f'<line x1="{x-4:.1f}" y1="{yy:.1f}" x2="{x+4:.1f}" y2="{yy:.1f}" '
                      f'stroke="#1e3a8a" stroke-width="1.5"/>')
        el.append(f'<circle cx="{x:.1f}" cy="{_y(p.success_rate):.1f}" r="4" '
                  f'fill="#2563eb"/>')

    el.append(f'<text x="{_W-_MR}" y="{_H-6}" text-anchor="end" font-size="11" '
              f'fill="#9ca3af">error bars: Wilson 95% CI, n per hop shown in baseline.json</text>')
    el.append('</svg>')
    return "\n".join(el) + "\n"
