# CHECKPOINT-23 — reproducible cross-component incident

**Mission.** Create one reproducible incident where faults and recovery interact
across components.

**Required evidence.** Seeded cascade scenario, trace narrative, and causal graph.

**Fail condition.** The cascade cannot be reproduced from one seed and
configuration. — **Not triggered.**

## Incident specification

One input pair defines the run:

```
seed = 2026080207
configuration digest =
939e2343e9f989713e332e7c404256e908f01e12c0d7b0746707817711560b26
```

The seed produces:

- primary trigger roll `0.20506752 < 0.25` → F2 latency spike fires;
- fallback roll `0.73846822` → `borderline_tokens` stale fallback;
- strict fallback quality `false`;
- narrow judge false-accept `true`.

The committed input and trigger truth are in
`evidence/cascade_scenario.json`.

## Labelled propagation chain

| event | component | role |
|---|---|---|
| E01 `primary_latency_spike` | primary provider | initiating F2 fault |
| E02 `retry_amplification` | M2 retry | recovery adds a second failing call |
| E03 `breaker_open` | M3 breaker | second timeout opens 2-of-2 breaker |
| E04 `fallback_routed` | M4 router | open breaker sends traffic secondary |
| E05 `stale_fallback_context` | secondary provider | correlated semantic fault |
| E06 `judge_false_accept` | quality gate | known token-order blind spot |
| E07 `verification_repetition` | agent controller | propagated non-progress |
| E08 `replan_reenters_fallback` | M6 recovery | replan returns to same secondary |
| E09 `cost_ceiling_abort` | M5 envelope | terminal containment |

Every event contains at least one supporting trace span. Every edge resolves to two
events. The graph is a single nine-node/eight-edge chain.

## Complete trace

- spans: **16/16 complete**
- error spans: **3/3 complete** (two primary timeouts and the ceiling abort)
- root spans: **1**
- unresolved parents: **0**
- unresolved event span references: **0**
- unresolved causal edges: **0**
- trace audit: **passed**

The complete trace plus label/edge index is in `evidence/cascade_trace.json`.

## Reproducibility proof

The same seed/config was executed:

- **20 times** in the evidence process;
- once under each Python hash seed **0, 1, 7, 99**.

All 24 runs produced:

- one incident digest:
  `fb9daf3e3af8c5b43fce756ca9ac9eee7ee9171d463beeef07d5af11a428d5ce`;
- one trace digest:
  `43e5f00f758a61e1b80f7b75fb69c4b7a993ca51a04668fdbd8c3f92a450e40e`;
- the exact nine-label chain above;
- a complete and labelled trace.

`reproducible_from_one_seed_and_config=true`.

## Outcome and recovery blast radius

- primary calls: 2 (one added by recovery);
- fallback calls: 2;
- repeated verifications: 3;
- replans: 1;
- cost: 11/12;
- steps: 8/9;
- virtual latency: 98;
- terminal: `contained_cost_ceiling`;
- correct answer returned: false;
- wrong fallback suppressed: true.

M5 limits the blast radius, but containment is not counted as recovery success.

## Required evidence

- **Seeded scenario:** `evidence/cascade_scenario.json`
- **Complete trace:** `evidence/cascade_trace.json`
- **Trace narrative:** `evidence/INCIDENT_NARRATIVE.md`
- **Causal graph:** `evidence/causal_graph.json` and `.svg`
- **Replay proof:** `evidence/replay_stability.json`
- **Incident skeleton:** `evidence/incident_skeleton.json`

## The fail condition, refused

The executable guard requires one seed, one full configuration and digest, a
labelled initiating fault, stable in-process and cross-process propagation, a
complete trace, a trace-referenced graph, and a trace-referenced incident skeleton.
All nine checks are true; `passed=true`.

## Mastery gate — all five

- **Explain** — `LEARN-causal-analysis.md`: causal chain versus temporal story.
- **Build** — seeded trigger, cross-component runner, complete trace, graph.
- **Debug** — narrative and skeleton resolve every causal event to spans.
- **Measure** — repeated/cross-process digests and trace completeness.
- **Defend** — causal graph, intervention caveat, decisions, executable gate.
