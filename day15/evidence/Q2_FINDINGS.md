# Q2 — Detection accuracy per fault (dataset `de5068d574cae9fd`, split=`all`, n=44)

Measured against injection truth. Read **per class** — the aggregate below is shown only to demonstrate what it hides.

## Per-class confusion + 95% Wilson intervals

| Fault | TP | FP | FN | TN | recall | recall 95% CI | precision | precision 95% CI |
|---|---|---|---|---|---|---|---|---|
| F1 | 4 | 0 | 2 | 3 | 0.666667 | [0.3, 0.9032] | 1.0 | [0.5101, 1.0] |
| F2 | 2 | 0 | 4 | 3 | 0.333333 | [0.0968, 0.7] | 1.0 | [0.3424, 1.0] |
| F3 | 2 | 0 | 2 | 3 | 0.5 | [0.15, 0.85] | 1.0 | [0.3424, 1.0] |
| F4 | 2 | 0 | 0 | 3 | 1.0 | [0.3424, 1.0] | 1.0 | [0.3424, 1.0] |
| F5 | 2 | 0 | 2 | 3 | 0.5 | [0.15, 0.85] | 1.0 | [0.3424, 1.0] |
| F6 | 4 | 0 | 0 | 3 | 1.0 | [0.5101, 1.0] | 1.0 | [0.5101, 1.0] |

## Deterministic vs semantic groups

| Group | recall | recall 95% CI | FP | FN |
|---|---|---|---|---|
| deterministic (F2, F4, F6) | 0.666667 | [0.3906, 0.8619] | 0 | 4 |
| semantic (F1, F3, F5) | 0.571429 | [0.3259, 0.7862] | 0 | 6 |

## What the aggregate hides

- **micro recall** (all samples pooled): **0.615385**
- **macro recall** (mean of per-class): **0.6667**
- per-class recall: `{'F1': 0.666667, 'F2': 0.333333, 'F3': 0.5, 'F4': 1.0, 'F5': 0.5, 'F6': 1.0}`

The single micro number would let a reader believe detection is uniform. It is not: recall ranges across families, and the difference between micro and macro is the fingerprint of that imbalance.

## False positives / false negatives (nothing hidden)

- false positives: **0**
- false negatives: **10** (irreducible semantic escapes: 4, threshold-reducible: 6)
- reconciled (failures listed == FP+FN): **True**

### Each failing example (with trace)

| Sample | Fault | kind | sev | outcome | why | trace |
|---|---|---|---|---|---|---|
| `9a67ac6bf805e205` | F1 | corrupt | 1 | FN | threshold-reducible: the fault is below the detector's threshold (schema value range / latency budget); tightening it would catch this | [`evidence/traces/9a67ac6bf805e205.json`](evidence/traces/9a67ac6bf805e205.json) |
| `71c9339cd68dd487` | F1 | corrupt | 1 | FN | threshold-reducible: the fault is below the detector's threshold (schema value range / latency budget); tightening it would catch this | [`evidence/traces/71c9339cd68dd487.json`](evidence/traces/71c9339cd68dd487.json) |
| `6b4f1a7ebe7525de` | F2 | latency | 1 | FN | threshold-reducible: the fault is below the detector's threshold (schema value range / latency budget); tightening it would catch this | [`evidence/traces/6b4f1a7ebe7525de.json`](evidence/traces/6b4f1a7ebe7525de.json) |
| `ef8e08b532d42f96` | F2 | latency | 1 | FN | threshold-reducible: the fault is below the detector's threshold (schema value range / latency budget); tightening it would catch this | [`evidence/traces/ef8e08b532d42f96.json`](evidence/traces/ef8e08b532d42f96.json) |
| `04824a5f7eff2e74` | F2 | latency | 3 | FN | threshold-reducible: the fault is below the detector's threshold (schema value range / latency budget); tightening it would catch this | [`evidence/traces/04824a5f7eff2e74.json`](evidence/traces/04824a5f7eff2e74.json) |
| `97e1d283878d41f1` | F2 | latency | 3 | FN | threshold-reducible: the fault is below the detector's threshold (schema value range / latency budget); tightening it would catch this | [`evidence/traces/97e1d283878d41f1.json`](evidence/traces/97e1d283878d41f1.json) |
| `b1024f3e5b225317` | F3 | drift_value | 3 | FN | irreducible semantic escape: schema-valid, invariant-respecting, structurally identical to a correct output — only the oracle knows | [`evidence/traces/b1024f3e5b225317.json`](evidence/traces/b1024f3e5b225317.json) |
| `936251f9f3ec4981` | F3 | drift_value | 3 | FN | irreducible semantic escape: schema-valid, invariant-respecting, structurally identical to a correct output — only the oracle knows | [`evidence/traces/936251f9f3ec4981.json`](evidence/traces/936251f9f3ec4981.json) |
| `10c4fce1efa432dd` | F5 | context_drift | 2 | FN | irreducible semantic escape: schema-valid, invariant-respecting, structurally identical to a correct output — only the oracle knows | [`evidence/traces/10c4fce1efa432dd.json`](evidence/traces/10c4fce1efa432dd.json) |
| `599b51381f2d0c52` | F5 | context_drift | 2 | FN | irreducible semantic escape: schema-valid, invariant-respecting, structurally identical to a correct output — only the oracle knows | [`evidence/traces/599b51381f2d0c52.json`](evidence/traces/599b51381f2d0c52.json) |

## Q2 finding

Detection accuracy must be read PER CLASS, not aggregated. Precision is 1.0 everywhere (zero false positives across all families). The false negatives are of two kinds: THRESHOLD-REDUCIBLE (low-severity F1/F2 below a schema range / latency budget — caught by tightening the threshold) and IRREDUCIBLE SEMANTIC ESCAPES (F3 drift_value, F5 context_drift — no deterministic detector closes them). This confirms Q2's split hypothesis (Day 11); at this sample size the group interval bands are wide, so the split is directional evidence plus the structural proof that the escapes are undetectable.

