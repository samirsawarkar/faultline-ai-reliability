"""A deterministic SVG of the breaker state machine (the transition diagram)."""
from __future__ import annotations

from typing import Any, Dict, List


def render_state_diagram() -> str:
    return """<svg viewBox="0 0 560 220" xmlns="http://www.w3.org/2000/svg" font-family="system-ui" font-size="12">
<rect width="560" height="220" fill="white"/>
<text x="280" y="20" text-anchor="middle" font-size="14" font-weight="700">Circuit breaker states</text>
<circle cx="110" cy="120" r="42" fill="#e8f5e9" stroke="#2e7d32" stroke-width="2"/>
<text x="110" y="124" text-anchor="middle" font-weight="700">CLOSED</text>
<circle cx="440" cy="120" r="42" fill="#ffebee" stroke="#c62828" stroke-width="2"/>
<text x="440" y="124" text-anchor="middle" font-weight="700">OPEN</text>
<circle cx="275" cy="120" r="46" fill="#fff8e1" stroke="#f9a825" stroke-width="2"/>
<text x="275" y="118" text-anchor="middle" font-weight="700">HALF</text>
<text x="275" y="132" text-anchor="middle" font-weight="700">OPEN</text>
<line x1="152" y1="105" x2="398" y2="105" stroke="#c62828" stroke-width="1.5" marker-end="url(#a)"/>
<text x="275" y="96" text-anchor="middle" fill="#c62828">failure_threshold</text>
<line x1="398" y1="140" x2="321" y2="140" stroke="#f9a825" stroke-width="1.5" marker-end="url(#a)"/>
<text x="360" y="158" text-anchor="middle" fill="#f9a825">cooldown_elapsed</text>
<line x1="230" y1="150" x2="150" y2="150" stroke="#2e7d32" stroke-width="1.5" marker-end="url(#a)"/>
<text x="192" y="168" text-anchor="middle" fill="#2e7d32">recovered</text>
<path d="M300 90 q60 -40 120 0" fill="none" stroke="#c62828" stroke-width="1.5" marker-end="url(#a)"/>
<text x="360" y="52" text-anchor="middle" fill="#c62828">half_open_failed</text>
<defs><marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
<path d="M0,0 L8,4 L0,8 z" fill="#555"/></marker></defs>
</svg>
"""


def render_timeline(transitions: List[Dict[str, Any]]) -> str:
    if not transitions:
        return "(no transitions)"
    return " -> ".join(f"[t{tr['tick']}] {tr['from']}→{tr['to']} ({tr['reason']})"
                       for tr in transitions)
