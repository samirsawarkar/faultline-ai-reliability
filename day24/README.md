# FAULTLINE — Day 24: Q5 cascade policy decision

Identify the cascade policy with the best **user-visible correct success** per
unit cost and latency, without selecting a winner that violates correctness or
hides uncertainty.

> **Fail condition:** the winning policy is chosen without cost, latency, and
> uncertainty.
> **Status: not triggered.** Every policy row includes correctness and
> wrong-answer Wilson intervals, cost and p95-latency bootstrap intervals, and
> paired evidence over the same 400 seeds. The executable guard passes. See
> [CHECKPOINT-24.md](CHECKPOINT-24.md).

## Q5 answer

**Recommend `P4_selective_guarded` as the reference upper-bound policy inside
the measured base envelope.**

It retries faults classified as transient and sends persistent faults to one
quality-gated fallback. Across the shared seeds it returns 373/400 correct visible
answers:

- correct success: **0.9325**, Wilson 95% CI **[0.9036, 0.9532]**;
- wrong visible answer: **0**, Wilson upper bound **0.0095**;
- mean cost: **1.4656**, bootstrap 95% CI **[1.4100, 1.5212]**;
- p95 latency: **50 virtual ms**, bootstrap 95% CI **[50, 50]**;
- correct successes per cost: **0.6362**;
- correct successes per 100 virtual ms: **3.5389**.

This is a conditional recommendation, not a universal winner. It fails the
success floor under both the worse-severity and tight-budget attacks.

P4 receives the simulator's transient/persistent label and uses the strict
simulator oracle as its fallback guard. Those assumptions are serialized in the
configuration. Production retryability classification and guard errors are not
covered by these intervals and must be measured before deployment.

## Policy comparison

All five policies run on seeds `2026080300…2026080699`.

| policy | correct success | wrong visible | mean cost | p95 latency | success/cost | success/100 ms | decision |
|---|---:|---:|---:|---:|---:|---:|---|
| P0 no recovery | 0.5750 | 0 | 1.0000 | 30 | 0.5750 | 3.1081 | fails success floor |
| P1 bounded retry | 0.8375 | 0 | 1.4250 | 65 | 0.5877 | 2.8450 | eligible |
| P2 unchecked fallback | 0.8350 | 0.1650 | 1.4250 | 42 | 0.5860 | 3.5381 | fails wrong-answer bound |
| P3 full cascade | 0.9325 | 0 | 1.6719 | 81 | 0.5578 | 2.8576 | fails cost and latency bounds |
| **P4 selective guarded** | **0.9325** | **0** | **1.4656** | **50** | **0.6362** | **3.5389** | **winner** |

The complete table, including every 95% interval, is
[Q5_RECOMMENDATION.md](evidence/Q5_RECOMMENDATION.md).

## Decision rule

The selection is constraint-first:

1. success Wilson lower bound must be at least `0.78`;
2. wrong-visible Wilson upper bound must be at most `0.02`;
3. mean-cost bootstrap upper bound must be at most `1.75`;
4. p95-latency bootstrap upper bound must be at most `80`;
5. among eligible policies, one policy must lead both efficiency measures;
6. its paired bootstrap difference intervals against every other eligible policy
   must stay above zero.

This prevents a policy from winning by failing quickly, exposing wrong answers, or
trading one objective away inside sampling noise.

Against the only other eligible policy, P1, P4 gains:

- **+0.0950** correct-success rate; McNemar p ≈ `1.95e-9`;
- **+0.0485** success/cost, paired 95% CI **[0.0319, 0.0664]**;
- **+0.6939** success/100 ms, paired 95% CI **[0.5544, 0.8367]**.

## Attack boundary

| attack | success (95% CI) | mean cost | p95 latency | result |
|---|---|---:|---:|---|
| worse severity/correlation | 0.6950 [0.6482, 0.7381] | 1.7419 | 80 | success and cost bounds fail |
| cost ≤2, latency ≤45 | 0.5750 [0.5261, 0.6225] | 1.4250 | 45 | success bound fails |

Under the tight budgets, 65 persistent cases hit the cost ceiling and 105
otherwise-recoverable transient cases hit the latency ceiling. Lower observed
cost and latency therefore do not imply a better outcome.

## Day plan delivered

| block | delivered |
|---|---|
| **08:00–10:00 · Build A** | no-recovery baseline plus four candidate policies |
| **10:15–12:15 · Build B** | 400 aligned seeds, Wilson/bootstrap intervals, McNemar and paired bootstrap comparisons |
| **13:00–15:00 · Attack + experiment** | worse-severity/correlation and tight-budget attacks |
| **15:15–16:15 · Learn** | [constraint-first multi-objective decisions](LEARN-multi-objective.md) |
| **16:30–17:30 · Evidence + market** | Q5 evidence, checkpoint, tradeoff statement, [market note](MARKET.md) |

## What's here

```text
faultline_q5/
  scenario.py    shared seeded population and operating configurations
  policies.py    P0–P4 policy outcomes and per-request budget enforcement
  metrics.py     correctness, wrong-answer, cost, tail, efficiency, paired stats
  selection.py   uncertainty-aware constraints and dual-dominance rule
  experiment.py  aligned policy comparison
  report.py      winner attacks, Q5 recommendation, executable fail guard
  render.py      measured Q5 Markdown
scripts/
  make_evidence.py
tests/           shared-seed, policy, statistics, attack, and report gates
evidence/
  policy_comparison.json
  paired_statistics.json
  winner_attack.json
  q5_recommendation.json
  Q5_RECOMMENDATION.md
CHECKPOINT-24.md · LEARN-multi-objective.md · DECISIONS.md
REFLECTION.md · MARKET.md
```

## Quickstart

```bash
python -m pytest tests/ -q
python scripts/make_evidence.py
```

The experiment is standard-library only and reuses Day 14's verified Wilson,
bootstrap, and paired-test implementations.

## Mastery gate — all five

- **Explain** — distinguish correct success, availability, containment, and
  efficiency; explain why constraints precede optimization.
- **Build** — define candidate policies and run them over one aligned population.
- **Debug** — trace each rejected policy to a specific constraint and each
  tight-budget loss to its cost or latency ceiling.
- **Measure** — report paired outcomes, cost, tail latency, efficiency, and 95%
  uncertainty.
- **Defend** — state the operating envelope, attack the winner, and withdraw the
  recommendation when its bounds fail.
