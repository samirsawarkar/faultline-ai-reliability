# Derived experimental results

Source: `experiments/raw/analysis.json`, `experiments/raw/replay_results.json`, and `redteam/statistics_review.md`.

## 1. Paradigm-pooled results

| Paradigm | Arm | n | n_valid | Success | ASR (valid) | 95% Wilson CI | Replay Block Rate (on success) | Replay False Block Rate |
|---|---|---|---|---|---|---|---|---|
| Template-1 | Arm A | 288 | 272 | 67 | 0.2463 | [0.1989, 0.3008] | N/A | N/A |
| Template-1 | Arm B | 288 | 273 | 5 | 0.0183 | [0.0078, 0.0421] | 0.9262 | 0.1087 |
| Template-2 | Arm A | 648 | 625 | 151 | 0.2416 | [0.2097, 0.2767] | N/A | N/A |
| Template-2 | Arm B | 648 | 613 | 67 | 0.1093 | [0.0870, 0.1365] | 0.8189 | 0.1953 |
| Template-3 | Arm A | 864 | 815 | 301 | 0.3693 | [0.3369, 0.4030] | N/A | N/A |
| Template-3 | Arm B | 864 | 789 | 52 | 0.0659 | [0.0506, 0.0854] | 0.8755 | 0.3199 |

## 2. Retry mechanics (pooled across 1,800 instances)

| Metric | Count | Percentage of total (n=1800) | Notes |
|---|---|---|---|
| Step 1 allowed | 957 | 53.2% | Allowed on initial invocation |
| Step 1 blocked | 613 | 34.1% | Intercepted by ProvenancePolicy |
| Step 1 no call (prose/refusal) | 230 | 12.8% | Gated: no retry injected, passed verbatim to judge |
| Retried: allowed on Step 2 | 479 | 26.6% | Model corrected tool call or recovered |
| Retried: blocked again | 134 | 7.4% | Second tool call also violated policy (92 call, 42 no-call) |
| Residual leak: Success on Step 2 | 22 | 1.2% | Exploits that evaded contract on retry |

## 3. Statistical comparisons (pooled McNemar and permutation test)

### Paired McNemar exact / continuity-corrected test

| Total pairs | Arm A only (b) | Arm B only (c) | Discordant (b+c) | Both success | Both fail | Chi2 stat | p-value (continuity-corrected) | p-value (exact) | Significant (alpha=0.05) |
|---|---|---|---|---|---|---|---|---|---|
| 1800 | 421 | 26 | 447 | 98 | 1255 | 347.2841 | 1.65e-77 | 5.61e-93 | True |

### Stats check: Paired sign-flip permutation and effect size

| System | n paired | Mean Δ | 95% CI | p (sign-flip) | p (signed-rank) | p (Holm) | Cohen's d_z |
|---|---|---|---|---|---|---|---|
| arm_B | 1800 | -0.2194 | [-0.2400, -0.1983] | 0.0001 | 0.0001 | 0.0001 | -0.49 |
