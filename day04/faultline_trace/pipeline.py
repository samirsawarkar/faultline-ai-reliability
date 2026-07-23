"""An instrumented pipeline: agent -> model -> tool spans with parent links.

This is the deterministic 'system under trace'. The model slot is a stub, not
an LLM -- the tracer must not care whether the callee is a real model or a stub,
and keeping it deterministic makes the forced-failure experiment reproducible.

Each risky operation is wrapped in a span. `fail_at` injects a mid-tool
exception so we can prove failures still leave complete error spans. The secret
is threaded through payloads and the exception text to prove redaction.
"""
from __future__ import annotations

from typing import List, Optional

from .tracer import Tracer

STEPS = ("retrieve", "sum", "verify")


class RiskyToolError(RuntimeError):
    """Raised by a tool mid-operation."""


def _do_step(step: str, i: int) -> dict:
    # deterministic 'work'
    return {"step": step, "index": i, "ok": True, "value": (i + 1) * 10}


def run_pipeline(
    tracer: Tracer,
    task: str,
    fail_at: Optional[str] = None,
    secret: str = "hunter2",
) -> List[dict]:
    """Run the agent. Raises RiskyToolError if fail_at matches a step.

    Span tree:
        agent
          model.plan
          tool.retrieve
          tool.sum
          tool.verify
    """
    with tracer.span("agent", "agent",
                     payload={"task": task, "secret": secret}) as agent:
        with tracer.span("model.plan", "model",
                         payload={"prompt": task}) as model:
            plan = list(STEPS)
            model.set_output({"plan": plan})

        results: List[dict] = []
        for i, step in enumerate(plan):
            with tracer.span(f"tool.{step}", "tool",
                             payload={"step": step, "index": i}) as tool:
                if fail_at == step:
                    # secret in the message proves error redaction works
                    raise RiskyToolError(
                        f"tool {step} exploded (token={secret}) at index {i}"
                    )
                out = _do_step(step, i)
                tool.set_output(out)
                results.append(out)

        agent.set_output({"results": results})
        return results
