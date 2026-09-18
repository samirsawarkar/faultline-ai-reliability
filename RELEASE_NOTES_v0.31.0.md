## Highlights of Release v0.31.0

**FAULTLINE Phase 2 Milestone: Project P11 — Release Gate with Tolerance Bands**

This release marks the completion of **Project P11** (Active Release Gate with Tolerance Bands) by Samir Sawarkar (*FAULTLINE AI Reliability Engineering*).

Release v0.31.0 establishes an automated, empirically grounded release gate for model upgrades in autonomous multi-hop agents. Rather than evaluating candidate models against arbitrary point thresholds, P11 enforces tolerance bands derived from historical same-model serving variance, evaluated against a frozen SHA-256 content-addressed golden set and graded by a deterministic dual-condition oracle without subjective LLM judges. The release gate is fully integrated into continuous integration with zero-cost two-way stub drills on every push, and was validated through live candidate evaluations across three model rungs ($1.84 spend, $38.51 cumulative Phase 2 total).

---

### Executive Summary

1. **Why Bands, Not Point Thresholds**: Autonomous agents running at temperature 0.0 with pinned prompts still experience substantial cloud serving nondeterminism across days, infrastructure deployments, and provider gateway updates. Across five separate evaluations of the exact same production workhorse model (R2: `glm-5.3-flash`), pass rates on the 30 golden scenarios were $18/30 = 0.6000$, $21/30 = 0.7000$, $20/30 = 0.6667$, $24/30 = 0.8000$, and $26/30 = 0.8667$ (observed band $[0.6000, 0.8667]$, mean $0.7267$). A rigid point threshold (e.g., $\ge 0.75$) would fail a known-good production model on 3 of 5 historical runs purely due to serving noise. P11 replaces point thresholds with an empirical tolerance band:
   `PASS if candidate pass_rate >= (min_observed - 1/n_golden) AND malformed_rate <= (max_observed + 1/n_golden); FAIL if pass_rate < (min_observed - 3/n_golden); otherwise WARN.`
   With $n=30$, this sets $\text{PASS} \ge 0.5667$, $\text{FAIL} < 0.5000$, and $\text{malformed} \le 0.0333$ (at most 1 malformed call).
2. **Deterministic Golden Scenario Set**: A frozen benchmark of $n=30$ hard Tier-3 (5-hop) scenarios was selected from the canonical 350-scenario knowledge graph corpus (`golden.json`). The golden set is cryptographically pinned by its SHA-256 manifest hash `e79897ea42129ccd4fe38ce3e0a8f7ec0b321aa8be0f7a3899036f5148dcb06f`, ensuring immutable regression baselines across evaluations.
3. **Pinned Oracle Judge**: Candidate responses are evaluated exclusively by the frozen Day 1 deterministic dual-condition oracle (`oracle_check`). Correctness requires exact normalized answer string matching and cryptographically verified citation hashes against the frozen corpus (`84e6ff5907...`), eliminating uncalibrated, noisy LLM judges from the release pipeline.
4. **Single Source of Truth (`models.json`)**: All model metadata—including API identifiers, ladder rungs (R1–R6), gateway base URLs, context limits, and token pricing—has been consolidated into `faultline_p2/models.json` (consumed by `faultline_p2/config.py`). This establishes a unified catalog across all experimental harnesses and eliminates configuration drift.
5. **Live Candidate Upgrade Drill**: Conducted live release-gate evaluations across three candidate rungs under CEO authorization ($n=30$ scenarios each; total spend $1.8422 USD, 555,174 tokens total):
   - **R1** (`qwen/qwen3.7-flash`): Scored $7/30 = 0.2333$ (Wilson 95% CI $[0.1179, 0.4093]$) with 10 malformed tool calls (0.3333 rate) and 5 regressions against golden baselines. Verdict: **FAIL** ($0.2047 spend).
   - **R4** (`openai/gpt-5.6-luna`): Scored $8/30 = 0.2667$ (Wilson 95% CI $[0.1418, 0.4445]$) with 18 step-cap terminations (0.6000 rate) and 4 regressions. Verdict: **FAIL** ($1.4408 spend).
   - **R2 fresh** (`z-ai/glm-5.3-flash`): Scored $26/30 = 0.8667$ (Wilson 95% CI $[0.7032, 0.9469]$) with 0 malformed calls, 2 step-cap terminations, and 0 regressions. Verdict: **PASS** ($0.1967 spend).
6. **Continuous Integration Integration**: Automated gate verification is deployed in `.github/workflows/release-gate.yml`. On every push and pull request, the workflow runs a zero-cost two-way stub drill testing both gate acceptance (`stub:solver` $\rightarrow$ PASS, exit code 0) and gate rejection (`stub:wrong_answer` $\rightarrow$ FAIL, asserting exit code 2). Live paid sweeps execute on demand via manual workflow dispatch with explicit confirmation.

---

### Key Empirical Results: Release Gate Evaluation (Project P11)

Evaluated across the 30 golden Tier-3 scenarios against baseline band $[0.6000, 0.8667]$:

