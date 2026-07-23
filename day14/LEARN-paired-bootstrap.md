# LEARN — paired experiments and bootstrap assumptions

Day 14 is about making comparisons honest. Two ideas do most of the work: **pairing**
(how to compare two systems without confounding), and the **bootstrap** (how to get
an interval when there is no formula) — together with knowing when each is valid.

## Why pair, and what McNemar actually tests

Suppose you evaluate two detectors on a set of samples and detector B scores higher.
Is B better, or did B happen to see easier samples? If the two were run on
*different* samples you cannot tell — sample difficulty is confounded with the
system. The fix is a **paired design**: run both on the *same* seeded samples. Now
each sample contributes a pair of outcomes, and the difficulty is shared.

Once paired, the right test is **McNemar's**, and its key insight is that only the
**discordant** pairs matter — the samples where exactly one system was right.
Samples where both agree (both right or both wrong) tell you nothing about *which*
system is better; they only tell you the task's overall difficulty. McNemar throws
them away and asks: among the disagreements, are they lopsided enough to be
surprising under "the two systems are equally good?" That null makes each discordant
pair a fair coin, so the exact test is just a two-sided binomial on the discordant
counts.

Two traps this guards against:
- **Running an unpaired two-proportion test on paired data.** It ignores the pairing,
  wastes the variance reduction, and can give the wrong answer.
- **Reading significance as effect size.** A significant McNemar result says the
  systems differ; it says nothing about *how much*. Report it alongside the accuracy
  intervals. And significance needs enough discordant evidence: five one-directional
  disagreements give p = 0.0625 (not significant); it takes six (p = 0.03125).

## The bootstrap, and the assumptions it quietly makes

The bootstrap estimates the sampling distribution of a statistic by resampling the
data *with replacement* many times and looking at how the statistic varies. It is
wonderful because it needs no formula — it works for medians, ratios, AUCs, anything.
But it is not magic, and its assumptions are easy to forget:

- **The sample must represent the population.** The bootstrap resamples *your data*;
  if your data is biased or too small, the interval is confidently wrong. It
  estimates sampling variability, not sampling *bias*.
- **Observations should be (roughly) independent.** Plain bootstrap on correlated or
  clustered data understates uncertainty; block/cluster bootstraps exist for that.
- **It struggles at the extremes.** For a statistic like "the maximum," or a
  proportion at 0 or 1, the naive percentile bootstrap can be degenerate — which is
  exactly why FAULTLINE uses **Wilson** for proportions and treats the bootstrap as a
  cross-check, not the primary interval, in that case. (In this repo, all-ones data
  bootstraps to the point [1, 1] — correct, but a reminder the method has edges.)
- **More resamples reduce Monte-Carlo noise, not statistical uncertainty.** 3000
  iterations make the *interval* stable; they do not shrink the *interval* — only
  more real data does that.

The honest framing: the bootstrap turns "I have data but no formula" into an
interval, provided the sample is representative and the observations independent. When
a good closed form exists (a proportion → Wilson), prefer it, and use the bootstrap to
confirm the two agree.

## The through-line for FAULTLINE

Every rate in this project (a recall, an accuracy) is a proportion from a finite,
seeded sample, so it gets a Wilson interval; every system-vs-system claim runs on
paired seeds and gets McNemar. That is what lets later missions say "detection
accuracy is X (95% CI …)" and "recovery policy A beats B (McNemar p …)" without
hand-waving — the uncertainty and the pairing are built into the ruler.

## References worth reading next

- McNemar, *Note on the sampling error of the difference between correlated
  proportions* (1947); Edwards' continuity correction; the exact-binomial variant.
- Efron & Tibshirani, *An Introduction to the Bootstrap* (1993) — assumptions and
  failure modes.
- Wilson (1927) score interval; Brown, Cai & DasGupta, *Interval Estimation for a
  Binomial Proportion* (2001) — why Wilson beats the normal approximation.
