# Project P6: Pass^k Decay & Failure Concentration

## Purpose
Project P6 empirically evaluates multi-trial joint reliability ($\text{pass}^k$) and failure concentration dynamics across 3 representative model tiers on the 150 reserved hard-pool scenarios (`r-0201` to `r-0350`, all Tier 3 5-hop challenges). It tests whether agent failures concentrate on specific intractable scenarios ($\text{pass}^k > (\text{pass@1})^k$) or compound independently under repeated trials, evaluating Pre-Registered Hypotheses **H4** and **H5**.

---

## Evaluated Model Rungs
1. **Rung R2 (Cheap Workhorse)**: `z-ai/glm-5.3-flash`
2. **Rung R4 (OpenAI Frontier)**: `openai/gpt-5.6-luna`
3. **Rung R6 (Frontier Anchor)**: `deepseek/deepseek-v4-pro`

---

## Protocol & Experimental Design
- **Hard Pool**: 150 held-out Tier 3 5-hop scenarios ($n=150$).
- **Trial Multiplicity**: $k=3$ independent trials per scenario ($450$ runs per model; $1,350$ total runs).
- **Environment**: Phase 2 multi-hop graph environment with $T_{\max} = 24$ step budget per MEC v1.3 (Amendment A-003).
- **Metrics**: $\text{pass@1}$ (Wilson 95% CI), naive compounding prediction $(\text{pass@1})^3$, empirical joint reliability $\text{pass}^3$ (Wilson 95% CI), paired McNemar tests with declared statistical power annotations per MEC v1.0.

---

## Quickstart & Execution

```bash
# Dry run cost estimation & parameter check
make p06

# Execute full live multi-model sweep (1,350 runs across R2, R4, R6)
make p06 ARGS="--confirm --real --step-cap 24"

# Recompile results and figure directly from SQLite trace storage
.venv/bin/python projects/p06_passk/run.py --recompile

# Run P6 unit and integration tests
.venv/bin/python -m pytest tests/phase2/test_p06_passk.py -v
```

---

## Artifacts & Outputs
1. [`manifest.json`](manifest.json): Content-addressed hard-pool scenario manifest (SHA-256 attested).
2. [`results.json`](results.json): Measured $\text{pass@1}$, $(\text{pass@1})^3$, empirical $\text{pass}^3$, Wilson 95% CIs, McNemar paired comparisons, and H4/H5 hypothesis statuses.
3. [`figure.svg`](figure.svg): Publication-grade SVG chart illustrating naive compounding vs. empirical $\text{pass}^3$ curves across model rungs.
4. [`trace.db`](trace.db): SQLite database containing all 25,477 logged tool-use spans across the agent runs.
5. [`ledger.jsonl`](ledger.jsonl): Append-only token and spend accounting ledger ($23.73 USD spent of $45.00 USD cap).
6. [`DECISIONS.md`](DECISIONS.md): Architectural decisions, statistical power analysis, empirical findings, and hypothesis resolutions.
