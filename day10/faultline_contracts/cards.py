"""Fault cards for F3 (schema drift / semantic corruption) and F4 (provider error)."""
from __future__ import annotations

from typing import Any, Dict, List

from .spec import F3_KINDS, F3_SCHEMA_VALID


def fault_cards() -> List[Dict[str, Any]]:
    return [
        {
            "id": "F3",
            "name": "Schema drift / semantic corruption",
            "family": "wrong-data",
            "what": "The tool returns wrong data. Some outputs are malformed "
                    "(schema catches them); others are SCHEMA-VALID but wrong — a "
                    "different round-ten value, or a shifted-but-consecutive token "
                    "run — which a contract validator accepts.",
            "kinds": {k: ("schema-valid (may escape)" if F3_SCHEMA_VALID[k]
                          else "malformed (schema catches)") for k in F3_KINDS},
            "detectors": ["schema (structural)", "semantic invariant: value is a "
                          "round ten"],
            "detectability": "malformed -> schema; nonmultiple -> invariant; "
                             "drift_value / offbase_tokens -> ESCAPE all deterministic "
                             "contracts (only the oracle catches them)",
            "severity": "scales magnitude but NOT detectability of escaping kinds",
            "signal": "repair_signal (malformed) / invariant_violation",
            "truth_label_prefix": "F3:",
        },
        {
            "id": "F4",
            "name": "Provider error",
            "family": "explicit-failure",
            "what": "The provider returns an explicit error envelope instead of a "
                    "value (a 5xx-style hard failure). The call raises; there is no "
                    "content to inspect.",
            "kinds": {"provider_error": "explicit error (always detectable)"},
            "detectors": ["provider-error detector (explicit flag)"],
            "detectability": "recall 1.0 — the signal is explicit, not inferred",
            "signal": "circuit-breaker signal (open after threshold errors in window)",
            "truth_label_prefix": "F4:",
        },
    ]
