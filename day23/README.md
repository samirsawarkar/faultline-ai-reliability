# FAULTLINE — Day 23: seeded cross-component cascade

Create one reproducible incident where an initiating fault and recovery mechanisms
interact across provider, control-plane, quality, and agent components.

> **Fail condition:** the cascade cannot be reproduced from one seed and
> configuration.
> **Status: not triggered** — seed `2026080207` plus the committed configuration
> regenerates one incident digest, one trace digest, and the same nine labelled
> causal events across 20 in-process runs and four Python hash seeds. See
> [CHECKPOINT-23.md](CHECKPOINT-23.md).

## The one incident

```
F2 primary latency spike
  → M2 retry adds a second failing call
  → M3 breaker opens
  → M4 routes to the secondary
  → correlated stale context enters
  → narrow judge false-accepts token drift
  → verification repeats three times
  → M6 replans into the same fallback
  → M5 cost ceiling aborts before wrong synthesis
```

This is a cascade rather than a fault montage: each transition is labelled as a
cause/effect edge and backed by exact Day-4 trace span IDs.

## Day plan delivered

| block | delivered |
|---|---|
| **08:00–10:00 · Build A** | initiating F2 fault, nine-event propagation contract, one serializable configuration |
| **10:15–12:15 · Build B** | seeded trigger, M2/M3/M4/M5/M6 interactions, 16-span complete trace |
| **13:00–15:00 · Attack + experiment** | 20 repeated runs plus four cross-process/hash-seed replays |
| **15:15–16:15 · Learn** | [causal incident analysis](LEARN-causal-analysis.md) |
| **16:30–17:30 · Evidence + market** | scenario, trace, narrative, graph JSON/SVG, skeleton, replay proof, [market note](MARKET.md) |

## What's here

```
faultline_cascade/
  config.py      one validated incident configuration
  cascade.py     seeded trigger, cascade runner, trace + label audit
  replay.py      repeated and cross-process stability proof
  graph.py       trace-referenced causal graph JSON + deterministic SVG
  narrative.py   incident narrative generated from measured run
  report.py      incident skeleton and executable fail-condition gate
scripts/
  make_evidence.py
  replay_once.py
tests/           config, cascade, trace, replay, graph, narrative gates (15 tests)
evidence/
  cascade_scenario.json
  cascade_trace.json
  replay_stability.json
  INCIDENT_NARRATIVE.md
  causal_graph.json
  causal_graph.svg
  incident_skeleton.json
CHECKPOINT-23.md · LEARN-causal-analysis.md · DECISIONS.md
REFLECTION.md · MARKET.md
```

## Quickstart

```bash
python -m pytest tests/ -q
python scripts/make_evidence.py

# Reproduce from the one committed seed/config:
python scripts/replay_once.py --scenario evidence/cascade_scenario.json
```

Standard library only. Builds on Day 4 (complete linked traces), Day 16/21
(narrow judge and known blind spot), Day 18 (bounded retry), Day 20
(breaker/fallback), and Day 22 (ceilings and repetition recovery).

## Canonical evidence

- seed: **2026080207**
- configuration digest:
  `939e2343e9f989713e332e7c404256e908f01e12c0d7b0746707817711560b26`
- incident digest:
  `fb9daf3e3af8c5b43fce756ca9ac9eee7ee9171d463beeef07d5af11a428d5ce`
- trace digest:
  `43e5f00f758a61e1b80f7b75fb69c4b7a993ca51a04668fdbd8c3f92a450e40e`
- trace: **16 complete spans**, including **3 complete error spans**
- causal graph: **9 observed nodes**, **8 edges**, every node trace-referenced
- replay: **20/20 identical** in-process; **4/4 identical** across hash seeds

## Recovery interaction

The initiating timeout does not exhaust the system by itself. Recovery propagates
it:

- M2 increases primary load from one call to two.
- M3 turns repeated timeouts into a routing transition.
- M4 restores an answer but exposes correlated semantic degradation.
- The narrow judge's known token-order blind spot lets that degradation cross the
  quality gate.
- M6 reacts to repeated verification by re-entering the same fallback.
- M5 prevents final synthesis at cost 11/12 and steps 8/9.

The terminal state is **contained**, not successful: no wrong answer reaches the
user, but no correct answer is returned.

## Mastery map — all five

- **Explain** → [LEARN-causal-analysis.md](LEARN-causal-analysis.md)
- **Build** → `faultline_cascade/` (trigger, propagation, tracing, replay, graph)
- **Debug** → [incident narrative](evidence/INCIDENT_NARRATIVE.md) with exact span IDs
- **Measure** → `replay_stability.json` and complete-trace audit
- **Defend** → `causal_graph.json/.svg`, `incident_skeleton.json`,
  [DECISIONS.md](DECISIONS.md), and the one-seed/config gate
