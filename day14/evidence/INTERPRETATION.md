# Interpreting FAULTLINE intervals and paired tests

A plain-English guide to reading the two things this project reports for every
comparison: a **confidence interval** on a rate, and a **McNemar test** on a paired
comparison.

## Confidence intervals (Wilson)

Every rate we report (a detector's recall, an accuracy) is an estimate from a
finite sample, so it comes with a **95% Wilson interval**. Read it like this:

- The point value (e.g. "recall 0.75") is the best single guess.
- The interval (e.g. "[0.65, 0.83]") is the range of true rates consistent with the
  data. **It is not a probability about this one interval**; it means a procedure
  that produces such intervals contains the truth 95% of the time.
- **Two rates whose intervals overlap are not distinguishable at this sample size.**
  A higher point estimate with an overlapping interval is not evidence of a real
  difference — collect more samples to narrow the bands.
- Smaller n → wider interval. At n=0 the interval is [0, 1]: no data, no claim.
- Wilson is used (not the normal approximation) because it stays inside [0, 1] and
  is correct at the extremes (p near 0 or 1) and for small n.

## Paired comparisons (McNemar)

To compare two systems fairly we run them on the **same seeded samples** (a paired
design). This cancels sample-to-sample difficulty, so the only evidence about a
difference lives in the **discordant pairs** — samples where exactly one system was
right.

- McNemar looks only at the two discordant counts (A-right/B-wrong and
  A-wrong/B-right). Pairs where both agree carry no information and are correctly
  ignored.
- Small discordant counts use the **exact binomial** p; larger counts use the
  continuity-corrected **chi-square**. We report both and mark which to trust.
- p < 0.05 means the difference is unlikely under "the two systems are equally
  good." **A significant McNemar result says the systems differ, not by how much** —
  pair it with the accuracy intervals to see the size.
- Watch the counts: 5 one-directional discordant pairs give p = 0.0625 (not
  significant); it takes 6 (p = 0.03125) to cross 0.05. Significance needs enough
  discordant evidence, not just a clean direction.

## The rule of thumb

Never report a bare number. Report the estimate, its interval, and — when comparing
— the paired test. A difference is only real if the paired test says so; a rate is
only precise if its interval is narrow.
