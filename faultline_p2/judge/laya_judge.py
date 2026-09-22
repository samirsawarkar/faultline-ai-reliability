"""Laya Decision Model Adapter for FAULTLINE P5 Judge Evaluation.

Scores the open-source local decision model Laya (HF: convaiinnovations/laya)
using its native 'noul' (yes/no) calibrated decision head over 512-token context.
"""
from __future__ import annotations

import threading
from typing import Any, Dict, Optional, Tuple

_AGENT = None
_AGENT_LOCK = threading.Lock()

TOTAL_CALLS: int = 0
TRUNCATED_CALLS: int = 0
_STATS_LOCK = threading.Lock()


def get_laya_agent():
    """Lazy singleton loader for English Laya model."""
    global _AGENT
    if _AGENT is None:
        with _AGENT_LOCK:
            if _AGENT is None:
                import laya
                _AGENT = laya.load("convaiinnovations/laya")
    return _AGENT


def reset_truncation_stats() -> None:
    """Reset call and truncation counters."""
    global TOTAL_CALLS, TRUNCATED_CALLS
    with _STATS_LOCK:
        TOTAL_CALLS = 0
        TRUNCATED_CALLS = 0


def get_truncation_stats() -> Dict[str, Any]:
    """Return current call counts and truncation rate."""
    with _STATS_LOCK:
        rate = (TRUNCATED_CALLS / TOTAL_CALLS) if TOTAL_CALLS > 0 else 0.0
        return {
            "total_calls": TOTAL_CALLS,
            "truncated_calls": TRUNCATED_CALLS,
            "truncation_rate": rate,
        }


def call_laya(
    rubric: str,
    trace_context: str,
) -> Tuple[bool, float, str, Dict[str, int]]:
    """Invoke Laya local decision model on rubric and trace context.

    Args:
        rubric: Evaluation instructions / rubric.
        trace_context: State string containing scenario prompt, answer, trace.

    Returns:
        (detected, confidence, reason, tokens)
        - detected: bool, True if p >= 0.5
        - confidence: float, calibrated confidence in the decision
        - reason: str, 'laya p=0.xx'
        - tokens: dict, {'prompt': 0, 'completion': 0}
    """
    global TOTAL_CALLS, TRUNCATED_CALLS

    agent = get_laya_agent()

    # Check truncation against Laya's 512-token context
    tok_ids = agent.tok(trace_context, add_special_tokens=False)["input_ids"]
    is_truncated = len(tok_ids) > 512

    with _STATS_LOCK:
        TOTAL_CALLS += 1
        if is_truncated:
            TRUNCATED_CALLS += 1

    questions = {
        "detected": {
            "type": "noul",
            "instructions": rubric,
        }
    }

    with _AGENT_LOCK:
        result = agent.predict(trace_context, questions)

    ans = result["answers"]["detected"]
    p = float(ans["noul"])
    detected = p >= 0.5
    confidence = float(ans.get("confidence", max(p, 1.0 - p)))
    reason = f"laya p={p:.2f}"
    tokens = {"prompt": 0, "completion": 0}

    return detected, confidence, reason, tokens
