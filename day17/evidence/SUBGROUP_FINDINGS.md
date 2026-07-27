# Day 17 — Subgroup findings (where aggregates hide failure)

Every rate is gated: subgroups below the minimum sample size (5) are marked non-reportable, and headline tests are Holm-corrected for multiple comparisons. A subgroup 'contradicts' the headline only when its 95% interval EXCLUDES the headline value.

## Known limitations (read first)

- Small evaluation set (n=44): most fault x severity cells are below the minimum sample size (5) and are reported as insufficient, not as conclusions.
- The deterministic-vs-semantic ordering REVERSES within some severity slices (see deterministic_vs_semantic_reversal): the deterministic group is dragged down by F2 latency below its budget, so at those severities it scores below the semantic group. This is a confounded, underpowered reversal — acknowledged, not ignored.
- Detection subgroups (fault, severity) and hop-count subgroups come from DIFFERENT evaluation populations (Day 13 dataset vs Day 7 hop sweep); they are not pooled, and cross-axis claims are not made.
- The 'naive p^n overpredicts' headline does not hold at low hop counts (hops < first_divergence_hop); those hops are surfaced as contradictions.
- All results are for a single dataset version; wider intervals or more seeds would sharpen the underpowered subgroups.

## Detection headline: overall accuracy = **0.772727** (n=44)

### By fault

| subgroup | n | rate | 95% CI | reportable | CI excludes headline |
|---|---|---|---|---|---|
| fault=F1 | 9 | 0.7778 | [0.4526, 0.9368] | True | False |
| fault=F2 | 9 | 0.5556 | [0.2667, 0.8112] | True | False |
| fault=F3 | 7 | 0.7143 | [0.3589, 0.9178] | True | False |
| fault=F4 | 5 | 1.0 | [0.5655, 1.0] | True | False |
| fault=F5 | 7 | 0.7143 | [0.3589, 0.9178] | True | False |
| fault=F6 | 7 | 1.0 | [0.6457, 1.0] | True | False |

### By severity

| subgroup | n | rate | 95% CI | reportable | CI excludes headline |
|---|---|---|---|---|---|
| severity=0 | 18 | 1.0 | [0.8241, 1.0] | True | True |
| severity=1 | 4 | 0.0 | [0.0, 0.4899] | False | True |
| severity=2 | 8 | 0.75 | [0.4093, 0.9285] | True | False |
| severity=3 | 8 | 0.5 | [0.2152, 0.7848] | True | False |
| severity=5 | 6 | 1.0 | [0.6097, 1.0] | True | False |

## Deterministic vs semantic — an ordering REVERSAL

Aggregate: deterministic 0.809524 (n=21) vs semantic 0.73913 (n=23) → deterministic ahead. But within slices:

| severity | deterministic | semantic | n(det) | n(sem) | reverses aggregate |
|---|---|---|---|---|---|
| 0 | 1.0 | 1.0 | 9 | 9 | False |
| 1 | 0.0 | 0.0 | 2 | 2 | False |
| 2 | 1.0 | 0.5 | 4 | 4 | False |
| 3 | 0.0 | 0.666667 | 2 | 6 | True |
| 5 | 1.0 | 1.0 | 4 | 2 | False |

The severity-3 slice reverses the headline: the deterministic group (only F2 latency there, below its budget) scores 0.0 vs the semantic group's 0.667 — a confounded, underpowered reversal, surfaced not hidden.

## Hop count (Day 7 reliability curve)

Headline: *naive p^n overpredicts end-to-end reliability*; first divergence at hop **3**. Hops that do NOT support it: [1, 2] (naive lies inside the measured CI there).

## Contradictions (all surfaced, none ignored)

- detected: `['detect:fault=F1,severity=1', 'detect:fault=F2,severity=1', 'detect:fault=F2,severity=3', 'detect:severity=0', 'detect:severity=1', 'hop:1', 'hop:2', 'reversal:severity=3']`
- significant after Holm correction: `[]` (none — the spread is real but under-powered at this n)
- measurement gate passed: **True**

