# CHECKPOINT-24 — uncertainty-aware cascade policy choice

**Mission.** Identify the best user-visible success per unit cost and latency for
the cascade.

**Required evidence.** Policy comparison, paired statistics, and Q5
recommendation.

**Fail condition.** The winning policy is chosen without cost, latency, and
uncertainty. — **Not triggered.**

## 1. Experimental contract

The comparison uses one deterministic population:

- `n = 400`;
- seeds `2026080300…2026080699`;
- seed-list digest `99b53f8869731323`;
- 230 clean trials;
- 105 transient faults;
- 65 persistent cascades.

Every P0–P4 outcome has the same seed at the same index. A paired comparison
refuses unequal populations or misaligned seed order.

The primary operating envelope is:

| parameter | value |
|---|---:|
| primary fault rate | 0.40 |
| persistent share given fault | 0.40 |
| exact fallback share | 0.55 |
| clear-wrong fallback share | 0.25 |
| per-request cost ceiling | 5 |
| per-request latency ceiling | 120 virtual ms |
| retryability signal | simulator truth |
| fallback guard | strict simulator oracle |

## 2. User-visible outcome definition

A success is a **correct answer returned to the user**. The following do not count
as success:

- an available but wrong fallback;
- a rejected answer;
- breaker or ceiling containment;
- a recovery action that begins but exceeds its budget.

This definition keeps Day 21's availability/quality distinction and Day 23's
containment distinction intact.

## 3. Policy comparison with uncertainty

| policy | correct success, Wilson 95% CI | wrong visible, Wilson 95% CI | mean cost, boot 95% CI | p95 latency, boot 95% CI | success/cost, boot 95% CI | success/100 ms, boot 95% CI |
|---|---|---|---|---|---|---|
| P0 | 0.5750 [0.5261, 0.6225] | 0 [0, 0.0095] | 1.0000 [1, 1] | 30 [30, 30] | 0.5750 [0.5225, 0.6250] | 3.1081 [2.7121, 3.5714] |
| P1 | 0.8375 [0.7982, 0.8704] | 0 [0, 0.0095] | 1.4250 [1.3775, 1.4725] | 65 [65, 65] | 0.5877 [0.5473, 0.6268] | 2.8450 [2.5569, 3.1889] |
| P2 | 0.8350 [0.7955, 0.8682] | 0.1650 [0.1318, 0.2045] | 1.4250 [1.3775, 1.4725] | 42 [42, 42] | 0.5860 [0.5462, 0.6271] | 3.5381 [3.2252, 3.9148] |
| P3 | 0.9325 [0.9036, 0.9532] | 0 [0, 0.0095] | 1.6719 [1.5869, 1.7594] | 81 [81, 98] | 0.5578 [0.5179, 0.6005] | 2.8576 [2.5757, 3.1751] |
| **P4** | **0.9325 [0.9036, 0.9532]** | **0 [0, 0.0095]** | **1.4656 [1.4100, 1.5212]** | **50 [50, 50]** | **0.6362 [0.6037, 0.6720]** | **3.5389 [3.2488, 3.8344]** |

P0 is cheap partly because it abandons 170 faulted requests. P2 is fast partly
because it exposes 66 wrong answers. Neither is allowed to turn those failures
into an efficiency win.

## 4. Paired outcome evidence

Every candidate is paired against P0:

| candidate | Δ correct-success rate | candidate-only correct | P0-only correct | McNemar p |
|---|---:|---:|---:|---:|
| P1 bounded retry | +0.2625 | 105 | 0 | 3.34e-24 |
| P2 unchecked fallback | +0.2600 | 104 | 0 | 5.53e-24 |
| P3 full cascade | +0.3575 | 143 | 0 | 1.60e-32 |
| P4 selective guarded | +0.3575 | 143 | 0 | 1.60e-32 |

The final eligible-policy decision is also paired:

| P4 minus P1 | point delta | paired bootstrap 95% CI |
|---|---:|---|
| correct-success rate | +0.0950 | McNemar p ≈ 1.95e-9 |
| mean cost | +0.0406 | [0.0319, 0.0500] |
| mean latency | −3.0875 | [−3.8000, −2.4225] |
| success/cost | +0.0485 | [0.0319, 0.0664] |
| success/100 ms | +0.6939 | [0.5544, 0.8367] |

P4 costs slightly more per request than P1, but it recovers 38 additional correct
answers, reduces mean latency, and improves both aggregate efficiency ratios with
intervals wholly above zero.

## 5. Selection and Q5

Eligibility uses confidence bounds, not point estimates:

- success lower bound ≥ `0.78`;
- wrong-visible upper bound ≤ `0.02`;
- mean-cost upper bound ≤ `1.75`;
- p95-latency upper bound ≤ `80`.

Only P1 and P4 clear all four. P4 leads both efficiency measures, and its paired
efficiency-difference lower bounds versus P1 are positive.

**Q5 recommendation: choose `P4_selective_guarded` as the reference upper-bound
policy in the base operating envelope.**

P4's routing label and strict guard are simulator oracles. This experiment does
not claim that a production classifier or the Day-16 narrow judge has the same
performance. Those error rates and their resource costs need a separate paired
measurement before deployment.

## 6. Winner attacks

### Worse severity and correlation

Fault rate rises to 0.65, persistence given fault to 0.70, exact fallback quality
falls to 0.35, and latency scales by 1.6.

- success: 0.6950, Wilson 95% CI [0.6482, 0.7381];
- mean cost: 1.7419, bootstrap upper bound 1.7975;
- p95 latency: 80;
- base-to-attack success delta: −0.2375;
- recommendation survives: **false**.

The success and mean-cost constraints fail.

### Tight budgets

The cost ceiling falls to 2 and latency ceiling to 45 virtual ms.

- success: 0.5750, Wilson 95% CI [0.5261, 0.6225];
- 65 cost-budget aborts;
- 105 latency-budget aborts;
- base-to-attack success delta: −0.3575;
- recommendation survives: **false**.

The budgets appear controlled only because recovery is suppressed. This is a
measured new failure, not an acceptable cost optimization.

## 7. Executable fail-condition guard

The report gate verifies:

- all policy comparisons share seeds;
- the winner has measured cost;
- the winner has measured p95 latency;
- success, wrong answers, cost, latency, and both efficiencies have intervals;
- paired statistics exist;
- dual efficiency dominance is proven;
- the winner is attacked under two changed envelopes.
- the report carries the winner's model-scope caveats.

All checks are true; `passed=true`.

## Required evidence

- **Policy comparison:** `evidence/policy_comparison.json`
- **Paired statistics:** `evidence/paired_statistics.json`
- **Winner attacks:** `evidence/winner_attack.json`
- **Q5 machine-readable recommendation:** `evidence/q5_recommendation.json`
- **Q5 human-readable recommendation:** `evidence/Q5_RECOMMENDATION.md`

## Mastery gate — all five

- **Can explain** — correctness is the outcome; cost and latency are resources;
  uncertainty controls the decision boundary.
- **Can build** — five policies run over one deterministic cascade population.
- **Can debug** — every exclusion maps to a failed constraint; attack aborts retain
  the responsible ceiling.
- **Can measure** — Wilson intervals, bootstrap intervals, McNemar, and paired
  efficiency deltas.
- **Can defend** — selection is predeclared, constraint-first, paired, attacked,
  and explicitly conditional.
