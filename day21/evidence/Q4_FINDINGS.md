# Q4 — Availability versus silent fallback degradation

**Answer: yes.** On the same 120 seeds, fallback raised availability by 0.3333 to 1.0, but strict quality among delivered answers changed by -0.25 to 0.75. Only 0.25 of fallback answers met the strict rubric; 0.75 were bad while the route-level degraded flag stayed false.

## Availability and quality (same seeded requests)

| configuration | availability | oracle correctness / answered | strict quality / answered | strict-quality service rate |
|---|---:|---:|---:|---:|
| primary only | 0.6667 | 1.0 | 1.0 | 0.6667 |
| fallback enabled | 1.0 | 0.9167 | 0.75 | 0.75 |

- Availability change: **+0.3333**.
- Strict quality among answered change: **-0.25**.
- Strict-quality service-rate change: **+0.0833**.
- Fallback slice: 10/40 strictly acceptable; 30/40 silently degraded.

Conditional answer quality fell, while strict-quality service rate rose by 0.0833: fallback delivered some useful answers as well as bad ones. Both denominators are reported.

## Silent-degradation attack

The attack held availability at **1.0** while delivering **30** bad fallback answers. The availability-only monitor and the route-level degraded-flag monitor both raised zero alerts.

The quality detector's fallback-only confusion matrix is `{'tp': 20, 'fp': 0, 'fn': 10, 'tn': 10}`: recall **0.6667** (95% Wilson CI [0.4878, 0.8077]), precision **1.0** (95% Wilson CI [0.8389, 1.0]). Every false negative is committed in `degradation_detector.json`.

## Judge caveats (load-bearing)

- The Day-16 judge has kappa 0.5 versus a 0.8 human inter-rater ceiling.
- It is not validated for standalone use and is forbidden from core success scoring.
- It is used pointwise only, on fallback quality; strict human-rubric labels remain ground truth.
- All detector false negatives are the known borderline_tokens failure slice.

The detector therefore supplies an alert, not truth. Day-1 oracle results and the strict human rubric remain separate; the judge never contributes to core success.

## Operating conclusion

Do not declare fallback healthy from availability alone. Budget and alert on fallback strict quality, retain provenance, and route the judge's known failure slice to deterministic checks or human audit.

Fail-condition guard passed: **True** (availability and fallback quality are reported together).
