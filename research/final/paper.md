# Multi-Trial Reliability and Failure Concentration in Multi-Hop AI Agents
*Grounding Collapse, Failure Taxonomy, and Evaluator Calibration*

**Samir Sawarkar**  
*FAULTLINE AI Reliability Engineering*  

---

### Abstract
When deploying autonomous language model agents on critical multi-step tasks, system architects require joint operational reliability across repeated runs [@yao2024taubench; @jiang2026beyondpassk]. In evaluation practice, a common working assumption is that the multi-trial success rate $\text{pass}^k$—the probability that an agent completes all $k$ independent repetitions of a task—can be estimated by extrapolating single-trial benchmark accuracy via the naive independent Bernoulli formula $\text{pass}^k = (\text{pass@1})^k$. While $\tau$-bench reports $\text{pass}^k$, it does not benchmark the empirical gap to $(\text{pass@1})^k$; in this work, we test this gap directly on a controlled, contamination-resistant 5-hop knowledge retrieval benchmark with 150 held-out hard scenarios executed over $k=3$ repeated trials graded by a deterministic dual-condition oracle without subjective model judges in the loop. We report the pre-registered *as-run* analysis ($n=150$) alongside an *infra-excluded* sensitivity analysis ($n=117$) that purges external cloud gateway dropouts. Our pre-registered working hypotheses H4 (that measured $\text{pass}^3$ strictly exceeds naive $(\text{pass@1})^3$) and H5 (that positive deviation from naive compounding is larger on cheaper model tiers) are both **NOT_TESTABLE_AS_PREREGISTERED** because only 2 of 6 rungs produced valid data [C021] [C022]; on the valid rungs, R4 met the pre-registered per-rung criterion under both as-run and infra-excluded variants while R2 did not. Crucially, across both evaluated commercial model tiers, naive Bernoulli compounding matches empirical observations within 2.5 percentage points at $k=3$ [C011] [C016] [C028], predicting joint reliability within 2.5 percentage points of measured values—well within our pre-registered 10 percentage point minimum effect of interest. For the higher-accuracy tier (R2, $\text{pass@1} = 0.6311$), repeated outcomes are consistent with a homogeneous-binomial null ($\text{pass}^3 = 0.2267$ vs naive $0.2514$, parametric bootstrap goodness-of-fit $p = 0.3794$, Tarone overdispersion $z = -0.655, p = 0.7438$, $\text{ICC}(1,1) = -0.0287$, $C_3 \in [0.7161, 1.0793]$) [C009] [C010] [C011] [C012] [C013] [C066]. For the lower-accuracy tier (R4, $\text{pass@1} = 0.1489$ as-run), an apparent excess of 3-of-3 successes ($\text{pass}^3 = 0.0200$ vs naive $0.0033$, parametric bootstrap $p = 0.0053$) is heavily driven by serving infrastructure dropouts [C014] [C015] [C017] [C026]. Purging dropouts ($n=117$) leaves only a marginal excess ($\text{pass}^3 = 0.0256$ vs naive $0.0070$, exact tail $p = 0.0488$, Tarone $z = 0.764, p = 0.2224$), rendering the concentration ratio $C_3$ unresolved with a 95% bootstrap confidence interval of $[0.0000, 7.5772]$ spanning 1.0 [C016] [C027] [C028] [C066]. While observations at $k=3$ cannot separate across-scenario heterogeneity from within-scenario serial dependence, beta-binomial compounding extrapolation demonstrates that even undetectable intra-scenario correlation ($\text{ICC}_{\text{hi}} = 0.0668$ on R2) yields compounding divergence at larger depths ($C_8 \approx 2.25$, $\text{pass}^8 \approx 0.057$ vs naive $0.025$) [C068]. All runs were conducted at pinned temperature 0.0, where run-to-run variation is driven by serving infrastructure nondeterminism rather than stochastic sampling [@he2025defeating; @reddy2026sameweights; @pape2026silent] [C003] [C004].

---

## 1 Introduction

For LLM tool-use agents on a fixed set of 5-hop grounded-retrieval tasks, does the joint reliability over $k$ repeated executions equal the independence prediction $\text{pass}^k = (\text{pass@1})^k$, and if not, in which direction and by how much? Autonomous language model agents are increasingly integrated into operational pipelines where single-turn success is insufficient [@yao2024taubench; @bellibatlu2026samepatient]. Deployments require execution stability across repeated invocations on the same task instance [@yao2024taubench; @jiang2026beyondpassk]. In standard evaluation, $\text{pass@k}$ was formalized by Chen et al. [@chen2021codex] as an unbiased estimator for whether at least one of $k$ generated code samples succeeds [C001]. In contrast, autonomous agent reliability requires joint consistency: $\text{pass}^k$, defined by Yao et al. [@yao2024taubench] as the probability of successfully completing all $k$ repeated interaction episodes on a task instance [C002].

In engineering practice, a common working assumption is that single-run evaluation scores ($\text{pass@1}$) can be extrapolated to predict multi-execution reliability by assuming repeated runs behave as independent Bernoulli trials: $\text{pass}^k = (\text{pass@1})^k$. This assumption presumes that task difficulty is homogeneous and that repeated executions fail independently. When agents encounter structural obstacles, such as search loops or query syntax errors, failures can concentrate within specific scenario instances. Under across-scenario heterogeneity, tractable tasks pass reliably while intractable tasks fail, causing measured $\text{pass}^k$ to exceed $(\text{pass@1})^k$ via Jensen's inequality. Conversely, if execution paths diverge unpredictably due to serving engine jitter, runs may compound independently [@he2025defeating; @reddy2026sameweights].

Existing agent benchmarks typically publish point estimates of $\text{pass@1}$ without instance-level confidence intervals or formal tests of independence [@miller2024errorbars] [C005] [C008]. Additionally, evaluations often rely on subjective LLM judges that introduce position, verbosity, and self-enhancement biases [@zheng2023judging; @rao2026agreement] [C006] [C011].

We present a controlled empirical test of the independence assumption $\text{pass}^k = (\text{pass@1})^k$ on a synthetic, contamination-resistant 5-hop knowledge graph benchmark. We execute 150 held-out hard Tier-3 scenarios across $k=3$ repetitions under greedy decoding (temperature 0.0) across two commercial model tiers: a fast tier (R2: `z-ai/glm-5.3-flash`) and a frontier tier (R4: `openai/gpt-5.6-luna`). We grade every trial with a deterministic dual-condition oracle requiring exact answer normalization and verified document citation, eliminating model judges from the evaluation loop. We treat the comparison between R2 and R4 strictly as evidence regarding different accuracy regimes under repetition rather than a general capability ranking.

Our contributions are:
1. **Empirical test of the independence assumption:** We provide a formal statistical test of $\text{pass}^k = (\text{pass@1})^k$ on 150 controlled multi-hop retrieval scenarios across two accuracy regimes ($k=3$) [C009] [C010] [C012] [C014] [C015] [C017]. Across both models, the naive independent formula predicts joint reliability within 2.5 percentage points of measured values ($\Delta_3 = -0.0247$ on R2; $\Delta_3 = +0.0187$ on R4 infra-excluded), well below the 10 percentage point minimum effect of interest [C011] [C028].
2. **Characterization of failure clustering and overdispersion:** We show that for R2 ($\text{pass@1} = 0.6311$), repeated execution outcomes are consistent with a homogeneous-binomial null ($C_3 = 0.9017$ [95% CI $0.7161, 1.0793$], parametric bootstrap $p = 0.3794$, Tarone overdispersion $z = -0.655, p = 0.7438$, $\text{ICC}(1,1) = -0.0287$) [C009] [C011] [C012] [C013] [C066]. For R4 ($\text{pass@1} = 0.1489$), an apparent excess of 3-of-3 successes is heavily driven by serving timeouts; purging dropouts leaves only a marginal 1.86 pp excess ($p_{\text{param}} = 0.0243$, Tarone $z = 0.764, p = 0.2224$), leaving $C_3$ unresolved with a bootstrap CI spanning 1.0 ($[0.0000, 7.5772]$) [C016] [C027] [C028] [C066].
3. **Compounding extrapolation and harness post-mortem:** We demonstrate via beta-binomial modeling that while $k=3$ cannot separate across-scenario heterogeneity from within-scenario serial correlation and leaves naive compounding accurate to 2.5 pp, even undetectable intra-scenario correlation ($\text{ICC}_{\text{hi}} = 0.0668$) compounds into notable divergence at scale ($C_8 \approx 2.25$, $\text{pass}^8 \approx 0.057$ vs naive $0.025$) [C068]. Furthermore, our trace post-mortem demonstrates how external provider outages interact with client-side circuit breakers to fabricate false clustering signatures, and we quantify the two-pass execution where 18.9M tokens (34.8%) were discarded [C026] [C060] [C061] [C067].

## 2 Question and Pre-Registration

### 2.1 Research Question
We investigate the pre-registered research question:
> *For LLM tool-use agents on a fixed set of 5-hop grounded-retrieval tasks, does the joint reliability over $k$ repeated executions equal the independence prediction $\text{pass}^k = (\text{pass@1})^k$, and if not, in which direction and by how much?*

The unit of analysis is the scenario instance ($n=150$ Tier-3 scenarios, IDs `r-0201` to `r-0350`). The $k=3$ executions per scenario represent repeated nested measurements; scenarios are the sampling units for all confidence intervals, bootstraps, and paired tests.

### 2.2 Pre-Registered Hypotheses and Both-Outcomes Commitment
Before data collection on Project P06, two primary hypotheses were pre-registered in `HYPOTHESES.md` (and `research/method/hypothesis.md`):
- **Hypothesis H4 (verbatim):** *"Measured pass^3 strictly exceeds naive (pass@1)^3 for >=4 of 6 rungs."*  
  - *Prediction if true:* 95% Wilson score interval of measured $\text{pass}^3$ strictly excludes and exceeds naive $(\text{pass@1})^3$ on $\ge 4$ rungs.
  - *Prediction if false:* Wilson interval of measured $\text{pass}^3$ contains or falls below naive on $\ge 3$ rungs.
- **Hypothesis H5 (verbatim):** *"Deviation from naive compounding (delta = pass^3 - (pass@1)^3) is larger for cheaper rungs than frontier rungs."*  
  - *Prediction if true:* $\Delta_{R2} > \Delta_{R4}$; concentration ratio $C_3$ higher on R2 than R4.
  - *Prediction if false:* $\Delta_{R2} \le \Delta_{R4}$ or rank ordering across the ladder is reversed.

