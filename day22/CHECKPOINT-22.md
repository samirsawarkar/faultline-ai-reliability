# CHECKPOINT-22 — six-mechanism recovery matrix

**Mission.** Add ceilings and repetition recovery, then compare all mechanisms by
outcome, cost, and latency.

**Required evidence.** A six-mechanism matrix and Checkpoint 22.

**Fail condition.** Any mechanism lacks paired evidence or creates an unmeasured
failure. — **Not triggered.**

## What was built

- **M5 step/cost ceilings** — checks both bounds before every action; a
  non-terminating plan cannot overshoot either.
- **M6 repetition recovery** — detects a third consecutive identical action,
  performs one bounded replan, and aborts a second repetition.
- **A 6×6 matrix** — M1–M6 against F1–F6, 24 aligned seeds per cell.
- **A shared outcome contract** — correct success, availability, answered-wrong,
  contained failure, cost, latency, and induced harms.
- **Paired inference** — McNemar for binary outcome/availability and deterministic
  bootstrap intervals for paired cost/latency deltas.

17 tests gate it; four evidence artifacts prove it.

## Matrix completeness

```
6 mechanisms × 6 faults = 36 cells
24 paired seeds/cell = 18 faulted + 6 clean controls
144 paired requests/mechanism
dimensions/cell = outcome + availability + cost + latency + induced harms
unpaired cells = 0
```

The complete compact matrix is
[`evidence/SIX_MECHANISM_MATRIX.md`](evidence/SIX_MECHANISM_MATRIX.md); every
interval, McNemar table, outcome count, and harm example is in
`evidence/six_mechanism_matrix.json`.

## Outcome, cost, and latency

| mechanism | correct success | availability | contained | mean cost | p95 latency | recovered | regressed |
|---|---:|---:|---:|---:|---:|---:|---:|
| no recovery | 0.25 | 0.625 | 0.0 | 3.2917 | 120 | — | — |
| M1 | 0.3333 | 0.5833 | 0.0417 | 3.5417 | 120 | 12 | 0 |
| M2 | 0.3333 | 0.7083 | 0.0417 | 3.5417 | 120 | 12 | 0 |
| M3 | 0.2153 | 0.5903 | 0.1042 | 3.0764 | 120 | 0 | 5 |
| M4 | 0.3333 | 0.75 | 0.0 | 3.4167 | 120 | 12 | 0 |
| M5 | 0.1667 | 0.5417 | 0.2083 | 2.4583 | 60 | 0 | 12 |
| M6 | 0.25 | 0.625 | 0.125 | 2.4583 | 70 | 12 | 12 |

The aggregate is not a universal ranking: mechanisms are intentionally narrow and
fault prevalence is synthetic. The per-fault paired cells are the evidence used to
select a recovery.

## M5/M6 attacks

- **Ceilings:** a 100-action plan stops at exactly six steps under the step policy
  and exactly cost five under the cost policy. Neither bound is overshot.
- **Transient repetition:** one replan reaches `complete`.
- **Persistent repetition:** the second repeated loop terminates as
  `repetition_aborted`, within eight steps and cost units.
- **Legitimate repetition:** pagination is deliberately misclassified and aborted,
  proving the false-positive path is surfaced rather than hidden.

## New failures caused by recovery

All **47** induced harms are committed by seed:

- M1: 6 wasted persistent repair budgets;
- M2: 6 wasted persistent timeout retry budgets;
- M3: 5 false-open healthy blocks;
- M4: 6 silently wrong fallback answers;
- M5: 12 premature ceilings on legitimate long work;
- M6: 12 false repetition positives.

The per-cell total equals the aggregate audit total, every mechanism has a harm
audit, and `all_harms_surfaced=true`.

## Recovery policy composition

1. Put **M5 outside** the workflow as the structural envelope.
2. Detect the fault before selecting recovery.
3. Apply only the narrow matching mechanism: M1/F1, M2/F2, M3+M4/F4, M6/F6.
4. Run the deterministic oracle or narrow semantic quality check after recovery.
5. Return correct success, contain the failure, or escalate.

F3 and F5 have no M1–M6 winner. They require semantic rejection/re-grounding;
retrying or falling back does not prove correctness.

## The fail condition, refused

`checkpoint_22.json` asserts:

- six-mechanism matrix complete;
- paired evidence complete;
- recovery-induced failures measured;
- ceilings hold;
- Checkpoint 22 passed.

The executable matrix gate additionally requires 36/36 cells, zero unpaired cells,
outcome/cost/latency in every cell, a harm audit for every mechanism, and complete
harm reconciliation. All are true.

## Mastery gate — all five

- **Explain** — `LEARN-recovery-composition.md`: why matching and order matter.
- **Build** — M5 ceilings, M6 repetition recovery, and the shared M1–M6 adapter.
- **Debug** — `recovery_attacks.json`: every new failure by mechanism, seed, and type.
- **Measure** — `six_mechanism_matrix.json`: paired outcome, cost, and latency.
- **Defend** — `SIX_MECHANISM_MATRIX.md`, `DECISIONS.md`, and the checkpoint gate.
