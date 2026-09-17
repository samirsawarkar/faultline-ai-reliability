# P7 — Provider Variance: one model, two gateways

## What was measured
google/gemini-3.7-flash via AI Credits vs the same model via Antigravity (agy), 150 matched standard-pool scenarios each, oracle-graded, MEC v1.3, step cap 24.

## Result table
| Endpoint | Model String | n | Passed | Pass Rate | Wilson 95% CI | Latency p50 (s) | Latency p95 (s) | Spend (USD) |
|---|---|---|---|---|---|---|---|---|
| aicredits | google/gemini-3.7-flash | 150 | 144 | 0.96 | [0.9155, 0.9815] | 16.0911 | 29.4546 | $0.285181 |
| agy | gemini-3.7-flash | 150 | 134 | 0.8933 | [0.8338, 0.9333] | 18.6402 | 67.8926 | $0.156729 |

## H6
criterion_disjoint_ci: NOT MET: Wilson intervals overlap on [0.9155, 0.9333]
paired_mcnemar: SIGNIFICANT: exact p=0.0308837890625, 14 aicredits-only vs 4 agy-only discordant pairs, favouring aicredits
power_note: Observed gap 6.67pp is below the MEC 10pp declared power. Reported as a detected difference with that caveat; never as no difference.

## Contingency and McNemar
The 2x2 contingency table across the 150 shared scenarios:
- Both passed: 130
- aicredits only passed: 14
- agy only passed: 4
- Neither passed: 2

Exact McNemar test p-value: exact p=0.0308837890625 (14 vs 4 discordant pairs, significant at alpha = 0.05).

## Latency finding
Latency ratios from results.json (ratio_agy_over_aicredits):
- p50 ratio: 1.1584
- p95 ratio: 2.305

The median is close and the tail is where the gateways differ.

## Operational note
The agy sweep exhausted a per-user quota that reset after ~2.5 hours; AI Credits did not.

## Reproduce
`.venv/bin/python projects/p07_variance/finalize.py` rebuilds results.json from trace.db; the live sweep is `run.py --confirm` and spends.

## Limitations
Single model, two gateways, n=150, one day, one region, agy served without a provider prefix in its model string (normalised for the comparison).
