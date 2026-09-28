# Pre-Registration: Laya Trace Pre-Filter for `OVERCONSTRAINED_SEARCH_LOOP`

## 1. Objective & Hypothesis
This study evaluates whether the local open-source decision model **Laya** (`convaiinnovations/laya`, ModernBERT-large 421M, 512-token context) can serve as a zero-marginal-cost, high-reliability pre-filter for the `OVERCONSTRAINED_SEARCH_LOOP` failure mode.

In Project P5, zero-shot Laya achieved perfect recall on the held-out test split ($n=60$, 14 positives) with $\text{TPR} = 1.0000$ (14/14), but suffered from low specificity ($\text{TNR} = 0.3696$, 29 false positives out of 46 negatives), resulting in Cohen's $\kappa = 0.2148$. We hypothesize that:
1. Optimal probability threshold tuning on `train + dev` can increase TNR while preserving high sensitivity.
2. Direct RLCD task fine-tuning on `train` with dev calibration can produce a specialized model that clears the pre-registered operational gate.

---

## 2. Pre-Registered Success Criteria
A candidate evaluator is deemed **SUCCESSFUL** if and only if it achieves on the single-pass frozen test split ($n=60$, 14 positives, 46 negatives):

$$\text{TPR} \ge \frac{13}{14} \approx 0.9286 \quad \text{AND} \quad \text{TNR} \ge 0.8000$$

- **Target TPR**: $\ge 92.86\%$ (at most 1 false negative out of 14 ground-truth failure traces).
- **Target TNR**: $\ge 80.00\%$ (at least 37 true negatives out of 46 non-failure traces).
- Evaluation is executed **EXACTLY ONCE** per candidate on the test split.

---

## 3. Protocol & Split Discipline
Evaluation strictly follows the content-addressed manifest established in Project P5:
- **Manifest File**: [`projects/p05_judge/manifest.json`](../p05_judge/manifest.json)
- **Manifest SHA-256**: `7460de00a0ae4d5c4357937b895ed9e848ddcaf24fb6a373f0a20f14bca1bc02`
- **Human Ground Truth**: [`projects/p04_taxonomy/coding_sheet.csv`](../p04_taxonomy/coding_sheet.csv) (`axial_failure_mode == 'OVERCONSTRAINED_SEARCH_LOOP'`)
- **Data Splits**:
  - **Train Split**: $n=101$ (17 positives, 84 negatives)
  - **Dev Split**: $n=39$ (5 positives, 34 negatives)
  - **Test Split**: $n=60$ (14 positives, 46 negatives)

### Leakage Controls
1. **Train + Dev Only**: All threshold selection, hyperparameter tuning, model training, and post-training temperature calibration must use `train` and `dev` splits exclusively.
2. **Single-Pass Test Protocol**: The test split will be read at most **twice** across the entire project—once for each of the two pre-registered candidates:
   - **Candidate 1**: Base Laya with optimal threshold selected from `train + dev`.
   - **Candidate 2**: Fine-tuned Laya checkpoint trained on `train` and calibrated on `dev`.
3. **No Retuning on Test**: Test split outputs are final and immutable; no threshold adjustment, re-prompting, or iterative re-tuning on test metrics is permitted.

---

## 4. Evaluator Context & Rubric Parity
All candidates evaluate identical scenario representations imported directly from [`faultline_p2/judge/evaluators.py`](../../faultline_p2/judge/evaluators.py):
- **Rubric**: `OVERCONSTRAINED_SEARCH_RUBRIC`
- **State Representation**: `build_overconstrained_context(sid, spans, sweep_item, sc)`
- **Question Structure**: Native single `'noul'` question evaluated by Laya's non-autoregressive decision head.

---

## 5. Metrics & Reporting
Results will be recorded with full statistical rigor using [`faultline_p2/judge/metrics.py`](../../faultline_p2/judge/metrics.py):
- Confusion matrix: True Positives (TP), False Positives (FP), True Negatives (TN), False Negatives (FN).
- Sensitivity (TPR) and Specificity (TNR) with Wilson 95% score confidence intervals.
- Cohen's $\kappa$ agreement against human ground truth.
- Rogan-Gladen adjusted prevalence estimation.
- Explicit `PASS` / `FAIL` determination against Section 2 criteria.
