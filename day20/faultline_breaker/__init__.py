"""FAULTLINE Day 20: M3/M4 — circuit breaker + provider fallback, fully traceable.

Restore availability under a failing dependency without hiding failures (degraded
answers are flagged) or blocking healthy traffic (a tuned breaker rides out blips).
Every breaker transition and every fallback provenance is recorded. Builds on Day 4
(traces), Day 14 (McNemar), Day 19 (why the breaker is needed).

Public surface:
    breaker:  CircuitBreaker, BreakerConfig, CLOSED, OPEN, HALF_OPEN
    fallback: Served, route_fallback
    runner:   run_stream
    experiment: build_report, false_open, flapping, fallback_failure, paired_outage
    diagram:  render_state_diagram, render_timeline
"""
from . import breaker, diagram, experiment, fallback, runner
from .breaker import CLOSED, HALF_OPEN, OPEN, BreakerConfig, CircuitBreaker
from .diagram import render_state_diagram, render_timeline
from .experiment import (build_report, fallback_failure, false_open, flapping,
                         paired_outage)
from .fallback import Served, route_fallback
from .runner import run_stream

__all__ = [
    "CircuitBreaker", "BreakerConfig", "CLOSED", "OPEN", "HALF_OPEN",
    "Served", "route_fallback", "run_stream",
    "build_report", "false_open", "flapping", "fallback_failure", "paired_outage",
    "render_state_diagram", "render_timeline",
    "breaker", "fallback", "runner", "experiment", "diagram",
]
