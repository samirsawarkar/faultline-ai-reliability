# MARKET — postmortems that prove the action item

## The gap

Incident tools can generate polished summaries from logs, but the resulting
action items are often disconnected from verification:

- “improve retry logic”;
- “add monitoring”;
- “make fallback safer.”

The next incident then reveals that the prose changed while the failure path did
not.

## Day 25's evidence contract

A durable incident product should package:

1. a frozen seed/input and configuration;
2. a timeline whose events cite complete traces;
3. impact, detection, root cause, and contributing factors;
4. system-level, blameless corrective actions;
5. one unchanged outcome predicate;
6. a legacy replay that demonstrably fails it;
7. a fixed replay that demonstrably passes it;
8. repeated and fresh-process proof that green is stable;
9. an explicit boundary on what the simulator result does not prove.

This turns a postmortem into a portable regression asset for incident review,
release gating, vendor evaluation, and reliability training.

## Published case study

The Day 23 recovery cascade is packaged in
`evidence/CASE_STUDY.md`. It demonstrates a non-obvious result: the cost ceiling
worked and the system still failed the user. The corrective policy returns a
correct answer at the same cost with fewer steps and lower latency.

## Defensible claim

> Two frozen incidents replay red under their legacy policies and green under
> trace-linked fixes, then remain green across repeated and fresh-process replay.

It is not:

> These controls eliminate all fallback or deadline failures in production.

Production independence, reference availability, concurrency, and provider-load
effects remain outside the deterministic model. The value is a verifiable
learning loop, not a claim of universal prevention.