The pre-registration committed to publishing findings regardless of outcome. Both H4 and H5 are **NOT_TESTABLE_AS_PREREGISTERED** because only 2 of 6 rungs produced valid data (R6 was invalidated by gateway dropouts, and R1/R3/R5 remained unexecuted); on the 2 evaluable rungs, the per-rung criterion was met on R4 under both as-run and infra-excluded variants, and not met on R2 [C021] [C022] [C029] [C030].

### 2.3 Frozen Artifact Hashes
Pipeline artifacts were cryptographically pinned prior to execution:
- **Synthetic graph corpus:** `build_corpus(42)`, SHA256 `84e6ff590704aa94d10912f8002716b14c7436080e1a3270b53f9385dc728efc`.
- **Scenario manifest:** 150 Tier-3 scenarios (`r-0201`–`r-0350`), manifest SHA256 `7e0a1b79d6e756f712d27e29168fed8b3bc5c4cd7beba7f8fc21d50366d41b83`.
- **System prompt:** `faultline_p2/agent/prompt.py` (Amendment A-001), SHA256 `87c7641e74964dcfe00c605051d7f5ddfade01f4019c95a00fd5dc3f1907c8df`.
- **Trace database:** `projects/p06_passk/trace.db`, SHA256 `1c83d147b5d7e5509a97eb46bf6fc400ca45b36aaa189bb18810bc75c56fe222`.

---

## 3 Environment

### 3.1 Synthetic Pseudoword Knowledge Graph
Real-world corpora suffer from pre-training contamination, enabling models to recall memorized facts [@chen2021codex]. To ensure contamination resistance, we construct a synthetic knowledge graph of 300 entities interconnected by directed relational edges, generated with master seed 42. All entity names, document IDs, relational predicates, and target attributes are coined pseudowords absent from public text. Documents define local attributes and outgoing relational pointers. Traversing the graph requires sequential tool calls: retrieving document $A$, extracting entity $B$, querying document $B$, and repeating until reaching terminal document $E$.

### 3.2 Tier-3 Multi-Hop Scenarios
The benchmark partitions tasks into three complexity tiers: Tier 1 (1-hop), Tier 2 (2–3 hops), and Tier 3 (5 hops). We isolate the reserved hard pool of 150 Tier-3 scenarios (`r-0201` to `r-0350`), requiring five sequential document traversals to locate the target attribute. This pool is unsaturated (pass rates range from 14.9% on R4 to 63.1% on R2 across the two valid rungs), preventing ceiling and floor saturation from masking trial variance [C009, C014].

### 3.3 Deterministic Dual-Condition Oracle
To eliminate automated judge biases [@zheng2023judging; @rao2026agreement] [C006], we implement a deterministic dual-condition oracle (`faultline_p2/oracle/oracle_check`). An execution trial is scored as a success ($y_{i,j} = 1$) if and only if:
1. **Normalized Answer Match:** The final answer string, after lowercase conversion and punctuation stripping, matches the ground-truth terminal attribute.
2. **Cited Source Provenance:** The ground-truth document identifier containing the terminal attribute appears within the agent's citation list.

Hallucinated answers without citations, or retrieved documents without correct attribute extraction, are scored as failures ($y_{i,j} = 0$).

---

## 4 Method

### 4.1 Protocol and Temperature Disclosures
Each scenario $i \in \{1, \dots, 150\}$ is executed across $k=3$ distinct runs per model tier (450 trials per model, 1,350 total) with a 24-step cap (Amendment A-003, MEC v1.3) using `get_document(doc_id)` and `search_entity(query)`. Each step constitutes one agent turn (model inference followed by tool execution); we score step-cap exhaustion without an oracle-verified answer as an incomplete failure. A single execution worker dispatched trials sequentially, looping over scenarios and repetitions with inter-trial pacing set by gateway response turnaround to prevent client-side concurrency contention.

All queries were executed with greedy decoding pinned to `temperature = 0.0`, `top_p = null`, and `max_tokens = 2048`. In benchmark literature, temperature 0 is assumed to ensure deterministic execution [@he2025defeating] [C003]. However, parallel GPU reduction kernels violate floating-point associativity: dynamic batching, concurrent thread scheduling, and kernel implementations alter summation order, inducing output divergence even at temperature 0 [@he2025defeating; @reddy2026sameweights; @pape2026silent; @fu2026beyond; @yuan2025nondeterminism; @gale2026tempzero] [C003] [C004] [C073]. When candidate token probabilities are close (particularly in the range 0.1 to 0.9), small numerical variations in logits can invert greedy argmax selection [@fu2026beyond] [C073]. Thus, we interpret between-trial variation across our runs as inference engine and serving backend nondeterminism rather than stochastic sampling [C003] [C004] [C025].

### 4.2 Metrics: Pass@k versus Pass^k
Let $N = 150$ and let $y_{i,j} \in \{0, 1\}$ denote the binary oracle verdict for scenario $i$ on trial $j \in \{1, \dots, k\}$ ($k=3$). Single-trial accuracy is $\text{pass@1} = \frac{1}{N \cdot k} \sum_{i=1}^N \sum_{j=1}^k y_{i,j}$.

Chen et al. [@chen2021codex] defined $\text{pass@k}$ as the probability that at least one of $k$ generated samples succeeds among $n \ge k$ attempts ($c_i$ correct):
$$\text{pass@k} = \mathbb{E}\left[ 1 - \frac{\binom{n - c_i}{k}}{\binom{n}{k}} \right]$$
where $c_i = \sum_{j=1}^k y_{i,j}$ [C001]; when $n = k$, this reduces directly to the probability of at least one success $\mathbb{I}(c_i \ge 1)$. For autonomous agents, Yao et al. [@yao2024taubench] defined joint reliability $\text{pass}^k$ as the probability that all $k$ repeated interaction episodes succeed [C002]:
$$\text{pass}^k = \frac{1}{N} \sum_{i=1}^N \prod_{j=1}^k y_{i,j} = \frac{1}{N} \sum_{i=1}^N \mathbb{I}(c_i = k)$$

Under independent Bernoulli trials with parameter $p = \text{pass@1}$, expected joint reliability is $\text{naive } (\text{pass@1})^k = (\text{pass@1})^k$. We define the concentration ratio $C_k$ and deviation delta $\Delta_k$:
$$C_k = \frac{\text{pass}^k}{(\text{pass@1})^k}, \quad \Delta_k = \text{pass}^k - (\text{pass@1})^k$$
$C_k > 1.0$ ($\Delta_k > 0$) indicates positive failure concentration, $C_k = 1.0$ indicates perfect independence, and $C_k < 1.0$ indicates negative clustering.

### 4.3 Statistical Testing Framework
1. **Wilson Score Intervals:** Proportions report 95% Wilson score intervals [@wilson1927] [C007] [C013].
2. **Scenario-Level Percentile Bootstrap:** To account for nested trials, we compute confidence intervals for $\text{pass@1}$, $\text{pass}^k$, risk differences, and ratio $C_k$ using a scenario-level percentile bootstrap with 10,000 resamples (seed 42), resampling entire scenario vectors $(y_{i,1}, \dots, y_{i,k})$ [@efron1979] [C017].
3. **Parametric Bootstrap Goodness-of-Fit:** Under independence, $c_i \sim \text{Binomial}(3, \text{pass@1})$. Because single-trial accuracy $p$ is estimated from the same sample, the asymptotic reference distribution has $\text{df} = 4 - 1 - 1 = 2$. We report Pearson $\chi^2$ goodness-of-fit with parametric bootstrap Monte Carlo (10,000 draws, seed 42) where $\text{pass@1}^*$ is re-estimated within each replicate, along with the exact one-sided binomial upper-tail test on the 3-of-3 cell [C012] [C017].
4. **Tarone's Score Test for Overdispersion:** To formally evaluate whether intra-scenario clustering exceeds binomial variation, we compute Tarone's (1979) $C(\alpha)$ score test for goodness-of-fit against beta-binomial overdispersion [@tarone1979] [C066]. The test statistic $z$ has an asymptotic standard normal distribution under the null hypothesis of no overdispersion [C066].
5. **Beta-Binomial Extrapolation:** Using the estimated intra-scenario correlation $\rho = \text{ICC}(1,1)$, we model joint reliability across depths $k \in \{1, \dots, 10\}$ under a beta-binomial distribution: $\mathbb{E}[\text{pass}^k] = \prod_{m=0}^{k-1} \frac{p + m \theta}{1 + m \theta}$ where $\theta = \rho / (1 - \rho)$ [C068]. We evaluate compounding divergence at the point estimate and at the upper bound of the ICC 95% bootstrap confidence interval [C068].
6. **Intra-Scenario Correlation:** We report one-way random effects Intraclass Correlation Coefficient $\text{ICC}(1,1)$ [@shrout1979] [C016] and Fleiss' multi-rater kappa $\kappa$ [@fleiss1971].
7. **Paired Comparisons:** Matched scenarios are compared via exact McNemar tests conditioned on discordant pairs [@mcnemar1947] [C008] [C014], with matched odds ratios ($b/c$), bootstrap risk differences, and paired Cohen's $d_z$.
8. **Multiple Testing Correction:** Family-Wise Error Rate is controlled via Holm-Bonferroni step-down adjustment over the declared primary family of tests [@holm1979] [C018] [C065].
9. **Declared Minimum Effect of Interest:** Per pre-registered protocol (MEC v1.0 §5), our declared power threshold and minimum effect of interest (MEI) is 10 percentage points (0.10) in joint reliability.

### 4.4 Infrastructure Incident and Sensitivity Exclusion Rule
During the sweep on 2026-09-11, external gateway disruptions impacted execution traces [C023] [C026] [C031]. Trace analysis (`infra_signature.json`, Decision D-008) revealed that across two windows (14:42–14:45 UTC and 22:30–22:41 UTC), 95 of 450 R4 trials dropped out, each recording two step-1 spans with `completion_tokens = 0` [C026]. 93 of 95 first attempts showed latencies $<1.0$ ms following two ~67 s gateway timeouts [C026]. The client harness configured `CircuitBreaker(failure_threshold=5, cooldown_seconds=30)` (`projects/p06_passk/run.py`). When remote API gateway requests timed out (~67 s), successive failures tripped the breaker once the threshold was reached, fast-failing subsequent trial requests with sub-millisecond latencies and zero completion tokens until the 30-second cooldown period elapsed [C026]. [limitation] Traces record latencies and tokens but not exception strings, so the circuit-breaker explanation is an inference from latency signatures [C023] [C026].

