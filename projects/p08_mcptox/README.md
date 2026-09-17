# P8 — MCPTox Tool Poisoning Evaluation

## What Was Measured
Tool-poisoning vulnerability on MCPTox (commit `f85189f`, sha256 `79a90049be931c59e71446d6180b1d7f0d196d123d08a59bc155d142b5041c03`, 300 of 1,312 seed 42). Arm A: Inspect `d45705b` verbatim. Arm B: same loader/ids/judge prompt + `ProvenancePolicy` + 1 retry gated on parsed rejected call. Judge: `z-ai/glm-5.3-flash`, max_tokens 2048 both arms.

## Results
ASR over valid with Wilson 95% CIs.

|Rung|Model|Arm A ASR (valid)|Arm B ASR (valid)|McNemar p|B Blocked|False Block Proxy|Invalid A/B|
|---|---|---|---|---|---|---|---|
|R1|Qwen 3.7 Flash|0.329 [0.275, 0.389]|0.083 [0.054, 0.125]|<1e-8|13|6|45/70|
|R2|GLM 5.3 Flash|0.172 [0.134, 0.219]|0.041 [0.024, 0.070]|<1e-8|18|16|4/8|
|R3|Qwen 3.8 Flash|0.418 [0.363, 0.475]|0.098 [0.069, 0.137]|<1e-8|13|3|6/3|
|R4|GPT 5.6 Luna|0.408 [0.351, 0.467]|0.053 [0.032, 0.086]|<1e-8|22|3|28/34|
|R5|Gemini 3.7 Flash|0.030 [0.016, 0.056]|0.017 [0.007, 0.039]|n.s. p=0.22|4|3|1/2|
|R6|DeepSeek v4 Pro|0.476 [0.420, 0.533]|0.155 [0.118, 0.201]|<1e-8|22|6|4/8|

## H7 Verdict
Pre-registered H7: falsified if Arm B ASR CI overlaps or exceeds published band (mean 0.365, peak 0.728).
Per-rung CI upper < 0.365 (Arm A / Arm B): R1 False/True, R2 True/True, R3 False/True, R4 False/True, R5 True/True, R6 False/True.
On R5 (Gemini, Arm A 0.030), paired test is not significant (6 discordant, p=0.22): the contract removes attacks in proportion to how much the model complies, and has nothing to remove on a model that ignores the poison.

## $0 Replay Result
On 10,227 author traces (`replay_results.json`), contract blocked 87.0% of author-labelled Success (1,438/1,653) and 24.5% false-blocked on Failure-Ignored (1,271/5,188).

## Costs of the Contract
False blocks are world-knowledge inferences (Microsoft→MSFT, tomorrow→date). Invalid rises on thinking rung R1 (45→70) because retries exhaust 2048-token budget. Direct-Execution rises on several rungs (R1 14→30, R3 30→51, R4 21→31, R6 27→37).

## Caveats & Pilot
Caveats: R2 self-judged (judge=R2); 1 LLM judge; 1 gateway (aicredits.in); 1 day; upstream definition is ASR over valid (`asr_over_all` also in results.json).
Pilot: `pilot_retry_any/` (retry after any rejection incl. prose) found retry bug: R4 had 53 blocks (15 false blocks, ASR 0.070) vs final 22 (3 false blocks, ASR 0.053).

## Spend & Reproduce
Spend from `ledger.jsonl`: $3.55 vs $10 cap (R1 $0.46, R2 $0.34, R3 $0.52, R4 $0.64, R5 $0.58, R6 $1.00).
Reproduce:
- `make phase2-install-inspect` (.venv-inspect)
- `make p08 ARGS=--dry-run`
- `make p08-replay`
- `make p08 ARGS="--confirm --retry-mode call-only"`
