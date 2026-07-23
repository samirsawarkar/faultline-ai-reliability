# LEARN — schema validity vs. semantic correctness

## The distinction

There are two different questions you can ask about an agent's answer, and it is
easy — and dangerous — to confuse them.

1. **Schema validity** — *is the answer well-formed?* Does it have the right
   fields, the right types, no stray keys, and does it satisfy its structural
   invariants? This is what **Pydantic** checks in `contracts.py`.

2. **Semantic correctness** — *is the answer right?* Does the number match the
   truth, and is it grounded in the sources that actually contain the facts?
   This is what **`verdict.py`** checks.

Schema validity is **necessary but not sufficient**. A perfectly well-formed
outcome can be completely wrong.

## The demonstration

`scripts/schema_vs_semantic.py` builds three `AgentOutcome`s that **all pass
Pydantic** — each object exists, so each validated — and runs the verdict:

```
outcome         schema  correct  grounded  passes
-------------------------------------------------
agent_real       valid     True      True    True
wrong_number     valid    False      True   False    # answer off by one
ungrounded       valid     True     False   False    # right number, cites nothing
```

`wrong_number` is a syntactically flawless `SOLVED` outcome carrying `"12016"`
instead of `"12015"`. Pydantic has no basis to reject it — `"12016"` is a valid
string. Only a judge with access to ground truth can. `ungrounded` reports the
correct sum but cites no sources; it is right by luck, not by retrieval, and the
grounded check catches it — the same stance as Day 1's required-source oracle.

## Why FAULTLINE needs both layers

- If you **only validate the schema**, a fault that corrupts the *content*
  (a mis-ranked search hit, an off-by-one in `calc`, a dropped citation)
  produces a still-valid outcome and slips through as a "pass." You would report
  that the system works when it is silently wrong.
- If you **only check semantics**, a malformed or unstructured outcome has no
  stable shape to judge — you would be back to eyeballing, which Day 1 abolished.

So the pipeline is a funnel: **Pydantic guarantees there is always a
well-formed thing to judge; the verdict decides whether that thing is true.**
The gap between the two layers is precisely where injected faults will try to
hide, which is why Day 2 makes the boundary explicit and tests it
(`tests/test_semantics.py`) before any fault is introduced.

## The one-sentence version

*Valid means "the shape is right"; correct means "the content is right" — and a
measurement framework that cannot tell them apart cannot be trusted to say a
system works.*
