# P1 Baseline

Measures grounded pass rates across T1, T2, T3 using the standard corpus pool (100 scenarios).

## Dry Run (Cost Estimate Only)
To inspect the cost estimate without spending:
```bash
make p01
# or: .venv/bin/python projects/p01_baseline/run.py
```

## Real Run (Execution)
To execute the dress rehearsal sweep with the stub model:
```bash
.venv/bin/python projects/p01_baseline/run.py --confirm
```

On spend day, to execute against the live model (LiteLLM / deepseek-v4-flash):
```bash
.venv/bin/python projects/p01_baseline/run.py --confirm --real
```
This generates `results.json` and `figure.svg`.
