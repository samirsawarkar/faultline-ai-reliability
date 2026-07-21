"""Failure taxonomy by PRODUCING COMPONENT (the Learn block).

The six faults are re-organized by which component of the agent architecture
produces them. This is the view that turns a flat list into a mental model: to
harden the system you harden components, and each component has a characteristic
failure signature (and a characteristic detection nature).
"""
from __future__ import annotations

from typing import Any, Dict, List

# Component -> (layer, characteristic detection nature).
_LAYER = {
    "tool output (data plane)": ("provider boundary", "content"),
    "tool/provider transport (timing)": ("provider boundary", "transport"),
    "tool/provider transport (availability)": ("provider boundary", "transport"),
    "agent context / state (memory)": ("agent internals", "state"),
    "agent control loop (controller)": ("agent internals", "control"),
}


def taxonomy_by_component(catalog: Dict[str, Any]) -> Dict[str, Any]:
    by_component: Dict[str, List[Dict[str, Any]]] = {}
    for c in catalog["cards"]:
        by_component.setdefault(c["producing_component"], []).append({
            "fault": c["id"], "name": c["name"],
            "detection_nature": c["detector"]["nature"],
        })

    components = []
    for comp, faults in by_component.items():
        layer, kind = _LAYER.get(comp, ("unknown", "unknown"))
        natures = sorted({f["detection_nature"] for f in faults})
        components.append({
            "component": comp, "layer": layer, "failure_kind": kind,
            "faults": faults, "detection_natures": natures,
        })
    components.sort(key=lambda x: x["component"])

    # Roll up to two layers for the headline mental model.
    layers: Dict[str, List[str]] = {}
    for comp in components:
        for f in comp["faults"]:
            layers.setdefault(comp["layer"], []).append(f["fault"])
    for k in layers:
        layers[k] = sorted(set(layers[k]))

    return {
        "note": "Faults grouped by the component that PRODUCES them. Hardening is "
                "per-component; provider-boundary faults are mostly deterministic to "
                "detect, agent-internal value faults are where semantics bite.",
        "by_component": components,
        "by_layer": layers,
        "observation": {
            "provider boundary": "F1-F4: content (F1/F3) + transport (F2/F4). "
                                 "Transport faults are deterministic; content faults "
                                 "split (malformed deterministic, semantic wrong escapes).",
            "agent internals": "F5 (context/state) is semantic; F6 (control loop) is "
                               "deterministic (counting/termination).",
        },
    }