| Source / Candidate | Model | Role | $n$ | Passed | Pass Rate | Wilson 95% CI | Malformed | Primary Exit Mode | Regressions | Verdict | Spend |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `p06_k1` (Baseline) | `glm-5.3-flash` | P6 Trial 1 | 30 | 18 | 0.6000 | [0.423, 0.754] | 0 (0.0%) | Answered (18/30) | N/A | Baseline | N/A |
| `p06_k2` (Baseline) | `glm-5.3-flash` | P6 Trial 2 | 30 | 21 | 0.7000 | [0.521, 0.833] | 0 (0.0%) | Answered (21/30) | N/A | Baseline | N/A |
| `p06_k3` (Baseline) | `glm-5.3-flash` | P6 Trial 3 | 30 | 20 | 0.6667 | [0.488, 0.808] | 0 (0.0%) | Answered (20/30) | N/A | Baseline | N/A |
| `p12_a` (Baseline) | `glm-5.3-flash` | P12 Arm A | 30 | 24 | 0.8000 | [0.627, 0.905] | 0 (0.0%) | Answered (24/30) | N/A | Baseline | N/A |
| **R1 Candidate** | `qwen3.7-flash` | Fast Workhorse | 30 | 7 | 0.2333 | [0.118, 0.409] | 10 (33.3%) | Malformed (10/30) | 5 | **FAIL** | $0.2047 |
| **R4 Candidate** | `gpt-5.6-luna` | Frontier Anchor | 30 | 8 | 0.2667 | [0.142, 0.445] | 1 (3.3%) | Step Cap (18/30) | 4 | **FAIL** | $1.4408 |
| **R2 Fresh Live** | `glm-5.3-flash` | Cheap Workhorse | 30 | 26 | **0.8667** | [0.703, 0.947] | 0 (0.0%) | Answered (28/30) | 0 | **PASS** | $0.1967 |

---

### Included Release Assets

- 📊 **`projects/p11_release_gate/figure.png`** & **`figure.pdf`**: Publication-quality release gate chart comparing baseline sources, the observed R2 variance band, and candidate gate evaluations with Wilson 95% confidence intervals.
- 📦 **`projects/p11_release_gate/report_R1.json`**, **`report_R4.json`**, **`report_R2.json`**: Machine-readable gate evaluation reports recording verdicts, exact pass rates, malformed rates, per-scenario regressions, and token spend.
- 📦 **`projects/p11_release_gate/band.json`** & **`band_v1.json`**: Frozen tolerance band definitions, per-source pass/malformed rates, per-scenario historical agreement counts, and tolerance rule thresholds.
- 📦 **`projects/p11_release_gate/golden.json`**: The canonical 30-scenario golden evaluation set with SHA-256 manifest hash `e79897ea42129ccd4fe38ce3e0a8f7ec0b321aa8be0f7a3899036f5148dcb06f`.
- 📋 **`projects/p11_release_gate/DECISIONS.md`**: Architectural decision record documenting tolerance-band formulation, golden scenario selection, and gate CI design.
- 📋 **`projects/p11_release_gate/README.md`**: Comprehensive technical specification, gate algebra, and local reproduction instructions.
- ⚙️ **`.github/workflows/release-gate.yml`**: GitHub Actions release-gate workflow enforcing two-way stub drills on pull requests and manual execution for live candidate sweeps.

---

### One-Command Reproduction

```bash
make venv
make test          # Runs all 528 Phase 1 tests
make phase2-test   # Runs all 143 Phase 2 tests (P00-P08, P10, P11, P12, P13, P15, P16)
make p11 ARGS=--dry-run   # P11 cost estimation dry-run ($0 spend)
make p11-drill            # Run P11 CI release-gate stub drills (both pass & fail)
```

**Test Gate Verification:** 671 / 671 Unit/Integration tests passing (528 Phase 1 + 143 Phase 2). All pre-registered hypotheses tracked in `HYPOTHESES.md`.

---

### Limitations

1. **All-T3 Golden Set**: The golden evaluation set consists entirely of Tier-3 (5-hop) hard reasoning tasks. It stress-tests agents at the complexity ceiling but does not assess shallow single-hop retrieval or basic conversational performance.
2. **Single Trial ($k=1$) Execution**: Candidate gate evaluations run at $k=1$ trial per scenario under a hard 24-step cap (Amendment A-003). Multi-trial pass rate compounding ($\text{pass}^k$) and within-scenario failure clustering are not evaluated during the gate sweep.
3. **Band Derived from Single Model Baseline**: The baseline tolerance band $[0.6000, 0.8667]$ was fit from historical runs of `glm-5.3-flash` (R2). Alternative model families may possess distinct variance profiles and may require calibrated baseline bands.
4. **Noisy Regression Attribution on $n=30$**: With a 30-scenario golden set, individual per-scenario regression signals have wide binomial margins ($\pm 15\text{pp}$), making scenario-level regressions indicative diagnostic warnings rather than statistically definitive regressions.
5. **Upward Serving Drift on R2 Workhorse**: The live R2 fresh run achieved $26/30 = 0.8667$, exceeding the earlier P6 trials ($0.6000-0.7000$), reflecting provider-side optimizations or prompt cache hit advantages.
6. **Single-Threaded Execution in First Live Chain**: To ensure strict ledger serialization and eliminate rate-limiting contention during initial validation, candidate sweeps were executed sequentially in a single process chain before enabling multi-threaded concurrency.