This disruption touched 33 R4 scenarios (31 all-3 dropped), artificially inflating the 0-of-3 failure cell ($c_i = 0$) [C026]. Model rung R6 (`deepseek/deepseek-v4-pro`), starting at 14:47:33 UTC, suffered 100% step-1 failures across all 450 runs (900 spans, 869 with latency $<1$ ms, 12 timeouts $>60$ s, 0 verdicts) [C023] [C031]. R6 was completely invalidated as an infrastructure failure and excluded from capability analyses [D-003] [C023] [C031]. Figure 4 illustrates the execution timeline and terminal states across rungs.

![Figure 4: Per-trial execution timeline and terminal states across R6, R4, and R2 final pass runs on 2026-09-11 UTC. Shaded bands indicate the two gateway outage windows (14:42–14:45 UTC and 22:30–22:42 UTC). R6 suffered 100% dead-at-start runs ($n=450$ trials) due to gateway step-1 connection drops. R4 experienced 95 dead trials (87 with $<1$ ms latency from client-side circuit breaker trips). R2 executed prior to the outage with 0 dead trials.](fig_4_incident_timeline.png)

We register a post-hoc sensitivity exclusion rule (Decision D-008):
- **Exclusion Rule:** A trial is *infrastructure-dead* iff every span of that `(run_id, scenario_id)` has `completion_tokens == 0` (or `None`) AND `max(step_index) <= 1` [D-008]. A scenario is dropped if it experienced $\ge 1$ dead trial [D-008].

R2 had 0 dead trials ($n=150$) [C009]. For R4, 33 scenarios are dropped, leaving $n=117$ valid scenarios (351 trials) [C027]. We report the pre-registered *as-run* analysis ($n=150$) as the primary evaluation and the *infra-excluded* sensitivity analysis ($n=117$) alongside it to measure the impact of external dropouts [D-008]. Additionally, we evaluate a strict sensitivity variant (*infra_excluded_strict*) that purges scenarios experiencing any midrun timeout or dead trial in Pass 2 (retaining $n=49$ for R2 and $n=24$ for R4) [C062].

### 4.5 Attempt Segmentation and Final-Pass Isolation
Forensic analysis of `projects/p06_passk/trace.db` (Decision D-010) revealed that the database contains two chronological execution passes: Pass 1 under step cap 12 (12:15–14:47 UTC) and Pass 2 under step cap 24 (19:20–22:42 UTC) [C067]. Because `record_verdict` updated all spans for a run upon completion, the stored verdicts in `trace.db` correspond to Pass 2 [C067]. First-pass verdicts are unrecoverable because raw completion text was not stored. Pass 1 consumed 18,917,495 tokens ($0.3974 USD discarded spend), while Pass 2 consumed 35,401,507 tokens ($23.0719 USD final spend), for a grand total of 54,319,002 tokens and $23.4693 USD across 1,800 runs (34.83% tokens discarded) [C024] [C067].

To avoid mixing step caps and invalidating span counts, all span-level metrics—including token usage, terminal-state classifications, and cost per grounded pass—are strictly computed on Pass 2 spans isolated via timestamp bounds [D-010] [C024] [C060] [C067]. Under Pass 2 isolation, zero runs terminate at step 12 (`step_cap_sub24 = 0`) [C060].

## 5 Results

We report findings in the strict order: **RAW RESULT**, **DERIVED RESULT**, and **INTERPRETATION**.

### 5.1 Raw Results
Raw counts from `analysis.json` and `p06_results.md`:
- **R2 (`z-ai/glm-5.3-flash`, as-run, $n=150$, 450 trials):** 284 passes out of 450 trials [C009]. Observed histogram: $\{0: 8, 1: 34, 2: 74, 3: 34\}$ [C012]. Concentration counts: 3-pass = 34, mixed = 108, 0-pass = 8 [C010]. Dead trials: 0 [C009]. Final-pass spend: $5.0994 USD ($5.1485 USD across passes; $0.01796 per grounded pass) [C024]. Pass 2 terminal states: answered_pass = 284, midrun_no_completion = 109, step_cap (>=24) = 14, dead_at_start = 23, answered_fail = 17, other = 3, step_cap_sub24 = 0 [C060]. Latency signatures: midrun_no_completion exhibits 104 spans $>60$ s [C061].
- **R4 (`openai/gpt-5.6-luna`, as-run, $n=150$, 450 trials):** 67 passes out of 450 trials [C014]. Observed histogram: $\{0: 95, 1: 46, 2: 6, 3: 3\}$ [C017]. Concentration counts: 3-pass = 3, mixed = 52, 0-pass = 95 [C015]. Dead trials: 95 across 33 scenarios (31 all-3 dead; split: $k_1=31, k_2=32, k_3=32$; window: 14:42:37 to 22:41:55 UTC) [C026]. Final-pass spend: $17.9725 USD ($18.3208 USD across passes; $0.26825 per grounded pass) [C024]. Pass 2 terminal states: step_cap (>=24) = 118, midrun_no_completion = 119, answered_pass = 67, dead_at_start = 114, answered_fail = 32, other = 0, step_cap_sub24 = 0 [C060]. Latency signatures: dead_at_start exhibits 106 spans $<1$ ms (breaker fast-fail), 2 spans $>60$ s (timeouts); midrun_no_completion exhibits 100 spans $>60$ s [C061].
- **R4 (`openai/gpt-5.6-luna`, infra-excluded, $n=117$, 351 trials):** 67 passes out of 351 trials [C027]. Observed histogram: $\{0: 62, 1: 46, 2: 6, 3: 3\}$ [C028]. Concentration counts: 3-pass = 3, mixed = 52, 0-pass = 62 [C028].
- **R6 (`deepseek/deepseek-v4-pro`, invalid):** 450 runs, 900 spans, 0 verdicts (869 spans $<1$ ms, 12 timeouts $>60$ s) [C023, C031]. Spend: $0.07 USD [C024].
- **Sweep Cumulative Spend & Attempts Breakdown:** Pass 1 (cap 12) consumed 18,917,495 tokens ($0.3974 USD discarded); Pass 2 (cap 24) consumed 35,401,507 tokens ($23.0719 USD final spend); grand total across all 1,800 runs was 54,319,002 tokens and $23.4693 USD (34.83% tokens discarded from Pass 1) [C024, C067].

### 5.2 Derived Results

#### Primary Consistency, Goodness-of-Fit, and Overdispersion
Table 1 presents consistency metrics, confidence intervals, concentration ratios, and goodness-of-fit statistics across model tiers. Table 2 details observed versus expected successes-per-scenario distributions.

| Model Tier & Analysis | Scenarios ($n$) | Measured $\text{pass@1}$ [95% CI] | Measured $\text{pass}^3$ [95% CI] | Naive $(\text{pass@1})^3$ [Bootstrap CI] | Concentration Ratio $C_3$ [Bootstrap CI] | Goodness-of-Fit $\chi^2$ (df=2) [Param MC $p$] | Tarone $Z$ Score [$p$-value] | $\text{ICC}(1,1)$ [Bootstrap CI] |
|---|---|---|---|---|---|---|---|---|
| **R2 (as-run)** | 150 | 0.6311 [0.5856, 0.6744] | 0.2267 [0.1670, 0.3000] | 0.2514 [0.2019, 0.3053] | 0.9017 [0.7161, 1.0793] | 1.8919 [$p=0.3794$] | $z=-0.655$ [$p=0.7438$] | -0.0287 [-0.1217, 0.0668] |
| **R4 (as-run)** | 150 | 0.1489 [0.1190, 0.1847] | 0.0200 [0.0068, 0.0571] | 0.0033 [0.0015, 0.0065] | 6.0596 [0.0000, 12.7450] | 13.6052 [$p=0.0053$] | $z=1.869$ [$p=0.0308$] | 0.0905 [-0.0499, 0.2347] |
| **R4 (infra-excluded)** | 117 | 0.1909 [0.1532, 0.2353] | 0.0256 [0.0088, 0.0727] | 0.0070 [0.0033, 0.0128] | 3.6867 [0.0000, 7.5772] | 7.8047 [$p=0.0243$] | $z=0.764$ [$p=0.2224$] | 0.0438 [-0.0978, 0.1907] |

*Table 1: Multi-trial consistency metrics ($k=3$). Single-trial pass@1 proportions report 95% Wilson score intervals assuming trial-level exchangeability ($n=450$ trials; scenario-level bootstrap CIs are $[0.5867, 0.6733]$ for R2, $[0.1133, 0.1867]$ for R4 as-run, and $[0.1481, 0.2336]$ for R4 infra-excluded); naive predictions, $C_3 = \text{pass}^3 / (\text{pass@1})^3$, and $\text{ICC}(1,1)$ report 95% scenario-level percentile bootstrap intervals (10,000 resamples, $n=150$ scenarios). Goodness-of-fit reports Pearson $\chi^2$ test with parametric bootstrap $p$-values ($\text{df}=2$) against the homogeneous-binomial null $\text{Binomial}(3, \text{pass@1})$. Tarone $Z$ reports the $C(\alpha)$ test for binomial goodness-of-fit against beta-binomial overdispersion. [C009] [C010] [C011] [C012] [C013] [C014] [C015] [C016] [C017] [C018] [C027] [C028] [C066]*

**R2 Homogeneous Binomial Null:** As reported in Table 1, R2 achieves $\text{pass@1} = 0.6311$ (Wilson CI $[0.5856, 0.6744]$; bootstrap CI $[0.5867, 0.6733]$) [C009] and joint reliability $\text{pass}^3 = 0.2267$ (34/150; Wilson CI $[0.1670, 0.3000]$; bootstrap CI $[0.1600, 0.2933]$), closely matching naive compounding $(\text{pass@1})^3 = 0.2514$ (bootstrap CI $[0.2019, 0.3053]$) [C010]. With $\Delta_3 = -0.0247$, concentration ratio $C_3 = 0.9017$ (bootstrap CI $[0.7161, 1.0793]$) comfortably spans 1.0 [C011]. Pearson goodness-of-fit yields $\chi^2 = 1.8919$ ($\text{df}=2$, parametric bootstrap $p = 0.3794$, exact upper tail $p = 0.7840$), indicating that observed successes-per-scenario ($\{8, 34, 74, 34\}$ vs expected $\{7.53, 38.65, 66.12, 37.71\}$ in Table 2) are not distinguishable from the homogeneous-binomial null [C012]. Tarone's score test for overdispersion confirms the absence of clustering: $z = -0.655$ ($p = 0.7438, S = 140.735$) [C066]. Intra-scenario correlation is null: $\text{ICC}(1,1) = -0.0287$ (bootstrap CI $[-0.1217, 0.0668]$) and Fleiss' $\kappa = -0.0309$ (bootstrap CI $[-0.1235, 0.0644]$) [C013].

