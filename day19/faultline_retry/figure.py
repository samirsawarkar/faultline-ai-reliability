"""Deterministic SVG of the crossover curve: success and p99 vs retry budget K."""
from __future__ import annotations

from typing import Any, Dict, List

W, H, PAD = 520, 300, 45


def _pts(points: List[Dict[str, Any]], key: str, vmax: float) -> str:
    n = len(points)
    xs = [PAD + (W - 2 * PAD) * (i / (n - 1)) for i in range(n)]
    ys = [H - PAD - (H - 2 * PAD) * (points[i][key] / vmax) for i in range(n)]
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))


def render_svg(independent: List[Dict[str, Any]], correlated: List[Dict[str, Any]],
               recommended_independent: int) -> str:
    kmax = independent[-1]["K"]
    p99max = max(max(p["p99_latency"] for p in independent),
                 max(p["p99_latency"] for p in correlated))
    recx = PAD + (W - 2 * PAD) * ((recommended_independent - 1) / (kmax - 1))
    return f"""<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="system-ui" font-size="11">
<rect width="{W}" height="{H}" fill="white"/>
<text x="{W/2}" y="18" text-anchor="middle" font-size="13" font-weight="700">Retry crossover — success (solid) vs p99 latency (dashed) by budget K</text>
<line x1="{PAD}" y1="{H-PAD}" x2="{W-PAD}" y2="{H-PAD}" stroke="#333"/>
<line x1="{PAD}" y1="{PAD}" x2="{PAD}" y2="{H-PAD}" stroke="#333"/>
<rect x="{PAD}" y="{PAD}" width="{recx-PAD}" height="{H-2*PAD}" fill="#2e7d3211"/>
<line x1="{recx:.1f}" y1="{PAD}" x2="{recx:.1f}" y2="{H-PAD}" stroke="#2e7d32" stroke-dasharray="2,2"/>
<text x="{recx+4:.1f}" y="{PAD+12}" fill="#2e7d32" font-size="10">recommended ≤ K{recommended_independent} (independent)</text>
<polyline points="{_pts(independent,'success_rate',1.0)}" fill="none" stroke="#1565c0" stroke-width="2"/>
<polyline points="{_pts(correlated,'success_rate',1.0)}" fill="none" stroke="#c62828" stroke-width="2"/>
<polyline points="{_pts(independent,'p99_latency',p99max)}" fill="none" stroke="#1565c0" stroke-width="1.5" stroke-dasharray="4,3"/>
<polyline points="{_pts(correlated,'p99_latency',p99max)}" fill="none" stroke="#c62828" stroke-width="1.5" stroke-dasharray="4,3"/>
<text x="{W-PAD}" y="{H-PAD+16}" text-anchor="end" fill="#666">K=1..{kmax}</text>
<text x="{PAD-6}" y="{PAD+4}" text-anchor="end" fill="#666">1.0</text>
<text x="{PAD+8}" y="{H-PAD+28}" fill="#1565c0">independent</text>
<text x="{PAD+110}" y="{H-PAD+28}" fill="#c62828">correlated (retry storm)</text>
</svg>
"""
