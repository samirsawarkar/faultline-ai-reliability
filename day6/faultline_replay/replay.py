"""Deterministic replay harness (Build B).

replay_bundle re-runs the SAME program with a ReplayChannel fed from the bundle.
It never computes a provider output — it only serves recorded ones — so what it
reproduces is exactly what was captured, no more. Version drift or a program that
leaves the recorded path raises rather than fabricating a result.
"""
from __future__ import annotations

from typing import Any, Dict

from .bundle import check_versions
from .program import ToolFailure, new_tracer, run_program
from .providers import ReplayChannel


def replay_bundle(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Replay a bundle. Returns {trace, final_state, calls_consumed}."""
    check_versions(bundle)  # refuse to over-claim under version drift

    inputs = bundle["inputs"]
    channel = ReplayChannel(bundle["recorded_calls"])
    tracer = new_tracer(inputs["seed"])

    failed = False
    try:
        final_state = run_program(tracer, channel, inputs["task"], inputs.get("fail_at"))
    except ToolFailure:
        failed = True
        final_state = {"results": [r["output"]
                                   for r in bundle["recorded_calls"][:channel.consumed]]}

    return {
        "trace": tracer.to_dict(),
        "final_state": {"results": final_state["results"], "failed": failed},
        "calls_consumed": channel.consumed,
    }