**R4 Failure Concentration and Infrastructure Attenuation:** For R4 as-run ($n=150$), $\text{pass@1} = 0.1489$ (Wilson CI $[0.1190, 0.1847]$; bootstrap CI $[0.1133, 0.1867]$) [C014]. Measured $\text{pass}^3$ is 0.0200 (3/150; Wilson CI $[0.0068, 0.0571]$; bootstrap CI $[0.0000, 0.0467]$) vs naive 0.0033 (bootstrap CI $[0.0015, 0.0065]$), yielding point $C_3 = 6.0596$ and $\Delta_3 = +0.0167$ [C015] [C016] [C022]. While as-run data exhibits marginal overdispersion (Tarone $z = 1.869, p = 0.0308, S = 176.433$; parametric bootstrap GoF $p = 0.0053$) [C017] [C066], this effect is heavily driven by 95 infrastructure dropouts clustering in the 0-pass cell [C026]. Under infra-excluded sensitivity analysis ($n=117$), purging 33 dropout scenarios raises $\text{pass@1}$ to 0.1909 (Wilson CI $[0.1532, 0.2353]$; bootstrap CI $[0.1481, 0.2336]$) [C027]. Measured $\text{pass}^3 = 0.0256$ (3/117; Wilson CI $[0.0088, 0.0727]$; bootstrap CI $[0.0000, 0.0598]$) vs naive 0.0070 (bootstrap CI $[0.0033, 0.0128]$), giving $\Delta_3 = +0.0187$ and point $C_3 = 3.6867$ [C028] [C030]. Overdispersion evaporates once dropouts are removed: Tarone $z = 0.764$ ($p = 0.2224, S = 126.543$) and exact binomial tail $p = 0.0488$ on 3 vs 0.81 expected [C028] [C066]. The bootstrap CI on $C_3$ spans $[0.0000, 7.5772]$ (where the zero lower bound is a small-count artifact of 3 observed 3-pass scenarios appearing in zero draws for $\approx 4.8\%$ of resamples), encompassing 1.0, while $\text{ICC}(1,1)$ attenuates to 0.0438 (bootstrap CI $[-0.0978, 0.1907]$) and Fleiss' $\kappa$ to 0.0408 (bootstrap CI $[-0.1004, 0.1875]$) [C028].

**Strict Sensitivity Variant:** To ensure results are not confounded by soft-timeout runs, the strict sensitivity variant (*infra_excluded_strict*) purges any scenario experiencing a midrun timeout ($>60$ s) or dead trial in Pass 2 [C062]. R2 retains $n=49$ scenarios ($\text{pass@1} = 0.8776$, $\text{pass}^3 = 0.6939$ vs naive $0.6758$, $C_3 = 1.0267$ [CI $0.8654, 1.1578$], parametric bootstrap GoF $p = 0.4475$), remaining consistent with independence within confidence intervals [C062]. R4 retains $n=24$ scenarios ($\text{pass@1} = 0.3889$, $\text{pass}^3 = 0.1250$ vs naive $0.0588$, $C_3 = 2.1262$ [CI $0.0000, 4.4172$], parametric bootstrap GoF $p = 0.2787$), where the apparent departure from independence attenuates entirely [C062].

| Model Tier & Analysis | $c_i = 0$ Pass (Obs / Exp) | $c_i = 1$ Pass (Obs / Exp) | $c_i = 2$ Pass (Obs / Exp) | $c_i = 3$ Pass (Obs / Exp) | Exact Tail $p$ ($c_i = 3$) | Parametric MC $p$ |
|---|---|---|---|---|---|---|
| **R2 (as-run, $n=150$)** | 8 / 7.53 | 34 / 38.65 | 74 / 66.12 | 34 / 37.71 | 0.7840 | 0.3794 |
| **R4 (as-run, $n=150$)** | 95 / 92.48 | 46 / 48.53 | 6 / 8.49 | 3 / 0.50 | 0.0138 | 0.0053 |
| **R4 (infra-excluded, $n=117$)** | 62 / 61.98 | 46 / 43.86 | 6 / 10.35 | 3 / 0.81 | 0.0488 | 0.0243 |

*Table 2: Observed vs expected successes-per-scenario distributions ($c_i \in \{0, 1, 2, 3\}$). Expected counts derived under $c_i \sim \text{Binomial}(3, \text{pass@1})$. [C012] [C017] [C028]*

Figure 1 plots the observed successes-per-scenario distributions alongside the theoretical Binomial(3, pass@1) null. Figure 2 compares measured multi-trial pass rates against naive compounding predictions across $k \in \{1, 2, 3\}$.

![Figure 1: Observed versus Binomial(3, pass@1) expected scenario counts across success counts $s \in \{0, 1, 2, 3\}$. Panel A: R2 ($n=150$, $\chi^2 = 1.8919, p = 0.3794$). Panel B: R4 as-run ($n=150$, $\chi^2 = 13.6052, p = 0.0053$). Panel C: R4 infra-excluded ($n=117$, $\chi^2 = 7.8047, p = 0.0243$). Expected counts follow the homogeneous binomial model with $\hat{p} = \text{pass@1}$.](fig_1_successes_per_scenario.png)

![Figure 2: Empirical joint reliability $\widehat{\text{pass}}^k$ with 95% scenario-level bootstrap confidence intervals compared against naive compounding $(\text{pass@1})^k$ for $k \in \{1, 2, 3\}$. Panel A: R2 ($n=150$, $\text{pass}^3 = 0.2267$ vs naive $0.2514$). Panel B: R4 as-run ($n=150$, $\text{pass}^3 = 0.0200$ vs naive $0.0033$). Panel C: R4 infra-excluded ($n=117$, $\text{pass}^3 = 0.0256$ vs naive $0.0070$).](fig_2_passk_vs_naive.png)

#### Paired Scenario Comparisons (R2 vs R4)
Table 3 presents paired analyses on matched scenario IDs.

| Comparison & Sample | Discordant Pairs ($b$ R2-only / $c$ R4-only) | Risk Difference [Bootstrap CI] | Matched Odds Ratio [95% CI] | Exact McNemar $p$ | Holm-Adjusted $p$ | Paired Cohen's $d_z$ |
|---|---|---|---|---|---|---|
| **All-3-Pass (as-run, $n=150$)** | 34 / 3 | +0.2067 [0.1333, 0.2800] | 11.3333 [3.4808, 36.9004] | $1.23 \times 10^{-7}$ | $4.93 \times 10^{-7}$ | 0.46 |
| **Trial-1 Pass (as-run, $n=150$)** | 77 / 10 | +0.4467 [0.3467, 0.5400] | 7.7000 [3.9844, 14.8804] | $5.92 \times 10^{-14}$ | $2.96 \times 10^{-13}$ | 0.72 |
| **All-3-Pass (infra-excluded, $n=117$)** | 22 / 3 | +0.1624 [0.0855, 0.2393] | 7.3333 [2.1949, 24.5013] | $1.57 \times 10^{-4}$ | $4.70 \times 10^{-4}$ | 0.37 |
| **Trial-1 Pass (infra-excluded, $n=117$)** | 55 / 10 | +0.3846 [0.2650, 0.5043] | 5.5000 [2.8037, 10.7892] | $1.18 \times 10^{-8}$ | $4.70 \times 10^{-8}$ | 0.60 |

*Table 3: Paired comparisons on identical scenario IDs. For All-3-Pass (as-run), ties $= 113$ (0 concordant pass, 113 concordant fail). For Trial-1 Pass (as-run), ties $= 63$ (13 concordant pass, 50 concordant fail). Holm-adjusted $p$-values computed across the primary family of 5 tests. [C019] [C020] [C065]*

In matched paired comparisons, R2 outperforms R4 across both metrics (All-3-Pass risk difference $+0.2067$, exact McNemar $p = 1.23 \times 10^{-7}$; Trial-1 Pass risk difference $+0.4467$, exact McNemar $p = 5.92 \times 10^{-14}$) [C019] [C020]. Under the strict sensitivity variant ($n=14$ paired scenarios surviving), R2 maintains higher accuracy (Trial-1 exact McNemar $p = 0.0312$, 5 R2-only vs 0 R4-only; All-3-Pass exact McNemar $p = 0.1250$, 3 R2-only vs 0 R4-only) [C063].

#### Compounding Extrapolation across Depth $k=1..10$
To evaluate the practical consequences of small intra-scenario correlations at higher depths, Table 4 presents beta-binomial compounding extrapolations across $k \in \{1, \dots, 10\}$ for R2 [C068].

| Depth $k$ | Naive Prediction $(\text{pass@1})^k$ | Beta-Binomial Expected $\text{pass}^k$ | Concentration Ratio $C_k$ (Point Estimate) | Concentration Ratio $C_k$ (at $\text{ICC}_{\text{hi}} = 0.0668$) |
|---|---|---|---|---|
| $k=1$ | 0.6311 | 0.6311 | 1.00 | 1.00 |
| $k=2$ | 0.3983 | 0.3983 | 1.00 | 1.04 |
| $k=3$ | 0.2514 | 0.2514 | 1.00 | 1.10 |
| $k=4$ | 0.1586 | 0.1586 | 1.00 | 1.21 |
| $k=5$ | 0.1001 | 0.1001 | 1.00 | 1.39 |
| $k=6$ | 0.0632 | 0.0632 | 1.00 | 1.60 |
| $k=7$ | 0.0399 | 0.0399 | 1.00 | 1.89 |
| $k=8$ | 0.0252 | 0.0252 | 1.00 | 2.25 |
| $k=9$ | 0.0159 | 0.0159 | 1.00 | 2.74 |
| $k=10$ | 0.0100 | 0.0100 | 1.00 | 3.36 |

*Table 4: Beta-binomial compounding extrapolation across repetition depths $k \in \{1, \dots, 10\}$ for R2 ($\text{pass@1} = 0.6311$). While $C_3 \approx 1.10$ at $k=3$ (a 1.4 pp gap), divergence amplifies to $C_8 \approx 2.25$ by $k=8$ ($\text{pass}^8 \approx 0.057$ vs naive $0.025$). [C068]*

Figure 3 displays the compounding extrapolation across depths $k=1..10$ for R2 and R4 (both variants), demonstrating why consistency at $k=3$ cannot license compounding claims at higher depths.

![Figure 3: Implied concentration ratio $C_k = \text{pass}^k / (\text{pass@1})^k$ extrapolated across depth $k=1..10$ under the beta-binomial model. Panel A: R2 ($n=150, \widehat{\text{ICC}} = -0.0287$, capped at 0). Panel B: R4 as-run ($n=150, \widehat{\text{ICC}} = 0.2057$, upper 95% bootstrap bound $\text{ICC} = 0.3804$). Panel C: R4 infra-excluded ($n=117$, $\widehat{\text{ICC}} = 0.0849$, upper 95% bootstrap bound $\text{ICC} = 0.2642$). The dotted line marks the independence null $C_k = 1.0$.](fig_3_icc_extrapolation.png)

