# Decisions for Project P4: Failure Taxonomy (Human Open Coding)

## 1. Dataset & Scope of Qualitative Coding
- **Traces Analyzed**: All $N=200$ standard pool multi-hop scenarios across T1 (1-hop), T2 (3-hop), and T3 (5-hop).
- **Human Coding**: Completed across all $N=200$ scenario traces in [`coding_sheet.csv`](coding_sheet.csv) and [`coding_sheet.md`](coding_sheet.md).
- **Failures Identified & Coded**: $N=183$ failed traces ($53 \text{ T1}, 64 \text{ T2}, 66 \text{ T3}$).
- **Compute Spend**: **$0.00 USD** (pure human qualitative analysis on committed P3 traces).

---

## 2. Human-Coded Axial Failure Taxonomy

Through open coding and axial clustering of the real failure traces, 9 mutually exclusive failure modes were established:

| Mode ID | Mode Name | Family | Count ($n=183$) | Prevalence | Status vs Phase 1 Catalog (F1–F6) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`INFRASTRUCTURE_RATE_LIMIT`** | Infrastructure Rate Limit | `transport_infrastructure` | 114 | 62.3% | Maps to F4 (Provider Error / Transport) |
| **`OVERCONSTRAINED_SEARCH_LOOP`** | Overconstrained Search Loop | `retrieval_strategy` | 36 | 19.7% | **NOVEL (Absent from F1–F6)** |
| **`MALFORMED_TOOL_CALL`** | Malformed Tool Call | `structured_output` | 23 | 12.6% | Maps to F1 (Structured-Output Corruption) |
| **`INFRASTRUCTURE_SERVER_ERROR`** | Infrastructure Server Error | `transport_infrastructure` | 3 | 1.6% | Maps to F4 (Provider Error / Transport) |
| **`MULTI_HOP_TRAVERSAL_EXHAUSTION`** | Multi-Hop Traversal Exhaustion | `budget_exhaustion` | 3 | 1.6% | **NOVEL (Absent from F1–F6)** |
| **`RETRIEVAL_FAILURE_ABSTENTION`** | Retrieval Failure Abstention | `epistemic_abstention` | 1 | 0.5% | **NOVEL (Absent from F1–F6)** |
| **`ANSWER_EXTRACTION_TRUNCATION`** | Answer Extraction Truncation | `fact_extraction` | 1 | 0.5% | Maps to F3 (Semantic Drift / Exact Token Match) |
| **`PREMATURE_STOP_WRONG_HOP`** | Premature Stop at Wrong Hop | `control_flow` | 1 | 0.5% | **NOVEL (Absent from F1–F6)** |
| **`MULTI_HOP_DIRECTION_ERROR`** | Multi-Hop Direction Error | `graph_traversal` | 1 | 0.5% | **NOVEL (Absent from F1–F6)** |

---

## 3. Boundary Definitions & Positive Examples

1. **`OVERCONSTRAINED_SEARCH_LOOP` (NOVEL)**:
   - *Definition*: Agent issues search queries with excessive keyword constraints that return 0 candidate documents, repeatedly reformulating with similar multi-token queries until step cap 12.
   - *Example*: Scenario `s-0074` (T2) — 9 out of 12 queries returned 0 candidates, looping until budget exhaustion.
2. **`MULTI_HOP_TRAVERSAL_EXHAUSTION` (NOVEL)**:
   - *Definition*: Agent executes valid, progressive search hops on 5-hop (T3) chains but runs out of the 12-step budget before reaching the terminal hop document.
   - *Example*: Scenario `s-0138` (T3) — Agent successfully completed 3 hops but hit step cap 12 before hop 5.
3. **`RETRIEVAL_FAILURE_ABSTENTION` (NOVEL)**:
   - *Definition*: Agent fails to find the required source in initial queries and explicitly abstains from fabricating an answer.
   - *Example*: Scenario `s-0020` (T1) — Agent explicitly stated: *"I couldn’t verify the external auditor... searches returned no matching source."*
4. **`PREMATURE_STOP_WRONG_HOP` (NOVEL)**:
   - *Definition*: Agent terminates early on a multi-hop task and outputs a transit entity attribute as the final answer.
   - *Example*: Scenario `s-0110` (T2) — Agent stopped at step 2 and emitted an intermediate entity.
5. **`MULTI_HOP_DIRECTION_ERROR` (NOVEL)**:
   - *Definition*: Agent navigates the dependency graph in the reverse direction.
   - *Example*: Scenario `s-0165` (T3) — Agent queried backward dependencies rather than forward link documents.

---

## 4. Saturation Curve Evidence

- **Milestones**:
  - Failure #1: `MALFORMED_TOOL_CALL`
  - Failure #7: `INFRASTRUCTURE_RATE_LIMIT`
  - Failure #16: `RETRIEVAL_FAILURE_ABSTENTION`
  - Failure #19: `ANSWER_EXTRACTION_TRUNCATION`
  - Failure #43: `INFRASTRUCTURE_SERVER_ERROR`
  - Failure #59: `OVERCONSTRAINED_SEARCH_LOOP`
  - Failure #94: `PREMATURE_STOP_WRONG_HOP`
  - Failure #121: `MULTI_HOP_TRAVERSAL_EXHAUSTION`
  - Failure #148: `MULTI_HOP_DIRECTION_ERROR`
- **Saturation Point**: Complete saturation reached at **failure #148 / 183 (80.9%)**. No new failure modes emerged across the final 35 failure traces.

---

## 5. Pre-Registered Hypothesis H2 Evaluation

> **Hypothesis H2 (`HYPOTHESES.md`)**:
> *$\ge 2$ discovered failure modes are absent from the injected F1–F6 catalog.*
> *Falsified by: every mode maps onto the catalog.*

- **Modes Genuinely Absent from F1–F6**:
  1. `OVERCONSTRAINED_SEARCH_LOOP` (36 occurrences)
  2. `MULTI_HOP_TRAVERSAL_EXHAUSTION` (3 occurrences)
  3. `RETRIEVAL_FAILURE_ABSTENTION` (1 occurrence)
  4. `PREMATURE_STOP_WRONG_HOP` (1 occurrence)
  5. `MULTI_HOP_DIRECTION_ERROR` (1 occurrence)
- **Verdict**: **CONFIRMED** (5 emergent failure modes discovered in real multi-hop execution that were completely absent from the synthetic Phase 1 single-step injection catalog F1–F6).
