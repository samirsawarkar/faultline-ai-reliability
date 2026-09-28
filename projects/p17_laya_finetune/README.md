# Project P17: Laya Fine-Tuning & Pre-Filter Calibration

Local preparation and fine-tuning pipeline to test whether the local open-source decision model **Laya** (`convaiinnovations/laya`, ModernBERT-large 421M) can become an effective zero-cost trace pre-filter for `OVERCONSTRAINED_SEARCH_LOOP`.

---

## 1. Overview & Protocol
In Project P5, zero-shot Laya showed high sensitivity ($\text{TPR} = 1.00$) but high false positive rates ($\text{TNR} = 0.37$) on the held-out test split. Project P17 tests two mitigation paths:
1. **Candidate 1 (Tuned Threshold)**: Optimal decision threshold selected strictly on `train + dev` (preserving $\text{TPR} = 1.0$).
2. **Candidate 2 (Fine-Tuned Checkpoint)**: RLCD fine-tuned ModernBERT model trained on `train.jsonl` and calibrated on `dev.jsonl` using Kaggle 2x T4 GPUs.

Both candidates are governed by [`PREREG.md`](PREREG.md): Success requires **$\text{TPR} \ge 13/14$ ($92.86\%$)** AND **$\text{TNR} \ge 0.80$ ($80.00\%$)** on the single-pass test split.

---

## 2. Local Preparation Scripts
From the repository root:

```bash
# 1. Evaluate base model on train+dev to select optimal threshold
.venv/bin/python projects/p17_laya_finetune/threshold.py

# 2. Export train.jsonl (101 cases) and dev.jsonl (39 cases)
.venv/bin/python projects/p17_laya_finetune/export_data.py
```

---

## 3. Kaggle Fine-Tuning Instructions (Step-by-Step)

Follow these exact steps to fine-tune on Kaggle's free dual T4 GPUs without network API keys or Hub tokens:

1. **Upload Dataset:**
   - On [Kaggle](https://www.kaggle.com/), click **Create** $\rightarrow$ **New Dataset**.
   - Upload `projects/p17_laya_finetune/train.jsonl` and `projects/p17_laya_finetune/dev.jsonl`.
   - Name the dataset `faultline-p17-data` and create it.

2. **Create Notebook:**
   - Click **Create** $\rightarrow$ **New Notebook**.
   - In the top menu: **File** $\rightarrow$ **Import Notebook** $\rightarrow$ select `projects/p17_laya_finetune/kaggle_finetune.ipynb`.

3. **Configure Hardware:**
   - In the right-hand settings panel:
     - **Accelerator**: Select **`GPU T4 x2`**.
     - **Internet**: Toggle to **`On`**.

4. **Attach Dataset:**
   - In the right panel under **Input**, click **Add Data** and select your `faultline-p17-data` dataset.

5. **Execute Training:**
   - Click **Run All**.
   - Training runs multi-GPU Distributed Data Parallel (`torchrun --standalone --nproc_per_node=2`) and completes in ~4–6 minutes.
   - Temperature calibration is automatically fitted on `dev.jsonl`.

6. **Download Artifact:**
   - In the right panel under **Output**, download the folder `/kaggle/working/laya_finetuned_overconstrained`.

---

## 4. Test Split Evaluation (Single-Pass Protocol)

Once threshold tuning or fine-tuning is complete, evaluate on the held-out test split ($n=60$) once:

```bash
# Evaluate tuned-threshold base model:
.venv/bin/python projects/p17_laya_finetune/eval_test.py --threshold <TAU> --confirm

# Evaluate downloaded fine-tuned checkpoint:
.venv/bin/python projects/p17_laya_finetune/eval_test.py --checkpoint /path/to/laya_finetuned_overconstrained --confirm
```

---

## 5. Results

The fine-tuned model was trained on Kaggle 2xT4 for 6 epochs, with calibration temperature `noul=4.486` fitted on dev. A decision threshold of `0.282` was chosen from train+dev only (the lowest positive probability on dev) BEFORE the single test read.

### Test Split Evaluation (Single-Pass)

Evaluating on the frozen test split ($n=60$: 14 positives, 46 negatives) yielded:
- **Confusion Matrix**: TP 13, FP 2, TN 44, FN 1
- **Sensitivity (TPR)**: 0.9286 (Wilson 95% CI: 0.685–0.987)
- **Specificity (TNR)**: 0.9565 (Wilson 95% CI: 0.855–0.988)
- **Cohen's $\kappa$**: 0.864
- **PREREG Status**: **PASS** (met TPR $\ge 13/14$ and TNR $\ge 0.80$)

### Comparison

| Evaluator / Candidate | Split | Threshold $\tau$ | TP | FP | TN | FN | TPR (Recall) | TNR (Specificity) | Cohen's $\kappa$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Fine-tuned Laya (Candidate 2)** | **Test ($n=60$)** | **0.282** | **13** | **2** | **44** | **1** | **0.9286** | **0.9565** | **0.864** |
| Base Laya (P5 baseline) | Test ($n=60$) | 0.500 | 14 | 29 | 17 | 0 | 1.0000 | 0.3696 | 0.2148 |
| Base Laya best threshold | Train+Dev ($n=140$) | 0.635 | 21 | 48 | 70 | 1 | 0.9545 | 0.5932 | 0.2931 |

*(Note: Base Laya at $\tau=0.635$ was tuned on train+dev and never run on test).*

### Limitations

- **TPR Floor**: TPR sits exactly at the pre-registered floor with $n=14$ positives (13/14 caught; one false negative).
- **Single Failure Mode**: One failure mode (`OVERCONSTRAINED_SEARCH_LOOP`) evaluated.
- **Synthetic Distribution**: Synthetic in-distribution traces only.
- **Probability Compression**: At the notebook's default 0.5 threshold the fine-tuned model flags nothing because calibration compresses probabilities.

---

Checkpoint: private Kaggle model https://www.kaggle.com/models/samirsawarkar/faultline-laya-searchloop (instance p17-v1, 807 MB; not in git). Load with laya.load(path); use threshold 0.282.