#### Hypothesis Verdicts
Both pre-registered hypotheses are unresolved under pre-registered rules due to design shortfall:
- **Hypothesis H4:** NOT_TESTABLE_AS_PREREGISTERED (2 of 6 rungs valid) [C021]. The pre-registered rule required $\ge 4$ of 6 rungs to evaluate. On the 2 valid rungs, the pre-registered per-rung criterion (Wilson CI of measured $\text{pass}^3$ excludes and exceeds naive $(\text{pass@1})^3$) held on R4 under both as-run (Wilson CI $[0.0068, 0.0571]$ vs naive $0.0033$) and infra-excluded (Wilson CI $[0.0088, 0.0727]$ vs naive $0.0070$) analyses, but did not hold on R2 (Wilson CI $[0.1670, 0.3000]$ contained naive $0.2514$) [C029]. Note that this per-rung criterion treats the naive prediction as fixed; parametric bootstrap goodness-of-fit and exact tail tests properly account for sampling error in $\text{pass@1}$.
- **Hypothesis H5:** NOT_TESTABLE_AS_PREREGISTERED (2 of 6 rungs valid) [C022]. Testing monotonic ordering requires a multi-tier ladder across $\ge 4$ rungs; with 2 valid rungs, rank correlation is degenerate. Point estimates show $\Delta_{R2} = -0.0247$ vs $\Delta_{R4} = +0.0167$ (as-run) and $\Delta_{R4} = +0.0187$ (infra-excluded), reversing the hypothesized ordering, but the difference $\Delta_{R4} - \Delta_{R2} = +0.0414$ has a 95% scenario bootstrap CI of $[-0.0080, 0.0922]$ which includes zero and is not statistically distinguishable from null [C030].

### 5.3 Interpretation
[we interpret] Drawing together the evidence, we interpret these results under four core findings [C025]:
1. **Remarkable Accuracy of Naive Compounding at $k=3$:** Across both evaluated model tiers, naive independent Bernoulli compounding is within 2.5 percentage points of measured joint reliability ($\Delta_3 = -0.0247$ on R2; $\Delta_3 = +0.0187$ on R4 infra-excluded) [C011] [C028]. In both cases, the deviation and its upper 95% bootstrap confidence bound ($+0.048$) are far below our pre-registered 10 percentage point minimum effect of interest.
2. **Homogeneous Binomial Null Holds on R2:** On the evaluated higher-accuracy tier (R2), agent outcomes are not distinguishable from independent Bernoulli trials (parametric bootstrap GoF $p = 0.3794$, Tarone overdispersion $z = -0.655, p = 0.7438$, $\text{ICC} = -0.0287$) [C012] [C013] [C066]. There is no detectable across-scenario task difficulty clustering or within-scenario serial dependence.
3. **Apparent Low-Accuracy Excess is Attenuated by Infrastructure Outages:** On R4, the apparent overdispersion is heavily driven by 95 network timeouts clustering in the 0-pass cell [C026]. Purging infrastructure dropouts evaporates overdispersion (Tarone $z = 0.764, p = 0.2224$), leaving a marginal 1.86 pp excess ($p = 0.0488$) and an unresolved concentration ratio ($C_3$ bootstrap CI $[0.0000, 7.5772]$ includes 1.0) [C016] [C028] [C066]. Under strict exclusion of midrun timeouts ($n=24$), the departure attenuates entirely ($p = 0.2787$) [C062].
4. **Indistinguishability at $k=3$ versus Compounding Divergence at Scale:** At repetition depth $k=3$, observations cannot mathematically separate across-scenario task heterogeneity from within-scenario serial correlation. However, beta-binomial compounding extrapolation demonstrates that even undetectable intra-scenario correlation ($\text{ICC}_{\text{hi}} = 0.0668$) compounds into a $2.25\times$ divergence at $k=8$ ($\text{pass}^8 \approx 0.057$ vs naive $0.025$) [C068]. Small departures at shallow evaluation depths compound into notable operational divergence at higher depths ($C_8 \approx 2.25$) [C068].

---

## 6 Supporting Evidence: Diagnostic Sweep Failure Taxonomy

> **Provenance Caveat:** Experiments P3, P4, and P5 were preliminary diagnostic sweeps under MEC v1.2 with step cap 12 (Amendment A-002), prior to Amendment A-003 expanding the cap to 24 for primary experiment P6 [C032] [C033] [C034]. P3 was contaminated by gateway rate limits [C038]. P4 human axial coding was performed on 200 traces from P3 by a single author [C037]. P5 judge calibration evaluated `z-ai/glm-5.3` on a frozen 60-trace test split of P4, belonging to the same model family as rung R2 [C049] [C058]. None of P3, P4, or P5 data originates from the P6 runs upon which our main result rests. Findings here are designated as **SUPPORTING** (appendix-bound) [C032].

In P3 diagnostic sweeps across 200 scenarios, accuracy collapsed as retrieval depth expanded: Tier 1 (1-hop) reached $\text{pass@1} = 1.0000$ (67/67; Wilson CI $[0.9458, 1.0000]$) requiring 4.01 steps and 2,633 tokens [C032]; Tier 2 (2–3 hops) reached $\text{pass@1} = 0.6119$ (41/67; Wilson CI $[0.4922, 0.7195]$) with 10.57 steps and 18,647 tokens [C033]; Tier 3 (5 hops) collapsed to $\text{pass@1} = 0.0758$ (5/66; Wilson CI $[0.0328, 0.1654]$) with 11.74 steps and 25,945 tokens [C034]. Disjoint Wilson intervals confirm diagnostic hypothesis H1: multi-hop depth degrades real-model pass rates [C036].

Axial coding of 200 execution traces from P3 (17 passed, 183 failed; pass rate 0.085) revealed that failures stem from diverse structural pathologies [C037]. Beyond gateway rate limits (`INFRASTRUCTURE_RATE_LIMIT`, 114 traces, 62.30%) [C038] and syntax errors (`MALFORMED_TOOL_CALL`, 23 traces, 12.57%) [C040], the analysis uncovered five emergent failure modes absent from initial catalogs (confirming hypothesis H2) [C047] [C048]: `OVERCONSTRAINED_SEARCH_LOOP` (36 traces, 19.67%) [C039], `MULTI_HOP_TRAVERSAL_EXHAUSTION` (3 traces, 1.64%) [C042], `INFRASTRUCTURE_SERVER_ERROR` (3 traces, 1.64%) [C041], `RETRIEVAL_FAILURE_ABSTENTION` (1 trace, 0.55%) [C043], `ANSWER_EXTRACTION_TRUNCATION` (1 trace, 0.55%) [C044], `PREMATURE_STOP_WRONG_HOP` (1 trace, 0.55%) [C045], and `MULTI_HOP_DIRECTION_ERROR` (1 trace, 0.55%) [C046]. Full definitions appear in Appendix C.

In P5, automated evaluators were calibrated against human labels on a frozen $n=60$ test split [C049]. Hypothesis H3 was **FALSIFIED**: only 2 of 5 core modes met $\kappa \ge 0.70$ [C058]. P5 also exposed mathematical fragility under class imbalance [@rao2026agreement] [C012]. For four failure modes (`MULTI_HOP_TRAVERSAL_EXHAUSTION`, `RETRIEVAL_FAILURE_ABSTENTION`, `ANSWER_EXTRACTION_TRUNCATION`, `MULTI_HOP_DIRECTION_ERROR`), the test split contained zero human positives ($\text{tp} + \text{fn} = 0$) [C053] [C054] [C055] [C057]. In these degenerate splits, evaluators predicting all-negative achieved 100% TNR and $\kappa = 1.0$ (or 0.0), creating the illusion of perfect performance without positive detection capability [we interpret] [C059]. Full calibration data appears in Appendix D.

---

## 7 Implications for Evaluation Practice

1. **Do Not Assume Naive $(\text{pass@1})^k$ Compounding Holds:** [we interpret] System designers cannot assume naive independent Bernoulli compounding holds across all regimes; empirical multi-trial consistency should be measured directly rather than extrapolated from single-trial pass rates [C002] [C025].
2. **Disclose Inference Backends and Report Instance-Level Error Bars:** Publishing point estimates obscures noise [@miller2024errorbars] [C005]. As shown by our bootstrap intervals, concentration ratios near zero are highly volatile ($C_3 \in [0.0000, 7.5772]$) [C016] [C028]. Evaluators should report Wilson score intervals for proportions [@wilson1927] [C007] and cluster-level bootstrap intervals for derived ratios [@efron1979] [C076]. Because temperature 0 does not ensure determinism [@he2025defeating; @pape2026silent], papers must document serving engines, batch concurrency, and gateway configurations [C003] [C004] [C071].
3. **Audit Traces for Client-Side Fast-Fails:** Client-side circuit breakers can silently convert transient remote timeouts into batches of $<1$ ms step-1 failures, inflating zero-pass counts [C023] [C026] [C031]. Benchmarking pipelines must record full exception text and conduct sensitivity analyses separating infrastructure dropouts from reasoning failures [D-008] [C026].
4. **Deploy Deterministic Dual-Condition Oracles:** Automated LLM judges suffer from position bias, verbosity bias, and reliability attenuation under class imbalance [@zheng2023judging; @rao2026agreement] [C006] [C012]. Wherever feasible, agent benchmarks should grade completion using deterministic oracles that verify both normalized semantic outputs and explicit citation of ground-truth provenance.

---

## 8 Related Work

### 8.1 Functional Code Generation and Multi-Trial Agent Reliability
Chen et al. [@chen2021codex] formalized the unbiased $\text{pass@k}$ estimator for functional code generation, evaluating the probability that at least one of $k$ generated sample programs passes unit tests [C001, E001]. Yao et al. [@yao2024taubench] introduced $\tau$-bench, formalizing joint reliability $\text{pass}^k$ for multi-turn tool interaction where an agent must successfully complete all $k$ repeated interaction episodes on a task instance, observing that high single-trial performance ($\text{pass@1}$) can mask severe multi-trial reliability degradation [C002, E002]. However, $\tau$-bench did not benchmark the empirical gap to $(\text{pass@1})^k$ or evaluate across-scenario heterogeneity versus within-scenario serial correlation; our work directly tests this compounding gap under repetition. Jiang et al. [@jiang2026beyondpassk] demonstrated that multi-turn agent evaluations frequently conflate internal unit test assertions with independent agent rollouts, inflating reported operational reliability [C069, E009]. Bellibatlu et al. [@bellibatlu2026samepatient] showed that clinical decision agents can achieve nominal task success while executing discordant intermediate tool actions across repeated runs [C070, E010].

