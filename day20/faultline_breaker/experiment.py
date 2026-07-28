"""Attacks + paired configs: false opens, flapping, fallback failure, availability.

  false_open   — a twitchy breaker (threshold=1) opens on an isolated blip and then
                 blocks HEALTHY traffic; a tuned breaker (threshold within a window)
                 rides the blip out and blocks nothing. Tuning is the whole game.
  flapping     — a marginally-up dependency makes a too-eager breaker oscillate
                 OPEN<->HALF_OPEN; a higher success_threshold damps the flapping.
  fallback_failure — primary AND secondary both down: the degraded tier keeps the
                 request answered (flagged degraded), never a hang, provenance intact.
  paired       — no-breaker/no-fallback vs breaker+fallback under a correlated
                 outage: availability, healthy-blocked, and calls-to-a-failing-primary,
                 with a McNemar on per-request "answered".
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable, Dict, List

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT / "day14") not in sys.path:
    sys.path.insert(0, str(_ROOT / "day14"))

from faultline_stats import mcnemar_from_pairs  # noqa: E402 (Day 14)

from .breaker import BreakerConfig, CircuitBreaker
from .runner import run_stream

N = 60
OUTAGE = (20, 40)                       # primary down for ticks [20, 40)


def _outage_fails(t: int) -> bool:
    return OUTAGE[0] <= t < OUTAGE[1]


def _blip_fails(t: int) -> bool:
    return t % 10 == 5                  # a single isolated failure every 10 ticks


def false_open() -> Dict[str, Any]:
    twitchy = run_stream(40, _blip_fails,
                         CircuitBreaker(BreakerConfig(1, 1, 8, 1)), use_fallback=True)
    tuned = run_stream(40, _blip_fails,
                       CircuitBreaker(BreakerConfig(3, 5, 8, 2)), use_fallback=True)
    return {"blip_pattern": "one isolated failure every 10 ticks",
            "twitchy_threshold1": {"healthy_blocked": twitchy["metrics"]["healthy_blocked"],
                                   "opens": sum(1 for x in twitchy["transitions"] if x["to"] == "open")},
            "tuned_threshold3_of_5": {"healthy_blocked": tuned["metrics"]["healthy_blocked"],
                                      "opens": sum(1 for x in tuned["transitions"] if x["to"] == "open")},
            "tuning_prevents_false_opens": tuned["metrics"]["healthy_blocked"] == 0}


def flapping() -> Dict[str, Any]:
    # marginal dependency: fails on odd ticks after the outage starts (never fully recovers)
    def marginal(t): return t >= 15 and t % 2 == 1
    eager = run_stream(N, marginal, CircuitBreaker(BreakerConfig(2, 3, 4, 1)))
    damped = run_stream(N, marginal, CircuitBreaker(BreakerConfig(2, 3, 12, 3)))
    return {"eager": {"transitions": len(eager["transitions"])},
            "damped": {"transitions": len(damped["transitions"])},
            "damping_reduces_flapping": len(damped["transitions"]) < len(eager["transitions"])}


def fallback_failure() -> Dict[str, Any]:
    # primary down for the whole run AND secondary down: only the degraded tier remains
    r = run_stream(N, lambda t: True, CircuitBreaker(BreakerConfig(3, 5, 10, 2)),
                   use_fallback=True, secondary_up=lambda t: False)
    m = r["metrics"]
    return {"availability": m["availability"], "served_degraded": m["served_degraded"],
            "unanswered": m["unanswered"], "primary_calls": m["primary_calls"],
            "degraded_kept_availability": m["availability"] == 1.0 and m["served_degraded"] > 0,
            "failure_not_hidden": m["served_degraded"] > 0}  # degraded answers are flagged


def paired_outage() -> Dict[str, Any]:
    cfg = BreakerConfig(3, 5, 10, 2)
    naive = run_stream(N, _outage_fails, None, use_fallback=False)               # no breaker, no fallback
    breaker_only = run_stream(N, _outage_fails, CircuitBreaker(cfg), use_fallback=False)
    breaker_fb = run_stream(N, _outage_fails, CircuitBreaker(cfg), use_fallback=True)
    mc = mcnemar_from_pairs([o["answered"] for o in naive["outcomes"]],
                            [o["answered"] for o in breaker_fb["outcomes"]])
    return {
        "outage": list(OUTAGE),
        "naive_no_breaker_no_fallback": naive["metrics"],
        "breaker_only": breaker_only["metrics"],
        "breaker_plus_fallback": breaker_fb["metrics"],
        "primary_calls_saved_by_breaker": (naive["metrics"]["primary_calls"]
                                           - breaker_only["metrics"]["primary_calls"]),
        "availability_gain_from_fallback": round(
            breaker_fb["metrics"]["availability"] - naive["metrics"]["availability"], 4),
        "mcnemar_answered_naive_vs_breaker_fb": mc,
    }


def build_report() -> Dict[str, Any]:
    return {
        "false_open": false_open(),
        "flapping": flapping(),
        "fallback_failure": fallback_failure(),
        "paired_outage": paired_outage(),
    }
