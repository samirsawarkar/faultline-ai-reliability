# LEARN — validation limits and latency budgets

Day 9 builds two detectors and scores them. The two Build blocks teach two
lessons that recur throughout reliability work: **validation tells you an output
is malformed, not that it is wrong**, and **latency is only "too slow" relative
to a budget you chose**.

## Validation catches malformed, not wrong

The F1 detector is a schema validator. Schema validation is the cheapest,
most-deterministic quality gate a system can have, and every production pipeline
should have one — a malformed tool output should never reach business logic. But
it is easy to over-trust. A schema answers *"is this the right shape?"*, never
*"is this the right answer?"*.

The severity sweep makes the boundary visible. A severity-1 `corrupt` fault nudges
`value` by 111 — often leaving it inside the schema's `[10, 150]` range. The
output is still a well-typed object with four consecutive tokens and a non-empty
step, so the schema **passes it** (recall 0.667 at severity 1). Only when the
corruption is gross enough to break a structural rule does validation catch it
(recall 1.0 from severity 2). The missed cases are not a bug in the detector —
they are the definition of what a schema can and cannot see. Catching
*plausible-but-wrong* outputs needs an oracle (Day 1) or a judge (Mission 16),
not a validator.

The practical rule: **use schema validation to reject the malformed cheaply, but
never report schema-valid as correct.** FAULTLINE keeps the two layers separate
on purpose (Day 2's two-layer judging; Day 9's schema-vs-oracle distinction).

## Latency is a budget, not a property

The F2 detector flags a call when its duration exceeds a budget. The key insight
is that **there is no absolute "too slow."** The identical severity-4 latency
fault (duration 50) is a timeout under a 45-unit budget and perfectly fine under
a 60-unit budget — `f2_budget_sensitivity` shows exactly this. Detection is a
*policy* you set, not a fact about the fault.

That has consequences a real system lives with:

- **A tighter budget raises recall but risks false positives** on naturally slow
  calls. The right budget is a trade-off against the *distribution* of clean
  latencies, not a single number pulled from the air.
- **A budget must be stated to be defended.** "The service was slow" is not a
  finding; "12% of calls exceeded the 200 ms p99 budget" is. FAULTLINE makes the
  budget an explicit, swept constant so every timeout claim carries the
  threshold that produced it.
- **Virtual time keeps the measurement honest.** Because duration here is logical
  cost, not a wall clock, the sweep is byte-reproducible and never conflates host
  jitter with the injected latency. When a real clock arrives, the budget detector
  is unchanged — only the source of `duration` differs (D9-004).

## Why scoring against injection truth is the whole game

Both lessons only land because every number is scored against the Day-8 injection
log. Recall 0.667 is a *true* statement about the schema detector precisely
because we know, per call, whether a corruption was injected. Score a detector
against its own output and you learn nothing; score it against independent truth
and "how good is this detector?" becomes a number you can defend. The specificity
check (schema detector vs latency truth → recall 0) is the reminder that a
detector's score is meaningless unless it is measured against the *right* truth.

## References worth reading next

- Two-layer validation (well-formedness vs semantics): see Day 2's
  schema-vs-correctness split and the classic distinction between syntactic and
  semantic validation.
- Latency budgets / SLOs: Beyer et al., *Site Reliability Engineering* (Google),
  chapters on SLOs and error budgets.
- Precision/recall and confusion matrices for detector evaluation: any standard
  treatment of binary classification metrics; the subtlety here is the *source of
  labels*, not the arithmetic.
