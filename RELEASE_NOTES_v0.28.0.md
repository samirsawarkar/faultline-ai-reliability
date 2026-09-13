## Highlights of Release v0.28.0

**FAULTLINE Phase 2 Milestone: Publication #1 & Project P6 Joint Reliability Evaluation**

This release marks the public launch of **Publication #1**:  
**"The Illusion of Compound Independence: Grounding Collapse, Human-in-the-Loop Taxonomy, and Failure Concentration in Multi-Hop AI Agents"**  
by Samir Sawarkar (*FAULTLINE AI Reliability Engineering & Antigravity Research*).

---

### Executive Summary

Contemporary evaluations of autonomous tool-use agents frequently rely on the foundational assumption of **compound independence**—namely, that repeated independent trials on a task distribution behave as independent Bernoulli processes whose joint multi-trial reliability decays exponentially according to naive compounding:
$$\text{pass}^k = (\text{pass@1})^k$$

Across **2,700+ agent executions**, **25,477 logged telemetry spans**, and 3 distinct foundation model rungs (**R2 `glm-5.3-flash`**, **R4 `gpt-5.6-luna`**, and **R6 `deepseek-v4-pro`**) evaluated on a deterministic 300-entity graph environment under Master Evaluation Contract (MEC) v1.3, we report five primary empirical findings:

1. **Regime-Dependent Failure Dynamics**: We falsify universal naive compounding $(\text{pass@1})^k$ and prove that failure concentration is strictly **regime-dependent**. In low-accuracy frontier regimes (R4, $\text{pass@1} = 14.89\%$), agent success is tightly concentrated on a tractable scenario core, exhibiting a **$6.06\times$ failure concentration ratio** ($\text{pass}^3 = 2.00\%$ $[0.68\%, 5.71\%]$ strictly disjoint from naive $0.33\%$). In disciplined, high-accuracy regimes (R2, $\text{pass@1} = 63.11\%$), errors compound as independent stochastic trials ($\text{pass}^3 = 22.67\%$ vs naive $25.14\%$).
2. **The Economic Workhorse Inversion**: Smaller, tool-disciplined models ($R2, \text{glm-5.3-flash}$) outperformed high-cost frontier reasoning models ($R4, \text{gpt-5.6-luna}$) by **$+20.67\text{ pp}$** on joint reliability ($p = 8.14 \times 10^{-7}$, McNemar paired test) while achieving an **$18.3\times$ cost reduction** per grounded answer ($\$0.0147$ vs $\$0.268$).
3. **Grounding Collapse Across Graph Depth**: Single-hop fact retrieval ($T1$) exhibits robust reliability ($\text{pass@1} = 100.0\%$), but 5-hop knowledge traversals ($T3$) experience catastrophic grounding collapse ($7.58\%$ under tight step limits), wherein agents emit plausible surface answers supported by fabricated or incomplete provenance.
4. **The Human-in-the-Loop Taxonomy Gap**: Rigorous open and axial coding of $n=200$ real agent execution traces by human researchers identified 8 distinct failure modes, including 4 emergent structural pathologies (`MULTI_HOP_DIRECTION_ERROR`, `OVERCONSTRAINED_SEARCH_LOOP`, `MULTI_HOP_TRAVERSAL_EXHAUSTION`, `RETRIEVAL_FAILURE_ABSTENTION`) that do not exist in standard synthetic perturbation benchmarks (`F1`–`F6`).
5. **LLM Judge Calibration Fragility**: Automated LLM judges evaluated on held-out test splits ($n=60$) failed to identify subtle search pathologies ($\kappa = -0.04$), while test splits with zero positive instances produced deceptive agreement scores ($\kappa = 1.00$). Uncalibrated LLM judges cannot substitute for deterministic code assertions and **Rogan-Gladen prevalence correction**.

---

### Included Release Assets

- 📄 **`paper.pdf`**: Complete research paper publication (1.6 MB, PDF) with formal proofs, methodology, and empirical curves.
- 📘 **`FAULTLINE_AI_Reliability_Engineering_Case_Study.pdf`**: Comprehensive 40-page case study and architecture record (878 KB, PDF).
- 📊 **`figure_cost_vs_passk.png`**: Empirical Pareto frontier showing Joint Reliability ($\text{pass}^3$) vs Cost per Grounded Answer.
- 🗺️ **`figure_overview.jpg`**: End-to-end experimental framework and multi-hop traversal setting.
- 🖼️ **`poster_image.png`**: Full high-resolution research poster summary.
- 📦 **`p06_results.json`**, **`p05_results.json`**, **`p04_results.json`**: Machine-readable raw benchmark data and metric intervals.

---

### Cryptographic Verification & Pre-Registration

| Layer | Contract / File | SHA-256 Digest |
|---|---|---|
| **Evaluation Contract** | `MEC.md` (v1.3) | `2c9a41de9103e839210086bbcf28c460cf2b2b1d64c0dbd0658a529cc5ce4d33` |
| **Hypothesis Ledger** | `HYPOTHESES.md` | `a1098bfe710328dc4357937b895ed9e848ddcaf24fb6a373f0a20f14bca1bc02` |
| **Knowledge Graph** | `projects/_corpus/corpus.json` | `84e6ff590704aa94d10912f8002716b14c7436080e1a3270b53f9385dc728efc` |
| **Hard Pool Manifest** | `projects/p06_passk/manifest.json` | `7e0a1b79d6e756f712d27e29168fed8b3bc5c4cd7beba7f8fc21d50366d41b83` |

---

### One-Command Reproduction

To verify all test suites and regenerate benchmark evidence:

```bash
git clone https://github.com/samirsawarkar/faultline-ai-reliability.git
cd faultline-ai-reliability
make venv
make test       # Runs all 528 Phase 1 tests
make phase2-test # Runs all 86 Phase 2 tests (P00-P06)
make p06        # Reproduces P6 pass^k decay results and figures
```

**Test Gate Verification:** 614 / 614 Unit/Integration tests passing (528 Phase 1 + 86 Phase 2). All 20 audit rows in Section 31 evidence index strictly verified.
