# MARKET — a recovery choice a buyer can audit

## The gap

Recovery products are commonly sold with one headline:

> success rate increased.

That number does not show whether the system spent twice as much, doubled tail
latency, or quietly returned plausible wrong answers. A cheap, fast policy may
simply abandon the hardest requests.

## Day 24's evidence contract

A policy recommendation should ship with:

1. an explicit correct user-visible outcome;
2. a no-recovery baseline and named candidates;
3. shared-seed paired results;
4. wrong-answer risk beside success;
5. cost and tail latency in original units;
6. intervals for every decision dimension;
7. declared admissibility thresholds;
8. paired evidence against every admissible alternative;
9. attacks that state when the recommendation stops applying.

This makes the artifact useful for architecture review, provider procurement,
SLO/budget negotiation, and regression gating.

## Q5 tradeoff statement

In the measured base envelope, selective retry plus one strict-oracle-gated fallback
returns the same number of correct answers as the full cascade with less cost and
lower tail latency. It beats bounded retry on both paired efficiency measures.
Unchecked fallback is excluded because its 16.5% wrong-visible rate violates the
quality constraint.

The recommendation is withdrawn when severity/correlation rise or budgets prevent
recovery from completing.

## Defensible claim

> Over 400 aligned simulator seeds, the reference P4 policy is the only admissible policy with
> uncertainty-backed leadership on both correct-success-per-cost and
> correct-success-per-latency.

It is not:

> P4 is always the cheapest, fastest, or safest production recovery policy.

Production pricing, provider dependence, classifier error, workload mix, and
latency distributions still need measurement. Naming those limits is part of the
product, not a disclaimer added after the sale.
