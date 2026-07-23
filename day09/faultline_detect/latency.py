"""Virtual latency model + budget — no wall clock anywhere.

Time in FAULTLINE is virtual and logical, for the same reason spans use a logical
clock (Day 4): a real timer would make traces non-reproducible and conflate host
jitter with the fault under study. So "duration" here is *cost units*, not
milliseconds — but it behaves exactly like a latency budget problem.

Per call:
    duration = BASE_LATENCY + injected
where `injected` is the Day-8 `stall` cost delta observed on that call
(`severity * 10`, and 0 on a call with no latency fault). The `stall` mode leaves
output content identical, so latency is observable ONLY as duration — never in
the payload.

A call breaches the budget when `duration > budget`. The duration detector turns
that breach into a timeout signal (see detectors.py). Because the breach depends
on the budget, F2 detection is budget-gated: the same fault is caught under a
tight budget and missed under a loose one, which is the Learn block's point.
"""
from __future__ import annotations

BASE_LATENCY = 10          # every call costs this much before any fault
DEFAULT_BUDGET = 45        # duration strictly above this is a timeout


def duration(base: int, injected: int) -> int:
    return base + injected


def breaches_budget(dur: int, budget: int = DEFAULT_BUDGET) -> bool:
    return dur > budget
