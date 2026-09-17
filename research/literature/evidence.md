# Evidence table

CLAIM → SOURCE → EVIDENCE → INTERPRETATION. Direction is relative to the claim ID.

| ID | Claim | Source (bib key or data file) | Finding (numbers, conditions) | Direction |
|---|---|---|---|---|
| E001 | C001 | chen2021codex | Evaluated HumanEval with $n \in [1, 100]$ completions; pass@k unbiased estimator avoids evaluating all $n \choose k$ subsets. | supports |
| E002 | C002 | yao2024taubench | Evaluated tool-calling agents across Airline and Retail domains over repeated interaction episodes (up to k=8); shows pass^k decays sharply with repetition depth k. | supports |
| E003 | C003 | he2025defeating | Documents that prevailing benchmarks assume greedy decoding yields identical token generation across multiple invocations. | supports |
| E004 | C004 | he2025defeating | Demonstrates floating-point non-associativity across GPU batching; in 1000 greedy temperature-0 completions of Qwen3-235B, observes 80 unique outputs with first divergence at token 103. | supports |
| E005 | C005 | pape2026silent | Benchmarks open models across 5 serving engines (incl. vLLM, SGLang, llama.cpp) at temperature 0; finds backend choice shifts downstream benchmark scores by up to 16.6 percentage points. | supports |
| E006 | C006 | reddy2026sameweights | Evaluates 7 open-weight models across commercial API providers at temperature 0; observes 0% exact agreement across providers on creative tasks and 67%–100% exact-match-across-3-reps within provider cells. | supports |
| E007 | C007 | fu2026beyond | Tracks logit variations on GPUs from floating-point rounding in fused attention; shows that small numerical shifts invert greedy argmax selection when candidate tokens have close probabilities (effect largest for p in 0.1–0.9). | supports |
| E008 | C008 | miller2024errorbars | Argues that language model evaluations are scientific experiments requiring clustered standard errors and paired significance tests rather than bare point estimates. | supports |
| E009 | C009 | jiang2026beyondpassk | Evaluates a synthetic agent benchmark; shows reported pass@k inflated by 0.85–0.97 in absolute terms (0.96–0.98 reported vs 0.00–0.12 corrected) when internal assertions are conflated with independent rollouts. | supports |
| E010 | C010 | bellibatlu2026samepatient | Evaluates clinical decision agents over repeated runs; finds that across 43 ordering groups that emit different order sets, 22 report the same failing benchmark verdict for materially different behavior. | supports |
| E011 | C011 | zheng2023judging | GPT-4 judge exhibits a 5% to 7% first-position bias and a 65% preference for longer answers on MT-Bench. | supports |
| E012 | C012 | rao2026agreement | Demonstrates that protocol choice alone moves reported judge accuracy from 0.551 to 0.899 and can carry kappa across zero under label prevalence shifts. | supports |
| E013 | C013 | wilson1927 | Derives the score interval for a binomial proportion based on the score test inversion. | supports |
| E014 | C014 | mcnemar1947 | Introduces the paired test on correlated proportions conditioned on discordant pairs (b, c). | supports |
| E015 | C015 | rogan1978 | Formula $p_{true} = (p_{obs} + Sp - 1) / (Se + Sp - 1)$ corrects prevalence given sensitivity $Se$ and specificity $Sp$. | supports |
| E016 | C016 | shrout1979 | Formulates one-way random effects intraclass correlation ICC(1,1) for assessing agreement among repeated measurements. | supports |
| E017 | C017 | efron1979 | Demonstrates asymptotic convergence of percentile bootstrap intervals for non-linear estimators. | supports |
| E018 | C018 | holm1979 | Shows sequential rejective threshold $\alpha / (m - i + 1)$ maintains strong control of FWER at $\alpha$. | supports |
| E019 | C003 | reddy2026sameweights | Contradicts the common belief in temperature-0 determinism by observing extensive inter-provider divergence. | contradicts |
| E020 | C003 | he2025defeating | Contradicts temperature-0 determinism by identifying floating-point non-associativity in parallel GPU reductions. | contradicts |
