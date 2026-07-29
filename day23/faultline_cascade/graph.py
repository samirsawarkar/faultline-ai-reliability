"""Causal graph data and deterministic SVG rendering with trace references."""
from __future__ import annotations

import hashlib
import html
import json
from typing import Any, Dict, List

_COLORS = {
    "initiating_fault": "#dc2626",
    "recovery_side_effect": "#d97706",
    "recovery_transition": "#2563eb",
    "propagated_fault": "#7c3aed",
    "detection_failure": "#be185d",
    "terminal_containment": "#0f766e",
}
_COMPONENT_X = {
    "primary_provider": 40,
    "retry_controller": 280,
    "circuit_breaker": 520,
    "fallback_router": 760,
    "secondary_provider": 1000,
    "quality_gate": 760,
    "agent_controller": 520,
    "repetition_recovery": 280,
    "global_budget": 40,
}


def _digest(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_causal_graph(run: Dict[str, Any]) -> Dict[str, Any]:
    nodes = [
        {
            "id": event["event_id"],
            "label": event["label"],
            "component": event["component"],
            "category": event["category"],
            "detail": event["detail"],
            "trace_span_refs": event["span_refs"],
            "observed": event["observed"],
        }
        for event in run["events"]
    ]
    graph = {
        "graph_version": "1.0.0",
        "incident_id": run["incident_id"],
        "seed": run["seed"],
        "config_digest": run["config_digest"],
        "trace_digest": run["trace_digest"],
        "root_cause": "E01",
        "terminal_event": "E09",
        "nodes": nodes,
        "edges": list(run["causal_edges"]),
        "audit": {
            "node_count": len(nodes),
            "edge_count": len(run["causal_edges"]),
            "all_nodes_observed": all(node["observed"] for node in nodes),
            "all_nodes_trace_referenced": all(
                node["trace_span_refs"] for node in nodes
            ),
            "single_chain": len(run["causal_edges"]) == len(nodes) - 1,
        },
    }
    graph["graph_digest"] = _digest(graph)
    return graph


def _split(label: str) -> List[str]:
    words = label.replace("_", " ").split()
    midpoint = max(1, len(words) // 2)
    return [" ".join(words[:midpoint]), " ".join(words[midpoint:])]


def render_causal_graph_svg(graph: Dict[str, Any]) -> str:
    width, height = 1280, 1050
    box_w, box_h = 220, 66
    positions = {}
    for index, node in enumerate(graph["nodes"]):
        positions[node["id"]] = (
            _COMPONENT_X[node["component"]],
            70 + index * 105,
        )
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        "<defs>",
        '<marker id="arrow" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">',
        '<polygon points="0 0, 10 3.5, 0 7" fill="#64748b"/>',
        "</marker>",
        "</defs>",
        '<rect width="1280" height="1050" fill="#f8fafc"/>',
        '<text x="40" y="34" font-family="sans-serif" font-size="22" '
        'font-weight="700" fill="#0f172a">Day 23 seeded causal incident</text>',
        f'<text x="40" y="55" font-family="monospace" font-size="12" '
        f'fill="#475569">seed={graph["seed"]} · config={graph["config_digest"][:12]} '
        f'· trace={graph["trace_digest"][:12]}</text>',
    ]
    for edge in graph["edges"]:
        x1, y1 = positions[edge["cause"]]
        x2, y2 = positions[edge["effect"]]
        parts.append(
            f'<line x1="{x1 + box_w / 2}" y1="{y1 + box_h}" '
            f'x2="{x2 + box_w / 2}" y2="{y2}" stroke="#64748b" '
            'stroke-width="2" marker-end="url(#arrow)"/>'
        )
        mx = (x1 + x2) / 2 + box_w / 2
        my = (y1 + box_h + y2) / 2 - 5
        parts.append(
            f'<text x="{mx}" y="{my}" text-anchor="middle" '
            f'font-family="sans-serif" font-size="10" fill="#475569">'
            f'{html.escape(edge["relation"])}</text>'
        )
    for node in graph["nodes"]:
        x, y = positions[node["id"]]
        color = _COLORS[node["category"]]
        lines = _split(node["label"])
        refs = ", ".join(ref.rsplit("-", 1)[-1] for ref in node["trace_span_refs"])
        parts.extend([
            f'<rect x="{x}" y="{y}" width="{box_w}" height="{box_h}" rx="8" '
            f'fill="white" stroke="{color}" stroke-width="3"/>',
            f'<text x="{x + 10}" y="{y + 17}" font-family="monospace" '
            f'font-size="11" font-weight="700" fill="{color}">'
            f'{html.escape(node["id"])} · {html.escape(node["component"])}</text>',
            f'<text x="{x + 10}" y="{y + 36}" font-family="sans-serif" '
            f'font-size="13" font-weight="700" fill="#0f172a">'
            f'{html.escape(lines[0])}</text>',
            f'<text x="{x + 10}" y="{y + 51}" font-family="sans-serif" '
            f'font-size="13" font-weight="700" fill="#0f172a">'
            f'{html.escape(lines[1])}</text>',
            f'<text x="{x + 10}" y="{y + 62}" font-family="monospace" '
            f'font-size="8" fill="#64748b">trace: {html.escape(refs)}</text>',
        ])
    parts.append("</svg>\n")
    return "\n".join(parts)