### 8.2 Inference Nondeterminism at Temperature 0
Greedy decoding at temperature 0 is widely assumed by practitioners to produce deterministic output across repeated API queries [C003, E003, E019, E020]. However, He et al. [@he2025defeating] demonstrated that modern GPU batching and parallel floating-point reductions cause non-zero output divergence even at temperature 0 [C004, E004]. Pape et al. [@pape2026silent] found that differing serving engines (vLLM, SGLang, llama.cpp) produce measurable output disagreement on fixed benchmarks at temperature 0, shifting benchmark scores by up to 16.6 percentage points [C071, E005]. Reddy et al. [@reddy2026sameweights] showed that routing identical open-weight models across commercial API providers yields discordant task completions [C072, E006]. Fu et al. [@fu2026beyond] also demonstrated that non-associative floating-point addition in GPU attention kernels alters token logits, occasionally flipping greedy argmax selection when candidate token probabilities are close [C073, E007].

### 8.3 Statistical Foundations of Model Evaluation
Miller [@miller2024errorbars] argues that language model evaluations are scientific experiments that should report standard errors and paired tests, noting that standard benchmark practice rarely tests claimed improvements for statistical significance [C005, E008]. Zheng et al. [@zheng2023judging] documented systematic position, verbosity, and self-enhancement biases in automated model judges [C006, E011]. Rao and Callison-Burch [@rao2026agreement] showed that percent agreement and kappa can diverge sharply depending on protocol choices and label prevalence under class imbalance [C012, E012]. Our evaluation methodology is grounded in classical statistical foundations: asymmetric Wilson score intervals [@wilson1927] [C007, E013], paired exact McNemar tests conditioned on discordant observation pairs [@mcnemar1947] [C008, E014], Rogan-Gladen prevalence estimation [@rogan1978] [C074, E015], one-way random effects intraclass correlation [@shrout1979] [C075, E016], percentile bootstrap resampling [@efron1979] [C076, E017], and sequentially rejective Holm-Bonferroni testing [@holm1979] [C077, E018].

## 9 Limitations

[limitation] We explicitly document nine threats to validity and scope constraints:
1. **Single Synthetic Environment:** Evaluations were conducted exclusively on a synthetic 300-entity pseudoword knowledge graph. While synthetic graphs eliminate pre-training contamination, they do not replicate the syntactic variety of unstructured web documents or noisy production databases.
2. **Two Valid Model Tiers:** Following the invalidation of R6 due to gateway failures, our primary capability data rests on two commercial models (R2 and R4). Findings regarding accuracy regimes cannot be extrapolated to all LLM architectures.
3. **Repetition Depth ($k=3$):** Repeated measurements were restricted to $k=3$ trials per scenario ($N=150$). While sufficient to test $\text{pass}^3$ compounding, larger repetition depths ($k \in [5, 10]$) are required to map higher-order reliability decay curves [C068].
4. **Sample Size and Resolution ($n=150$):** With 150 scenarios, observing 3 scenarios with all three trials passing in R4 yields a bootstrap confidence interval spanning $[0.0000, 7.5772]$ [C016]. Resolving whether $C_3$ strictly exceeds 1.0 at low pass rates requires larger sample sizes (hundreds of scenarios, e.g., $n \ge 500$ to achieve statistical power $\ge 0.95$ under subtle deviations).
5. **Temperature 0 Greedy Decoding:** All trials were executed at temperature 0.0. Our results reflect inference engine and gateway nondeterminism rather than deliberate stochastic temperature exploration ($T > 0$).
6. **Single Commercial API Gateway:** Remote inference was routed through a single commercial gateway provider (`aicredits.in`). We cannot isolate how much between-trial variance originated within provider routing proxies versus internal datacenter scheduling.
7. **Single-Author Qualitative Trace Coding:** Failure mode coding in diagnostic experiment P4 was conducted by a single annotator across 200 traces, lacking multi-annotator inter-rater reliability verification.
8. **Same-Family Judge Confound in Supporting Study:** Diagnostic evaluator calibration in P5 employed `z-ai/glm-5.3` to evaluate traces from the same model family, introducing potential self-enhancement bias.
9. **Post-Hoc Sensitivity Rule:** The infrastructure exclusion rule was formulated post-hoc following discovery of the 2026-09-11 gateway incident, although formalized prior to final paper drafting (Decision D-008).
10. **Protocol Unknowns:** [limitation] As recorded in `research/method/protocol.md`, several provider variables remain unknown: upstream model snapshot versions, cloud provider routing behind gateway aliases, physical GPU architectures, serving frameworks (e.g., vLLM vs TensorRT-LLM), server-side CUDA driver versions, and instantaneous batch concurrency levels on remote gateway clusters.

---

## 10 Reproduction

Reproduction of the experimental analyses is supported by artifacts preserved in the project repository:
- **Pre-Registration:** Primary hypotheses, statistical analysis plan, and decision thresholds were pre-registered in `HYPOTHESES.md` (and `research/method/hypothesis.md`) prior to primary data collection.
- **Corpus Generation:** Deterministic synthetic knowledge graph generated via `build_corpus(42)`, matching content hash `84e6ff590704aa94d10912f8002716b14c7436080e1a3270b53f9385dc728efc` of the canonical JSON graph export.
- **Scenario Manifest:** The 150 reserved Tier-3 scenarios (`r-0201` to `r-0350`) are pinned by SHA256 `7e0a1b79d6e756f712d27e29168fed8b3bc5c4cd7beba7f8fc21d50366d41b83` of the scenario JSON file.
- **System Prompt:** Frozen prompt module `faultline_p2/agent/prompt.py`, SHA256 `87c7641e74964dcfe00c605051d7f5ddfade01f4019c95a00fd5dc3f1907c8df`.
- **Analysis Pipeline & Invocation:** All tables, confidence intervals, exact tests, and bootstrap distributions are generated deterministically by `projects/p06_passk/analysis.py` operating on SQLite database `projects/p06_passk/trace.db` (SHA256 `1c83d147b5d7e5509a97eb46bf6fc400ca45b36aaa189bb18810bc75c56fe222`) via:
  ```bash
  python projects/p06_passk/analysis.py \
    --db projects/p06_passk/trace.db \
    --ledger projects/p06_passk/ledger.jsonl \
    --out projects/p06_passk/analysis.json \
    --seed 42 --resamples 10000
  ```
- **Software Dependencies:** Python 3.11, LiteLLM 1.98.0 pinned, Pydantic 2.13.4, SQLite 3. The analysis pipeline relies strictly on the Python standard library (`random.seed(42)` and `math`), ensuring bitwise identical bootstrap and Monte Carlo results across platforms without external RNG dependencies.
- **Licensing:** Code is released under the MIT License; benchmark scenarios, evaluation protocols, and trace data are released under CC-BY-4.0.
- **Repository:** Open-source code, scenario configs, and analysis pipelines are available at https://github.com/samirsawarkar/faultline-ai-reliability.

---

## References

- [@bellibatlu2026samepatient]
- [@chen2021codex]
- [@dalal2025inconsistency]
- [@dragoi2025breadthdepth]
- [@edwards2026rogan]
- [@efron1979]
- [@fleiss1971]
- [@fu2026beyond]
- [@gale2026tempzero]
- [@he2025defeating]
- [@holm1979]
- [@jiang2026beyondpassk]
- [@kopacka2026rogan]
- [@mcnemar1947]
- [@miller2024errorbars]
- [@pape2026silent]
- [@rao2026agreement]
- [@reddy2026sameweights]
- [@rogan1978]
- [@shrout1979]
- [@tarone1979]
- [@wilson1927]
- [@yao2024taubench]
- [@yuan2025nondeterminism]
- [@zheng2023judging]

---

## Appendix A: Statistical Details

### A.1 Collapsed versus Uncollapsed Goodness-of-Fit Testing
Standard statistical procedures recommend collapsing discrete bins when the expected count under the null model is less than 5.0 to preserve the asymptotic $\chi^2$ approximation. For R4 as-run ($n=150, p=0.1489$), expected counts across cells $c_i \in \{0, 1, 2, 3\}$ under $\text{Binomial}(3, 0.1489)$ are $E(c_i = 0) = 92.4805$, $E(c_i = 1) = 48.5341$, $E(c_i = 2) = 8.4903$, and $E(c_i = 3) = 0.4951$. Because $E(c_i = 3) < 5.0$, classical automated collapsing merges the $c_i = 2$ and $c_i = 3$ bins into a single composite bin $\{2, 3\}$ [D-004]. The resulting collapsed observed counts are $\{95, 46, 9\}$ against expected $\{92.4805, 48.5341, 8.9854\}$. On this collapsed table, the Pearson statistic is $\chi^2 = 0.200982$ ($\text{df} = 2$), yielding an asymptotic $p$-value of $0.9044$ (exact Monte Carlo $p = 0.9030$) [C017].

However, collapsing merges the 6 observed 2-of-3 scenarios with the 3 observed 3-of-3 scenarios. As detailed in Decision D-004, the entire physical effect of failure concentration resides in the 3-of-3 cell (where 3 scenarios succeeded versus 0.50 expected) [D-004]. Collapsing masks this tail excess because the 2-of-3 cell exhibits a slight deficit (6 observed vs 8.49 expected), completely canceling the signal [D-004]. To maintain transparency, we report the collapsed test in this appendix while adopting the uncollapsed exact Monte Carlo test ($p = 0.0123$) and exact binomial tail test ($p = 0.0140$) as primary in the main body [D-004, C017].

Similarly, for R4 under infra-excluded analysis ($n=117, p=0.1909$), expected counts are $\{61.9754, 43.8629, 10.3479, 0.8137\}$ against observed $\{62, 46, 6, 3\}$. Collapsing $\{2, 3\}$ yields observed $\{62, 46, 9\}$ vs expected $\{61.9754, 43.8629, 11.1617\}$, with $\chi^2 = 0.522788$ ($\text{df}=2, p=0.7825$), whereas the uncollapsed exact Monte Carlo test yields $p = 0.0511$ ($\chi^2 = 7.804732, \text{df}=3$) and exact tail $p = 0.0488$ [C028]. For R2 ($n=150, p=0.6311$), all expected counts exceed 5.0 ($\{7.5297, 38.6464, 66.1180, 37.7059\}$), requiring no collapsing ($\chi^2 = 1.891856, \text{df}=3$, exact Monte Carlo $p = 0.5939$) [C012].

