# Literature map

Not a paper-by-paper summary. Organise by the research problem.

## Problem being studied
Characterizing the multi-trial reliability ($pass^k$) of LLM tool-use agents on multi-hop knowledge retrieval tasks, and testing whether repeated execution outcomes follow independent Bernoulli compounding ($pass^k = (pass@1)^k$) or exhibit regime-dependent task-level failure concentration under greedy decoding at temperature 0.

## Approaches (families, not papers)
| Approach | Key papers (bib keys) | Core assumption | Datasets | Metrics |
|---|---|---|---|---|
| Functional Code & Unit Generation | chen2021codex, jiang2026beyondpassk, dalal2025inconsistency | Independent stochastic sampling produces completions; problems solved independently; $pass@k$ measures any-success. | HumanEval, MBPP, synthetic multi-rollout coding tasks | $pass@k$, reliability@k |
| Conversational & Tool-Agent Consistency | yao2024taubench, bellibatlu2026samepatient, dragoi2025breadthdepth | Multi-turn interaction episodes are repeatable; success requires all $k$ episodes to pass ($pass^k$ joint reliability). | $\tau$-bench (Airline, Retail), synthetic clinical workflows | $pass^k$ (all-$k$-pass), trajectory sequence divergence |
| Inference Nondeterminism & Serving Backends | he2025defeating, pape2026silent, reddy2026sameweights, fu2026beyond, yuan2025nondeterminism, gale2026tempzero | Temperature 0 does NOT guarantee deterministic execution; GPU kernel reductions, batching, and serving backends alter greedy outputs. | GSM8K, HumanEval, AlpacaEval, synthetic logit probe prompts | Exact token match rate, logit divergence, benchmark score drift |
| Statistical Foundations & Metric Calibration | miller2024errorbars, zheng2023judging, rao2026agreement, wilson1927, mcnemar1947, rogan1978, fleiss1971, shrout1979, efron1979, holm1979, tarone1979 | Benchmark instances are sampling units subject to item variance; repeated trials are clustered; chance agreement must be corrected. | MT-Bench, Chatbot Arena, standard eval sets | Wilson score CI, exact McNemar $p$-value, ICC(1,1), Fleiss' $\kappa$, percentile bootstrap CI, Rogan-Gladen |
 
 ## Reported results by approach
 | Approach | Result | Conditions | Source (bib key) | Evidence ID |
 |---|---|---|---|---|
 | Functional Code & Unit Generation | $pass@k$ unbiased estimator computes exact any-pass probability from $n$ samples without combinatorial evaluation. | $n \ge k$, random sampling with temperature $> 0$ | chen2021codex | E001 |
 | Conversational & Tool-Agent Consistency | Multi-turn agent reliability over $k$ episodes decays markedly with repetition depth $k$. | Tool-use agents interacting in simulated multi-turn domains ($k \le 8$) | yao2024taubench | E002 |
| Inference Nondeterminism | GPU floating-point non-associativity causes non-zero output token divergence even with greedy decoding ($T=0$) (e.g. 80 unique completions per 1000 greedy runs on Qwen3-235B). | Parallel batching on GPUs across modern serving backends (vLLM, TGI) | he2025defeating | E004 |
| Inference Nondeterminism | Switching inference engines at $T=0$ shifts benchmark accuracies by up to $16.6$ percentage points on identical model weights. | Fixed open weights across serving engines (vLLM, SGLang, llama.cpp) on standard benchmarks | pape2026silent | E005 |
| Statistical Foundations | Language model evaluations are scientific experiments; benchmark gains frequently lack statistical power when evaluated with proper error bars and paired tests. | Standard benchmark leaderboards without error bars | miller2024errorbars | E008 |
 | Statistical Foundations | Wilson score intervals avoid zero-width degeneracy at boundary probabilities ($p=0$ and $p=1$). | Binomial proportion estimation with small sample sizes | wilson1927 | E013 |
 | Statistical Foundations | Exact McNemar test isolates paired treatment differences strictly from discordant pairs $(b, c)$. | Paired binary evaluation on matched benchmark instances | mcnemar1947 | E014 |
 | Statistical Foundations | Chance-corrected agreement (Cohen's $\kappa$) and Rogan–Gladen prevalence estimation correct for class imbalance and imperfect test sensitivity/specificity. | Evaluation of imperfect evaluators under imbalanced class prevalence | rao2026agreement, rogan1978 | E012, E015 |
 
 ## Where findings disagree
 | Topic | Position A (source) | Position B (source) | Plausible reason for the difference | Claim ID |
 |---|---|---|---|---|
 | Greedy decoding determinism ($T=0$) | Temperature 0 guarantees deterministic, reproducible model completions (common assumption in benchmarks). | Temperature 0 produces non-deterministic token trajectories and score divergence across runs (he2025defeating, reddy2026sameweights, pape2026silent). | Parallel GPU batching, thread scheduling, and floating-point summation non-associativity in attention reduction kernels flip near-tied logits. | C003 |
 | Metric operationalization ($pass@k$ vs $pass^k$) | Any-of-$k$ success ($pass@k$) accurately measures LLM generation utility (chen2021codex). | Any-of-$k$ hides failure concentration and overestimates operational reliability; all-$k$ joint reliability ($pass^k$) is essential for agents (yao2024taubench, jiang2026beyondpassk). | Single-turn code generation benefits from multiple attempts with an external test filter, whereas autonomous agents execute unmonitored action chains where every trial must succeed. | C001, C002, C009 |
 | LLM Judge reliability evaluation | Percent raw agreement with humans is sufficient to validate an automated LLM judge (early LLM-as-a-judge pipelines). | Raw agreement is severely inflated by label prevalence imbalance; chance-corrected metrics ($\kappa$, ICC) show poor reliability (rao2026agreement, zheng2023judging). | Asymmetric class distributions (e.g. 90% correct answers) yield high base agreement even with random majority guessing. | C011, C012 |

## Recurring limitations
1. **Unstated Inference Backends & Sampling Confounders**: Benchmark studies rarely disclose the underlying serving framework (vLLM, TensorRT-LLM, cloud gateway), kernel quantization, or concurrency levels, which directly induce run-to-run divergence at $T=0$.
2. **Conflation of Instance Variance and Trial Variance**: Papers frequently pool all $N \times k$ observations as independent samples rather than accounting for intra-instance correlation via hierarchical models, ANOVA/ICC, or cluster-level bootstrapping.
3. **Overreliance on Point Estimates**: Widespread publication of benchmark rank changes based on point deltas under 2–3 pp without reporting Wilson score intervals or paired McNemar tests.

## What has not been tested
1. **Empirical testing of the independence assumption $pass^k = (pass@1)^k$ across model capability rungs on fixed multi-hop grounded retrieval tasks**: Previous work either assumes independence or measures empirical $pass^k$ on single models without testing for systematic failure concentration across high-accuracy vs low-accuracy regimes.
2. **The behavior of $pass^k$ under strict deterministic dual-condition oracles (exact answer + explicit cited source provenance)**: Prior agent benchmarks primarily grade on end-state database mutations or subjective LLM judges rather than deterministic grounded knowledge graph traversal.

## Source register pointer
Every bib key above appears in `research/evidence/source_register.md` with an explicit read-status (`full-text` or `abstract`).
