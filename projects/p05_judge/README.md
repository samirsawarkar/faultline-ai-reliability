# Project P5: Automated Judge Validation & Calibration

## Purpose
Project P5 validates automated binary evaluators against human ground-truth failure mode labels from Project P4 across a content-addressed Train / Dev / Test split. It computes diagnostic sensitivity (TPR), specificity (TNR), accuracy, precision, Cohen's $\kappa$ with Wilson 95% confidence intervals, and Rogan-Gladen prevalence adjustments, evaluating Pre-Registered Hypothesis **H3**.

---

## Architecture
- **Model**: `MODEL_R7="z-ai/glm-5.3"` (temperature=0.0)
- **Code Assertions**: Deterministic rule-based checkers for execution-level faults (`INFRASTRUCTURE_RATE_LIMIT`, `INFRASTRUCTURE_SERVER_ERROR`, `MALFORMED_TOOL_CALL`, `MULTI_HOP_TRAVERSAL_EXHAUSTION`).
- **LLM Judges**: Structured JSON prompt rubrics for semantic agent trajectory errors (`OVERCONSTRAINED_SEARCH_LOOP`, `RETRIEVAL_FAILURE_ABSTENTION`, `ANSWER_EXTRACTION_TRUNCATION`, `PREMATURE_STOP_WRONG_HOP`, `MULTI_HOP_DIRECTION_ERROR`).
- **Split Manifest**: Train (50%, $n=101$), Dev (20%, $n=39$), Test (30%, $n=60$). Single-pass test evaluation protocol.

---

## Quickstart

```bash
# Dry run cost estimation
make p05

# Execute validation on test split using live GLM-5.3 judge
make p05 ARGS="--confirm --real"

# Run offline regression test
make p05 ARGS="--confirm"

# Run automated unit tests
.venv/bin/python -m pytest tests/phase2/test_p05_judge.py -v
```

---

## Artifacts & Outputs
1. [`manifest.json`](manifest.json): Content-addressed dataset split (SHA-256 attested).
2. [`results.json`](results.json): Full evaluation metrics, confusion matrices, Wilson CIs, Rogan-Gladen prevalence, and H3 hypothesis status.
3. [`figure.svg`](figure.svg): Publication-grade SVG visualization of Cohen's $\kappa$ agreement across all 9 failure modes against the $H_3$ threshold ($\kappa \ge 0.70$).
4. [`DECISIONS.md`](DECISIONS.md): Architectural decisions, evaluator prompts, error analysis, and H3 resolution.
5. [`ledger.jsonl`](ledger.jsonl): Append-only spend ledger for P5 judge calls.
