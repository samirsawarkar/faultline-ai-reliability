"""The program under capture/replay: an agent that calls a provider per step.

It is deliberately identical in capture and replay — only the *channel* changes.
Provider outputs are fed into the Day-4 trace (set_output), so any provider
nondeterminism surfaces as a different trace, where the diff can catch it.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Optional

_DAY4 = Path(__file__).resolve().parents[2] / "day4"
if str(_DAY4) not in sys.path:
    sys.path.insert(0, str(_DAY4))

import faultline_trace as ft  # noqa: E402

PLAN = ("retrieve", "sum", "verify")


class ToolFailure(RuntimeError):
    pass


def run_program(tracer, channel, task: str, fail_at: Optional[str] = None
                ) -> Dict[str, Any]:
    """Run the agent. Returns the final state. Provider results come from
    `channel` (live or replay); the program cannot tell which."""
    with tracer.span("agent", "agent", payload={"task": task}) as agent:
        with tracer.span("model.plan", "model", payload={"prompt": task}) as model:
            plan = list(PLAN)
            model.set_output({"plan": plan})

        state: Dict[str, Any] = {"results": []}
        for i, step in enumerate(plan):
            with tracer.span(f"tool.{step}", "tool",
                             payload={"step": step, "index": i}) as tool:
                out = channel.call(f"tool.{step}", {"step": step, "index": i})
                if fail_at == step:
                    raise ToolFailure(f"tool {step} failed at index {i}")
                tool.set_output(out)
                state["results"].append(out)

        agent.set_output({"results": state["results"]})
        return state


def new_tracer(seed: int):
    return ft.Tracer(seed)
