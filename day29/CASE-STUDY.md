# One-page case study — stale fallback re-entered recovery

## Layer 1 · Decision

**What FAULTLINE proved.** For one seeded simulator incident, exact fallback
validation, quarantine, and route-diverse recovery changed the same user-visible
regression from red to green and stayed green under replay.

The decision is narrow but useful: a fallback answer is not eligible merely
because it is available or a narrow judge accepts it. Recovery must validate the
answer, change the failed dependency path, and remain inside the user’s envelope.

## Layer 2 · Incident

Two primary calls timed out. The fallback preserved the headline value while
shifting context tokens. The narrow judge accepted a documented blind-spot
variant; verification repeated; replanning selected the same provider and
fingerprint; the cost ceiling then blocked synthesis. The ceiling prevented a
wrong visible answer, but containment was still lost service.

The complete legacy trace connects every step. This replaces “the model made a
mistake” with a causal system diagnosis: an advisory judge had too much authority,
and replanning had no route-diversity fence.

## Layer 3 · Evidence

| verified number | value | committed result |
|---|---:|---|
| Replay seed | **2026080207** | [red/green replay](../day25/evidence/red_green_replay.json) |
| Legacy terminal latency | **98** | [red/green replay](../day25/evidence/red_green_replay.json) |
| Fixed terminal latency | **94** | [red/green replay](../day25/evidence/red_green_replay.json) |
| Fixed cost | **11** | [red/green replay](../day25/evidence/red_green_replay.json) |
| Repetitions per policy version | **20** | [red/green replay](../day25/evidence/red_green_replay.json) |

The fixed path compares tokens exactly, quarantines the stale route and
fingerprint, chooses trusted independent context, and returns a correct visible
answer. The same seed, configuration, and regression test flip red→green; both
versions remain stable across their repeated executions.

## Layer 4 · Boundary

This case proves the corrective controls for the configured simulator incident.
It does not prove that providers labelled independent are operationally
independent in production. Before deployment, measure guard error, map shared
dependencies, price the route change, and run live fault drills.

**Staff-engineer takeaway:** recovery reliability is a traceable outcome change,
not the presence of a retry or fallback mechanism.
