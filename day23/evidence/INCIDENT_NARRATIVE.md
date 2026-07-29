# INCIDENT — retry/fallback/repetition cascade

## Summary

Incident `cascade-2026080207-1.0.0` is reproduced from seed **2026080207** and configuration digest `939e2343e9f989713e332e7c404256e908f01e12c0d7b0746707817711560b26`. The trace digest is `43e5f00f758a61e1b80f7b75fb69c4b7a993ca51a04668fdbd8c3f92a450e40e`.

A seeded primary latency spike caused a retry, opened the breaker, routed to a stale fallback that the narrow judge accepted, repeated downstream verification, and sent repetition recovery back to the same secondary. The global cost ceiling then stopped final synthesis before it could return the wrong answer.

## Causal chain with trace references

| event | component | observation | supporting span(s) |
|---|---|---|---|
| E01 `primary_latency_spike` | primary_provider | Seeded F2 latency exceeds the primary timeout. | `trace-2026080207-span-0001`, `trace-2026080207-span-0003` |
| E02 `retry_amplification` | retry_controller | M2 converts one timeout into a second failing primary call. | `trace-2026080207-span-0002`, `trace-2026080207-span-0004`, `trace-2026080207-span-0005` |
| E03 `breaker_open` | circuit_breaker | The second timeout satisfies the 2-of-2 breaker threshold. | `trace-2026080207-span-0006` |
| E04 `fallback_routed` | fallback_router | The open breaker sends the request to the secondary provider. | `trace-2026080207-span-0007` |
| E05 `stale_fallback_context` | secondary_provider | The correlated secondary preserves the headline value but shifts context tokens. | `trace-2026080207-span-0008` |
| E06 `judge_false_accept` | quality_gate | The known token-order blind spot accepts a strictly bad fallback. | `trace-2026080207-span-0009` |
| E07 `verification_repetition` | agent_controller | Accepted drift causes the agent to repeat the same failed verification. | `trace-2026080207-span-0010`, `trace-2026080207-span-0011`, `trace-2026080207-span-0012` |
| E08 `replan_reenters_fallback` | repetition_recovery | M6 replans into the same correlated secondary and consumes the remaining envelope. | `trace-2026080207-span-0013`, `trace-2026080207-span-0014` |
| E09 `cost_ceiling_abort` | global_budget | M5 refuses final synthesis before cost can exceed the configured ceiling. | `trace-2026080207-span-0015` |

## Why this is a cascade, not a list of faults

- **E01 → E02**: timeout triggers retry.
- **E02 → E03**: second failure opens breaker.
- **E03 → E04**: open state routes fallback.
- **E04 → E05**: secondary serves correlated stale context.
- **E05 → E06**: semantic drift crosses judge blind spot.
- **E06 → E07**: accepted drift reaches verification.
- **E07 → E08**: repetition triggers replan.
- **E08 → E09**: re-entry exhausts remaining cost.

The initiating F2 fault alone did not consume the envelope. Recovery composition propagated it: M2 added a primary call; M3 redirected traffic; M4 exposed a correlated semantic fault; the quality gate missed it; M6 re-entered the degraded route. M5 contained the final blast radius.

## Outcome and blast radius

- primary calls: **2** (1 added by retry)
- fallback calls: **2**
- repeated verifications: **3**
- cost: **11/12**; steps: **8/9**
- virtual latency: **98**
- terminal state: **contained_cost_ceiling**
- user-visible wrong answer: **suppressed**, not counted as success

## Trace completeness

The trace contains **16** closed spans, including **3** complete error spans. Parent links, event-to-span references, and causal-edge endpoints all resolve. Trace audit passed: **True**.

## Reproduction proof

The incident was replayed **20** times in-process and under four different Python hash seeds. Unique incident digests: `['fb9daf3e3af8c5b43fce756ca9ac9eee7ee9171d463beeef07d5af11a428d5ce']`; unique trace digests: `['43e5f00f758a61e1b80f7b75fb69c4b7a993ca51a04668fdbd8c3f92a450e40e']`. Cross-process stable: **True**.

From the repository root:

```bash
python day23/scripts/replay_once.py --scenario day23/evidence/cascade_scenario.json
```

Expected incident digest: `fb9daf3e3af8c5b43fce756ca9ac9eee7ee9171d463beeef07d5af11a428d5ce`.

## Causal-analysis caveat

The graph is intervention-informed within this deterministic simulator: the seed/config fixes the initiating fault and each edge is backed by an observed transition. It is not a claim that temporal order alone proves causality in production; external confounders would require additional counterfactual or intervention evidence.
