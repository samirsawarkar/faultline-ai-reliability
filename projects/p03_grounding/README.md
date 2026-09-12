# Project P3 — Grounding Zero-Point

Measures empirical grounded pass rates across multi-hop difficulty tiers (T1 = 1 hop, T2 = 3 hops, T3 = 5 hops) over the $N=200$ standard pool scenarios across **three distinct model rungs**:
1. **Model 1 (R2 Cheap Workhorse)**: `z-ai/glm-5.3-flash` ($0.075 / $0.25 per 1M tokens)
2. **Model 2 (R4 Frontier OpenAI)**: `openai/gpt-5.6-luna` ($0.200 / $0.60 per 1M tokens)
3. **Model 3 (R6 Frontier Anchor)**: `deepseek/deepseek-v4-pro` ($0.435 / $0.87 per 1M tokens)

Evaluates Hypothesis **H1** (grounded pass rate degradation on T3 vs simulator baseline) and establishes the content-addressed dataset manifest freezing the 150-scenario reserved hard subset for P6.

---

## Quickstart

### 1. Dry Run (Cost Estimate & Manifest Verification)
```bash
make p03
# or: .venv/bin/python projects/p03_grounding/run.py
```

### 2. Offline Deterministic Verification (Solver Stub, $0 Spend)
```bash
.venv/bin/python projects/p03_grounding/run.py --confirm
```

### 3. Live Three-Model Execution (AICredits / R2 + R4 + R6)
```bash
# Run all 3 models across all 200 standard scenarios
.venv/bin/python projects/p03_grounding/run.py --confirm --real --rung all --concurrency 5

# Or run a specific rung
.venv/bin/python projects/p03_grounding/run.py --confirm --real --rung R2
.venv/bin/python projects/p03_grounding/run.py --confirm --real --rung R4
.venv/bin/python projects/p03_grounding/run.py --confirm --real --rung R6
```

---

## Artifacts Produced

- `manifest.json`: Content-addressed scenario split definitions (200 standard + 150 reserved hard).
- `results.json`: Empirical pass@1, tier breakdowns (T1/T2/T3), average steps/tokens, Wilson 95% confidence intervals, and 3-way cross-model comparison deltas.
- `figure.svg`: Publication-quality grouped bar chart comparing R2 vs R4 vs R6 vs Day 3 simulator baseline.
- `trace.db`: SQLite database storing step-level telemetry, tool calls, and execution spans for all models.
- `ledger.jsonl`: Append-only USD cost and token usage log.
- `DECISIONS.md`: Methodological decisions, dataset partitioning criteria, and H1 evaluation.
