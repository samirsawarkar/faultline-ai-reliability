"""The six fault cards — the normalized, defensible specification of F1-F6.

Each card carries a NORMALIZED 10-field spec (the Day-8 field contract, used
uniformly for all six families) plus the five fields the mission requires every
card to have: trigger, trace, detector, recovery, metric. `validate_card`
enforces that none is missing — that is the mission's fail condition made into an
assertion.

The static skeleton lives here; the live `metric` (pulled from the day that
measured it) and the labelled `trace` (regenerated deterministically) are filled
in by `catalog.build_catalog`, so the card is evidence-backed, not hand-typed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

SPEC_VERSION = "1.0.0"
SPEC_FIELDS = ("fault_id", "component", "mode", "severity", "trigger",
               "trigger_value", "seed", "rate", "label", "spec_version")
REQUIRED_CARD_FIELDS = ("trigger", "trace", "detector", "recovery", "metric")


def _spec(fault_id: str, mode: str, label: str, *, severity: int = 3,
          trigger: str = "every_n", trigger_value: str = "2") -> Dict[str, Any]:
    """A normalized 10-field spec (same field contract for every family)."""
    return {
        "fault_id": fault_id, "component": "*", "mode": mode, "severity": severity,
        "trigger": trigger, "trigger_value": trigger_value, "seed": 1, "rate": 1.0,
        "label": label, "spec_version": SPEC_VERSION,
    }


@dataclass
class FaultCard:
    id: str
    name: str
    family: str
    producing_component: str
    spec: Dict[str, Any]
    trigger: str
    detector: Dict[str, Any]
    recovery: Dict[str, Any]
    metric: Dict[str, Any] = field(default_factory=dict)   # filled by catalog
    trace: Dict[str, Any] = field(default_factory=dict)     # filled by catalog

    def validate(self) -> "FaultCard":
        if list(self.spec.keys()) != list(SPEC_FIELDS):
            raise ValueError(
                f"{self.id}: spec must have exactly the 10 normalized fields "
                f"{SPEC_FIELDS}, got {tuple(self.spec.keys())}")
        for f in REQUIRED_CARD_FIELDS:
            if not getattr(self, f):
                raise ValueError(
                    f"{self.id}: fault card is missing required field '{f}' "
                    f"(a card must have trigger, trace, detector, recovery, metric)")
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "name": self.name, "family": self.family,
            "producing_component": self.producing_component, "spec": self.spec,
            "trigger": self.trigger, "trace": self.trace, "detector": self.detector,
            "recovery": self.recovery, "metric": self.metric,
        }


def card_skeletons() -> List[FaultCard]:
    """The six cards with everything except the live metric and trace."""
    return [
        FaultCard(
            id="F1", name="Structured-output corruption", family="structured-output",
            producing_component="tool output (data plane)",
            spec=_spec("F1", "corrupt", "F1:corrupt"),
            trigger="Deterministic: every_n=2 on the call index; verdict is a pure "
                    "function of (spec, run_seed, seq, input_digest). Severity scales "
                    "the value offset.",
            detector={"name": "schema validator", "nature": "deterministic",
                      "signal": "repair_signal", "measured_in": "day9"},
            recovery={"strategy": "structured repair, then bounded retry",
                      "signal_today": "repair_signal (day9)",
                      "planned_mechanism": "M1 repair-retry (Mission 18)",
                      "deterministic": True}),
        FaultCard(
            id="F2", name="Tool latency / timeout", family="latency",
            producing_component="tool/provider transport (timing)",
            spec=_spec("F2", "stall", "F2:latency", severity=4),
            trigger="Deterministic: every_n=2 on the call index; virtual duration = "
                    "BASE + severity*10 (no wall clock).",
            detector={"name": "duration vs budget", "nature": "deterministic",
                      "signal": "timeout_signal", "measured_in": "day9"},
            recovery={"strategy": "timeout then bounded retry / hedge",
                      "signal_today": "timeout_signal (day9)",
                      "planned_mechanism": "M2 timeout policy (Mission 18)",
                      "deterministic": True}),
        FaultCard(
            id="F3", name="Schema drift / semantic corruption", family="wrong-data",
            producing_component="tool output (data plane)",
            spec=_spec("F3", "drift_value", "F3:drift_value"),
            trigger="Deterministic: call_index on a fixed run; produces a different "
                    "in-range round-ten value (schema-valid, wrong).",
            detector={"name": "schema + value invariant", "nature": "mixed",
                      "signal": "invariant_violation (caught subset only)",
                      "measured_in": "day10",
                      "note": "drift_value/offbase_tokens ESCAPE all deterministic checks"},
            recovery={"strategy": "semantic validation (oracle/judge), then reject/repair",
                      "signal_today": "invariant_violation for incoherent subset; "
                                      "coherent drift escapes",
                      "planned_mechanism": "validated judge (Mission 16)",
                      "deterministic": False}),
        FaultCard(
            id="F4", name="Provider error", family="explicit-failure",
            producing_component="tool/provider transport (availability)",
            spec=_spec("F4", "provider_error", "F4:provider_error", severity=5),
            trigger="Deterministic: every_n=2 on the call index; the call raises an "
                    "explicit error envelope (no content).",
            detector={"name": "explicit error flag", "nature": "deterministic",
                      "signal": "provider_error + circuit-breaker", "measured_in": "day10"},
            recovery={"strategy": "circuit breaker, then fallback provider",
                      "signal_today": "circuit-breaker open (day10)",
                      "planned_mechanism": "M3 circuit breaker / M4 fallback (Mission 20)",
                      "deterministic": True}),
        FaultCard(
            id="F5", name="Context corruption", family="semantic",
            producing_component="agent context / state (memory)",
            spec=_spec("F5", "context_drift", "F5:context_drift", severity=2,
                       trigger="call_index", trigger_value="0"),
            trigger="Deterministic: call_index on the run; a plausible wrong context "
                    "value is inserted and the final recomputed to stay consistent.",
            detector={"name": "context-consistency invariant", "nature": "semantic",
                      "signal": "context_integrity violation (incoherent only)",
                      "measured_in": "day11",
                      "note": "coherent context_drift escapes; needs the oracle"},
            recovery={"strategy": "context re-grounding / cross-source agreement",
                      "signal_today": "context_integrity violation for incoherent subset",
                      "planned_mechanism": "context validation + judge",
                      "deterministic": False}),
        FaultCard(
            id="F6", name="Loop exhaustion", family="deterministic-termination",
            producing_component="agent control loop (controller)",
            spec=_spec("F6", "repetition", "F6:repetition", severity=2,
                       trigger="call_index", trigger_value="0"),
            trigger="Deterministic: call_index on the run; the loop repeats a step or "
                    "burns the step budget without completing.",
            detector={"name": "repetition + step-budget", "nature": "deterministic",
                      "signal": "loop_detect (repetition or budget-exhaustion)",
                      "measured_in": "day11"},
            recovery={"strategy": "structural step-budget cap + abort; progress check",
                      "signal_today": "loop_detect (day11)",
                      "planned_mechanism": "bounded loop (Day 2) + recovery policies",
                      "deterministic": True}),
    ]
