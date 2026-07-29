"""Deterministic legacy/fixed executions with complete trace-linked regressions."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

_ROOT = Path(__file__).resolve().parents[2]
_DAY04 = str(_ROOT / "day04")
if _DAY04 not in sys.path:
    sys.path.insert(0, _DAY04)

from faultline_trace import Tracer, is_complete  # noqa: E402
from faultline_trace.schema import assert_links_intact  # noqa: E402

from .catalog import IncidentSpec, get_incident
from .config import PostmortemConfig, canonical_config

VERSIONS = ("legacy", "fixed")


class PrimaryTimeout(RuntimeError):
    """The primary did not return before its timeout."""


class BudgetCeilingExceeded(RuntimeError):
    """The next operation cannot fit the configured resource envelope."""


class UserDeadlineExceeded(RuntimeError):
    """The serial recovery cannot complete before the user deadline."""


def canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class _CascadeBudget:
    def __init__(self, config: PostmortemConfig):
        self.cost = 0
        self.steps = 0
        self.latency = 0
        self.config = config

    def charge(self, cost: int, latency: int, operation: str) -> None:
        if self.steps + 1 > self.config.cascade_step_budget:
            raise BudgetCeilingExceeded(
                f"step ceiling blocks {operation}: "
                f"{self.steps + 1}>{self.config.cascade_step_budget}"
            )
        if self.cost + cost > self.config.cascade_cost_budget:
            raise BudgetCeilingExceeded(
                f"cost ceiling blocks {operation}: "
                f"{self.cost + cost}>{self.config.cascade_cost_budget}"
            )
        self.cost += cost
        self.steps += 1
        self.latency += latency

    def delay(self, latency: int) -> None:
        self.latency += latency

    def metrics(self) -> Dict[str, int]:
        return {
            "cost": self.cost,
            "steps": self.steps,
            "latency": self.latency,
            "cost_budget": self.config.cascade_cost_budget,
            "step_budget": self.config.cascade_step_budget,
        }


def _timeline_item(
    at: int,
    event: str,
    detail: str,
    *span_refs: str,
) -> Dict[str, Any]:
    return {
        "at": at,
        "event": event,
        "detail": detail,
        "span_refs": list(span_refs),
    }


def _trace_audit(
    tracer: Tracer,
    timeline: List[Dict[str, Any]],
    regression_refs: List[str],
) -> Dict[str, Any]:
    assert_links_intact(tracer.spans)
    trace = tracer.to_dict()
    span_ids = {span["span_id"] for span in trace["spans"]}
    timeline_refs = {
        ref for item in timeline for ref in item["span_refs"]
    }
    unresolved = sorted((timeline_refs | set(regression_refs)) - span_ids)
    errors = [span for span in trace["spans"] if span["status"] == "error"]
    all_errors_complete = all(
        span["end_seq"] is not None
        and span["error"]
        and span["error"]["type"]
        and span["error"]["message"]
        for span in errors
    )
    result = {
        "span_count": trace["span_count"],
        "error_span_count": len(errors),
        "all_spans_complete": all(is_complete(span) for span in tracer.spans),
        "all_error_spans_complete": bool(errors) and all_errors_complete,
        "unresolved_trace_references": unresolved,
    }
    result["passed"] = (
        result["all_spans_complete"]
        and result["all_error_spans_complete"]
        and not unresolved
    )
    return result


def _regression_result(
    spec: IncidentSpec,
    terminal: Dict[str, Any],
    metrics: Dict[str, Any],
    trace_refs: List[str],
) -> Dict[str, Any]:
    if spec.incident_id == "INC-25-001":
        passed = (
            terminal["correct_answer_returned"]
            and terminal["visible_answer"]
            and not terminal["wrong_visible_answer"]
            and metrics["cost"] <= metrics["cost_budget"]
            and metrics["steps"] <= metrics["step_budget"]
        )
    else:
        passed = (
            terminal["correct_answer_returned"]
            and terminal["visible_answer"]
            and not terminal["wrong_visible_answer"]
            and metrics["cost"] <= metrics["cost_budget"]
            and metrics["latency"] <= metrics["latency_budget"]
        )
    return {
        "test_id": spec.regression_test_id,
        "predicate": spec.regression_predicate,
        "passed": passed,
        "color": "green" if passed else "red",
        "trace_refs": trace_refs,
    }


def _run_stale_fallback(
    spec: IncidentSpec,
    version: str,
    config: PostmortemConfig,
) -> Dict[str, Any]:
    tracer = Tracer(spec.seed)
    budget = _CascadeBudget(config)
    timeline: List[Dict[str, Any]] = []
    reference = {"value": 100, "tokens": [1, 2, 3, 4]}
    stale = {"value": 100, "tokens": [3, 4, 5, 6]}
    regression_refs: List[str] = []

    with tracer.span(
        "postmortem.incident",
        "agent",
        payload={"incident_id": spec.incident_id, "policy_version": version},
    ) as root:
        root.set_attribute("regression_test_id", spec.regression_test_id)
        for attempt in range(2):
            try:
                with tracer.span(
                    f"provider.primary.attempt.{attempt}",
                    "tool",
                    payload={"timeout": 30, "attempt": attempt},
                ) as primary:
                    primary_id = primary.span_id
                    budget.charge(2, 30, f"primary_attempt_{attempt}")
                    raise PrimaryTimeout("primary latency 80 exceeded timeout 30")
            except PrimaryTimeout:
                timeline.append(
                    _timeline_item(
                        budget.latency,
                        f"primary_timeout_{attempt + 1}",
                        "The primary call exceeded its 30-unit timeout.",
                        primary_id,
                    )
                )
            if attempt == 0:
                with tracer.span(
                    "recovery.retry_backoff",
                    "agent",
                    payload={"delay": 5},
                ) as backoff:
                    budget.delay(5)
                    backoff.set_output({"next_attempt": 1})

        with tracer.span(
            "provider.secondary.stale",
            "tool",
            payload={"route": "secondary", "variant": "borderline_tokens"},
        ) as secondary:
            secondary_id = secondary.span_id
            budget.charge(2, 12, "secondary_fallback")
            secondary.set_output(stale)
        timeline.append(
            _timeline_item(
                budget.latency,
                "stale_fallback_returned",
                "The secondary preserved the value but shifted the context tokens.",
                secondary_id,
            )
        )

        if version == "legacy":
            with tracer.span(
                "quality.narrow_judge",
                "model",
                payload={"known_failure_slice": "borderline_tokens"},
            ) as judge:
                judge_id = judge.span_id
                budget.charge(1, 4, "narrow_judge")
                judge.set_output({"verdict": "accept", "strict_quality": False})
            timeline.append(
                _timeline_item(
                    budget.latency,
                    "judge_false_accept",
                    "The narrow judge accepted content in its known failure slice.",
                    judge_id,
                )
            )

            verify_ids: List[str] = []
            for index in range(3):
                with tracer.span(
                    f"agent.verify.{index}",
                    "model",
                    payload={"fingerprint": "stale-fallback", "index": index},
                ) as verify:
                    verify_ids.append(verify.span_id)
                    budget.charge(1, 3, f"verification_{index}")
                    verify.set_output({"consistent": False, "same_fingerprint": True})
            timeline.append(
                _timeline_item(
                    budget.latency,
                    "verification_repeated",
                    "Three checks repeated without changing evidence or route.",
                    *verify_ids,
                )
            )

            with tracer.span(
                "recovery.replan_same_route",
                "agent",
                payload={"blocked_routes": []},
            ) as replan:
                replan_id = replan.span_id
                replan.set_output({"selected_route": "secondary"})
            with tracer.span(
                "provider.secondary.reentry",
                "tool",
                payload={"fingerprint": "stale-fallback"},
            ) as reentry:
                reentry_id = reentry.span_id
                budget.charge(1, 8, "secondary_reentry")
                reentry.set_output(stale)
            timeline.append(
                _timeline_item(
                    budget.latency,
                    "same_route_reentry",
                    "Replan selected the same secondary and identical fingerprint.",
                    replan_id,
                    reentry_id,
                )
            )

            ceiling_id = ""
            try:
                with tracer.span(
                    "budget.final_synthesis",
                    "agent",
                    payload={"cost_before": budget.cost, "next_cost": 2},
                ) as ceiling:
                    ceiling_id = ceiling.span_id
                    budget.charge(2, 5, "final_synthesis")
            except BudgetCeilingExceeded:
                pass
            timeline.append(
                _timeline_item(
                    budget.latency,
                    "cost_ceiling_abort",
                    "Final synthesis would cost 13/12 and was blocked.",
                    ceiling_id,
                )
            )
            terminal = {
                "status": "contained_cost_ceiling",
                "correct_answer_returned": False,
                "visible_answer": False,
                "wrong_visible_answer": False,
            }
            regression_refs = [judge_id, reentry_id, ceiling_id]
        else:
            with tracer.span(
                "quality.strict_token_guard",
                "tool",
                payload={"required": reference, "candidate": stale},
            ) as strict_guard:
                strict_id = strict_guard.span_id
                budget.charge(1, 4, "strict_token_guard")
                strict_guard.set_output(
                    {"verdict": "reject", "tokens_exact": False}
                )
            timeline.append(
                _timeline_item(
                    budget.latency,
                    "strict_guard_reject",
                    "Exact token comparison quarantined the stale response.",
                    strict_id,
                )
            )

            with tracer.span(
                "recovery.route_diversity_fence",
                "agent",
                payload={
                    "quarantined": ["secondary:stale-fallback"],
                    "candidate": "trusted_tertiary",
                },
            ) as diversity:
                diversity_id = diversity.span_id
                diversity.set_output({"selected_route": "trusted_tertiary"})
            with tracer.span(
                "provider.trusted_tertiary",
                "tool",
                payload={"independent_context": True},
            ) as tertiary:
                tertiary_id = tertiary.span_id
                budget.charge(
                    config.trusted_tertiary_cost,
                    config.trusted_tertiary_latency,
                    "trusted_tertiary",
                )
                tertiary.set_output(reference)
            timeline.append(
                _timeline_item(
                    budget.latency,
                    "independent_route_correct",
                    "Route diversity selected an independent exact response.",
                    diversity_id,
                    tertiary_id,
                )
            )

            with tracer.span(
                "agent.final_synthesis",
                "agent",
                payload={"candidate": reference},
            ) as synthesis:
                synthesis_id = synthesis.span_id
                budget.charge(2, 5, "final_synthesis")
                synthesis.set_output({"visible_answer": reference})
            timeline.append(
                _timeline_item(
                    budget.latency,
                    "correct_answer_returned",
                    "The corrected path synthesized within both ceilings.",
                    synthesis_id,
                )
            )
            terminal = {
                "status": "recovered_correct",
                "correct_answer_returned": True,
                "visible_answer": True,
                "wrong_visible_answer": False,
            }
            regression_refs = [
                strict_id,
                diversity_id,
                tertiary_id,
                synthesis_id,
            ]

        root.set_output(
            {
                "policy_version": version,
                "terminal": terminal,
                "metrics": budget.metrics(),
            }
        )

    return _assemble(
        spec, version, config, terminal, budget.metrics(), timeline,
        regression_refs, tracer
    )


def _run_deadline(
    spec: IncidentSpec,
    version: str,
    config: PostmortemConfig,
) -> Dict[str, Any]:
    tracer = Tracer(spec.seed)
    timeline: List[Dict[str, Any]] = []
    cost = 0
    steps = 0
    primary_id = ""
    retry_id = ""

    with tracer.span(
        "postmortem.incident",
        "agent",
        payload={"incident_id": spec.incident_id, "policy_version": version},
    ) as root:
        root.set_attribute("regression_test_id", spec.regression_test_id)
        if version == "fixed":
            with tracer.span(
                "recovery.deadline_feasibility",
                "agent",
                payload={
                    "serial_finish": 50,
                    "deadline": config.deadline_latency_budget,
                    "idempotent_read": True,
                },
            ) as feasibility:
                feasibility_id = feasibility.span_id
                feasibility.set_output(
                    {"serial_feasible": False, "selected": "bounded_hedge"}
                )
            with tracer.span(
                "recovery.hedge_scheduled",
                "agent",
                payload={"start_at": config.hedge_start_latency},
            ) as hedge:
                hedge_id = hedge.span_id
                hedge.set_output({"attempt_limit": 2, "cancel_loser": True})
            timeline.append(
                _timeline_item(
                    config.hedge_start_latency,
                    "bounded_hedge_started",
                    "A second idempotent read started before the primary timeout.",
                    feasibility_id,
                    hedge_id,
                )
            )

        try:
            with tracer.span(
                "provider.primary",
                "tool",
                payload={"timeout": 30, "fault": "transient_latency"},
            ) as primary:
                primary_id = primary.span_id
                cost += 1
                steps += 1
                raise PrimaryTimeout("primary latency exceeded timeout 30")
        except PrimaryTimeout:
            timeline.append(
                _timeline_item(
                    30,
                    "primary_timeout",
                    "The initial idempotent read timed out.",
                    primary_id,
                )
            )

        if version == "legacy":
            try:
                with tracer.span(
                    "recovery.serial_retry",
                    "tool",
                    payload={"start_at": 30, "duration": 20, "deadline": 45},
                ) as retry:
                    retry_id = retry.span_id
                    cost += 1
                    steps += 1
                    raise UserDeadlineExceeded(
                        "serial retry completes at 50 after deadline 45"
                    )
            except UserDeadlineExceeded:
                pass
            timeline.append(
                _timeline_item(
                    config.deadline_latency_budget,
                    "latency_budget_abort",
                    "The recoverable retry could not finish by the user deadline.",
                    retry_id,
                )
            )
            latency = config.deadline_latency_budget
            terminal = {
                "status": "latency_budget_abort",
                "correct_answer_returned": False,
                "visible_answer": False,
                "wrong_visible_answer": False,
            }
            regression_refs = [primary_id, retry_id]
        else:
            with tracer.span(
                "provider.hedged_retry",
                "tool",
                payload={
                    "start_at": config.hedge_start_latency,
                    "complete_at": config.hedge_completion_latency,
                },
            ) as retry:
                retry_id = retry.span_id
                cost += 1
                steps += 1
                retry.set_output(
                    {"answer": "correct", "cancelled_outstanding_calls": 0}
                )
            latency = config.hedge_completion_latency
            timeline.append(
                _timeline_item(
                    latency,
                    "hedged_retry_correct",
                    "The bounded hedge returned a correct answer at the deadline.",
                    retry_id,
                )
            )
            terminal = {
                "status": "recovered_correct",
                "correct_answer_returned": True,
                "visible_answer": True,
                "wrong_visible_answer": False,
            }
            regression_refs = [feasibility_id, hedge_id, primary_id, retry_id]

        metrics = {
            "cost": cost,
            "steps": steps,
            "latency": latency,
            "cost_budget": config.deadline_cost_budget,
            "latency_budget": config.deadline_latency_budget,
        }
        root.set_output(
            {
                "policy_version": version,
                "terminal": terminal,
                "metrics": metrics,
            }
        )

    return _assemble(
        spec, version, config, terminal, metrics, timeline,
        regression_refs, tracer
    )


def _assemble(
    spec: IncidentSpec,
    version: str,
    config: PostmortemConfig,
    terminal: Dict[str, Any],
    metrics: Dict[str, Any],
    timeline: List[Dict[str, Any]],
    regression_refs: List[str],
    tracer: Tracer,
) -> Dict[str, Any]:
    regression = _regression_result(
        spec, terminal, metrics, regression_refs
    )
    audit = _trace_audit(tracer, timeline, regression_refs)
    trace = tracer.to_dict()
    result = {
        "incident_id": spec.incident_id,
        "seed": spec.seed,
        "config": config.to_dict(),
        "config_digest": canonical_digest(config.to_dict()),
        "policy_version": version,
        "terminal": terminal,
        "metrics": metrics,
        "timeline": timeline,
        "regression": regression,
        "trace": trace,
        "trace_digest": canonical_digest(trace),
        "trace_audit": audit,
    }
    result["run_digest"] = canonical_digest(result)
    return result


def run_incident(
    incident_id: str,
    version: str,
    config: PostmortemConfig = None,
) -> Dict[str, Any]:
    if version not in VERSIONS:
        raise ValueError(f"version must be one of {VERSIONS}")
    config = (config or canonical_config()).validate()
    spec = get_incident(incident_id)
    if incident_id == "INC-25-001":
        return _run_stale_fallback(spec, version, config)
    return _run_deadline(spec, version, config)
