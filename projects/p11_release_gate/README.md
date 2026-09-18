# P11 — Release Gate: Calibrated Model Deployment Verification

## Executive Summary
A model update cannot ship on uncalibrated exact thresholds: identical deterministic configurations of the cheap workhorse (`z-ai/glm-5.3-flash`, R2) vary between **60.0%** and **86.7%** pass rate across test dates and sweeps due to upstream provider inference drift. Exact pass-rate thresholds cause false rejections and false flaking.

Project P11 builds a calibrated **Release Gate** designed not to flake:
1. **Stable Golden Set ($n=30$)**: Content-addressed selection from the reserved hard-pool scenarios, pinned by SHA-256 manifest.
2. **Tolerance Band Across Historical Replicates**: Tolerance bounds derived from empirical run-to-run variance across 5 independent R2 sweeps on the golden set.
3. **Deterministic Oracle Judge**: MEC-pinned ground-truth oracle judge (`faultline_p2/oracle/_day01_oracle.py`); rejects uncalibrated LLM evaluators (P5 showed Cohen's $\kappa \approx 0$).
4. **$0 CI Verification & Safe Live Deployment**: Stub drills (`stub:solver` $\to 0$, `stub:wrong_answer` $\to 2$) run on every pull request at $0 spend; live candidate runs require manual workflow dispatch with explicit budget confirmation (`--confirm`).

---

## Why Bands Instead of Exact Thresholds
Evaluating identical prompts at temperature 0.0 with `z-ai/glm-5.3-flash` across 5 independent evaluation sweeps on the 30 golden scenarios reveals substantial empirical variation:
- **P6 pass^k Trial 1 (`p06_k1`)**: 18/30 = **60.00%** (0 malformed)
- **P6 pass^k Trial 2 (`p06_k2`)**: 21/30 = **70.00%** (0 malformed)
- **P6 pass^k Trial 3 (`p06_k3`)**: 20/30 = **66.67%** (0 malformed)
- **P12 Attribution Arm A (`p12_a`)**: 24/30 = **80.00%** (0 malformed)
- **P11 Live Candidate Run (`p11_r2_fresh`)**: 26/30 = **86.67%** (0 malformed)

An exact threshold set at 75% would arbitrarily fail 3 out of 5 valid baseline deployments of the identical model, while a 65% threshold would fail Trial 1. The tolerance band accommodates this empirical drift while enforcing hard regression and malformation bounds.

---

## Golden Scenario Set & Manifest
The golden test suite consists of $n=30$ scenarios selected deterministically by hashing scenario IDs from the 150 reserved hard-pool 5-hop tasks (`r-0201` to `r-0350`):
$$\text{rank}(\text{sid}) = \text{sha256}(\text{sid})$$
The first 30 ranked scenarios are selected and frozen in `golden.json`:
- **Scenario Count**: $n = 30$
- **Manifest SHA-256**: `e79897ea42129ccd4fe38ce3e0a8f7ec0b321aa8be0f7a3899036f5148dcb06f`
- **Tiers**: 100% Tier 3 (5-hop hard retrieval & synthesis chains)

---

## Pinned Deterministic Oracle Judge
Evaluations use the pure, deterministic ground-truth oracle (`faultline_p2/oracle/_day01_oracle.py`), SHA-256 pinned in MEC. LLM-as-a-judge was explicitly excluded: Project P5 established that LLM judge evaluators exhibit near-zero agreement (Cohen's $\kappa \approx 0$) with ground truth on multi-hop entity grounding, introducing subjective variance that invalidates release gating.

---

## Tolerance Rule
From `band.json` verbatim:
> **PASS** if candidate `pass_rate` $\ge (\text{min\_observed} - 1/n_{\text{golden}})$ AND `malformed_rate` $\le (\text{max\_observed} + 1/n_{\text{golden}})$;  
> **FAIL** if `pass_rate` $< (\text{min\_observed} - 3/n_{\text{golden}})$;  
> otherwise **WARN**.

Parameters for $n=30$ on baseline min pass 0.6000, max malformed 0.0000:
- **One scenario of slack**: $1/30 \approx 0.0333$
- **Three scenarios of slack**: $3/30 = 0.1000$
- **PASS Pass-Rate Threshold**: $\ge 0.6000 - 0.0333 = \mathbf{0.5667}$
- **FAIL Pass-Rate Threshold**: $< 0.6000 - 0.1000 = \mathbf{0.5000}$
- **Max Malformed Threshold**: $\le 0.0000 + 0.0333 = \mathbf{0.0333}$

---

## Results Table: Candidate Evaluations

| Candidate Model | Role | Pass Count | Pass Rate | 95% Wilson CI | Malformed | Step Cap | Regressions | Verdict | Exit Code | Spend (USD) |
|---|---|---|---|---|---|---|---|---|---|---|
| **R1** `qwen/qwen3.7-flash` | Entry Tier | 7/30 | 23.33% | [11.79%, 40.93%] | 10/30 (33.3%) | 4/30 | 5 | **FAIL** | 2 | $0.2047 |
| **R4** `openai/gpt-5.6-luna` | Frontier Tier | 8/30 | 26.67% | [14.18%, 44.45%] | 1/30 (3.3%) | 18/30 (60.0%) | 4 | **FAIL** | 2 | $1.4408 |
| **R2** `z-ai/glm-5.3-flash` (fresh) | Current Workhorse | 26/30 | 86.67% | [70.32%, 94.69%] | 0/30 (0.0%) | 2/30 | 0 | **PASS** | 0 | $0.1967 |

### Detailed Findings
- **R1 Failure Mode**: R1 collapsed primarily on contract compliance, emitting 10 malformed tool calls (33.3% malformed rate vs 3.3% tolerance ceiling). Pass rate (23.33%) fell deep into the FAIL zone ($< 50.0\%$).
- **R4 Failure Mode**: R4 failed not on syntax (only 1 malformed), but on looping: 18 out of 30 runs (60.0%) exhausted the 24-step cap without answering. Pass rate (26.67%) triggered a hard FAIL.
- **R2 Fresh Validation**: Fresh live R2 scored 26/30 (86.67%), outperforming historical baselines (previous maximum 80.0%), with 0 malformed responses and 0 regressions against baselines.
- **Regressions List**:
  - R1 regressions (scenarios passed by all baselines that R1 failed): `r-0292`, `r-0318`, `r-0344`, `r-0349`, `r-0307`.
  - R4 regressions: `r-0216`, `r-0292`, `r-0344`, `r-0322`.
- **Project Economics**: Total sweep spend was **$1.8422 USD** against the pre-registered $5.00 budget ceiling ($3.1578 remaining).

---

## CI Stub Drills & Automation
Workflow [`.github/workflows/release-gate.yml`](file:///.github/workflows/release-gate.yml) implements two jobs:
1. `gate-stub` (Runs on every `push` and `pull_request` at **$0**):
   - Drill 1: `run.py --model stub:solver --band band_stub.json` $\to$ expects **PASS** (exit 0).
   - Drill 2: `run.py --model stub:wrong_answer --band band_stub.json` $\to$ asserts **FAIL** (exit 2).
2. `gate-live` (Manual `workflow_dispatch` only):
   - Takes inputs `rung` (default R2) and `confirm` (boolean).
   - Evaluates candidate against `band.json` and uploads `report.json` as an artifact.

---

## Centralized Model Ladder & Technical Debt
- **Single Source of Truth**: [`faultline_p2/models.json`](file:///Volumes/SamirDrive/Development/FAULTLINE/faultline_p2/models.json) defines rungs R1–R6, model identifiers, providers (`aicredits`), and prices. [`faultline_p2/config.py`](file:///Volumes/SamirDrive/Development/FAULTLINE/faultline_p2/config.py) loads `MODEL_LADDER` directly from this JSON.
- **Tracked Technical Debt**: Prior runners (`projects/p06_passk/run.py` and `projects/p12_attribution/run.py`) maintain duplicate inline `RUNG_CONFIG` / `DEFAULT_RUNGS` dictionaries. These remain untouched per phase isolation rules and should be consolidated in a future cleanup.

---

## Limitations
1. **Hard Pool Representation**: The golden scenario set is drawn exclusively from Tier 3 (5-hop hard pool). Tier 1 and Tier 2 are not represented because only the hard pool had four prior independent R2 replicate runs under the identical 24-step cap to build a multi-sweep variance band.
2. **Single Pass ($k=1$)**: Candidate runs evaluate each golden scenario once. Multi-trial pass@k variance is captured in the baseline band rather than per-candidate runs.
3. **Single Model Baseline Family**: Historical variance is measured entirely from `z-ai/glm-5.3-flash`. Cross-architecture tolerance bands would require multi-run historical sweeps for each candidate architecture.
4. **Sample Size Granularity ($n=30$)**: At $n=30$, each scenario represents $3.33\%$ pass rate. Per-scenario regression lists are informative but subject to binomial noise.
5. **Gateway Upward Drift**: The fresh R2 candidate achieved 86.67%, exceeding the previous four baselines (60.0%–80.0%). While fully passing, it highlights continued provider-side model updates.

---

## Reproduce

```bash
# 1. Rebuild golden manifest and tolerance band v2
.venv/bin/python projects/p11_release_gate/build_band.py

# 2. Run CI $0 stub drills
.venv/bin/python projects/p11_release_gate/run.py --model stub:solver --band projects/p11_release_gate/band_stub.json
.venv/bin/python projects/p11_release_gate/run.py --model stub:wrong_answer --band projects/p11_release_gate/band_stub.json

# 3. Dry-run cost estimation (no API calls, no spend)
.venv/bin/python projects/p11_release_gate/run.py --model R2 --golden projects/p11_release_gate/golden.json --band projects/p11_release_gate/band.json --dry-run

# 4. Generate publication figure (SVG, 2x PNG, 1-page PDF)
.venv/bin/python projects/p11_release_gate/make_figure.py

# 5. Live candidate evaluation (paid, requires --confirm)
# .venv/bin/python projects/p11_release_gate/run.py --model R2 --golden projects/p11_release_gate/golden.json --band projects/p11_release_gate/band.json --concurrency 4 --confirm --report report_R2.json
```
