# CHECKPOINT-25 — failures become replay-verified fixes

**Mission.** Turn failures into replay-verified postmortems whose fixes stay
fixed.

**Required evidence.** Two or three incident reports, red→green tests, and
Checkpoint 25.

**Fail condition.** The incident cannot flip red→green across its replay-verified
fix. — **Not triggered.**

## Incident inventory

| incident | frozen source | seed | regression |
|---|---|---:|---|
| INC-25-001 stale fallback re-entry | Day 23 cascade trace | 2026080207 | R25-001 correct within cascade envelope |
| INC-25-002 serial retry misses deadline | Day 24 tight-budget attack | 2026080301 | R25-002 correct by user deadline |

Source-provenance checks pass:

- INC-25-001 matches the Day 23 seed and terminal event E09.
- INC-25-002 belongs to the Day 24 shared-seed population whose tight-budget
  attack recorded 105 latency aborts.

## Postmortem completeness

Both reports contain:

- a virtual-time timeline with exact span references;
- user impact;
- how the failure was detected;
- a system-condition root cause;
- multiple contributing factors;
- control-level corrective actions;
- a fixed timeline;
- the same regression predicate evaluated before and after;
- complete legacy and fixed trace artifacts.

The reports name failed controls and policy assumptions, not individual people.

## Red → green proof

| incident | before | after | same seed | same config | same test | after stays green |
|---|---|---|---|---|---|---|
| INC-25-001 | red: `contained_cost_ceiling` | green: `recovered_correct` | yes | yes | yes | yes |
| INC-25-002 | red: `latency_budget_abort` | green: `recovered_correct` | yes | yes | yes | yes |

### INC-25-001

Predicate:

> A correct answer is visible, no wrong answer is visible, cost ≤12, and steps
> ≤9.

| measurement | legacy | fixed |
|---|---:|---:|
| correct visible answer | no | yes |
| wrong visible answer | no | no |
| cost | 11 | 11 |
| steps | 8 | 6 |
| latency | 98 | 94 |
| regression | red | green |

The fix performs an exact token check, quarantines the bad
provider/fingerprint, and requires a diverse trusted route.

### INC-25-002

Predicate:

> A correct answer is visible, no wrong answer is visible, cost ≤2, and latency
> ≤45.

| measurement | legacy | fixed |
|---|---:|---:|
| correct visible answer | no | yes |
| wrong visible answer | no | no |
| cost | 2 | 2 |
| latency | 45 | 45 |
| regression | red | green |

The fix rejects the infeasible 30+20 serial schedule and starts one safe,
bounded hedge at virtual time 20.

## Replay stability

For each incident and policy version:

- 20/20 in-process executions produce one run digest;
- 20/20 produce one trace digest;
- all regression states are identical;
- every trace is complete and every regression reference resolves;
- fresh processes with Python hash seeds 0, 1, 7, and 99 reproduce the expected
  run digest, trace digest, and red/green state.

The fixed policy therefore stays green across 40 in-process post-fix replays and
eight fresh-process post-fix replays in total.

## Executable fail-condition guard

The gate requires:

- two or three incident reports;
- every required postmortem section;
- frozen source evidence match;
- every legacy regression red;
- every fixed regression green;
- the same test to flip;
- every fix replay-verified;
- complete after traces;
- trace-linked regression assertions.

All checks are true; `passed=true`.

## Required evidence

- **Incident 1:** `evidence/INC-25-001.md`
- **Incident 2:** `evidence/INC-25-002.md`
- **Strong case study:** `evidence/CASE_STUDY.md`
- **Red→green replay:** `evidence/red_green_replay.json`
- **Machine-readable reports:** `evidence/incident_reports.json`
- **Executable checkpoint:** `evidence/checkpoint_25.json`
- **Human checkpoint:** `evidence/CHECKPOINT-25.md`
- **Complete traces:** four `*-before-trace.json` / `*-after-trace.json` files

## Mastery gate — all five

- **Can explain** — each report distinguishes symptoms, impact, detection, root
  cause, and contributing conditions.
- **Can build** — two corrective policies and invariant regressions.
- **Can debug** — timelines and test assertions resolve to complete spans.
- **Can measure** — outcomes, budgets, latency, steps, digests, and replay
  stability.
- **Can defend** — same-seed/config/test intervention, blameless wording, explicit
  simulator boundary.
