"""Fault cards — the committed, human-readable spec for each fault family.

A fault card is the datasheet a stranger reads to understand, reproduce, and
grade a fault: what it does, when it fires, how severity scales it, what detects
it, and what signal that detector emits. Cards are the market/evidence artifact
of Day 9 (they get committed as `evidence/fault_cards.json`).
"""
from __future__ import annotations

from typing import Any, Dict, List

from .latency import BASE_LATENCY, DEFAULT_BUDGET
from .schema import TOKENS_LEN, VALUE_MAX, VALUE_MIN


def fault_cards() -> List[Dict[str, Any]]:
    return [
        {
            "id": "F1",
            "name": "Structured-output corruption",
            "family": "structured-output",
            "built_on": "day8 content modes: corrupt / drop / truncate / duplicate",
            "what": "The boundary returns a schema-violating payload — a wrong "
                    "value, an out-of-range number, or a short/empty/duplicated "
                    "token list.",
            "trigger": "any deterministic day8 trigger (call_index / every_n / "
                       "input_match / seeded-probabilistic)",
            "severity_schedule": {
                "corrupt": "value += severity*111 (leaves range for small severity)",
                "truncate": "drop >= 1 token (severity widens the cut)",
                "drop": "empty tokens + value 0",
                "duplicate": "prepend severity leading tokens (breaks length+order)",
            },
            "detector": "SchemaDetector (validate_output)",
            "schema": {"value_range": [VALUE_MIN, VALUE_MAX],
                       "tokens_length": TOKENS_LEN,
                       "tokens_order": "strictly consecutive (+1)",
                       "step": "non-empty string"},
            "signal": "repair_signal (attempt structured repair downstream)",
            "detectability": "severity-dependent for `corrupt` (small offsets stay "
                             "in-range and are MISSED); structural modes always caught",
            "truth_label_prefix": "F1:",
        },
        {
            "id": "F2",
            "name": "Virtual timeout / latency",
            "family": "latency",
            "built_on": "day8 stall mode (cost-only, content unchanged)",
            "what": "The boundary returns the correct payload but takes too long; "
                    "duration = BASE_LATENCY + severity*10.",
            "trigger": "any deterministic day8 trigger",
            "severity_schedule": {"duration": f"{BASE_LATENCY} + severity*10 "
                                              f"(20,30,40,50,60 for sev 1..5)"},
            "detector": "DurationDetector (duration > budget)",
            "budget": DEFAULT_BUDGET,
            "signal": "timeout_signal (trip a timeout/deadline downstream)",
            "detectability": "budget-gated: caught only when duration > budget "
                             f"(default {DEFAULT_BUDGET} -> severity >= 4)",
            "truth_label": "F2:latency",
        },
    ]
