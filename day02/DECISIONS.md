# DECISIONS.md — FAULTLINE decision log (Day 2)

Append-only, continues Day 1's log (D-001 … D-007). Each entry: date, decision,
why, and what it would take to reverse.

---

### 2026-07-13 · D-008 · The specimen is a single, deterministic agent
**Decision.** Day 2 builds ONE agent whose every branch is a pure function of
(env, task): no LLM sampling, no wall clock, no randomness, no second agent.
**Why.** FAULTLINE measures what an *injected fault* does. If the baseline had
its own nondeterminism, a behavior change could never be cleanly attributed to
the fault. A deterministic single agent is a controlled specimen — the fault is
the only moving part (see MARKET.md for the single-agent argument).
**Reversal cost.** Introducing an LLM policy would require pinning a model +
temperature=0 and re-establishing determinism evidence; large, deferred.

### 2026-07-13 · D-009 · Termination is structural, not best-effort
**Decision.** The loop is `while steps < step_cap` with exactly one tool call per
iteration; there is no `while True` and no unbounded recursion anywhere.
**Why.** "The agent can hang" is a Day-2 fail condition. Making the bound part of
the loop's shape (not a timeout we hope fires) means non-termination is
impossible by construction, and the proof is a five-line reading of `agent.run`.
**Reversal cost.** None desired; foundational to the mission.

### 2026-07-13 · D-010 · Every boundary is a Pydantic model with `extra="forbid"`
**Decision.** Tool calls, tool results, the task, and the outcome are all typed
models; unknown fields are rejected, not ignored. `Agent.run` is typed to return
`AgentOutcome`, and that model carries cross-field invariants.
**Why.** Closes the other two fail conditions — "bypass validation" and "return
an unstructured outcome" — at the type boundary. A malformed task can only become
a structured `INVALID` outcome; a `SOLVED` outcome with no answer cannot be
constructed at all.
**Reversal cost.** Loosening to dicts would reopen both fail conditions; not
contemplated.

### 2026-07-13 · D-011 · Two-layer judging: schema validity ≠ semantic correctness
**Decision.** Keep Pydantic (schema validity) strictly separate from `verdict.py`
(semantic correctness = correct AND grounded). An outcome must clear both.
**Why.** A well-formed outcome can still be wrong (off-by-one) or ungrounded
(right number, no citation). Conflating the two would let schema-valid-but-wrong
answers score as passes — exactly the faultline FAULTLINE exists to expose.
Demonstrated in `evidence/schema_vs_semantic.json`.
**Reversal cost.** None; this mirrors Day 1's required-source oracle stance.

### 2026-07-13 · D-012 · `calc` is a whitelisted-AST evaluator, never `eval`
**Decision.** `calc` parses the expression and walks a whitelist of AST nodes
(int literals, `+ - *`, unary sign). Names, calls, attributes, `**`, and division
are refused with `ok=False`; results over 1e12 are refused.
**Why.** A tool that ran arbitrary strings would be a code-execution hole the
moment a fault (or a caller) fed it hostile input. The tool must be safe *before*
we start attacking the system around it.
**Reversal cost.** Supporting division/exponent means new node types + an
overflow story; additive, low cost.

### 2026-07-13 · D-013 · One multi-hop task family whose step demand is a knob
**Decision.** The sole task is `archive_sum`, with
`steps_demanded = 2*len(entities) + 1`. Task size is the single dial that pushes
the agent over its step cap.
**Why.** Keeps the workload "small and bounded" while still exercising all three
tools and giving the over-budget attack a clean, arithmetic boundary
(`k ≤ 5` solvable, `k ≥ 6` over budget at `step_cap=12`).
**Reversal cost.** Adding task families is additive; each needs its own verdict
branch. Deferred until faults require more surface.
