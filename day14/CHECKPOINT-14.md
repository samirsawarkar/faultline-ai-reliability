# CHECKPOINT-14 — intervals + paired statistical design

**Mission.** Make every comparison honest with paired seeds and uncertainty
estimates.

**Fail condition.** You cannot explain or verify the interval and paired test. —
**Not triggered.**

## What was built

A dependency-free, verified statistics layer:

- **Wilson score interval** and **seeded bootstrap CI** (`intervals.py`).
- **McNemar's paired test** — continuity-corrected chi-square + exact binomial —
  with a paired-table builder (`paired.py`).
- **Independent verification** of every utility (`verify.py`).
- **Interpretation** in code and a committed guide (`interpret.py`, `INTERPRETATION.md`).

25 tests gate it; four evidence artifacts prove it.

## Verified — not self-referentially (`stats_verification.json`, all pass)

| utility | independent check |
|---|---|
| Wilson | bounds satisfy the score equation `(p̂−p*)² = z²·p*(1−p*)/n` (max residual < 1e-9) + textbook values (5/10 → [0.237, 0.763], 10/10 → [0.723, 1.0]) |
| `norm_ppf` | z₀.₉₇₅ = 1.959964, z₀.₉₅ = 1.644854, z₀.₉₉₅ = 2.575829 |
| `chi2_sf(df=1)` | critical values (3.841 → 0.05, 6.635 → 0.01) + cross-check `χ²₁ = Z²` |
| McNemar exact | `(1,5)` → 2·(C(6,0)+C(6,1))/2⁶ = 0.21875 exactly; `(10,2)` → χ² = 49/12 |
| bootstrap | deterministic; degenerate → point; agrees with Wilson on a proportion |

## Paired comparison (`paired_comparison.json`)

Schema-only (System A) vs schema+invariant (System B) on **80 identical seeded F3
samples**:

| system | accuracy | 95% Wilson CI |
|---|---|---|
| A — schema only | 0.50 | [0.393, 0.607] |
| B — schema+invariant | 0.75 | [0.645, 0.832] |

McNemar: b = 0, c = 20 discordant, exact **p ≈ 1.9e-6** — B strictly dominates,
catching the `nonmultiple` corruption the schema misses; neither catches coherent
`drift_value`. A real, significant, honestly-bounded improvement.

## Edge cases (`edge_cases.json`)

Wilson n=0 → [0, 1]; p=0 → lower 0; p=1 → upper 1; tiny rate 1/1000. Bootstrap
degenerate (all-ones → [1, 1]) and n=1. McNemar: no discordant → p=1; symmetric
(6,6) → not significant; one-sided small → exact; large → chi-square.

## Mastery gate — all five

- **Explain** — `LEARN-paired-bootstrap.md` (pairing, McNemar, bootstrap
  assumptions) + `INTERPRETATION.md` (overlap ≠ distinguishable; significant ≠ large).
- **Build** — `faultline_stats/`: Wilson, bootstrap, McNemar, math primitives.
- **Debug** — `edge_cases.json`: behaviour at every boundary.
- **Measure** — `paired_comparison.json`: CIs + McNemar on a real comparison.
- **Defend** — `stats_verification.json` (independent checks) + `DECISIONS.md`
  (D14-001…D14-007).
