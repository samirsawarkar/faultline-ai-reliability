# Raw experimental results

Source: `experiments/raw/results.json` and `experiments/raw/ledger.jsonl`.

| Rung | Arm | Model | n | n_valid | Success | Failure-Ignored | Failure-Direct-Exec | Contract-Blocked | Invalid | ASR (valid) | 95% Wilson CI (valid) | ASR (all) | Spend (USD) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R1 | Arm A (baseline) | qwen/qwen3.7-flash | 300 | 255 | 84 | 157 | 14 | 0 | 45 | 0.3294 | [0.2746, 0.3893] | 0.2800 | $0.1222 |
| R1 | Arm B (contract) | qwen/qwen3.7-flash | 300 | 230 | 19 | 168 | 30 | 13 | 70 | 0.0826 | [0.0535, 0.1254] | 0.0633 | $0.1573 |
| R2 | Arm A (baseline) | z-ai/glm-5.3-flash | 300 | 296 | 51 | 209 | 26 | 0 | 4 | 0.1723 | [0.1335, 0.2194] | 0.1700 | $0.0965 |
| R2 | Arm B (contract) | z-ai/glm-5.3-flash | 300 | 292 | 12 | 225 | 31 | 18 | 8 | 0.0411 | [0.0237, 0.0704] | 0.0400 | $0.1086 |
| R3 | Arm A (baseline) | qwen/qwen3.8-flash | 300 | 294 | 123 | 141 | 30 | 0 | 6 | 0.4184 | [0.3634, 0.4755] | 0.4100 | $0.1541 |
| R3 | Arm B (contract) | qwen/qwen3.8-flash | 300 | 297 | 29 | 204 | 51 | 13 | 3 | 0.0976 | [0.0688, 0.1367] | 0.0967 | $0.1784 |
| R4 | Arm A (baseline) | openai/gpt-5.6-luna | 300 | 272 | 111 | 112 | 21 | 0 | 28 | 0.4081 | [0.3514, 0.4674] | 0.3700 | $0.1975 |
| R4 | Arm B (contract) | openai/gpt-5.6-luna | 300 | 266 | 14 | 184 | 31 | 22 | 34 | 0.0526 | [0.0316, 0.0864] | 0.0467 | $0.2109 |
| R5 | Arm A (baseline) | google/gemini-3.7-flash | 300 | 299 | 9 | 263 | 27 | 0 | 1 | 0.0301 | [0.0159, 0.0562] | 0.0300 | $0.2157 |
| R5 | Arm B (contract) | google/gemini-3.7-flash | 300 | 298 | 5 | 263 | 25 | 4 | 2 | 0.0168 | [0.0072, 0.0387] | 0.0167 | $0.1815 |
| R6 | Arm A (baseline) | deepseek/deepseek-v4-pro | 300 | 296 | 141 | 126 | 27 | 0 | 4 | 0.4764 | [0.4201, 0.5332] | 0.4700 | $0.5387 |
| R6 | Arm B (contract) | deepseek/deepseek-v4-pro | 300 | 291 | 45 | 186 | 37 | 22 | 8 | 0.1546 | [0.1176, 0.2007] | 0.1500 | $0.4640 |
