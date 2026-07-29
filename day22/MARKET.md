# MARKET — buying recovery as a portfolio, not a checkbox

## The procurement mistake

“Has retries,” “has a circuit breaker,” or “has guardrails” are feature claims.
They do not tell a buyer which faults recover, what recovery costs, or what new
failures the mechanism creates.

Day 22 turns six recovery features into a comparable evidence contract:

- same requests with and without the mechanism;
- correct outcome and availability kept separate;
- total cost and tail latency;
- clean-control regressions;
- every induced harm by mechanism and seed.

## What a buyer should request

For every proposed mechanism × fault cell:

1. paired request identifiers;
2. correct-success and availability McNemar tables;
3. answered-wrong and contained counts;
4. paired cost/latency deltas with uncertainty;
5. clean controls representative of long and repetitive valid work;
6. a reconciled new-failure register.

A mechanism without the matching row should be treated as unmeasured, not assumed
safe.

## Commercial interpretation of this matrix

- M1/M2 earn their place on transient F1/F2, but persistent-fault budget must be
  priced.
- M3 is protection, not answer recovery; pair it with a quality-checked fallback.
- M4 increases availability and correct coverage but requires a fallback-quality
  SLO because answered-wrong failures become user-visible.
- M5/M6 are control-plane safety features whose false-positive budgets matter as
  much as their containment rate.
- F3/F5 remain a product gap: none of M1–M6 improves semantic correctness.

The marketable claim is not “all failures recovered.” It is “each recovery has a
measured operating envelope, paired benefit, and explicit harm budget.”
