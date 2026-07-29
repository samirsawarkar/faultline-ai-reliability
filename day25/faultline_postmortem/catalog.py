"""Two blameless incident specifications grounded in Day 23 and Day 24."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class IncidentSpec:
    incident_id: str
    slug: str
    title: str
    seed: int
    source_artifact: str
    impact: str
    detection: str
    root_cause: str
    contributing_factors: Tuple[str, ...]
    corrective_actions: Tuple[str, ...]
    regression_test_id: str
    regression_predicate: str

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["contributing_factors"] = list(self.contributing_factors)
        data["corrective_actions"] = list(self.corrective_actions)
        return data


INCIDENTS: Tuple[IncidentSpec, ...] = (
    IncidentSpec(
        incident_id="INC-25-001",
        slug="stale-fallback-reentry",
        title="Stale fallback crossed the quality gate and re-entered recovery",
        seed=2026080207,
        source_artifact="day23/evidence/cascade_trace.json",
        impact=(
            "The canonical request returned no correct answer. Recovery consumed "
            "11/12 cost units and 98 virtual ms; M5 contained the wrong fallback "
            "before synthesis, so this was lost service rather than a visible wrong answer."
        ),
        detection=(
            "The Day-23 trace linked a narrow-judge accept on strictly bad token "
            "context to three repeated verifications, same-provider re-entry, and "
            "the terminal cost-ceiling error."
        ),
        root_cause=(
            "The controller treated a narrow judge as sufficient inside its "
            "documented token-order failure slice, so corrupted fallback context "
            "remained eligible for recovery."
        ),
        contributing_factors=(
            "The secondary provider shared stale context with the failed primary path.",
            "M6 had no route-diversity fence and selected the same provider/fingerprint.",
            "The budget envelope contained the blast radius but reserved no path to a correct answer.",
        ),
        corrective_actions=(
            "Apply an exact deterministic token check before fallback content may re-enter synthesis.",
            "Quarantine the rejected provider/fingerprint for the request.",
            "Require repetition recovery to choose an independent trusted route.",
        ),
        regression_test_id="R25-001-correct-within-cascade-envelope",
        regression_predicate=(
            "correct answer is visible, no wrong answer is visible, cost <= 12, "
            "and steps <= 9"
        ),
    ),
    IncidentSpec(
        incident_id="INC-25-002",
        slug="serial-retry-misses-deadline",
        title="A recoverable transient fault missed the user deadline",
        seed=2026080301,
        source_artifact="day24/evidence/winner_attack.json",
        impact=(
            "The selected transient request had a recoverable second attempt, but "
            "the serial policy produced no answer by the 45-unit deadline. In the "
            "Day-24 tight-budget attack, all 105 transient cases followed this "
            "latency-abort path."
        ),
        detection=(
            "The Day-24 attack separated 105 latency-budget aborts from 65 "
            "cost-budget aborts. The trace shows that waiting for the full "
            "30-unit timeout left too little time for the 20-unit retry."
        ),
        root_cause=(
            "The recovery schedule was deadline-infeasible: it launched the retry "
            "only after the primary timeout even though 30 + 20 exceeded the "
            "45-unit user deadline."
        ),
        contributing_factors=(
            "The policy checked the latency ceiling after choosing a serial retry.",
            "The request was an idempotent read, but the policy did not exploit safe overlap.",
            "Aggregate budget reporting initially obscured whether cost or latency stopped recovery.",
        ),
        corrective_actions=(
            "Run a feasibility check before selecting recovery.",
            "For idempotent reads, launch one bounded hedge at virtual time 20.",
            "Keep the existing two-call cost ceiling and cancel outstanding work after the first valid answer.",
        ),
        regression_test_id="R25-002-correct-by-user-deadline",
        regression_predicate=(
            "correct answer is visible, no wrong answer is visible, cost <= 2, "
            "and latency <= 45"
        ),
    ),
)


def get_incident(incident_id: str) -> IncidentSpec:
    for incident in INCIDENTS:
        if incident.incident_id == incident_id:
            return incident
    raise ValueError(f"unknown incident: {incident_id}")
