# Pre-Registration: P18 Trace Triage of Agent Failure Types

- **Experiment ID**: P18
- **Date**: 2026-09-28
- **Status**: PRE-REGISTERED (Prior to any LLM judge labelling or evaluation)
- **Dataset**: `Exgentic/agent-llm-traces-v2` (10,056 runs across 6 benchmarks, OpenTelemetry GenAI chat spans)
- **Manifest**: [manifest.json](./manifest.json) (400 stratified runs, seed 42)

---

## 1. Failure Type Definitions (Verbatim)

The 4 CEO-approved failure modes to be detected:

- **T1 UNRECOVERED_TOOL_ERROR** — code rule: a tool/API call errors (`error.type`, error text in tool result) and the run never succeeds at that step afterwards.
- **T2 REPEATED_CALL_NO_PROGRESS** — code rule: the same tool call (same name + same normalized arguments) issued >=3 times with no new information in between.
- **T3 LOOP_WITHOUT_PROGRESS** — Laya judgment: agent cycles through reformulations/actions without getting closer to the goal (generalisation of FAULTLINE's `OVERCONSTRAINED_SEARCH_LOOP`).
- **T4 MISREAD_TOOL_OUTPUT** — Laya judgment: agent's next step contradicts or ignores what a tool actually returned.

---

## 2. LLM Judge Prompt & Strict Schema

The primary labelling judge utilizes `antigravity/gemini-3.8-flash` via an OpenAI-compatible endpoint at temperature `0.0`.

### System Prompt
```text
You are an expert AI reliability judge evaluating agent execution traces.
Given the step-by-step transcript of an agent run, you must evaluate the occurrence of four specific failure modes:

1. T1 UNRECOVERED_TOOL_ERROR:
   A tool/API call errors (error.type, error text in tool result) and the run never succeeds at that step afterwards.
   - Return label=true if a tool failed and the agent never recovered from that failure.
   - If the agent subsequently retried and succeeded, return label=false.

2. T2 REPEATED_CALL_NO_PROGRESS:
   The same tool call (same name + same normalized arguments) issued >= 3 times with no new information in between.
   - Return label=true if identical tool invocations were executed 3+ times without producing distinct informative state.

3. T3 LOOP_WITHOUT_PROGRESS:
   Agent cycles through reformulations/actions without getting closer to the goal (generalisation of FAULTLINE's OVERCONSTRAINED_SEARCH_LOOP).
   - Return label=true if the agent wanders in circles, repeatedly trying minor variations without making real headway.

4. T4 MISREAD_TOOL_OUTPUT:
   Agent's next step contradicts or ignores what a tool actually returned.
   - Return label=true if the agent ignores explicit information returned by a tool or acts in direct contradiction to it.

You must respond ONLY with valid JSON conforming to this schema:
{
  "T1": {"label": bool, "evidence_step": int or null, "reasoning": str},
  "T2": {"label": bool, "evidence_step": int or null, "reasoning": str},
  "T3": {"label": bool, "evidence_step": int or null, "reasoning": str},
  "T4": {"label": bool, "evidence_step": int or null, "reasoning": str}
}
```

### Validation Schema (Pydantic, `extra="forbid"`)
```python
class FailureTypeAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: bool
    evidence_step: Optional[int] = None
    reasoning: Optional[str] = ""

class TriageEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    T1: FailureTypeAssessment
    T2: FailureTypeAssessment
    T3: FailureTypeAssessment
    T4: FailureTypeAssessment
```

---

## 3. Sample Design & Split-by-Task Rule

### Stratification
A total sample of 400 runs is drawn from `Exgentic/agent-llm-traces-v2` across 12 strata formed by crossing 6 benchmarks with 2 binary outcome states (`success` in `{True, False}`):
- `appworld` (fail: 34, success: 34)
- `browsecompplus` (fail: 34, success: 34)
- `swebench` (fail: 33, success: 33)
- `tau2_airline` (fail: 33, success: 33)
- `tau2_retail` (fail: 33, success: 33)
- `tau2_telecom` (fail: 33, success: 33)

Sampling seed is fixed at `42`.

### Task Grouping & Split Rule
- The dataset lacks an explicit `task_id` attribute. Analysis reveals that underlying benchmark tasks are uniquely determined by the initial user problem prompt in `gen_ai.input.messages`.
- Task groups are defined as `f"{benchmark}:{sha256(initial_prompt)[:16]}"`.
- The 400 sampled runs span 284 unique tasks.
- Splitting is performed strictly at the **task group** level using seed `42` with target proportions:
  - **Train**: 50% of tasks (142 tasks, 236 runs)
  - **Dev**: 20% of tasks (57 tasks, 60 runs)
  - **Test**: 30% of tasks (85 tasks, 104 runs)
- **Zero Leakage**: All runs for any given task group are assigned to exactly one split. No task appears in multiple splits.

---

## 4. Audit Protocol

To validate the judge's accuracy without circular self-evaluation:
1. The CEO hand-labels an audit sample of 100 runs stratified across splits and failure types.
2. The audit labeling is conducted completely blind to the judge's labels.
3. Judge accuracy, precision, recall (TPR), and specificity (TNR) per failure type are scored against this ground-truth audit set.

---

## 5. Success Criteria & Power Calibration

- **Evaluation Split**: Evaluated on the held-out **test split** (104 runs, 85 tasks), read exactly once after development freeze.
- **Decision Threshold**:
  - $\text{TPR} \ge 0.90$
  - $\text{TNR} \ge 0.80$
- **Uncertainty**: 95% Wilson score confidence intervals reported for all point estimates.
- **Statistical Power Rule**: Any failure type with fewer than 30 positive cases in the test split ($n_{\text{pos}} < 30$) is formally reported as **underpowered**, rather than evaluated as a definitive pass/fail claim.

---

## 6. Rule Freeze (2026-09-28)

Code rules for **T1** and **T2** are frozen as of this amendment, strictly before any LLM judge labels are generated:

1. **T1 UNRECOVERED_TOOL_ERROR Structural Error Filtering**:
   - Substring matching across tool response bodies was replaced with structural error detection. Error words (e.g., `error`, `traceback`, `exception`) embedded in normal content (wiki pages, search results, code diffs, test outputs) do not count as errors.
   - A tool response is recognized as an error if and only if:
     - The `tool_call_response` part carries an explicit error flag/status field (`is_error=True`, `error`, `status="error"`/`"failed"`).
     - The response parses as JSON whose top-level object has an `'error'` key (e.g., `{"error": "Document 2809 not found"}`) or a top-level non-zero exit/return code (`exit_code`, `return_code`, `exitcode`, `returncode`, `exit_status`).
     - The response text is wrapped in `<tool_use_error>...</tool_use_error>`.
     - The response starts with (after whitespace): `'Error:'`, `'ERROR:'`, `'Traceback (most recent call last)'`, or `'An error occurred while parsing tool arguments'`.
     - Span-level `error.type` is set, or span status code equals 2.
   - Recovery requires a subsequent invocation of the same tool that completes without a structural error.

2. **T2 REPEATED_CALL_NO_PROGRESS Exact Identity Requirement**:
   - T2 now strictly detects when the identical tool call (same tool name and same normalized arguments) is issued $\ge 3$ times where all three responses are identical after whitespace normalization.
   - The former `intervening_distinct` and partial 2-of-3 response matching clauses were removed. Different tool responses constitute new information and do not trigger T2.

Both rules are verified by deterministic unit tests in `tests/phase2/test_p18_rules.py` prior to initiating any labelling run.

---

## 7. Outcome Blinding (2026-09-28)

To eliminate evaluation bias, both the LLM judge transcript view and the Laya state representation strictly exclude the run outcome:
- **No Outcome Leakage**: Neither `success` (boolean benchmark pass/fail) nor `status` (execution completion code) is exposed to the labelling judge (`build_judge_view`) or to Laya (`build_laya_state`).
- **Benchmark Identity**: Benchmark name (`swebench`, `appworld`, etc.) is retained in metadata exclusively for the LLM judge view to supply task domain context; it is omitted from Laya state.
- **Pre-Registration Constraint**: This protocol amendment is enacted and verified in unit tests (`test_outcome_blinding_in_adapter_views`) strictly prior to generating any LLM judge labels.

---

## 8. Audit Design (2026-09-28)

To evaluate the reliability of the automated judge (`antigravity/gemini-3.8-flash`) and code rules against human ground truth without circular bias, the CEO evaluates a blind sample of 100 runs prior to reviewing automated evaluations:

1. **Stratification & Sampling Protocol (Seed 42)**:
   - **Stratum A (Random, $n=50$)**: 50 runs drawn uniformly at random from the 400 manifest runs, allocated proportionally by split (train: 30, test: 13, dev: 7). Every run in the 400 has uniform design inclusion probability $\pi_i = 50 / 400 = 0.125$. Yields unbiased population prevalence and accuracy estimates.
   - **Stratum B (Enriched, $n=50$)**: 50 runs drawn from the remaining 350 runs where the judge indicates positive detection for any failure mode ($T1 \lor T2 \lor T3 \lor T4$) or where judge and code rule disagree on $T1$ or $T2$. Selected under strict priority ordering:
     1. All $T4$ judge-positives ($n=8$, inclusion probability $p=1.0$).
     2. All $T2$ judge-positives and $T2$ rule disagreements ($n=12$, inclusion probability $p=1.0$).
     3. Half of remaining slots ($n=15$) sampled from $T3$ judge-positives ($N=22$, inclusion probability $p = 15/22 \approx 0.6818$).
     4. Half of remaining slots ($n=15$) sampled from $T1$ judge-positives or disagreements ($N=54$, inclusion probability $p = 15/54 \approx 0.2778$).
   - **Presentation**: Merged into a single deterministically shuffled sequence (seed 42) presenting runs 1 through 100 without disclosing strata, inclusion weights, or group memberships.

2. **Blinded Human Review Interface**:
   - Delivered via a standalone, offline single-file page (`/Volumes/SamirDrive/scratch/faultline/p18_audit/audit.html`), not stored in the repository.
   - Strictly omits judge labels, judge reasoning, rule detections, run outcome status, and strata identifiers.
   - Trace transcripts are rendered purely via DOM `textContent` to prevent script execution. No external network requests (zero CDNs or remote web fonts).
   - Captures independent CEO ratings for $T1..T4$ (`yes` / `no` / `unsure`) alongside qualitative notes, autosaved locally to `localStorage` and exportable as `audit_labels.json`.

3. **Evaluation Protocol**:
   - Diagnostic performance (TP, FP, TN, FN, TPR with 95% Wilson CI, TNR with 95% Wilson CI, and Cohen's $\kappa$) is scored separately for:
     - **Stratum A alone**: Provides an unbiased representative estimate of rater agreement.
     - **All 100 runs combined**: Provides high statistical power across rare failure modes, explicitly designated as an enriched sample.
   - Ratings of `unsure` are counted and excluded from diagnostic sensitivity and specificity denominators.

---

## Amendment A-P18-1: audit rater (2026-09-28)

- At the CEO's request the 100-run audit is labelled by Claude Opus 5.5 (model id `claude-opus-5-5`, Anthropic) instead of the CEO. This is a different model family from the labelling judge (Gemini 3.8 Flash via llm-bridge).
- The rater sees only audit position, benchmark, session id and the judge_view text (same text the judge saw), in audit order. It does not see judge labels or reasoning, code-rule outputs, run success/status, stratum or group.
- Three audit runs were seen with judge labels earlier in the session during the labelling trial: `10d642ac9c10_56b2cfc3`, `0c890a5dde8c_5cc007d3`, `0b5e2a9b0887_a1b6c325`. They are labelled but flagged non-blind and excluded from the primary scoring; a secondary scoring including them is reported separately.
- Consequence: results measure inter-model agreement (Gemini judge vs Claude rater) and rule-vs-Claude agreement, NOT agreement with human ground truth. LLM raters can share errors. The CEO may adjudicate Claude-Gemini disagreements afterwards; adjudicated labels would then be reported as a third, human-adjudicated result.


