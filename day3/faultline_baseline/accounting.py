"""Deterministic token/cost accounting and *simulated* latency.

No API is called and no wall clock is read. Tokens are counted from the lengths
of the agent's own reasoning trace; cost is tokens x a committed price; latency
is a modeled function of the trace (fixed ms per tool + ms per token). Because
all three are pure functions of (outcome, config), they reproduce exactly — which
is the whole point of a *baseline*.
"""
from __future__ import annotations

import math
from typing import Tuple

from .records import CostModel, LatencyModel


def _toks(text: str, chars_per_token: int) -> int:
    return math.ceil(len(text) / chars_per_token) if text else 0


def account_outcome(outcome, cost: CostModel, latency: LatencyModel) -> Tuple[int, float, float]:
    """Return (tokens_total, cost_usd, latency_ms) for one agent outcome.

    Token model: a fixed per-task prompt overhead, plus, for each step, the
    serialized thought+tool_call ("input") and the serialized observation
    ("output"). Latency model: per-step tool base latency + per-token latency.
    """
    tokens = _toks("x" * cost.base_prompt_chars, cost.chars_per_token)
    latency_ms = 0.0
    for step in outcome.trace:
        step_in = step.thought + step.tool_call.model_dump_json()
        step_out = step.observation.model_dump_json()
        step_tokens = _toks(step_in, cost.chars_per_token) + _toks(step_out, cost.chars_per_token)
        tokens += step_tokens
        tool = step.tool_call.tool
        latency_ms += latency.tool_base_ms.get(tool, 0.0) + latency.per_token_ms * step_tokens
    cost_usd = tokens / 1000.0 * cost.price_per_1k_tokens_usd
    return tokens, cost_usd, latency_ms