### A.2 Scenario-Level Bootstrap Settings
Bootstrap distributions were computed using 10,000 resamples with replacement under master seed 42. Resampling was conducted strictly at the scenario level: entire scenario vectors $(y_{i,1}, y_{i,2}, y_{i,3})$ were resampled, preserving intra-scenario correlation [@efron1979] [C017]. For concentration ratios $C_k = \text{pass}^k / (\text{pass@1})^k$, each replicate computed both numerator and denominator simultaneously from the resampled matrix.

### A.3 Family of Hypotheses and Holm-Bonferroni Adjustments
Table A1 records the pre-registered family of statistical tests and corresponding raw and Holm-adjusted $p$-values across the primary declared family of 5 tests [C018, C019, C020, C065].

| Test Identifier | Null Hypothesis Tested | Raw $p$ | Holm-Adjusted $p$ | Reject Null at $\alpha=0.05$? |
|---|---|---|---|---|
| `paired_mcnemar_R2_vs_R4_trial_1_pass` | Marginal homogeneity between R2 and R4 on Trial 1 | $5.92 \times 10^{-14}$ | $2.96 \times 10^{-13}$ | Yes |
| `paired_mcnemar_R2_vs_R4_all_3_pass` | Marginal homogeneity between R2 and R4 on All-3-Pass | $1.23 \times 10^{-7}$ | $4.93 \times 10^{-7}$ | Yes |
| `independence_goodness_of_fit_R4_as_run` | R4 as-run follows $\text{Binomial}(3, p)$ (parametric bootstrap) | $0.0053$ | $0.0159$ | Yes |
| `independence_goodness_of_fit_R4_infra_excluded` | R4 infra-excluded follows $\text{Binomial}(3, p)$ (parametric bootstrap) | $0.0243$ | $0.0486$ | Yes |
| `independence_goodness_of_fit_R2` | R2 follows $\text{Binomial}(3, p)$ (parametric bootstrap) | $0.3794$ | $0.3794$ | No |

*Table A1: Evaluated family of statistical tests and sequentially rejective Holm-Bonferroni adjustments. [C018, C019, C020, C065]*

---

## Appendix B: P3 Depth Diagnostic Results

Diagnostic experiment P3 evaluated retrieval depth degradation across complexity tiers under protocol MEC v1.2 (step cap 12, Amendment A-002) [C032, C033, C034, C035]. Evaluated rungs included R2 (`z-ai/glm-5.3-flash`), R4 (`openai/gpt-5.6-luna`), and R6 (`deepseek/deepseek-v4-pro`) [C035]. Table B1 details pass rates, step lengths, and token consumption across tiers.

| Complexity Tier | Evaluated Scenarios | Passing Trials | Measured $\text{pass@1}$ [95% Wilson CI] | Average Steps | Average Prompt Tokens | Average Completion Tokens | Average Total Tokens |
|---|---|---|---|---|---|---|---|
| **Tier 1 (1-hop)** | 67 | 67 | 1.0000 [0.9458, 1.0000] | 4.01 | 2,110 | 523 | 2,633 |
| **Tier 2 (2–3 hops)** | 67 | 41 | 0.6119 [0.4922, 0.7195] | 10.57 | 17,266 | 1,381 | 18,647 |
| **Tier 3 (5 hops)** | 66 | 5 | 0.0758 [0.0328, 0.1654] | 11.74 | 24,518 | 1,427 | 25,945 |

*Table B1: P3 diagnostic sweep results across retrieval depth tiers. Confirms hypothesis H1 with disjoint Wilson intervals between T1 and T3. [C032, C033, C034, C036]*

Figure B plots the single-trial pass rate progression across the three reasoning depth tiers for all three evaluated models.

![Figure B: Single-trial pass@1 success rate across reasoning depth tiers (T1: 1-hop, $n=67$; T2: 2–3 hops, $n=67$; T3: 4–5 hops, $n=66$) for R2 (`glm-5.3-flash`), R6 (`deepseek-v4-pro`), and R4 (`gpt-5.6-luna`). Error bars represent 95% Wilson score intervals.](fig_B_p03_depth.png)

---

## Appendix C: P4 Failure Mode Taxonomy

Qualitative axial coding of 200 execution traces from P3 (17 passing, 183 failing) was performed by the single author [C037]. Table C1 presents the failure mode taxonomy, raw counts, and prevalences (denominator = 183 failures).

| Failure Mode Identifier | Classification | Description | Count | Prevalence (% of 183 failures) |
|---|---|---|---|---|
| `INFRASTRUCTURE_RATE_LIMIT` | External Infrastructure | Remote HTTP 429 rate limit errors returned by cloud gateway | 114 | 62.30% |
| `OVERCONSTRAINED_SEARCH_LOOP` | Emergent Agent Pathology | Agent generates overly specific search strings, entering repetitive query loops | 36 | 19.67% |
| `MALFORMED_TOOL_CALL` | Agent Syntax Failure | Emitting invalid JSON or non-existent tool arguments | 23 | 12.57% |
| `INFRASTRUCTURE_SERVER_ERROR` | External Infrastructure | Remote HTTP 500/502/503 server errors returned by gateway | 3 | 1.64% |
| `MULTI_HOP_TRAVERSAL_EXHAUSTION` | Emergent Agent Pathology | Valid multi-hop reasoning that hits the 12-step cap before reaching terminal target | 3 | 1.64% |
| `RETRIEVAL_FAILURE_ABSTENTION` | Emergent Agent Pathology | Prematurely concluding target entity does not exist after initial search miss | 1 | 0.55% |
| `ANSWER_EXTRACTION_TRUNCATION` | Emergent Agent Pathology | Correctly retrieving terminal document but truncating attribute in emitted answer | 1 | 0.55% |
| `PREMATURE_STOP_WRONG_HOP` | Emergent Agent Pathology | Terminating search at intermediate hop and outputting intermediate entity | 1 | 0.55% |
| `MULTI_HOP_DIRECTION_ERROR` | Emergent Agent Pathology | Traversing relational pointers in reverse direction from question prompt | 1 | 0.55% |

*Table C1: P4 human failure mode taxonomy. Five emergent modes absent from the baseline catalog confirmed hypothesis H2 [C038, C039, C040, C041, C042, C043, C044, C045, C046, C047, C048].*

Figure C illustrates the prevalence distribution across the nine axial failure modes.

![Figure C: Prevalence of 9 axial failure categories across $n=183$ failed execution traces in the P4 open/axial coding study. Transport infrastructure rate limits account for 62.3% ($n=114$), overconstrained search loops for 19.7% ($n=36$), and malformed tool calls for 12.6% ($n=23$).](fig_C_p04_taxonomy.png)

---

## Appendix D: P5 Evaluator Calibration and Degenerate Splits

In P5, automated evaluators—deterministic code assertions and an LLM judge (`z-ai/glm-5.3`)—were calibrated against human labels on a frozen $n=60$ test split [C049]. Table D1 summarizes evaluation performance, confusion matrices, chance-corrected agreement ($\kappa$), and Rogan-Gladen adjusted prevalence estimates [@rogan1978; @edwards2026rogan; @kopacka2026rogan] [C015].

| Evaluated Failure Mode | Evaluator Type | Confusion Matrix (TP, FP, TN, FN) | True Positive Rate (TPR) [95% CI] | True Negative Rate (TNR) [95% CI] | Cohen's $\kappa$ | Raw Prevalence | Rogan-Gladen Prevalence | Degenerate Split? |
|---|---|---|---|---|---|---|---|---|
| `INFRASTRUCTURE_RATE_LIMIT` | Code Assertion | (34, 0, 26, 0) | 1.0000 [0.8985, 1.0000] | 1.0000 [0.8713, 1.0000] | 1.0000 | 0.5667 | 0.5667 | No |
| `OVERCONSTRAINED_SEARCH_LOOP` | LLM Judge | (0, 1, 45, 14) | 0.0000 [0.0000, 0.2153] | 0.9783 [0.8866, 0.9962] | -0.0321 | 0.2333 | 0.2333 | No |
| `MALFORMED_TOOL_CALL` | Code Assertion | (6, 21, 33, 0) | 1.0000 [0.6097, 1.0000] | 0.6111 [0.4779, 0.7296] | 0.2391 | 0.1000 | 0.1000 | No |
| `INFRASTRUCTURE_SERVER_ERROR` | Code Assertion | (1, 0, 59, 0) | 1.0000 [0.2065, 1.0000] | 1.0000 [0.9389, 1.0000] | 1.0000 | 0.0167 | 0.0167 | No |
| `MULTI_HOP_TRAVERSAL_EXHAUSTION` | Code Assertion | (0, 7, 53, 0) | 1.0000 [0.0000, 1.0000] | 0.8833 [0.7782, 0.9423] | 0.0000 | 0.0000 | 0.0000 | **Yes ($\text{pos}=0$)** |
| `RETRIEVAL_FAILURE_ABSTENTION` | LLM Judge | (0, 0, 60, 0) | 1.0000 [0.0000, 1.0000] | 1.0000 [0.9398, 1.0000] | 1.0000 | 0.0000 | 0.0000 | **Yes ($\text{pos}=0$)** |
| `ANSWER_EXTRACTION_TRUNCATION` | LLM Judge | (0, 0, 60, 0) | 1.0000 [0.0000, 1.0000] | 1.0000 [0.9398, 1.0000] | 1.0000 | 0.0000 | 0.0000 | **Yes ($\text{pos}=0$)** |
| `PREMATURE_STOP_WRONG_HOP` | LLM Judge | (0, 0, 59, 1) | 0.0000 [0.0000, 0.7935] | 1.0000 [0.9389, 1.0000] | 0.0000 | 0.0167 | 0.0000 | No |
| `MULTI_HOP_DIRECTION_ERROR` | LLM Judge | (0, 0, 60, 0) | 1.0000 [0.0000, 1.0000] | 1.0000 [0.9398, 1.0000] | 1.0000 | 0.0000 | 0.0000 | **Yes ($\text{pos}=0$)** |

*Table D1: P5 automated evaluator calibration against human labels ($n=60$). Modes with $\text{TP} + \text{FN} = 0$ represent degenerate test splits where metrics like $\kappa = 1.0$ reflect the absence of true positives rather than detection ability. [C049, C050, C051, C052, C053, C054, C055, C056, C057, C058, C059]*

Figure D plots the chance-corrected agreement ($\kappa$) across failure modes for the automated evaluators against human ground truth.

