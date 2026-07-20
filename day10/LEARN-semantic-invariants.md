# LEARN — semantic invariants and circuit-breaker signals

Day 10 sits on the most dangerous seam in a document-grounded AI system: the tool
that returns a **plausible, well-formed, wrong** answer. This note explains why
that seam is so hard, what semantic invariants buy you, and why explicit provider
errors are the easy case by comparison.

## The detectability ladder

Think of correctness checks as rungs, cheapest and weakest at the bottom:

1. **Schema / contract validation** — is it the right *shape*? (Day 9) Catches
   `malformed_range`, `malformed_tokens`. Cheap, deterministic, and the floor
   every pipeline should have. But a schema is blind to a well-typed wrong value.
2. **Semantic invariants** — does it obey *domain rules* the shape doesn't
   encode? Here: "value is a round ten." Catches `nonmultiple`. Invariants are the
   most under-used rung: they are still cheap and deterministic, and they catch a
   whole class of corruption that schemas miss (units wrong, sign flipped,
   checksum broken, ID not in the allowed set, total ≠ sum of parts).
3. **The oracle** — is it the *right answer*? Only the oracle catches
   `drift_value` (a different legal value) and `offbase_tokens` (a shifted but
   consecutive run). An oracle is expensive: it needs a source of truth (Day 1's
   required-source oracle, a golden dataset, or a validated judge — Mission 16).

The mission's finding is the gap between rungs 2 and 3. A finite set of invariants
raises the floor but never reaches the ceiling: for any invariant set you can
construct a wrong output that satisfies all of them. Day 10 makes that concrete —
**40% of injected wrong-data faults escape** schema + invariant, and the escape is
**severity-invariant**: making the value more wrong doesn't make it more visible,
because "more wrong" is still "a legal value."

## Why this is the honest, and uncomfortable, result

It is tempting to tighten the invariant until recall hits 1.0 and declare victory.
That is exactly the failure mode the mission forbids: at that point your
"invariant" is the oracle in disguise, and you have measured nothing. The
disciplined move is to keep the invariant partial, **report the escape set, and
prove each escape is wrong with the oracle** (`false_negatives.json`). A missed
detection with evidence is a real finding; a 1.0 recall with no evidence is a
false comfort. In production this is the difference between "our validator passed
it" and "our validator *cannot see* this class of error, and here are examples."

The practical rules:

- **Add invariants aggressively** — they are cheap wins (rung 2 is where most
  teams leave value on the table). But
- **never report schema-valid as correct.** Track the residual escape set as a
  known blind spot, and reserve the oracle/judge for the cases that matter.

## Provider errors are the easy case — so use them well

`F4` is the opposite of `F3`: an explicit provider error is trivially detectable
(recall 1.0) because the signal is *given*, not inferred. The interesting question
isn't detection but **action**. The canonical action is a **circuit breaker**:
once errors pile up (here, 2 in a 3-call window), stop calling the failing
dependency instead of hammering it — which prevents a provider's bad minute from
becoming your bad hour. Day 10 emits the signal deterministically; the policy
(open → half-open → close, fallbacks) is Mission 20.

The contrast is the lesson: **the faults that are loud are safe; the faults that
are quiet are dangerous.** An explicit 500 announces itself; a schema-valid wrong
value hides inside a green check. Reliability work is disproportionately about the
quiet faults — which is why measuring the escape set, not just the caught set, is
the whole game.

## References worth reading next

- Semantic validation / invariants and design by contract: Meyer, *Object-Oriented
  Software Construction* (contracts); property-based testing (Hughes, QuickCheck)
  as a way to discover invariants.
- Correctness oracles and the oracle problem: Barr et al., *The Oracle Problem in
  Software Testing: A Survey* (2015).
- Circuit breakers: Nygard, *Release It!* (the Circuit Breaker and Bulkhead
  stability patterns).
