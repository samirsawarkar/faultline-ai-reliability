# FAULTLINE Fault Gallery (F1-F6)

Every fault, linked **fault -> trace -> detector -> metric**. Generated from `catalog.json`; do not edit by hand.

| Fault | Name | Producing component | Detector (nature) | Signal | Recall | Precision | Recovery | Trace |
|---|---|---|---|---|---|---|---|---|
| **F1** | Structured-output corruption | tool output (data plane) | schema validator (deterministic) | repair_signal | 1.0 | 1.0 | structured repair, then bounded retry | `evidence/traces/F1.json` |
| **F2** | Tool latency / timeout | tool/provider transport (timing) | duration vs budget (deterministic) | timeout_signal | 1.0 | 1.0 | timeout then bounded retry / hedge | `evidence/traces/F2.json` |
| **F3** | Schema drift / semantic corruption | tool output (data plane) | schema + value invariant (mixed) | invariant_violation (caught subset only) | 0.6 | 1.0 | semantic validation (oracle/judge), then reject/repair | `evidence/traces/F3.json` |
| **F4** | Provider error | tool/provider transport (availability) | explicit error flag (deterministic) | provider_error + circuit-breaker | 1.0 | 1.0 | circuit breaker, then fallback provider | `evidence/traces/F4.json` |
| **F5** | Context corruption | agent context / state (memory) | context-consistency invariant (semantic) | context_integrity violation (incoherent only) | 0.5 | 1.0 | context re-grounding / cross-source agreement | `evidence/traces/F5.json` |
| **F6** | Loop exhaustion | agent control loop (controller) | repetition + step-budget (deterministic) | loop_detect (repetition or budget-exhaustion) | 1.0 | 1.0 | structural step-budget cap + abort; progress check | `evidence/traces/F6.json` |

## Cards

### F1 — Structured-output corruption

- **Family / component:** structured-output / tool output (data plane)
- **Trigger:** Deterministic: every_n=2 on the call index; verdict is a pure function of (spec, run_seed, seq, input_digest). Severity scales the value offset.
- **Detector:** schema validator — *deterministic* (signal: `repair_signal`, measured in day09)
- **Recovery:** structured repair, then bounded retry (planned: M1 repair-retry (Mission 18))
- **Metric:** recall 1.0, precision 1.0 — recall rises with severity; small in-range drift is a residual
- **Trace:** `evidence/traces/F1.json` (12 spans, 12 labelled)
- **Normalized spec:** `{'fault_id': 'F1', 'component': '*', 'mode': 'corrupt', 'severity': 3, 'trigger': 'every_n', 'trigger_value': '2', 'seed': 1, 'rate': 1.0, 'label': 'F1:corrupt', 'spec_version': '1.0.0'}`

### F2 — Tool latency / timeout

- **Family / component:** latency / tool/provider transport (timing)
- **Trigger:** Deterministic: every_n=2 on the call index; virtual duration = BASE + severity*10 (no wall clock).
- **Detector:** duration vs budget — *deterministic* (signal: `timeout_signal`, measured in day09)
- **Recovery:** timeout then bounded retry / hedge (planned: M2 timeout policy (Mission 18))
- **Metric:** recall 1.0, precision 1.0 — budget-gated (default budget 45)
- **Trace:** `evidence/traces/F2.json` (12 spans, 12 labelled)
- **Normalized spec:** `{'fault_id': 'F2', 'component': '*', 'mode': 'stall', 'severity': 4, 'trigger': 'every_n', 'trigger_value': '2', 'seed': 1, 'rate': 1.0, 'label': 'F2:latency', 'spec_version': '1.0.0'}`

### F3 — Schema drift / semantic corruption

- **Family / component:** wrong-data / tool output (data plane)
- **Trigger:** Deterministic: call_index on a fixed run; produces a different in-range round-ten value (schema-valid, wrong).
- **Detector:** schema + value invariant — *mixed* (signal: `invariant_violation (caught subset only)`, measured in day10)
- **Recovery:** semantic validation (oracle/judge), then reject/repair (planned: validated judge (Mission 16))
- **Metric:** recall 0.6, precision 1.0 — 40% of wrong-data escapes deterministic checks
- **Trace:** `evidence/traces/F3.json` (12 spans, 12 labelled)
- **Normalized spec:** `{'fault_id': 'F3', 'component': '*', 'mode': 'drift_value', 'severity': 3, 'trigger': 'every_n', 'trigger_value': '2', 'seed': 1, 'rate': 1.0, 'label': 'F3:drift_value', 'spec_version': '1.0.0'}`

### F4 — Provider error

- **Family / component:** explicit-failure / tool/provider transport (availability)
- **Trigger:** Deterministic: every_n=2 on the call index; the call raises an explicit error envelope (no content).
- **Detector:** explicit error flag — *deterministic* (signal: `provider_error + circuit-breaker`, measured in day10)
- **Recovery:** circuit breaker, then fallback provider (planned: M3 circuit breaker / M4 fallback (Mission 20))
- **Metric:** recall 1.0, precision 1.0 — explicit signal; recall 1.0
- **Trace:** `evidence/traces/F4.json` (12 spans, 12 labelled)
- **Normalized spec:** `{'fault_id': 'F4', 'component': '*', 'mode': 'provider_error', 'severity': 5, 'trigger': 'every_n', 'trigger_value': '2', 'seed': 1, 'rate': 1.0, 'label': 'F4:provider_error', 'spec_version': '1.0.0'}`

### F5 — Context corruption

- **Family / component:** semantic / agent context / state (memory)
- **Trigger:** Deterministic: call_index on the run; a plausible wrong context value is inserted and the final recomputed to stay consistent.
- **Detector:** context-consistency invariant — *semantic* (signal: `context_integrity violation (incoherent only)`, measured in day11)
- **Recovery:** context re-grounding / cross-source agreement (planned: context validation + judge)
- **Metric:** recall 0.5, precision 1.0 — consistency catches incoherent; drift escapes
- **Trace:** `evidence/traces/F5.json` (8 spans, 8 labelled)
- **Normalized spec:** `{'fault_id': 'F5', 'component': '*', 'mode': 'context_drift', 'severity': 2, 'trigger': 'call_index', 'trigger_value': '0', 'seed': 1, 'rate': 1.0, 'label': 'F5:context_drift', 'spec_version': '1.0.0'}`

### F6 — Loop exhaustion

- **Family / component:** deterministic-termination / agent control loop (controller)
- **Trigger:** Deterministic: call_index on the run; the loop repeats a step or burns the step budget without completing.
- **Detector:** repetition + step-budget — *deterministic* (signal: `loop_detect (repetition or budget-exhaustion)`, measured in day11)
- **Recovery:** structural step-budget cap + abort; progress check (planned: bounded loop (Day 2) + recovery policies)
- **Metric:** recall 1.0, precision 1.0 — deterministic; recall 1.0, no escape
- **Trace:** `evidence/traces/F6.json` (8 spans, 8 labelled)
- **Normalized spec:** `{'fault_id': 'F6', 'component': '*', 'mode': 'repetition', 'severity': 2, 'trigger': 'call_index', 'trigger_value': '0', 'seed': 1, 'rate': 1.0, 'label': 'F6:repetition', 'spec_version': '1.0.0'}`

