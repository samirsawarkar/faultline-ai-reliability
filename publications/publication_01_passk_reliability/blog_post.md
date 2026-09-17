# Multi-Trial Reliability and Failure Concentration in Multi-Hop AI Agents
*Grounding Collapse, Failure Taxonomy, and Evaluator Calibration*

**Samir Sawarkar** · *FAULTLINE AI Reliability Engineering* · September 2026

When engineers deploy autonomous tool-using language model agents in mission-critical pipelines, a standard assumption quietly underpins operational benchmarks: **compound independence**. That is, if an agent succeeds on a task with probability $\text{pass@1}$, its joint success rate across $k$ repeated independent trials is assumed to decay exponentially as:
$$\text{pass}^k = (\text{pass@1})^k$$

In this pre-registered study (Decision D-009, Project P06), we subjected this compounding assumption to rigorous empirical testing across 1,800 executed runs and 54.3 million tokens on a controlled multi-hop retrieval benchmark.

### The Research Question and Setting

We investigated whether repeated agent trials on fixed tasks behave as independent Bernoulli processes, or whether failures concentrate systematically on latent "hard" instances. To eliminate real-world confounding, our benchmark evaluates agents over a deterministic synthetic knowledge graph (300 documents, content hash pinned) across 150 reserved Tier-3 multi-hop scenarios requiring 4–5 hops. A deterministic dual-condition oracle requires both the exact factual answer string and citation of the canonical provenance document.

Two primary model tiers were evaluated:
- **R2 (`z-ai/glm-5.3-flash`):** A fast, tool-disciplined model achieving $\text{pass@1} = 0.6311$.
- **R4 (`openai/gpt-5.6-luna`):** A frontier model evaluated at $\text{pass@1} = 0.1489$ (as-run) and $0.1909$ (infrastructure-excluded).

All runs executed at greedy temperature 0.

### Honest Infrastructure and Protocol Disclosures

A credible evaluation requires full disclosure of test conditions:
1. **The Gateway Incident:** During R4 execution on 2026-09-11, upstream API gateway outages triggered client circuit breakers across two windows (14:42–14:45 UTC and 22:30–22:41 UTC). This caused 95 of 450 trials to drop out (87 with sub-millisecond latencies). A third rung, R6 (`deepseek/deepseek-v4-pro`), experienced 100% dead-at-start connection drops and was entirely invalidated. We report the pre-registered as-run data ($n=150$) and an infrastructure-excluded sensitivity cohort ($n=117$) side-by-side.
2. **The Two-Pass Protocol:** The SQLite telemetry reflects an exploratory first pass under step cap 12 followed by a final pass under step cap 24. Because terminal verdicts overwrite spans, all reported statistics are strictly isolated to final-pass spans using frozen timestamp boundaries.
3. **Pre-Registered Hypotheses H4 and H5:** Both pre-registered hypotheses required at least four valid rungs to test monotonic ordering and ranking. With only two rungs surviving infrastructure disruption, H4 and H5 are formally designated **NOT_TESTABLE_AS_PREREGISTERED**.

### Key Findings

1. **The Homogeneous Binomial Null Holds on R2:**
   On R2, observed joint reliability at $k=3$ was $\text{pass}^3 = 0.2267$ (34/150 scenarios), remarkably close to naive compounding $(\text{pass@1})^3 = 0.2514$ (a deviation of $\Delta_3 = -0.0247$). The concentration ratio $C_3 = \text{pass}^3 / (\text{pass@1})^3 = 0.9017$ encompasses 1.0 within its 95% bootstrap confidence interval $[0.7161, 1.0793]$. Pearson goodness-of-fit ($\chi^2 = 1.8919, \text{df}=2, p = 0.3794$) and Tarone's score test ($z = -0.655, p = 0.7438$) show no detectable departure from the independent Bernoulli null. Intra-scenario correlation is indistinguishable from zero ($\text{ICC} = -0.0287$).

2. **R4 Failure Clustering Is Driven by Infrastructure:**
   In as-run R4 data, measured $\text{pass}^3 = 0.0200$ (3/150) exceeded naive $0.0033$, yielding apparent overdispersion ($p = 0.0053$). However, excluding the 33 outage-affected scenarios ($n=117$) yields $\text{pass}^3 = 0.0256$ (3/117) versus naive $0.0070$. Tarone's overdispersion test attenuates to $z = 0.764$ ($p = 0.2224$), and $\text{ICC}$ attenuates to $0.0438$ ($[-0.0978, 0.1907]$). The apparent failure clustering is largely an artifact of external dropouts rather than intrinsic model intractability.

3. **Why $k=3$ Consistency Cannot License Deep Extrapolation:**
   While naive compounding holds within 2.5 percentage points at $k=3$, small unmeasured correlations amplify exponentially at greater depths. Under a beta-binomial compounding model, an upper-bound intra-scenario correlation of $\text{ICC} = 0.0668$ produces an expected concentration ratio of $C_8 \approx 2.25$ by $k=8$, where empirical reliability would be more than double the naive prediction. Short benchmarks cannot license deep unassisted compounding.

4. **Paired Comparisons:**
   In paired McNemar tests across identical scenario IDs, R2 significantly outperformed R4 on both Trial-1 accuracy ($+0.4467$ risk difference, $p = 5.92 \times 10^{-14}$) and All-3-Pass joint reliability ($+0.2067$ risk difference, $p = 1.23 \times 10^{-7}$). R2 achieved this reliability at $0.01796 USD per grounded pass versus $0.26825 USD for R4.

### Reproduction

All data, raw SQLite traces, spend ledgers, and deterministic analysis pipelines are open source:
```bash
make p06-analysis
python projects/p06_passk/make_figures.py
python publications/publication_01_passk_reliability/build_pdf.py
```