![Figure D: Cohen's $\kappa$ inter-rater agreement for automated LLM evaluators against human axial ground truth on $n=60$ test traces across 9 failure modes. Five evaluators achieved perfect agreement ($\kappa = 1.0$), while multi-hop traversal exhaustion and premature stopping showed chance-level agreement ($\kappa = 0.0$) and search looping had negative agreement ($\kappa = -0.032$).](fig_D_p05_kappa.png)

---

## Appendix E: Spend and Cost per Grounded Pass

All API invocations were tracked via `ledger.jsonl`. Cumulative spend across the 900 primary runs in Pass 2 of Project P06 totaled $23.0719 USD ($5.0994 USD on R2, $17.9725 USD on R4) across 35,401,507 tokens [C024, C067]. An earlier Pass 1 exploratory sweep (step cap 12) incurred $0.3974 USD across 18,917,495 tokens (34.83% of all generated tokens), bringing grand total project spend to $23.4693 USD across 54,319,002 tokens [C024, C067]. Table E1 breaks down final-pass spend, passing trials, and cost per grounded pass.

| Model Tier & Analysis | Final-Pass Spend (USD) | Passing Trials ($c$) | Cost per Grounded Pass (USD) [95% Bootstrap CI] | Cost per Attempted Run (USD) |
|---|---|---|---|---|
| **R2 (`z-ai/glm-5.3-flash`, as-run)** | $5.0994 | 284 | $0.017956 [$0.016830, $0.019316] | $0.011332 |
| **R4 (`openai/gpt-5.6-luna`, as-run)** | $17.9725 | 67 | $0.268246 [$0.213959, $0.352402] | $0.039939 |
| **R4 (`openai/gpt-5.6-luna`, infra-excluded)** | $17.9725 | 67 | $0.268246 [$0.213959, $0.352402] | $0.051204 |
| **Pass 1 Discarded Sweep (R2 + R4)** | $0.3974 | — | — | $0.000442 |
| **Complete Study Cumulative** | $23.4693 | 351 | — | $0.017385 |

*Table E1: Spend and cost per grounded pass across model tiers in Pass 2 and discarded Pass 1 sweep. Bootstrap intervals from 10,000 scenario-level resamples. [C024, C067]*

---

## Appendix F: Anticipated Objections

We address seven anticipated methodological objections:

1. **"The benchmark relies entirely on a synthetic pseudoword graph rather than real-world tasks."**  
   *Response:* Synthetic pseudoword graphs are intentionally employed to eliminate pre-training data contamination, ensuring agents cannot shortcut multi-hop reasoning via memorized semantic associations [@chen2021codex]. Every document link and attribute must be actively traversed via tool execution. However, [limitation] this paper cannot address whether failure clustering dynamics generalize to natural language documents with rich semantic redundancy.
2. **"Only two valid models were evaluated, precluding broad capability generalizations."**  
   *Response:* We agree that evaluating two models (R2 and R4) cannot support broad generalizations across the ecosystem of LLM architectures. The third planned model (R6) suffered an irreversible external gateway collapse and was excluded from capability claims [C023]. Accordingly, we treat R2 and R4 strictly as empirical demonstrations of distinct accuracy regimes rather than a comprehensive model ranking [D-002, D-006].
3. **"The benchmark design favors one model architecture over another."**  
   *Response:* All models received bitwise-identical system prompts, identical tool schema definitions, identical 24-step execution caps, and identical deterministic dual-condition oracle grading [C009, C014]. Neither prompt engineering nor tool tuning was performed to favor any provider. Differences in single-trial pass rates reflect intrinsic model tool-calling capability on 5-hop linear dependency chains.
4. **"The observed failure concentration is merely an empirical correlation, not an isolated causal mechanism."**  
   *Response:* This objection is entirely correct. Our primary experiment establishes the statistical validity of the independence assumption on scenario-level outcomes; it does not isolate internal model attention dynamics. While our diagnostic studies (P3–P5) identify failure modes such as overconstrained search loops, [limitation] this paper cannot address causal mechanistic activations inside proprietary model weights.
5. **"The post-hoc exclusion of 33 infrastructure-contaminated scenarios undermines pre-registered rigor."**  
   *Response:* To preserve methodological integrity, we report both the pre-registered as-run analysis ($n=150$) and the infra-excluded sensitivity analysis ($n=117$) side-by-side throughout the paper [D-008]. The 95 dropped trials exhibited a distinct latency signature ($<1$ ms fast-fails) following gateway timeouts, verifying an external failure mode [C026]. Disclosing both analyses demonstrates that while as-run data suggests strong failure concentration ($p=0.0123$), removing verifiable network dropouts renders the effect statistically marginal ($p=0.0488$) [C017, C028].
6. **"Why does joint reliability pass^3 matter if developers can simply retry failed tasks in production?"**  
   *Response:* Retrying is only possible when an external verification oracle exists to detect failure immediately. In autonomous enterprise workflows (e.g., executing database transactions or clinical orders), agents operate unmonitored and benchmarks scoring single runs miss intermediate action-level divergence [@bellibatlu2026samepatient]. In these settings, joint reliability $\text{pass}^k$ represents the operational consistency requirement [@yao2024taubench; @jiang2026beyondpassk].
7. **"Reproduction is impossible because closed commercial model API endpoints drift over time."**  
   *Response:* Proprietary cloud API snapshot drift is an inherent challenge in contemporary empirical AI research [@reddy2026sameweights; @pape2026silent]. To maximize reproducibility, we have preserved the complete raw SQLite trace database containing all 1,350 execution traces, timestamps, latency signatures, and token counts (SHA256 `1c83d147b5d7e5509a97eb46bf6fc400ca45b36aaa189bb18810bc75c56fe222`), enabling independent re-verification of all reported statistics without executing new API calls.

---

## List of Evidence Gaps (TODO Blocks)
1. `need empirical citation for industrial teams multiplying pass@1 as joint reliability SLA` (Section 1)
2. `need public repository URL and Zenodo archive DOI for open data release` (Section 10)

---

## List of Claims Ledger IDs Referenced
- `C001` (Section 1, Section 4.2, Section 8.1)
- `C002` (Section 1, Section 4.2, Section 7, Section 8.2)
- `C003` (Abstract, Section 4.1, Section 7, Section 8.3)
- `C004` (Abstract, Section 4.1, Section 7, Section 8.3)
- `C005` (Section 1, Section 7, Section 8.3, Section 8.4)
- `C006` (Section 1, Section 3.3, Section 7, Section 8.3, Section 8.4)
- `C007` (Section 1, Section 4.1, Section 4.3, Section 7, Section 8.3, Section 8.4)
- `C008` (Section 1, Section 4.3, Section 8.4)
- `C009` (Abstract, Section 1, Section 3.2, Section 4.4, Section 5.1, Section 5.2, Appendix F)
- `C010` (Abstract, Section 1, Section 5.1, Section 5.2)
- `C011` (Abstract, Section 1, Section 3.3, Section 5.2, Section 8.4)
- `C012` (Abstract, Section 1, Section 3.3, Section 4.3, Section 5.1, Section 5.2, Section 7, Section 8.4, Appendix A.1)
- `C013` (Abstract, Section 1, Section 4.3, Section 5.2, Section 7, Section 8.4)
- `C014` (Abstract, Section 1, Section 3.2, Section 5.1, Section 5.2, Appendix F)
- `C015` (Abstract, Section 1, Section 5.1, Section 5.2, Section 8.4)
- `C016` (Abstract, Section 1, Section 5.2, Section 7)
- `C017` (Abstract, Section 1, Section 4.3, Section 5.1, Section 5.2, Section 7, Section 8.4, Appendix A.1)
- `C018` (Section 1, Section 4.3, Section 5.2, Section 8.4, Appendix A.3)
- `C019` (Section 5.2, Appendix A.3)
- `C020` (Section 5.2, Appendix A.3)
- `C021` (Abstract, Section 2.2, Section 5.2)
- `C022` (Abstract, Section 2.2, Section 5.2)
- `C023` (Section 4.4, Section 5.1, Appendix F)
- `C024` (Section 5.1, Appendix E)
- `C025` (Abstract, Section 1, Section 4.1, Section 5.2, Section 5.3, Section 7)
- `C026` (Section 4.4, Section 5.1, Section 5.2, Section 7, Appendix F)
- `C027` (Abstract, Section 1, Section 4.4, Section 5.1, Section 5.2)
- `C028` (Abstract, Section 1, Section 5.1, Section 5.2, Section 7, Appendix A.1, Appendix F)
- `C029` (Section 2.2, Section 5.2)
- `C030` (Section 2.2, Section 5.2)
- `C031` (Section 4.4, Section 5.1, Section 7)
- `C032` (Section 6, Appendix B)
- `C033` (Section 6, Appendix B)
- `C034` (Section 3.2, Section 6, Appendix B)
- `C035` (Appendix B)
- `C036` (Section 6, Appendix B)
- `C037` (Section 6, Appendix C)
- `C038` (Section 6, Appendix C)
- `C039` (Section 6, Appendix C)
- `C040` (Section 6, Appendix C)
- `C041` (Section 6, Appendix C)
- `C042` (Section 6, Appendix C)
- `C043` (Section 6, Appendix C)
- `C044` (Section 6, Appendix C)
- `C045` (Section 6, Appendix C)
- `C046` (Section 6, Appendix C)
- `C047` (Section 6, Appendix C)
- `C048` (Section 6, Appendix C)
- `C049` (Section 6, Appendix D)
- `C050` (Appendix D)
- `C051` (Appendix D)
- `C052` (Appendix D)
- `C053` (Section 6, Appendix D)
- `C054` (Section 6, Appendix D)
- `C055` (Section 6, Appendix D)
- `C056` (Appendix D)
- `C057` (Section 6, Appendix D)
- `C058` (Section 6, Appendix D)
- `C059` (Section 6, Section 7, Appendix D)
- `C060` (Section 1, Section 4.5)
- `C061` (Section 1, Section 4.5, Section 5.1)
- `C062` (Section 4.1, Section 5.1, Section 5.3)
- `C063` (Section 5.2)
- `C064` (Section 4.4, Section 5.1)
- `C065` (Section 4.3, Section 5.2, Appendix A)
- `C066` (Abstract, Section 1, Section 4.2, Section 5.1, Section 5.3)
- `C067` (Section 1, Section 4.5, Appendix E)
- `C068` (Abstract, Section 1, Section 4.2, Section 5.2, Section 5.3, Section 9)

---

## Alternative Titles for the Researcher to Choose
1. *Beyond Independent Bernoulli Trials: Evaluating Multi-Trial Reliability and Failure Clustering in Autonomous LLM Tool Agents*
2. *When Greedy Decodes Diverge: Empirical Limits of pass^k Compounding on Multi-Hop Knowledge Benchmarks*
3. *Testing the pass^k Independence Assumption: Regimes of Consistency and Marginal Failure Concentration in LLM Agents*
