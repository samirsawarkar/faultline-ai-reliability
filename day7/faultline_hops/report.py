"""Assemble the Q1 result: the measured-vs-naive finding with intervals."""
from __future__ import annotations

from typing import Any, Dict

from .model import build_curves
from .observability import check_gate
from .simulator import DECAY, P0, PMIN
from .sweep import SweepConfig, run_sweep


def build_q1(config: SweepConfig | None = None) -> Dict[str, Any]:
    config = config or SweepConfig()
    sweep = run_sweep(config)
    gate = check_gate(sweep)          # observability gate must pass before we report
    curves = build_curves(sweep)

    pts = curves["points"]
    last = pts[-1]
    div = curves["first_divergence_hop"]

    finding = (
        f"End-to-end reliability decays faster than naive constant-per-step "
        f"compounding predicts. Single-hop reliability is "
        f"{curves['single_hop_reliability']['p1']}, but by {last['hops']} hops "
        f"measured success is {last['measured']} "
        f"(95% CI {last['measured_ci95']}) versus a naive prediction of "
        f"{last['naive']} — a gap of {abs(last['measured_minus_naive'])}. "
        + (f"The naive model leaves the measured 95% CI at n={div} hops."
           if div else "The naive model stays within the measured CI over this range.")
    )

    return {
        "question": "Q1: How does end-to-end reliability change as required tool "
                    "hops grow?",
        "config": config.as_dict(),
        "model": {"P0": P0, "DECAY": DECAY, "PMIN": PMIN,
                  "form": "p_k = clamp(P0 - DECAY*(k-1), PMIN, 1.0)"},
        "single_hop_reliability": curves["single_hop_reliability"],
        "per_hop_reliability": curves["per_hop"],
        "curve": curves["points"],
        "first_divergence_hop": div,
        "observability_gate": gate,
        "finding": finding,
    }
