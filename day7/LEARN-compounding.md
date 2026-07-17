# LEARN-compounding.md — compounding probability assumptions

Notes on the math behind Q1, and exactly which assumptions the measured curve
breaks.

## The naive compounding model

If a task needs `n` hops and each hop succeeds **independently** with the **same**
probability `p`, then end-to-end success is:

    P(all n succeed) = p^n

This is seductive because it's simple and often quoted ("each step is 95%
reliable, so 10 steps is 0.95^10 ≈ 60%"). It rests on **two** assumptions:

1. **Homogeneity** — every hop has the same success probability `p`.
2. **Independence** — one hop's outcome doesn't change another's.

## Why real chains decay faster (both assumptions fail)

- **Homogeneity fails: per-hop reliability degrades with depth.** Later hops run
  on more accumulated context and more opportunities for earlier partial errors
  to propagate, so `p_k` falls as `k` grows. Then the true product

      ∏_{k=1}^n p_k   <   p_1^n

  because you're multiplying by numbers smaller than `p_1`. This is exactly Day
  7's model (`p_k = P0 − DECAY·(k−1)`), and the measured `∏ p_k` (the `corrected`
  curve) matches the empirical end-to-end curve.
- **Independence fails: correlated failures.** In real systems a bad retrieval or
  a poisoned context makes *several* downstream hops fail together. Positive
  correlation makes the all-succeed probability fall faster than the independent
  product. (Day 7 isolates the homogeneity effect; correlation is an additional,
  compounding reason to distrust `p^n`.)

**Consequence:** `p^n` is an **optimistic upper bound** on multi-hop reliability.
Quoting it as a prediction overstates how reliable a long chain will be — which
is precisely what the measured-vs-naive gap shows.

## Measuring it honestly

- **Estimate per-step reliability separately** (per-hop accounting), don't assume
  it's constant. A declining `p_k` is the signal.
- **Put an interval on every rate.** We use the **Wilson** score interval (as in
  Day 3): the normal approximation collapses to zero width at `p = 1`, falsely
  claiming certainty. Wilson stays inside [0, 1] and never collapses.
- **Watch sample size at depth.** Because runs abort at the first failure, deep
  hops are reached by far fewer runs, so their intervals are wider. Uncertainty
  is not uniform across the curve, and the report must show that.
- **Falsification, not vibes.** The claim "naive is wrong" is made precise: the
  smallest `n` where the naive band and the measured band are **disjoint**. Here,
  n = 3.

## Takeaways

- Multi-hop reliability is a **product**, and products of sub-1 numbers fall off a
  cliff — but the real cliff is steeper than `p^n` once homogeneity/independence
  break.
- Design implication: reducing **required hops** (or adding recovery so a hop
  failure isn't fatal) buys more reliability than squeezing a few points out of a
  single hop's `p`.
- Always pair a reliability number with its **hop count** and a **confidence
  interval**; a bare "95% reliable" is meaningless without "per what, over how
  many hops, measured how."
