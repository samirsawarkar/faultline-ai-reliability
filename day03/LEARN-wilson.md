# LEARN — Wilson confidence intervals

## The problem with the obvious interval

You run 500 tasks in a tier, 500 succeed, and you report **"100% success."** But
you didn't test infinitely many tasks — you tested 500. What's the honest range
the true success rate could be in?

The textbook ("normal approximation" / Wald) interval is:

```
p ± z · sqrt( p(1-p) / n )
```

It has two failures that matter exactly where a baseline lives:

1. **At p = 0 or p = 1 it collapses to zero width.** With 500/500, `p(1-p) = 0`,
   so Wald reports `[1.0, 1.0]` — a claim of *perfect certainty* from a finite
   sample. That is false, and for a reliability baseline it is the most dangerous
   kind of false.
2. **It leaks outside [0, 1]** for small `n` or extreme `p`, producing negative
   lower bounds or upper bounds above 1 — impossible probabilities.

## The Wilson score interval

Wilson inverts the score test instead of assuming a symmetric normal around `p`.
With `z` the normal quantile (1.96 for 95%):

```
center = ( p + z²/2n ) / ( 1 + z²/n )
half   = ( z / (1 + z²/n) ) · sqrt( p(1-p)/n + z²/4n² )
CI     = center ± half        (clamped to [0, 1])
```

Properties that make it the right tool here:

- **Never zero-width at the extremes.** 500/500 becomes **[0.992, 1.000]** — it
  admits the true rate could be as low as ~99.2%, which is the honest statement.
- **Always inside [0, 1].** No impossible bounds.
- **Well-behaved for small n.** The classic reference case 0/10 gives an upper
  bound of ≈ 0.28 — you have *not* proven the rate is near zero from 10 tries.
- **Asymmetric near the edges**, which is correct: at high `p` there is more room
  to be wrong below than above.

## How FAULTLINE uses it

Every success rate in `baseline.json` — per tier and per hop — ships with a
Wilson 95% interval (`stats.wilson_interval`, `z = 1.96` from the frozen config).
That is why the committed baseline reads:

| tier | rate | Wilson 95% CI |
| --- | --- | --- |
| easy | 1.000 | **[0.992, 1.000]** |
| medium | 0.658 | **[0.615, 0.698]** |
| hard | 0.000 | **[0.000, 0.008]** |

The `easy` and `hard` rows are the tell: a lesser interval would print
`[1,1]` and `[0,0]` and pretend the sample settled the question. Wilson keeps the
residual uncertainty visible, which is the entire job of a confidence interval on
a zero point that later days will be compared against.

## One sentence

*Use Wilson, not Wald, because a baseline's most important numbers are the ones
near 0% and 100% — exactly where the naive interval lies and says "certain."*
