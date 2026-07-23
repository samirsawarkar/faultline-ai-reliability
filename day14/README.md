# FAULTLINE — Day 14: intervals + paired statistical design

Make every comparison honest: report a rate with an **uncertainty interval**, and
compare two systems on **paired seeds** with a test that only counts the evidence
that matters. Ships verified Wilson + bootstrap intervals, McNemar's paired test,
and a plain-English interpretation guide.

> **Fail condition:** you cannot explain or verify the interval and paired test.
> **Status: not triggered** — `verify.py` checks each utility against something
> independent (the Wilson bounds are plugged back into the score *equation* they
> solve; `norm_ppf`/`chi2_sf`/McNemar-exact against published values), and
> `LEARN-paired-bootstrap.md` + `INTERPRETATION.md` explain both. See
> [CHECKPOINT-14.md](CHECKPOINT-14.md).

## The one idea

Days 8–13 produced rates and comparisons. A rate without an interval and a
comparison without a paired test are not defensible — a higher number can be noise,
and an unpaired comparison confounds "which system is better" with "which samples
were easier." This day builds the (dependency-free, verified) statistics that make
every FAULTLINE number carry its uncertainty.

## What's here

```
faultline_stats/
  mathfns.py    norm_cdf/ppf, chi2_sf (df=1), binomial — stdlib only
  intervals.py  wilson_interval (closed form), bootstrap_ci (seeded resampling)
  paired.py     paired_table, mcnemar_test (chi-square + exact binomial)
  verify.py     independent verification of every utility
  interpret.py  plain-English interpretation of an interval and a McNemar result
  experiment.py grounded paired comparison: schema-only vs schema+invariant
scripts/ make_evidence.py
tests/   test_intervals.py test_paired_mcnemar.py test_verify_experiment.py (25)
evidence/
  stats_verification.json edge_cases.json paired_comparison.json INTERPRETATION.md
CHECKPOINT-14.md · LEARN-paired-bootstrap.md · DECISIONS.md · REFLECTION.md
```

## Quickstart

```
python -m pytest tests/ -q       # 25 tests
python scripts/make_evidence.py  # regenerate verification, edge cases, comparison
```

Standard library only. Consumes Days 8–10 in the grounded experiment.

## Build A — verified intervals

- **Wilson score interval** for a proportion (the project default: correct at the
  extremes and small n, inside [0, 1] always).
- **Bootstrap CI** for any statistic via seeded, deterministic resampling.

Verification is *independent*, not self-referential: the Wilson bounds are plugged
back into the score equation `(p̂ − p*)² = z²·p*(1−p*)/n` (max residual < 1e-9);
`norm_ppf` matches known quantiles (z₀.₉₇₅ = 1.959964, …); `chi2_sf(df=1)` matches
critical values and cross-checks `χ²₁ = Z²`; the bootstrap agrees with Wilson on a
proportion. All checks pass in `stats_verification.json`.

## Build B — paired design + McNemar

Two systems on **identical seeded samples** → paired outcomes. `mcnemar_test`
counts only the discordant pairs, reporting the continuity-corrected chi-square p
and, for small discordant counts, the **exact binomial** p (and which to trust).

**Grounded result** (`paired_comparison.json`): schema-only vs schema+invariant on
80 identical F3 samples. System A (schema) accuracy **0.50** (CI [0.393, 0.607]);
System B (schema+invariant) **0.75** (CI [0.645, 0.832]); McNemar **p ≈ 1.9e-6** —
B strictly dominates (b=0, c=20), catching the `nonmultiple` corruption the schema
misses. Neither catches coherent `drift_value`.

## Attack — known cases + edge samples

`edge_cases.json`: Wilson at n=0 → [0, 1], p=0 → lower 0, p=1 → upper 1, tiny rate
1/1000; bootstrap degenerate (all-ones → point) and n=1; McNemar with no discordant
pairs (p=1), symmetric counts (not significant), one-sided small (exact), and large
(chi-square). Each is exercised in the tests too.

## Mastery map

- **Explain** → [LEARN-paired-bootstrap.md](LEARN-paired-bootstrap.md) +
  `evidence/INTERPRETATION.md`
- **Build** → `faultline_stats/` (intervals, paired, mathfns)
- **Debug** → `evidence/edge_cases.json` (behaviour at the boundaries)
- **Measure** → `evidence/paired_comparison.json` (CIs + McNemar on a real comparison)
- **Defend** → `evidence/stats_verification.json`, [DECISIONS.md](DECISIONS.md),
  [CHECKPOINT-14.md](CHECKPOINT-14.md)
