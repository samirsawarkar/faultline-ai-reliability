# P18: Trace Triage of Failure Types on Real Agent Traces

Measures 4 failure-type detectors on real third-party agent traces (`Exgentic/agent-llm-traces-v2`, OpenTelemetry GenAI chat spans, 10,056 runs, 6 benchmarks).

## Deliverables & Components

- [PREREG.md](./PREREG.md): Formal pre-registration document specifying verbatim failure mode definitions, judge prompts, validation schema, task-grouped split design, audit protocol, and statistical power rules.
- [manifest.json](./manifest.json): Deterministic stratified sample of 400 runs across 12 strata (`benchmark` x `success`), split 50/20/30 by task group (284 unique tasks, 0% task leakage).
  - SHA-256: `471e41b2b57c1886a0120ca7c068029e98c69d4f732e39aba43a22f50daf2795`
- [adapter.py](./adapter.py): Generates compact `laya_state` (<= 512 Laya tokens) and `judge_view` (capped at 30,000 tokens / ~120,000 chars, preserving head and tail turns).
- [sample.py](./sample.py): Seeded (42) stratified sampler and task-grouped train/dev/test partitioner.
- [rules.py](./rules.py): Pure-function code detectors for:
  - T1: `UNRECOVERED_TOOL_ERROR`
  - T2: `REPEATED_CALL_NO_PROGRESS`
- [label.py](./label.py): OpenAI-compatible judge client validating against strict Pydantic schemas (`extra="forbid"`), resumable via `labels.jsonl`, tracking per-call token counts. (Setup only; not executed against model).
- [test_p18_rules.py](../../tests/phase2/test_p18_rules.py): Hand-crafted span unit tests verifying T1 and T2 detection logic.

## The 4 Failure Modes

1. **T1 UNRECOVERED_TOOL_ERROR** (Code rule): A tool/API call errors (`error.type`, error text in tool result) and the run never succeeds at that step afterwards.
2. **T2 REPEATED_CALL_NO_PROGRESS** (Code rule): The same tool call (same name + same normalized arguments) issued >= 3 times with no new information in between.
3. **T3 LOOP_WITHOUT_PROGRESS** (Laya judgment): Agent cycles through reformulations/actions without getting closer to the goal (generalisation of FAULTLINE's `OVERCONSTRAINED_SEARCH_LOOP`).
4. **T4 MISREAD_TOOL_OUTPUT** (Laya judgment): Agent's next step contradicts or ignores what a tool actually returned.

## Sample Splits Summary

- **Total Sampled Runs**: 400
- **Total Unique Tasks**: 284
- **Stratum Count**: 12 strata (34 or 33 runs each)
- **Train Split**: 142 tasks (50.0%), 236 runs
- **Dev Split**: 57 tasks (20.1%), 60 runs
- **Test Split**: 85 tasks (29.9%), 104 runs

## Adapter Truncation Evaluation (n = 400)

- `laya_state` (<= 512 tokens): 64/400 truncated (16.00%)
- `judge_view` (<= 30k tokens): 36/400 truncated (9.00%)
