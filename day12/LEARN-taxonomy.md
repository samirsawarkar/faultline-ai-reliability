# LEARN — a failure taxonomy by producing component

Day 12 consolidates the six faults, and the most useful lens for consolidation is
not "what does the failure look like?" but "**which component produced it?**" A
symptom-first taxonomy tells you what broke; a producer-first taxonomy tells you
*where to add a guard*. For an engineer, the second is the actionable one.

## The two layers and four producers

FAULTLINE's agent has two layers that fail differently:

**The provider boundary** — everything the agent gets from the outside (a tool, a
model API, a retrieval service). It fails in two ways:
- *Content* (the data plane): the value comes back wrong. F1 (malformed shape) and
  F3 (schema-valid-but-wrong) live here. Malformed content is deterministic to
  catch (a schema); wrong content splits — gross errors are caught, plausible ones
  escape and need semantics.
- *Transport* (availability and timing): F2 (too slow) and F4 (explicit error).
  Both are deterministic to detect — a duration versus a budget, an explicit error
  flag — and both have clean, well-known recovery patterns (timeout/retry, circuit
  breaker/fallback).

**The agent internals** — everything the agent does with what it got. It also
fails in two ways:
- *State/context* (memory): F5. A wrong value enters the running context and
  propagates. Semantic to catch, because a corrupted context can be perfectly
  self-consistent.
- *Control* (the loop): F6. The loop repeats or never terminates. Deterministic to
  catch, because termination is a counting property.

## The pattern that falls out

Lay the six faults on this grid and a striking regularity appears:

| producer | fault(s) | detection nature |
|---|---|---|
| provider transport | F2, F4 | **deterministic** |
| agent control loop | F6 | **deterministic** |
| provider content | F1 (malformed), F3 (malformed) | **deterministic** |
| provider content | F3 (schema-valid drift) | **semantic** |
| agent context | F5 | **semantic** |

Everything about *transport, control, and shape* is deterministic to detect —
counts, budgets, flags, schemas, no model of correctness required. Everything about
*the value being right* — coherent wrong data from a tool, a self-consistent wrong
context — is semantic, and carries an irreducible escape set under any
deterministic detector. This is exactly Day 11's deterministic-vs-semantic split,
now explained by *where* the fault is born: value-correctness faults come from the
two places that hold values (the data plane and the agent's memory), and only a
correctness model can judge a value.

## Why the producer view is the one to keep

Three payoffs:

1. **It tells you where to instrument.** Each producer gets its characteristic
   guard: schemas and duration/error checks at the provider boundary; a termination
   counter and a repetition check on the loop; a correctness oracle or judge for
   the value layers. You are not sprinkling detectors randomly; you are covering
   producers.
2. **It predicts the hard cases before you measure them.** Anything that is "a
   value from a tool or from memory" will need semantics; anything about transport,
   control, or shape will not. That is a design heuristic you can apply to a fault
   you have not catalogued yet.
3. **It scopes the expensive machinery.** A validated judge (Mission 16) is costly,
   so you want to deploy it *only* where deterministic detection provably cannot
   reach — F3's schema-valid drift and F5's context corruption. The producer
   taxonomy draws that boundary for you.

## References worth reading next

- Failure taxonomies and fault models: Avižienis et al., *Basic Concepts and
  Taxonomy of Dependable and Secure Computing* (2004) — the fault/error/failure
  chain and the value/timing distinction used here.
- Component-level hardening: Nygard, *Release It!* (stability patterns organized by
  integration point).
- The value-vs-transport split maps onto the classic *content* vs *timing* failure
  modes in distributed systems (byzantine vs crash/omission faults).
