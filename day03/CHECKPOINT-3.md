# Checkpoint 3 — the zero point

**Date:** 2026-07-14 · **Spec:** 3.0.0 · **Subject:** Day-2 deterministic agent

This checkpoint records the first FAULTLINE baseline: task success, steps, cost,
and latency across three difficulty tiers, with confidence intervals. Every
number below regenerates from the committed config (`BaselineConfig`) and seeds —
that reproducibility is the mission's pass/fail line.

## Configuration (the whole reproducibility surface)

| field | value |
| --- | --- |
| master_seed | 20260714 |
| n_per_tier | 500 (1500 runs total) |
| step_cap | 12 |
| tiers | easy = {1,2,3} hops · medium = {4,5,6} · hard = {6,7,8} |
| cost model | 4 chars/token, 200-char base prompt, $0.50 / 1k tokens |
| latency model | tool base {search 5, lookup 3, calc 1} ms + 0.05 ms/token |
| Wilson z | 1.96 (95%) |

`content_hash = adc9630595cfa8a992e8f5807de026022497c1ae7c7b75d2066fdda1a2f16b31`

## Results

| tier | n | success | rate | Wilson 95% CI | steps (mean) | cost $ (mean) | latency ms (mean) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| easy | 500 | 500 | 1.000 | [0.992, 1.000] | 5.0 | 0.2424 | 38.6 |
| medium | 500 | 329 | 0.658 | [0.615, 0.698] | 10.7 | 0.5434 | 92.6 |
| hard | 500 | 0 | 0.000 | [0.000, 0.008] | 12.0 | 0.6288 | 108.4 |

Figure: [`evidence/success_vs_hops.svg`](evidence/success_vs_hops.svg) — success
is a clean step: 1.0 for ≤ 5 hops, 0.0 for ≥ 6, with the drop at the budget cliff
(`2·hops + 1 > step_cap`).

## What the zero point says

- The deterministic subject has a **hard capability cliff at the step budget**:
  it solves everything it can afford and nothing it cannot. `medium` straddles
  the cliff, which is why its rate is intermediate and its Wilson interval is
  non-degenerate.
- **Cost and latency rise monotonically with hops** even where success is flat —
  a failed `hard` task still spends the full budget (12 steps, ~0.63 $, ~108 ms).
  Spend is *not* a proxy for success.

## Attack result (mislabeled inputs)

Filing 100 `hard` tasks under the `easy` label drops the naive `easy` rate to
**0.500**; recomputing each task's actual tier from its hop count flags all 100
and recovers the true `easy` rate of **1.000**, matching the clean baseline.
Malformed tasks all degrade to structured `INVALID` — no crash.
Evidence: [`evidence/mislabel_attack.json`](evidence/mislabel_attack.json).

## Reproduce it

```
make -C .. day03-baseline     # or: python day03/scripts/build_baseline.py
python day03/scripts/attack_mislabeled.py
python -m pytest day03/tests/ -q
```

`tests/test_reproducibility.py::test_committed_baseline_matches_fresh_build`
rebuilds from config and asserts the committed `content_hash` — the fail
condition, mechanized.
