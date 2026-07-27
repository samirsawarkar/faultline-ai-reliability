# CHECKPOINT-18 — bounded recovery (M1 repair-retry, M2 timeout policy)

**Mission.** Implement bounded recovery for invalid outputs and slow tools.

**Fail condition.** Recovery is unbounded, unsafe to repeat, or lacks a budget. —
**Not triggered.**

## What was built

- **M1 — schema repair-retry:** bounded re-validation against the Day-9 schema;
  transient corruption recovers, persistent exhausts cleanly; recovered output
  committed once via an idempotency ledger.
- **M2 — timeout policy:** per-attempt timeout + exponential backoff + full jitter,
  bounded by max attempts and a total latency budget.
- **The envelope:** `RetryPolicy` (max_attempts ≤ 10, cost budget, latency budget) +
  a retry engine that is terminal by construction.
- **Safety:** an `IdempotencyLedger` (side-effect-once) so retries are safe to repeat.

10 tests gate it; two evidence artifacts prove it.

## Bounded / budgeted / safe (the fail condition, refused)

| guard | mechanism | evidence |
|---|---|---|
| bounded | `max_attempts` + hard cap 10; engine always terminal | `exhaustion_attack` → `exhausted_attempts` |
| budgeted (cost) | strict pre-check; cost never exceeds `cost_budget` | `m1/m2_cost_le_budget: true` |
| budgeted (latency) | abort once exceeded (overshoot ≤ 1 timeout) | `m2_latency_bounded: true` |
| safe to repeat | idempotency ledger keyed by request id | 3 deliveries → **1** side effect (vs 3 naive) |

`all_ceilings_hold: true`.

## Does it help? (paired, seed 20260728)

| policy | no-recovery | bounded recovery | McNemar |
|---|---|---|---|
| M1 repair-retry | 0/9 | **6/9** | p = 0.03125, significant (b=0) |
| M2 timeout/backoff | 0/9 | **6/9** | p = 0.03125, significant (b=0) |

Recovery rescues every transient fault and never regresses a case (b=0); the
persistent faults exhaust within budget.

## New-failure analysis (recovery's bill)

On a persistent fault recovery cannot fix, it still spends 4 attempts / cost 4 /
latency 34 for **no benefit** — recovery trades cost for success only on transient
faults. Without the ledger, re-delivery would double side effects; the ledger keeps
it at one. Both are committed, not hidden.

## Mastery gate — all five

- **Explain** — `LEARN-idempotency.md`: why retry is dangerous, backoff/jitter, and
  idempotency as the bounded-vs-correct distinction.
- **Build** — `faultline_recovery/`: policy, engine, repair (M1), timeout (M2), ledger.
- **Debug** — `recovery_traces.json`: per-attempt Day-4 spans for recovered + exhausted runs.
- **Measure** — paired McNemar (recovery helps, p=0.031) + the ceiling checks.
- **Defend** — `DECISIONS.md` (D18-001…D18-007); bounded, budgeted, idempotent, with
  the cost of recovery reported.
