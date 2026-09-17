# Statistical review (recomputed from `research_pub02/experiments/processed/per_instance_R6.csv`)

Baseline: `arm_A`; alpha = 0.05; Holm correction over 1 comparisons; bootstrap 10k; permutation 20k; seed 0

| System | n instances | mean score |
|---|---|---|
| arm_A | 300 | 0.4700 |
| arm_B | 300 | 0.1500 |

Compare every number in the draft against this table — a headline figure that does not match is a HIGH finding (wrong number or wrong file).

| System | n paired |  mean Δ | 95% CI | p (sign-flip) | p (signed-rank) | p Holm | d_z | ties | unpaired dropped |
|---|---|---|---|---|---|---|---|---|---|
| arm_B | 300 | -0.3200 | [-0.3800, -0.2600] | 0.0001 | 0.0001 | 0.0001 | -0.59 | 182 | 0 |

Notes: sign-flip permutation on the paired mean is exact under exchangeability and needs no normality assumption. d_z is paired Cohen's d (mean diff / SD of diffs). Do not infer significance from bar-chart gaps.
