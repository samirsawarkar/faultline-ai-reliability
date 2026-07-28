"""Breaker states, fallback provenance, and the traceability fail-condition."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1].parent / "day04"))
import faultline_trace as ft

import faultline_breaker as cb
from faultline_breaker.breaker import BreakerConfig, CircuitBreaker, CLOSED, HALF_OPEN, OPEN


def test_config_rejects_bad_values():
    with pytest.raises(ValueError):
        BreakerConfig(failure_threshold=6, window=5).validate()
    with pytest.raises(ValueError):
        BreakerConfig(open_ticks=0).validate()


def test_full_transition_cycle_is_recorded():
    b = CircuitBreaker(BreakerConfig(3, 5, 10, 2))
    t = 0
    for _ in range(3):                    # CLOSED -> OPEN
        b.allow(t); b.record(False, t); t += 1
    assert b.state == OPEN
    assert not b.allow(t)[0]              # short-circuit during cooldown
    t = b.opened_tick + 10
    assert b.allow(t)[0]                  # OPEN -> HALF_OPEN (trial allowed)
    b.record(True, t); b.record(True, t + 1)   # 2 successes -> CLOSED
    assert b.state == CLOSED
    seq = [(x["from"], x["to"], x["reason"]) for x in b.transitions]
    assert seq == [("closed", "open", "failure_threshold"),
                   ("open", "half_open", "cooldown_elapsed"),
                   ("half_open", "closed", "recovered")]


def test_half_open_failure_reopens():
    b = CircuitBreaker(BreakerConfig(2, 3, 5, 2))
    for _ in range(2):
        b.allow(0); b.record(False, 0)
    assert b.state == OPEN
    b.allow(5)                            # cooldown elapsed -> half_open
    assert b.state == HALF_OPEN
    b.record(False, 5)                    # a trial fails -> OPEN again
    assert b.state == OPEN
    assert b.transitions[-1]["reason"] == "half_open_failed"


def test_transitions_and_provenance_are_traceable():
    # the fail condition: breaker transitions AND fallback provenance must be traceable
    tr = ft.Tracer(1)
    r = cb.run_stream(60, lambda t: 20 <= t < 40, CircuitBreaker(BreakerConfig(3, 5, 10, 2)),
                      use_fallback=True, tracer=tr)
    assert r["transitions"] and all({"from", "to", "reason", "tick"} <= set(x) for x in r["transitions"])
    for o in r["outcomes"]:
        assert "served_by" in o and "is_degraded" in o and "short_circuited" in o
    assert r["trace"]["span_count"] == 60          # every request traced


def test_tuning_prevents_false_opens():
    fo = cb.false_open()
    assert fo["twitchy_threshold1"]["healthy_blocked"] > 0
    assert fo["tuned_threshold3_of_5"]["healthy_blocked"] == 0
    assert fo["tuning_prevents_false_opens"] is True


def test_damping_reduces_flapping():
    fl = cb.flapping()
    assert fl["damped"]["transitions"] < fl["eager"]["transitions"]


def test_degraded_keeps_availability_without_hiding_failure():
    ff = cb.fallback_failure()
    assert ff["availability"] == 1.0 and ff["unanswered"] == 0
    assert ff["served_degraded"] > 0            # answered, but flagged degraded
    assert ff["failure_not_hidden"] is True


def test_breaker_cuts_primary_load_and_fallback_restores_availability():
    p = cb.paired_outage()
    assert p["primary_calls_saved_by_breaker"] > 0          # breaker protects the dependency
    assert p["availability_gain_from_fallback"] > 0         # fallback restores availability
    assert p["breaker_plus_fallback"]["availability"] == 1.0
    assert p["mcnemar_answered_naive_vs_breaker_fb"]["significant_at_0.05"] is True


def test_report_is_deterministic():
    assert cb.build_report() == cb.build_report()
