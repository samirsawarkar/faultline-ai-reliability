# FAULTLINE — Day 25: replay-verified postmortems

Turn observed failures into blameless, trace-linked incident reports and prove
that their fixes flip the same regression from red to green.

> **Fail condition:** an incident cannot flip red→green across its
> replay-verified fix.
> **Status: not triggered.** Two incidents use the same seed, configuration, and
> regression predicate before and after. Both legacy policies replay red; both
> fixed policies replay green and remain green across 20 in-process runs plus
> four fresh-process/hash-seed runs per version. See
> [CHECKPOINT-25.md](CHECKPOINT-25.md).

## The two postmortems

| incident | legacy outcome | fix | fixed outcome |
|---|---|---|---|
| [INC-25-001](evidence/INC-25-001.md) — stale fallback re-entry | no correct answer; cost 11/12, latency 98 | exact token guard, quarantine, independent route | correct answer; cost 11/12, latency 94 |
| [INC-25-002](evidence/INC-25-002.md) — serial retry misses deadline | recoverable request aborts at cost 2, latency 45 | feasibility check and one bounded hedge | correct answer at cost 2, latency 45 |

Each report includes timeline, impact, detection, root cause, contributing
factors, corrective actions, before/after traces, and the exact regression
predicate.

## Red → green contract

A fix is verified only when all of these hold:

1. the legacy and fixed executions use the same incident seed;
2. the serialized environment configuration is identical;
3. the exact same regression ID and predicate are evaluated;
4. legacy is deterministically red;
5. fixed is deterministically green;
6. all trace references resolve to complete spans;
7. repeated fixed replays remain green;
8. fresh processes with hash seeds 0, 1, 7, and 99 reproduce the same run,
   trace, and regression state.

The policy version is the only experimental intervention.

## Strong case study

[CASE_STUDY.md](evidence/CASE_STUDY.md) follows the Day 23 cascade from primary
timeouts through stale fallback, judge false acceptance, repeated verification,
same-route re-entry, and cost containment. Its fix does not merely silence the
alarm: it returns a correct answer under the original cost and step ceilings.

The claim remains simulator-bounded. Exact reference checks and genuine provider
independence must be established and costed in production.

## Day plan delivered

| block | delivered |
|---|---|
| **08:00–10:00 · Build A** | two reports with trace-linked timelines, impact, detection, root cause, and contributing factors |
| **10:15–12:15 · Build B** | strict guard/diverse route and deadline-aware hedge fixes; invariant regressions |
| **13:00–15:00 · Attack + experiment** | legacy/fixed replay, 20-run stability, fresh-process/hash-seed verification |
| **15:15–16:15 · Learn** | [blameless postmortems and system root cause](LEARN-blameless-postmortems.md) |
| **16:30–17:30 · Evidence + market** | Checkpoint 25 and one publishable, evidence-bounded case study |

## What's here

```text
faultline_postmortem/
  config.py       shared replay environment
  catalog.py      two complete incident specifications
  runner.py       legacy/fixed policies, traces, regression predicates
  replay.py       repeated and cross-process red→green verification
  replay_once.py  fresh-process replay entry point
  report.py       postmortems, source linkage, executable checkpoint
  render.py       incident, checkpoint, and case-study Markdown
scripts/
  make_evidence.py
tests/            catalog, trace, red→green, replay, report gates (19 tests)
evidence/
  INC-25-001.md
  INC-25-002.md
  CASE_STUDY.md
  CHECKPOINT-25.md
  incident_reports.json
  red_green_replay.json
  checkpoint_25.json
  <incident>-before-trace.json
  <incident>-after-trace.json
CHECKPOINT-25.md · LEARN-blameless-postmortems.md
DECISIONS.md · REFLECTION.md · MARKET.md
```

## Quickstart

```bash
python -m pytest tests/ -q
python scripts/make_evidence.py
```

Standard library only. Day 25 reuses Day 4's deterministic complete-span tracer
and the frozen Day 23–24 evidence as incident provenance.

## Mastery gate — all five

- **Can explain** — separate impact, detection, root cause, contributing factors,
  and containment without blaming an operator.
- **Can build** — produce complete before/after traces and one invariant
  regression per incident.
- **Can debug** — resolve every timeline and regression claim to exact spans.
- **Can measure** — report terminal outcome, cost, latency, steps, replay
  stability, and red→green state.
- **Can defend** — keep the seed/config/test fixed, bound the claim to the
  simulator, and refuse a fix that merely changes the test.
