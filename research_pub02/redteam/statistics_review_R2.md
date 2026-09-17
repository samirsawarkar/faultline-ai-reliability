# Statistical review (recomputed from `research_pub02/experiments/processed/per_instance_R2.csv`)

Baseline: `arm_A`; alpha = 0.05; Holm correction over 1 comparisons; bootstrap 10k; permutation 20k; seed 0

| System | n instances | mean score |
|---|---|---|
| arm_A | 300 | 0.1700 |
| arm_B | 300 | 0.0400 |

Compare every number in the draft against this table — a headline figure that does not match is a HIGH finding (wrong number or wrong file).

| System | n paired |  mean Δ | 95% CI | p (sign-flip) | p (signed-rank) | p Holm | d_z | ties | unpaired dropped |
|---|---|---|---|---|---|---|---|---|---|
| arm_B | 300 | -0.1300 | [-0.1700, -0.0900] | 0.0001 | 0.0001 | 0.0001 | -0.36 | 257 | 0 |

Notes: sign-flip permutation on the paired mean is exact under exchangeability and needs no normality assumption. d_z is paired Cohen's d (mean diff / SD of diffs). Do not infer significance from bar-chart gaps.
