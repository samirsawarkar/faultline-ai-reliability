# FAULTLINE — Day 18: bounded recovery (M1 repair-retry, M2 timeout policy)

Recover from the two faults recovery can actually fix — invalid outputs (F1) and
slow tools (F2) — **without** letting recovery become a new hazard. Every retry is
bounded, budgeted, and safe to repeat.

> **Fail condition:** recovery is unbounded, unsafe to repeat, or lacks a budget.
> **Status: not triggered** — `RetryPolicy` makes `max_attempts` + cost budget +
> latency budget structural (and caps attempts at 10 even for a careless caller);
> an `IdempotencyLedger` makes retries side-effect-once; and the exhaustion attack
> confirms every ceiling holds. See [CHECKPOINT-18.md](CHECKPOINT-18.md).

## The one idea

Retry is the most dangerous "fix" in reliability: done wrong it hangs, it costs
unboundedly, or it re-applies side effects until it corrupts state. So the recovery
here is defined by its *envelope* first — a bounded, budgeted retry engine that is
terminal by construction — and only then by what it retries. M1 repairs invalid
structured outputs against the Day-9 schema; M2 rides out slow tools with
exponential backoff and jitter. Both stop cleanly the moment a bound is hit.

## What's here

```
faultline_recovery/
  policy.py       RetryPolicy: max_attempts (<=10), cost/latency budgets, capped
                  deterministic backoff + full jitter
  engine.py       run_bounded_retry: terminal by construction; records which bound stopped it
  idempotency.py  IdempotencyLedger (side-effect-once) + NaiveNoLedger (the unsafe baseline)
  repair.py       M1 schema repair-retry over the Day-9 validator (+ commit once)
  timeout.py      M2 timeout + backoff + jitter over a slow-tool model
  experiment.py   paired no-recovery vs recovery (McNemar), exhaustion attack, new-failure analysis
scripts/ make_evidence.py
tests/   test_recovery.py  (10 tests)
evidence/ recovery_report.json  recovery_traces.json
CHECKPOINT-18.md · LEARN-idempotency.md · DECISIONS.md · REFLECTION.md
```

## Quickstart

```
python -m pytest tests/ -q       # 10 tests
python scripts/make_evidence.py  # regenerate the report + Day-4 recovery traces
```

Standard library only. Builds on Day 9 (schema), Day 14 (McNemar), Day 4 (traces).
No LLM: the "repair prompt" and the "tool" are deterministic producers; a real
repair/tool drops in behind the same interface, and the bounding/budget/idempotency
are unchanged.

## The results (paired, seed 20260728)

- **M1 repair-retry:** no-recovery **0/9** vs bounded recovery **6/9** — the 6
  transient corruptions are repaired within the attempt budget; the 3 persistent
  ones exhaust cleanly. McNemar **p = 0.03125, significant** (b=0: recovery never
  regresses a case).
- **M2 timeout/backoff/jitter:** no-recovery **0/9** vs recovery **6/9**; McNemar
  **p = 0.03125**.
- **Exhaustion attack:** forced persistent faults end in `exhausted_attempts` with
  `attempts ≤ max`, `cost ≤ cost_budget` (strict), and latency bounded — every
  ceiling holds, no hang.
- **Safe to repeat:** 3 duplicate deliveries → **1** side effect with the ledger vs
  **3** without. Idempotency turns "at least once" into "effectively once."

## New-failure analysis (recovery is not free)

`recovery_report.json.new_failure_analysis`: on a persistent fault recovery cannot
fix, it still spends its budget (4 attempts, cost 4, latency 34) for **no benefit** —
so recovery trades latency/cost for a success-rate gain only where faults are
transient. And a naive (non-idempotent) retry would double side effects on
re-delivery; the ledger is what prevents recovery from introducing that new fault.

## Mastery map

- **Explain** → [LEARN-idempotency.md](LEARN-idempotency.md)
- **Build** → `faultline_recovery/` (policy, engine, repair, timeout, ledger)
- **Debug** → `evidence/recovery_traces.json` (per-attempt Day-4 spans, recovered + exhausted)
- **Measure** → paired McNemar (recovery helps) + the ceiling checks
- **Defend** → [DECISIONS.md](DECISIONS.md), [CHECKPOINT-18.md](CHECKPOINT-18.md)
