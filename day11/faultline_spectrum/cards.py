"""Fault cards for F5 (context corruption) and F6 (loop exhaustion)."""
from __future__ import annotations

from typing import Any, Dict, List

from .task import M_STEPS, STEP_BUDGET


def fault_cards() -> List[Dict[str, Any]]:
    return [
        {
            "id": "F5",
            "name": "Context corruption",
            "family": "semantic",
            "what": "A plausible WRONG value enters the task's running context and "
                    "flows into the final result. The output stays well-formed.",
            "kinds": {
                "context_drift": "a coherent wrong value (final recomputed to match) "
                                 "-> passes the consistency invariant, ESCAPES; needs oracle",
                "context_inconsistent": "a wrong value with the final left unchanged "
                                        "-> breaks final==sum(context); caught",
            },
            "detector": "context-consistency invariant (final == sum(context))",
            "detection_nature": "semantic",
            "detectability": "consistency catches the incoherent kind; the coherent "
                             "drift requires semantic evaluation (oracle)",
            "signal": "context_integrity violation",
            "truth_label_prefix": "F5:",
        },
        {
            "id": "F6",
            "name": "Loop exhaustion",
            "family": "deterministic",
            "what": f"The agent loop fails to terminate correctly within its step "
                    f"budget ({STEP_BUDGET}); a clean task completes in {M_STEPS} steps.",
            "kinds": {
                "repetition": "the loop repeats a step and never progresses",
                "budget_exhaustion": "the loop hits the step budget without completing",
            },
            "detector": "repetition detector + step-budget detector",
            "detection_nature": "deterministic",
            "detectability": "recall 1.0 — counting and equality, no correctness model",
            "signal": "loop_detect (repetition or budget-exhaustion)",
            "truth_label_prefix": "F6:",
        },
    ]
