"""Capture a live run into a replay bundle (Build A)."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .bundle import build_bundle
from .program import ToolFailure, new_tracer, run_program
from .providers import LiveChannel, make_provider


def capture_run(provider_name: str, seed: int, task: str,
                fail_at: Optional[str] = None) -> Dict[str, Any]:
    """Run the program live, recording seeds, inputs, provider results, state,
    versions, and the resulting trace into a bundle."""
    provider = make_provider(provider_name)
    channel = LiveChannel(provider)
    tracer = new_tracer(seed)

    initial_state = {"results": []}
    failed = False
    try:
        final_state = run_program(tracer, channel, task, fail_at)
    except ToolFailure:
        failed = True
        final_state = {"results": [r["output"] for r in channel.records[:-1]]}

    return build_bundle(
        provider=provider_name,
        inputs={"seed": seed, "task": task, "fail_at": fail_at, "plan": list(_plan())},
        recorded_calls=channel.records,
        state={"initial": initial_state, "final": final_state, "failed": failed},
        trace=tracer.to_dict(),
    )


def _plan():
    from .program import PLAN
    return PLAN
