# REFLECTION — five-minute mission reflection (Day 24)

**Mission.** Identify the best user-visible success per unit cost and latency for
the cascade.

**Fail condition.** Choose the winner without cost, latency, and uncertainty. —
*Not triggered:* every policy and decision contrast includes the required
dimensions and intervals; the executable gate passes.

**The answer.** P4 selective guarded is the base-envelope winner: 93.25% correct
visible success, mean cost 1.4656, p95 latency 50, and zero observed visible wrong
answers. Its Wilson success interval is [0.9036, 0.9532].

**The most important design choice.** Constraints come before efficiency. P2 is
almost tied with P4 on success per latency, but it exposes 66 wrong answers. P0
looks inexpensive because it abandons all 170 faulted requests. Neither behavior
is allowed to masquerade as optimization.

**The uncertainty check.** P4 is not chosen from point estimates alone. Against
the only other eligible policy, P1, its paired success/cost advantage is 0.0485
[0.0319, 0.0664], and its success/100-latency advantage is 0.6939
[0.5544, 0.8367].

**The debug insight.** Tight budgets create two distinct failure routes: 65
persistent cascades exceed cost first; 105 transient retries meet the cost ceiling
but exceed latency. Aggregate “budget abort” would have hidden the policy lever.

**The honesty check.** Both stress attacks withdraw the recommendation. P4 is the
best policy measured for one operating envelope, not an eternal architecture
choice. It is also a reference upper bound: production retryability classification
and fallback-guard error remain outside the measured model.

**Mastery gate.**

- *Explain* — [LEARN-multi-objective.md](LEARN-multi-objective.md).
- *Build* — P0–P4, aligned scenario population, selection rule, attacks.
- *Debug* — explicit eligibility checks and cause-specific budget aborts.
- *Measure* — Wilson, bootstrap, McNemar, paired efficiency differences.
- *Defend* — [CHECKPOINT-24.md](CHECKPOINT-24.md), decisions, attack boundary,
  executable fail-condition guard.

**What I would study next.** Estimate a deployment frontier across more fault
mixtures and provider prices, then test whether online routing can recognize which
envelope it is in without introducing a classifier failure worse than the policy
gain.
