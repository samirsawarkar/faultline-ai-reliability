# Publication 01: Multi-Trial Agent Reliability and Compound Independence

This directory contains the complete publication package for the FAULTLINE Project P06 research paper.

## Paper Details

- **Title:** Multi-Trial Reliability and Failure Concentration in Multi-Hop AI Agents: Grounding Collapse, Failure Taxonomy, and Evaluator Calibration
- **Author:** Samir Sawarkar (`samir@faultline.ai`)
- **Target Venue:** arXiv / AI Evaluation Methodology Track
- **Status:** Complete & Reproducible

## Overview & Core Results

The paper investigates the foundational assumption of **compound independence** in autonomous tool-use evaluations: whether repeated independent executions on a task distribution compound as independent Bernoulli trials:
$$\text{pass}^k = (\text{pass@1})^k$$

Key findings include:
1. **Homogeneous Binomial Null Holds on R2:** On `glm-5.3-flash` ($n=150$), measured joint reliability at $k=3$ is $\text{pass}^3 = 0.2267$ vs naive $(\text{pass@1})^3 = 0.2514$ ($\Delta_3 = -0.0247, C_3 = 0.9017$, bootstrap CI $[0.7161, 1.0793]$). Pearson goodness-of-fit ($p=0.3794$), Tarone's score test ($z=-0.655, p=0.7438$), and $\text{ICC} = -0.0287$ confirm outcomes are indistinguishable from independent Bernoulli trials.
2. **Infrastructure Attenuation on R4:** On `gpt-5.6-luna`, as-run clustering was heavily driven by 95 dead trials caused by remote API gateway timeouts. In the sensitivity analysis excluding 33 affected scenarios ($n=117$), $\text{pass}^3 = 0.0256$ vs naive $0.0070$ ($\Delta_3 = +0.0187, C_3 = 3.6867$), and overdispersion attenuates to null ($z=0.764, p=0.2224, \text{ICC}=0.0438$).
3. **Pre-Registered Hypotheses:** H4 and H5 are formally marked **NOT_TESTABLE_AS_PREREGISTERED** due to surviving sample size (2 valid rungs rather than the pre-registered minimum of 4).
4. **Depth Extrapolation Warning:** Small correlations at $k=3$ amplify exponentially at higher depths ($C_8 \approx 2.25$ under beta-binomial compounding), demonstrating that $k=3$ consistency cannot license deep unassisted compounding.

## Directory Structure

- `paper.md`: Clean, publication-ready markdown paper (with artifact references and formatted bibliography).
- `paper.tex`: Standalone LaTeX paper formatted for arXiv (XeLaTeX, booktabs, graphicx).
- `paper.pdf`: Compiled 300 dpi publication PDF.
- `blog_post.md`: Executive summary blog post (≤ 900 words).
- `build_pdf.py`: Deterministic PDF compilation script via XeLaTeX.
- `fig_1_successes_per_scenario.png/.svg`: Observed vs Binomial(3, pass@1) expected histogram counts.
- `fig_2_passk_vs_naive.png/.svg`: Empirical pass^k vs naive (pass@1)^k for k=1,2,3.
- `fig_3_icc_extrapolation.png/.svg`: C_k extrapolation for k=1..10 from beta-binomial model.
- `fig_4_incident_timeline.png/.svg`: Per-trial terminal states over time during gateway incidents.
- `fig_B_p03_depth.png/.svg`: Reasoning depth pass@1 progression across T1, T2, T3.
- `fig_C_p04_taxonomy.png/.svg`: Axial failure mode prevalence across 9 categories.
- `fig_D_p05_kappa.png/.svg`: Cohen's kappa agreement for automated evaluators vs human labels.

## Deterministic Reproduction

To reproduce all analyses, regenerate figures, and build the paper PDF from scratch:

```bash
# 1. Run deterministic statistical analysis (trace.db -> analysis.json)
make p06-analysis

# 2. Generate all 7 publication figures (SVG and 300 dpi PNG)
python projects/p06_passk/make_figures.py

# 3. Compile the paper PDF via XeLaTeX
python publications/publication_01_passk_reliability/build_pdf.py
```