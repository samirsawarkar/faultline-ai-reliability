# LEARN — multi-objective reliability decisions

## Reliability choices are constrained decisions

A recovery policy is not “better” because it maximizes one score. It can increase
availability by showing wrong answers, lower latency by abandoning hard requests,
or lower cost by refusing recovery. Those are changes in the product outcome, not
free efficiency gains.

Day 24 treats the choice as:

1. define the user outcome that cannot be traded away;
2. reject policies that violate risk or resource constraints;
3. compare the remaining policies on cost and latency efficiency;
4. require uncertainty-backed paired dominance;
5. test whether the recommendation survives a changed operating envelope.

## Why not use one weighted utility?

A score such as

`success − 0.1 × cost − 0.01 × latency`

looks decisive but hides three judgments:

- the exchange rate between correctness and money;
- the exchange rate between correctness and waiting;
- whether wrong visible answers are ever acceptable.

Small weight changes can reorder policies, and no stakeholder can see which safety
boundary moved. Day 24 instead uses explicit confidence-bound constraints and
reports two efficiency ratios separately.

Weighted utility can still be useful after product owners supply defensible
weights. It should not invent those weights on their behalf.

## Constraint-first selection

The Day 24 admissibility set requires:

- a lower confidence bound on correct success;
- an upper confidence bound on wrong visible answers;
- an upper confidence bound on mean cost;
- an upper confidence bound on p95 latency.

This is a conservative chance-constrained decision. P2's latency efficiency is
competitive with P4, but P2 exposes wrong answers in 16.5% of trials, so it is not
an admissible substitute. P0's low latency partly measures early abandonment.

## Pareto reasoning

A policy is Pareto-dominated if another policy is no worse on all relevant
outcomes and better on at least one. P3 and P4 return the same 373 correct answers
with zero visible wrong answers, but P4 has lower mean cost and lower p95 latency
in this model. P3 therefore has no compensating measured benefit in the base
envelope.

P1 and P4 require a subtler comparison: P4 costs 0.0406 more per request, but
returns 38 more correct answers and lowers mean latency by 3.0875. Efficiency
ratios make that trade visible; paired intervals test whether the gain is stable.

## Why pairing matters

Every policy sees the same clean, transient, persistent, and fallback-quality
draws. The paired contrast asks what changes for the same request when only the
policy changes. That removes seed-difficulty variation from the comparison.

For binary success, McNemar's test uses only discordant pairs. For continuous
cost, latency, and efficiency differences, Day 24 resamples aligned outcome pairs.
An unpaired analysis would discard the experiment's strongest control.

## Ratio caution

Success per cost and success per latency are aggregate ratios:

`total correct visible answers / total resource consumed`.

They are useful for capacity and portfolio decisions but can be gamed:

- dropping difficult requests reduces the denominator;
- returning unchecked answers increases the numerator if “visible” is confused
  with “correct”;
- ratios with near-zero denominators can become unstable.

Therefore the numerator is oracle-correct success, denominators are always
reported in their original units, and eligibility constraints are evaluated
before ratios.

## Tail latency versus mean latency

Mean latency answers capacity questions; p95 answers user-experience questions.
P3's mean does not reveal its 81–98 unit recovery tail. A policy cannot pass Day
24's latency gate on the mean alone.

The bootstrap interval for a discrete p95 can be flat when the same latency tier
occupies a wide rank range. That does not mean the real world has zero uncertainty;
it means uncertainty conditional on this finite simulator distribution and
policy model does not move the nearest-rank statistic.

## Attacks define the recommendation's domain

The base result is not portable without its fault mixture, fallback quality,
correlation, and budgets. Worse persistence removes the guarded fallback's supply
of exact answers. Tight budgets prevent even transient retries from completing.

A defensible conclusion is therefore:

> P4 wins inside the measured base envelope and must be re-evaluated when the
> severity, correlation, provider quality, or budget envelope changes.

This is stronger than declaring a permanent winner because it states what would
falsify the recommendation.

## Review checklist

Before defending a multi-objective recovery choice, ask:

- Is success actually user-visible and correct?
- Are wrong answers counted separately from abstentions?
- Do all policies see the same seeds?
- Are cost and latency reported in original units?
- Is tail latency present?
- Does every decision dimension carry uncertainty?
- Are constraints explicit and stakeholder-reviewable?
- Is the winner compared with every admissible alternative?
- Was the winner attacked outside the base envelope?
- Does the recommendation state when it must be withdrawn?
