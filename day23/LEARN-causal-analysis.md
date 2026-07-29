# LEARN — causal incident analysis

## A timeline is not yet a causal explanation

A trace answers “what happened, and in what order?” A causal incident analysis asks
a harder question: “which event changed the conditions for the next one?”

Day 23 keeps both:

- trace spans provide ordered observations and component boundaries;
- causal edges state the proposed mechanism between observations;
- seed/config trigger truth fixes the initiating intervention;
- replay proves the same intervention produces the same chain.

The edge `E02 → E03`, for example, is stronger than “retry happened before the
breaker opened.” The breaker configuration says two failures in a two-call window
open the circuit; the retry produced the second failure; the transition log and
span output record the open state.

## Root cause, propagation, and containment

These are different roles.

- **Root cause:** E01, the seeded primary latency spike.
- **Propagation:** E02–E08, where recovery and downstream components transform the
  initial timeout into load amplification, routing, semantic degradation,
  detection failure, and control-loop repetition.
- **Containment:** E09, where the outer cost ceiling stops final synthesis.

Calling E09 the root cause would blame the safety mechanism for the incident.
Calling E01 the whole incident would ignore why one timeout crossed five component
boundaries.

## Recovery can be a causal link

Recovery is often written outside the incident story as “mitigation.” Here it is
inside the chain:

1. M2 retry adds load after the initiating timeout.
2. M3 breaker converts repeated failure into routing state.
3. M4 fallback introduces a second provider and a correlated quality fault.
4. M6 repetition recovery re-enters the same degraded route.
5. M5 contains the terminal effect.

The mechanisms are neither universally good nor universally bad. Their causal role
depends on placement, shared dependencies, and what they measure.

## Correlated fallback defeats naive redundancy

The fallback is available but not independent. It serves stale context with the
same headline value. That distinction matters:

- transport redundancy restores a response;
- semantic correlation preserves the underlying bad context;
- the narrow judge's documented blind spot accepts the plausible structure.

A causal graph needs the `fallback_routed → stale_fallback_context` edge because
“secondary provider” alone does not imply independence.

## Labels make replay scientifically useful

Byte-identical replay is necessary but not sufficient. A stable blob without
semantic labels cannot prove that the *same incident explanation* recurred.

The replay gate therefore checks three stable objects:

- full incident digest;
- complete trace digest;
- ordered nine-event label chain.

It also verifies every replay's trace completeness. This stops a truncated trace
from being celebrated merely because it truncates the same way every time.

## Trace references discipline the graph

Every causal node carries exact span IDs. The graph audit refuses:

- nodes with no observed trace support;
- parent links to missing spans;
- edges to missing events;
- incomplete failure spans.

This does not make the graph automatically causal, but it makes every claim
inspectable. A reader can move from narrative → event → span without guessing.

## The intervention caveat

In this simulator, the seed/config controls the initiating fault, component
policies, and correlated fallback slice. That makes the chain
intervention-informed and reproducible.

Production incidents contain confounders: traffic mix, deployment changes, queue
state, network topology, and provider behavior. Temporal order plus one trace does
not prove causality there. Stronger production evidence may require:

- disabling one recovery mechanism and comparing the downstream chain;
- replaying with the initiating fault removed;
- varying breaker/retry thresholds;
- testing an independent fallback provider;
- inspecting multiple incidents for the same edge.

Day 23's claim is deliberately narrow: **this one configured simulator incident is
causally specified, fully traced, and exactly reproducible from one seed/config.**
