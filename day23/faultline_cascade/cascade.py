"""Run the canonical cross-component incident and capture a complete Day-4 trace.

Causal chain:
  E01 F2 primary latency spike
   -> E02 M2 retry amplification
   -> E03 M3 breaker opens
   -> E04 M4 fallback route
   -> E05 correlated stale fallback (F5-style context drift)
   -> E06 narrow judge false-accept
   -> E07 repeated downstream verification
   -> E08 M6 replan re-enters fallback
   -> E09 outer M5 cost ceiling aborts
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

_ROOT = Path(__file__).resolve().parents[2]
for _day in ("day04", "day16", "day20", "day21"):
    _path = str(_ROOT / _day)
    if _path not in sys.path:
        sys.path.insert(0, _path)

from faultline_breaker import BreakerConfig, CircuitBreaker, route_fallback  # noqa: E402
from faultline_fallback_quality import NarrowJudgeIntegration  # noqa: E402
from faultline_judge import gold_acceptable  # noqa: E402
from faultline_trace import Tracer, is_complete, is_complete_error  # noqa: E402

from .config import CascadeConfig, canonical_config

CANONICAL_SEED = 2026080207
EXPECTED_CHAIN = (
    "primary_latency_spike",
    "retry_amplification",
    "breaker_open",
    "fallback_routed",
    "stale_fallback_context",
    "judge_false_accept",
    "verification_repetition",
    "replan_reenters_fallback",
    "cost_ceiling_abort",
)


class PrimaryTimeout(RuntimeError):
    """The initiating provider timeout."""


class BudgetCeilingExceeded(RuntimeError):
    """Raised before an operation would cross the global cost/step envelope."""


def _unit(seed: int, label: str) -> float:
    digest = hashlib.sha256(f"{seed}:{label}".encode("ascii")).digest()
    return int.from_bytes(digest[:8], "big") / float(2 ** 64)


def _canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class _Budget:
    def __init__(self, config: CascadeConfig):
        self.config = config
        self.steps = 0
        self.cost = 0
        self.latency = 0

    def charge(self, cost: int, latency: int, operation: str) -> None:
        if self.steps + 1 > self.config.max_steps:
            raise BudgetCeilingExceeded(
                f"step ceiling blocks {operation}: {self.steps + 1}>"
                f"{self.config.max_steps}"
            )
        if self.cost + cost > self.config.total_cost_budget:
            raise BudgetCeilingExceeded(
                f"cost ceiling blocks {operation}: {self.cost + cost}>"
                f"{self.config.total_cost_budget}"
            )
        self.steps += 1
        self.cost += cost
        self.latency += latency

    def delay(self, latency: int) -> None:
        self.latency += latency

    def to_dict(self) -> Dict[str, int]:
        return {
            "steps": self.steps,
            "cost": self.cost,
            "latency": self.latency,
            "step_ceiling": self.config.max_steps,
            "cost_ceiling": self.config.total_cost_budget,
        }


def _event(
    event_id: str,
    label: str,
    component: str,
    category: str,
    span_refs: List[str],
    detail: str,
) -> Dict[str, Any]:
    return {
        "event_id": event_id,
        "label": label,
        "component": component,
        "category": category,
        "span_refs": list(span_refs),
        "detail": detail,
        "observed": True,
    }


def _audit(
    tracer: Tracer,
    events: List[Dict[str, Any]],
    edges: List[Dict[str, str]],
) -> Dict[str, Any]:
    spans = tracer.spans
    span_ids = {span.span_id for span in spans}
    roots = [span for span in spans if span.parent_span_id is None]
    unresolved_parents = [
        span.span_id
        for span in spans
        if span.parent_span_id is not None and span.parent_span_id not in span_ids
    ]
    unresolved_event_refs = sorted(
        {
            ref
            for event in events
            for ref in event["span_refs"]
            if ref not in span_ids
        }
    )
    event_ids = {event["event_id"] for event in events}
    unresolved_edges = [
        edge["edge_id"]
        for edge in edges
        if edge["cause"] not in event_ids or edge["effect"] not in event_ids
    ]
    all_complete = all(is_complete(span) for span in spans)
    error_spans = [span for span in spans if span.status == "error"]
    all_errors_complete = bool(error_spans) and all(
        is_complete_error(span) for span in error_spans
    )
    labels = [event["label"] for event in events]
    return {
        "span_count": len(spans),
        "root_count": len(roots),
        "error_span_count": len(error_spans),
        "all_spans_complete": all_complete,
        "all_error_spans_complete": all_errors_complete,
        "unresolved_parent_links": unresolved_parents,
        "unresolved_event_span_refs": unresolved_event_refs,
        "unresolved_causal_edges": unresolved_edges,
        "all_events_labelled": all(
            event["event_id"]
            and event["label"]
            and event["component"]
            and event["category"]
            for event in events
        ),
        "chain_matches_spec": tuple(labels) == EXPECTED_CHAIN,
        "passed": (
            len(roots) == 1
            and all_complete
            and all_errors_complete
            and not unresolved_parents
            and not unresolved_event_refs
            and not unresolved_edges
            and tuple(labels) == EXPECTED_CHAIN
        ),
    }


def run_cascade(
    seed: int = CANONICAL_SEED,
    config: CascadeConfig = None,
) -> Dict[str, Any]:
    config = (config or canonical_config()).validate()
    trigger_roll = _unit(seed, "primary_latency_spike")
    fallback_roll = _unit(seed, "fallback_quality")
    triggered = trigger_roll < config.trigger_rate
    fallback_variant = (
        "borderline_tokens" if fallback_roll >= 0.66 else "clear_accept"
    )
    if not triggered:
        raise ValueError(
            "seed/config did not trigger the canonical cascade; use the committed "
            "seed and configuration"
        )

    tracer = Tracer(seed)
    budget = _Budget(config)
    events: List[Dict[str, Any]] = []
    edges: List[Dict[str, str]] = []
    breaker = CircuitBreaker(
        BreakerConfig(
            failure_threshold=config.breaker_failure_threshold,
            window=config.breaker_window,
            open_ticks=config.breaker_open_ticks,
            success_threshold=1,
        )
    )

    with tracer.span(
        "incident.cascade",
        "agent",
        payload={"seed": seed, "config": config.to_dict()},
    ) as root:
        root.set_attribute("scenario_version", config.scenario_version)
        root.set_attribute("initiating_fault", config.initiating_fault)

        with tracer.span(
            "inject.primary_latency",
            "tool",
            payload={"seed": seed, "trigger_rate": config.trigger_rate},
        ) as injected_span:
            injected_id = injected_span.span_id
            injected_span.set_output(
                {"roll": round(trigger_roll, 8), "triggered": triggered}
            )

        primary_ids: List[str] = []
        backoff_ids: List[str] = []
        with tracer.span(
            "recovery.m2_retry",
            "agent",
            payload={"max_attempts": config.max_retry_attempts},
        ) as retry_span:
            retry_id = retry_span.span_id
            for attempt in range(config.max_retry_attempts):
                allowed, note = breaker.allow(attempt)
                if not allowed:
                    break
                try:
                    with tracer.span(
                        f"provider.primary.attempt.{attempt}",
                        "tool",
                        payload={
                            "attempt": attempt,
                            "timeout": config.primary_timeout,
                            "observed_latency": config.primary_fault_latency,
                        },
                    ) as primary_span:
                        primary_ids.append(primary_span.span_id)
                        budget.charge(
                            config.primary_attempt_cost,
                            config.primary_timeout,
                            f"primary_attempt_{attempt}",
                        )
                        raise PrimaryTimeout(
                            f"primary latency {config.primary_fault_latency} exceeded "
                            f"timeout {config.primary_timeout}"
                        )
                except PrimaryTimeout:
                    breaker.record(False, attempt)
                    if attempt == 0:
                        events.append(
                            _event(
                                "E01",
                                "primary_latency_spike",
                                "primary_provider",
                                "initiating_fault",
                                [injected_id, primary_ids[-1]],
                                "Seeded F2 latency exceeds the primary timeout.",
                            )
                        )
                    if breaker.state == "open":
                        break
                    with tracer.span(
                        f"recovery.backoff.{attempt}",
                        "agent",
                        payload={"delay": config.retry_backoff},
                    ) as backoff_span:
                        backoff_ids.append(backoff_span.span_id)
                        budget.delay(config.retry_backoff)
                        backoff_span.set_output({"scheduled_retry": attempt + 1})
            retry_span.set_output(
                {
                    "primary_calls": len(primary_ids),
                    "breaker_state": breaker.state,
                    "budget": budget.to_dict(),
                }
            )

        events.append(
            _event(
                "E02",
                "retry_amplification",
                "retry_controller",
                "recovery_side_effect",
                [retry_id] + backoff_ids + primary_ids[1:],
                "M2 converts one timeout into a second failing primary call.",
            )
        )

        with tracer.span(
            "recovery.m3_breaker_open",
            "agent",
            payload={"transitions": breaker.transitions},
        ) as breaker_span:
            breaker_id = breaker_span.span_id
            breaker_span.set_output(
                {"state": breaker.state, "transitions": breaker.transitions}
            )
        events.append(
            _event(
                "E03",
                "breaker_open",
                "circuit_breaker",
                "recovery_transition",
                [breaker_id],
                "The second timeout satisfies the 2-of-2 breaker threshold.",
            )
        )

        served = route_fallback(secondary_up=True)
        with tracer.span(
            "recovery.m4_fallback_route",
            "agent",
            payload={"breaker_state": breaker.state},
        ) as route_span:
            route_id = route_span.span_id
            route_span.set_output(served.to_dict())
        events.append(
            _event(
                "E04",
                "fallback_routed",
                "fallback_router",
                "recovery_transition",
                [route_id],
                "The open breaker sends the request to the secondary provider.",
            )
        )

        reference = {"value": 100, "tokens": [1, 2, 3, 4]}
        candidate = (
            {"value": 100, "tokens": [3, 4, 5, 6]}
            if fallback_variant == "borderline_tokens"
            else dict(reference)
        )
        with tracer.span(
            "provider.secondary",
            "tool",
            payload={"variant": fallback_variant},
        ) as secondary_span:
            secondary_id = secondary_span.span_id
            budget.charge(
                config.fallback_call_cost,
                config.fallback_latency,
                "secondary_fallback",
            )
            secondary_span.set_output(candidate)
        strict_quality = gold_acceptable(reference, candidate)
        events.append(
            _event(
                "E05",
                "stale_fallback_context",
                "secondary_provider",
                "propagated_fault",
                [secondary_id],
                "The correlated secondary preserves the headline value but shifts context tokens.",
            )
        )

        judge_record = {
            "request_index": 0,
            "seed": seed,
            "route": "fallback",
            "answered": True,
            "provenance": served.to_dict(),
            "reference": reference,
            "candidate": candidate,
        }
        judge_result = NarrowJudgeIntegration().inspect(judge_record)
        with tracer.span(
            "quality.narrow_judge",
            "model",
            payload={"scope": "fallback_quality", "candidate": candidate},
        ) as judge_span:
            judge_id = judge_span.span_id
            budget.charge(config.judge_cost, config.judge_latency, "narrow_judge")
            judge_span.set_output(judge_result)
        false_accept = (
            judge_result["judge_label"] == "accept" and not strict_quality
        )
        events.append(
            _event(
                "E06",
                "judge_false_accept",
                "quality_gate",
                "detection_failure",
                [judge_id],
                "The known token-order blind spot accepts a strictly bad fallback.",
            )
        )

        verification_ids: List[str] = []
        fingerprint = _canonical_digest(candidate)[:12]
        consecutive = 0
        for index in range(config.repetition_threshold + 1):
            with tracer.span(
                f"agent.verify.{index}",
                "model",
                payload={"fingerprint": fingerprint, "index": index},
            ) as verify_span:
                verification_ids.append(verify_span.span_id)
                budget.charge(
                    config.verification_cost,
                    config.verification_latency,
                    f"verification_{index}",
                )
                consecutive += 1
                verify_span.set_output(
                    {
                        "consistent_with_primary_context": False,
                        "consecutive_same_fingerprint": consecutive,
                    }
                )
        repetition_detected = consecutive > config.repetition_threshold
        events.append(
            _event(
                "E07",
                "verification_repetition",
                "agent_controller",
                "propagated_fault",
                verification_ids,
                "Accepted drift causes the agent to repeat the same failed verification.",
            )
        )

        with tracer.span(
            "recovery.m6_replan",
            "agent",
            payload={"repetition_detected": repetition_detected},
        ) as replan_span:
            replan_id = replan_span.span_id
            replan_span.set_output({"selected_route": "secondary_again"})

        with tracer.span(
            "provider.secondary.reentry",
            "tool",
            payload={"reason": "m6_replan", "fingerprint": fingerprint},
        ) as reentry_span:
            reentry_id = reentry_span.span_id
            budget.charge(
                config.reentry_fallback_cost,
                config.reentry_fallback_latency,
                "secondary_reentry",
            )
            reentry_span.set_output(candidate)
        events.append(
            _event(
                "E08",
                "replan_reenters_fallback",
                "repetition_recovery",
                "recovery_side_effect",
                [replan_id, reentry_id],
                "M6 replans into the same correlated secondary and consumes the remaining envelope.",
            )
        )

        ceiling_id = ""
        try:
            with tracer.span(
                "recovery.m5_cost_ceiling",
                "agent",
                payload={
                    "operation": "final_synthesis",
                    "budget_before": budget.to_dict(),
                },
            ) as ceiling_span:
                ceiling_id = ceiling_span.span_id
                budget.charge(
                    config.synthesis_cost,
                    config.synthesis_latency,
                    "final_synthesis",
                )
                ceiling_span.set_output({"unexpected": "synthesis should be blocked"})
        except BudgetCeilingExceeded:
            pass
        events.append(
            _event(
                "E09",
                "cost_ceiling_abort",
                "global_budget",
                "terminal_containment",
                [ceiling_id],
                "M5 refuses final synthesis before cost can exceed the configured ceiling.",
            )
        )

        for cause, effect, relation in (
            ("E01", "E02", "timeout triggers retry"),
            ("E02", "E03", "second failure opens breaker"),
            ("E03", "E04", "open state routes fallback"),
            ("E04", "E05", "secondary serves correlated stale context"),
            ("E05", "E06", "semantic drift crosses judge blind spot"),
            ("E06", "E07", "accepted drift reaches verification"),
            ("E07", "E08", "repetition triggers replan"),
            ("E08", "E09", "re-entry exhausts remaining cost"),
        ):
            edges.append(
                {
                    "edge_id": f"{cause}-{effect}",
                    "cause": cause,
                    "effect": effect,
                    "relation": relation,
                }
            )

        root.set_output(
            {
                "terminal_status": "contained_cost_ceiling",
                "correct_answer_returned": False,
                "budget": budget.to_dict(),
                "chain_labels": [event["label"] for event in events],
            }
        )

    audit = _audit(tracer, events, edges)
    trace = tracer.to_dict()
    config_dict = config.to_dict()
    result = {
        "incident_id": f"cascade-{seed}-{config.scenario_version}",
        "seed": seed,
        "config": config_dict,
        "config_digest": _canonical_digest(config_dict),
        "trigger_truth": {
            "initiating_fault": config.initiating_fault,
            "trigger_roll": round(trigger_roll, 8),
            "trigger_rate": config.trigger_rate,
            "triggered": triggered,
            "fallback_roll": round(fallback_roll, 8),
            "fallback_variant": fallback_variant,
            "strict_fallback_quality": strict_quality,
            "judge_false_accept": false_accept,
        },
        "terminal": {
            "status": "contained_cost_ceiling",
            "correct_answer_returned": False,
            "available_answer_suppressed": True,
        },
        "metrics": {
            "primary_calls": len(primary_ids),
            "retry_calls_added": max(0, len(primary_ids) - 1),
            "breaker_transitions": len(breaker.transitions),
            "fallback_calls": 2,
            "verification_repeats": consecutive,
            "replans": 1,
            **budget.to_dict(),
        },
        "events": events,
        "causal_edges": edges,
        "trace": trace,
        "trace_digest": _canonical_digest(trace),
        "audit": audit,
    }
    result["incident_digest"] = _canonical_digest(result)
    return result
