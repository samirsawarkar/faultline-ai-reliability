# FAULTLINE — Day 22: six-mechanism recovery matrix

Add structural step/cost ceilings and repetition recovery, then compare all six
recovery mechanisms across all six fault families by **outcome, cost, and
latency** on paired request seeds.

> **Fail condition:** any mechanism lacks paired evidence or creates an unmeasured
> failure.
> **Status: not triggered** — all 36 mechanism × fault cells contain aligned paired
> outcomes, availability, cost, and latency; every induced harm is reconciled in a
> per-mechanism audit. See [CHECKPOINT-22.md](CHECKPOINT-22.md).

## The one idea

A recovery mechanism can help its target fault and still be harmful as a general
policy. Retry wastes budget on persistent faults. A breaker blocks healthy probes.
Fallback can answer incorrectly. Ceilings terminate legitimate long work.
Repetition detection can mistake pagination for a loop.

Day 22 therefore evaluates the full recovery set:

| id | mechanism | intended role |
|---|---|---|
| M1 | repair-retry | repair transient F1 structured-output corruption |
| M2 | timeout/backoff | retry transient F2 latency faults inside a budget |
| M3 | circuit breaker | contain repeated F4 provider calls |
| M4 | provider fallback | recover F4 availability through a secondary |
| M5 | step/cost ceilings | structurally contain F6 exhaustion |
| M6 | repetition recovery | detect F6 non-progress, replan once, then abort |

## Day plan delivered

| block | delivered |
|---|---|
| **08:00–10:00 · Build A** | M5 pre-execution step/cost ceilings and M6 bounded repetition/replan controller |
| **10:15–12:15 · Build B** | 6 mechanisms × 6 fault families × 24 paired seeds |
| **13:00–15:00 · Attack + experiment** | clean controls, persistent faults, false opens, bad fallback, premature ceilings, repetition false positives |
| **15:15–16:15 · Learn** | [recovery policy composition](LEARN-recovery-composition.md) |
| **16:30–17:30 · Evidence + market** | matrix JSON/Markdown, attack audit, checkpoint evidence, and [market note](MARKET.md) |

## What's here

```
faultline_recovery_matrix/
  ceilings.py     M5 structural step/cost bounds
  repetition.py   M6 repetition detection + one bounded replan
  scenario.py     six fault populations and paired no-recovery outcomes
  mechanisms.py   M1–M6 adapters over the shared outcome contract
  matrix.py       36 paired cells: outcome, availability, cost, latency, harms
  report.py       ceiling/repetition attacks, composition policy, checkpoint
  render.py       committed six-mechanism Markdown matrix
scripts/ make_evidence.py
tests/   ceilings/repetition, matrix, report gates (17 tests)
evidence/
  six_mechanism_matrix.json
  SIX_MECHANISM_MATRIX.md
  recovery_attacks.json
  checkpoint_22.json
CHECKPOINT-22.md · LEARN-recovery-composition.md · DECISIONS.md
REFLECTION.md · MARKET.md
```

## Quickstart

```bash
python -m pytest tests/ -q       # 17 tests
python scripts/make_evidence.py  # regenerate matrix, attacks, checkpoint
```

Standard library only. Builds on Day 14 (paired statistics), Day 18 (M1/M2
bounded retry), Day 20 (M3/M4 breaker/fallback), and Day 21 (fallback quality).

## Experiment design

Each of the 36 matrix cells uses the same 24 seeds for mechanism and no-recovery
baseline:

- 18 injected fault requests;
- 6 clean controls, including legitimate long work and legitimate repetition;
- paired McNemar evidence for correct success and availability;
- paired bootstrap intervals for cost and latency deltas;
- separate counts for correct success, answered-wrong, contained, and unavailable;
- every recovery-induced harm recorded by seed and type.

## Aggregate comparison (144 paired requests per mechanism)

| mechanism | correct success | availability | contained | answered wrong | mean cost | p95 latency | recoveries | regressions | harms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| no recovery | 0.25 | 0.625 | 0.0 | 0.375 | 3.2917 | 120 | — | — | — |
| M1 | 0.3333 | 0.5833 | 0.0417 | 0.25 | 3.5417 | 120 | 12 | 0 | 6 |
| M2 | 0.3333 | 0.7083 | 0.0417 | 0.375 | 3.5417 | 120 | 12 | 0 | 6 |
| M3 | 0.2153 | 0.5903 | 0.1042 | 0.375 | 3.0764 | 120 | 0 | 5 | 5 |
| M4 | 0.3333 | 0.75 | 0.0 | 0.4167 | 3.4167 | 120 | 12 | 0 | 6 |
| M5 | 0.1667 | 0.5417 | 0.2083 | 0.375 | 2.4583 | 60 | 0 | 12 | 12 |
| M6 | 0.25 | 0.625 | 0.125 | 0.375 | 2.4583 | 70 | 12 | 12 | 12 |

Interpret mechanism results against the paired cell for its intended fault—not as
a global leaderboard. M5, for example, cuts F6 cost and latency by containing the
loop, but it is not supposed to turn a loop into a correct answer.

## Target-fault findings

- **F1:** M1 recovers 12/18 faulted requests; success becomes 0.75.
- **F2:** M2 recovers 12/18; success becomes 0.75, with measurable retry latency.
- **F3/F5:** no M1–M6 mechanism improves correct success. Semantic rejection and
  re-grounding remain required.
- **F4:** M3 alone protects the provider but causes five false-open control
  regressions; M4 recovers 12/18 correctly and serves six silently wrong fallbacks.
- **F6:** M5 contains all injected loops within six steps/cost units; M6 recovers
  12 transient repetitions and contains six persistent ones.

## Recovery-induced harms (all measured)

| mechanism | harm | count |
|---|---|---:|
| M1 | wasted repair budget on persistent F1 | 6 |
| M2 | wasted timeout retry budget on persistent F2 | 6 |
| M3 | false-open blocked healthy request | 5 |
| M4 | silent fallback degradation | 6 |
| M5 | premature ceiling on legitimate long work | 12 |
| M6 | legitimate repetition false positive | 12 |

The right policy is compositional: M5 outside as the safety envelope; a
fault-specific detector; the narrow recovery that matches the signal; an oracle or
semantic quality check; then success, contained failure, or escalation. Applying
all mechanisms blindly compounds their failure modes.

## Mastery map — all five

- **Explain** → [LEARN-recovery-composition.md](LEARN-recovery-composition.md)
- **Build** → `faultline_recovery_matrix/` (M5/M6 plus M1–M6 adapters)
- **Debug** → `evidence/recovery_attacks.json` (every induced harm by seed/type)
- **Measure** → `evidence/six_mechanism_matrix.json` (36 paired cells)
- **Defend** → [Checkpoint 22](CHECKPOINT-22.md), [DECISIONS.md](DECISIONS.md),
  and the executable no-unpaired/no-unmeasured-failure gate
