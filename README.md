# FAULTLINE

**A reproducible research workbench for evaluating autonomous AI agent reliability under repeated execution and defending against Model Context Protocol (MCP) tool poisoning.**

[![CI](https://github.com/samirsawarkar/faultline-ai-reliability/actions/workflows/ci.yml/badge.svg)](https://github.com/samirsawarkar/faultline-ai-reliability/actions/workflows/ci.yml)
[![Phase 2](https://github.com/samirsawarkar/faultline-ai-reliability/actions/workflows/phase2.yml/badge.svg)](https://github.com/samirsawarkar/faultline-ai-reliability/actions/workflows/phase2.yml)
[![Tests: 654 passing](https://img.shields.io/badge/tests-528%20Phase%201%20%2B%20126%20Phase%202-brightgreen.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## Publications

### Multi-Trial Reliability and Failure Concentration in Multi-Hop AI Agents
*Grounding Collapse, Failure Taxonomy, and Evaluator Calibration*  
**Samir Sawarkar** · FAULTLINE AI Reliability Engineering  
[Paper (PDF)](publications/publication_01_passk_reliability/paper.pdf) · [Paper (Markdown)](publications/publication_01_passk_reliability/paper.md) · [Executive Summary](publications/publication_01_passk_reliability/blog_post.md)

![Multi-Trial Reliability vs Naive Independence](publications/publication_01_passk_reliability/fig_2_passk_vs_naive.png)

- **Empirical test of naive compounding:** Evaluated 150 held-out hard Tier-3 scenarios across $k=3$ repeated trials (1,350 total runs) across two commercial model tiers (R2: `glm-5.3-flash`, R4: `gpt-5.6-luna`, plus R6: `deepseek-v4-pro` infra-invalidated) graded by a deterministic dual-condition oracle without model judges.
- **Independence holds within 2.5 pp:** Naive Bernoulli compounding $\text{pass}^k = (\text{pass@1})^k$ matches empirical joint reliability within 2.5 percentage points at $k=3$ ($\Delta_3 = -0.0247$ on R2; $\Delta_3 = +0.0187$ on R4 infra-excluded), well within the pre-registered 10 pp minimum effect of interest.
- **Regime-dependent failure behavior:** Higher-accuracy tier (R2, $\text{pass@1} = 0.6311$) is consistent with a homogeneous-binomial null ($\text{pass}^3 = 0.2267$ vs naive $0.2514$, bootstrap $p = 0.3794$, Tarone $z = -0.655, p = 0.7438$, $\text{ICC} = -0.0287$). Apparent excess successes in frontier tier (R4, $\text{pass@1} = 0.1489$) was driven by gateway timeouts; purging dropouts ($n=117$) leaves a marginal excess ($\text{pass}^3 = 0.0256$ vs naive $0.0070$, Tarone $z = 0.764, p = 0.2224$).
- **Compounding extrapolation:** Beta-binomial modeling shows that while $k=3$ leaves naive compounding accurate, even undetectable intra-scenario correlation ($\text{ICC}_{\text{hi}} = 0.0668$ on R2) yields divergence at scale ($C_8 \approx 2.25$, $\text{pass}^8 \approx 0.057$ vs naive $0.025$).

### Runtime Provenance Contracts for Mitigating Tool Poisoning in MCP Agents
*A Paired Evaluation on MCPTox Across Six Models*  
**Samir Sawarkar** · FAULTLINE  
[Paper (PDF)](publications/publication_02_mcptox_contract/paper.pdf) · [Paper (Markdown)](publications/publication_02_mcptox_contract/paper.md) · [Executive Summary](publications/publication_02_mcptox_contract/blog_post.md)

![Attack Success Rate by Rung](publications/publication_02_mcptox_contract/fig_1_asr_by_rung.png)

| Rung | Model | Arm A ASR (Valid) | Arm B ASR (Valid) | McNemar ($b/c$, $p$) | Significant |
|---|---|---|---|---|---|
| R1 | `qwen/qwen3.7-flash` | 28.00% (32.94%) | 6.33% (8.26%) | $b=71, c=6, p = 3.02 \times 10^{-13}$ | Yes |
| R2 | `z-ai/glm-5.3-flash` | 17.00% (17.23%) | 4.00% (4.11%) | $b=41, c=2, p = 6.83 \times 10^{-9}$ | Yes |
| R3 | `qwen/qwen3.8-flash` | 41.00% (41.84%) | 9.67% (9.76%) | $b=98, c=4, p = 3.31 \times 10^{-20}$ | Yes |
| R4 | `openai/gpt-5.6-luna` | 37.00% (40.81%) | 4.67% (5.26%) | $b=99, c=2, p = 1.27 \times 10^{-21}$ | Yes |
| R5 | `google/gemini-3.7-flash` | 3.00% (3.01%) | 1.67% (1.68%) | $b=5, c=1, p = 0.2188$ | No (n.s.) |
| R6 | `deepseek/deepseek-v4-pro` | 47.00% (47.64%) | 15.00% (15.46%) | $b=107, c=11, p = 2.22 \times 10^{-18}$ | Yes |
| **Pooled** | **All 6 Models** | **28.83% (30.32%)** | **6.89% (7.41%)** | **$b=421, c=26, p = 5.61 \times 10^{-93}$** | **Yes** |

- **Significant attack reduction:** On 300 MCPTox instances across six models via one gateway, the provenance contract achieved a paired mean score reduction $\text{Mean } \Delta = -0.2194$ (95% CI $[-0.2400, -0.1983]$, $p < 0.0001$, $d_z = -0.49$), cutting pooled valid ASR from 30.32% to 7.41%.
- **Asymmetric transition matrix:** Removed 421 attack successes while inducing only 26 (McNemar exact $p = 5.61 \times 10^{-93}$).
- **Autonomous refusal regime:** Gemini 3.7 Flash (R5) reduction was non-significant ($b=5, c=1, p=0.2188$) due to high baseline resistance.
- **Operational false-block penalty:** Replay over 10,227 traces indicates substring grounding false-blocks 24.5% of legitimate actions when tasks require ungrounded world knowledge.

---

## How the evidence is produced

Every experimental result is bound to immutable contracts and reproducible seeds:
- **Master Experiment Contract & Hypotheses:** Evaluation protocol frozen in [MEC.md](MEC.md); all primary hypotheses registered prior to execution in [HYPOTHESES.md](HYPOTHESES.md); protocol adjustments logged in [AMENDMENTS.md](AMENDMENTS.md).
- **Deterministic Oracle:** Grounded answer verification uses deterministic normalization and verified citation hashes against a frozen corpus (SHA256 `84e6ff590704aa94d10912f8002716b14c7436080e1a3270b53f9385dc728efc`, master seed `42`).
- **Cost & Rate Governance:** Pinned model pricing, per-project budget caps, and append-only ledgers (`ledger.jsonl`) recording timestamp, model, token counts, and USD cost per call.
- **Red-Team Release Gate:** Both publications passed independent 7-gate red-team audits before publication: [Publication 1 Checklist](research/final/release_checklist.md) and [Publication 2 Checklist](research_pub02/final/release_checklist.md).

---

## Project Board

| ID | Project | Focus | Status | Spend |
|---|---|---|---|---|
| [P01](projects/p01_baseline/) | Baseline | Grounded multi-hop agent evaluation baseline | Complete | $0.14 |
| [P02](projects/p02_otel_exporter/) | OTel Exporter | OpenTelemetry GenAI semantic conventions & spans | Complete | $0.00 |
| [P03](projects/p03_grounding/) | Grounding Zero-Point | Multi-hop depth grounding decay across T1–T3 | Complete | $1.43 |
| [P04](projects/p04_taxonomy/) | Failure Taxonomy | Human-in-the-loop trace coding (8 failure modes) | Complete | $0.00 |
| [P05](projects/p05_judge/) | Evaluator Calibration | LLM judge calibration & Rogan-Gladen correction | Complete | $0.04 |
| [P06](projects/p06_passk/) | Multi-Trial Reliability | $\text{pass}^k$ independence testing & failure clustering (Pub 01) | Complete | $23.73 |
| [P07](projects/p07_variance/) | Serving Variance | Temperature-0 serving nondeterminism across providers | Complete | $1.20 |
| [P08](projects/p08_mcptox/) | MCP Defense | Client-side runtime provenance contract on MCPTox (Pub 02) | Complete | $3.55 |
| [P13](projects/p13_slo_incident/) | SLO Incident | Multi-window burn-rate SLO alerting & incident triage | Complete | $0.00 |
| [P15](projects/p15_resilience/) | Resilience | Adaptive circuit breakers & jittered backoff policies | Complete | $0.00 |
| [P16](projects/p16_runtime_policy/) | Runtime Policy | Deterministic call allowlists, path containment, token caps | Complete | $0.00 |

---

## Phase 1

Phase 1 established the simulation foundations, telemetry architecture, and recovery mechanisms across 30 reproducible modules. It evaluated deterministic execution environments, bounded agents with typed contracts, multi-hop difficulty tiers, complete trace logging, and fault injection catalogs (F1–F6) without unconstrained model loops.

Building on that foundation, Phase 1 designed and stress-tested automated recovery primitives: schema and latency detectors, wrong-data discrimination, bounded retries, adaptive circuit breakers, and multi-objective cascade policies, verifying fixes via replay postmortems and self-explaining reproducibility gates.

<details>
<summary>Phase 1 Day 01–Day 30 Research Modules & Claims</summary>

<!-- RESULTS:START -->
| Question | Result | Evidence and generating script | Reproduce |
|---|---|---|---|
| When does required tool depth break the naive reliability model? | **Measured success 0.818 versus naive 0.91833; first interval separation at 3 hops** | [result](day07/evidence/investigation.json) · [script](day07/scripts/run_q1.py) | `make day07-q1` |
| Does the frozen detector evaluation reproduce? | **Frozen test evaluation: F1 0.842105 over 17 samples** | [result](day13/evidence/eval_result.json) · [script](day13/scripts/make_evidence.py) | `make day13-evidence` |
| Does fallback preserve availability without preserving quality? | **Availability 0.6667 → 1.0 while strict quality among answers 1.0 → 0.75** | [result](day21/evidence/availability_quality_comparison.json) · [script](day21/scripts/make_evidence.py) | `make day21-q4` |
| Which reference cascade policy wins on correct success, cost, and latency? | **Reference P4: success 0.9325, mean cost 1.4656, p95 latency 50.0** | [result](day24/evidence/policy_comparison.json) · [script](day24/scripts/make_evidence.py) | `make day24-q5` |
| Do incident fixes fail before and stay fixed afterward? | **2 incidents replay red → green; Checkpoint 25 passes** | [result](day25/evidence/checkpoint_25.json) | `make day25-postmortems` |
| Does the complete repository gate pass? | **433 tests collected and passed** | [result](day26/evidence/test_report.json) | `make reproduce` |
<!-- RESULTS:END -->

| Module | Focus | Entry evidence |
|---|---|---|
| [Day 01](day01/) | deterministic environment and oracle | [evidence](day01/evidence/) |
| [Day 02](day02/) | bounded agent and typed contracts | [evidence](day02/evidence/) |
| [Day 03](day03/) | baseline across difficulty tiers | [evidence](day03/evidence/) |
| [Day 04](day04/) | complete failure tracing | [evidence](day04/evidence/) |
| [Day 05](day05/) | incident reconstruction | [evidence](day05/evidence/) |
| [Day 06](day06/) | exact replay boundary | [evidence](day06/evidence/) |
| [Day 07](day07/) | reliability versus tool hops | [evidence](day07/evidence/) |
| [Day 08](day08/) | reproducible fault injection | [evidence](day08/evidence/) |
| [Day 09](day09/) | schema and latency detectors | [evidence](day09/evidence/) |
| [Day 10](day10/) | wrong data versus provider errors | [evidence](day10/evidence/) |
| [Day 11](day11/) | semantic corruption and loops | [evidence](day11/evidence/) |
| [Day 12](day12/) | fault catalog | [evidence](day12/evidence/) |
| [Day 13](day13/) | versioned evaluation | [evidence](day13/evidence/) |
| [Day 14](day14/) | intervals and paired tests | [evidence](day14/evidence/) |
| [Day 15](day15/) | per-fault detection accuracy | [evidence](day15/evidence/) |
| [Day 16](day16/) | narrow judge validation | [evidence](day16/evidence/) |
| [Day 17](day17/) | subgroup measurement | [evidence](day17/evidence/) |
| [Day 18](day18/) | bounded repair and retry | [evidence](day18/evidence/) |
| [Day 19](day19/) | retry crossover | [evidence](day19/evidence/) |
| [Day 20](day20/) | breaker and fallback | [evidence](day20/evidence/) |
| [Day 21](day21/) | fallback availability versus quality | [evidence](day21/evidence/) |
| [Day 22](day22/) | recovery mechanism matrix | [evidence](day22/evidence/) |
| [Day 23](day23/) | cross-component cascade | [evidence](day23/evidence/) |
| [Day 24](day24/) | multi-objective policy choice | [evidence](day24/evidence/) |
| [Day 25](day25/) | replay-verified postmortems | [evidence](day25/evidence/) |
| [Day 26](day26/) | self-explaining reproducibility | [evidence](day26/evidence/) |
| [Day 27](day27/) | assumption-free cold-reader reproduction | [evidence](day27/evidence/) |
| [Day 28](day28/) | findings-first Q1–Q5 publication and claim audit | [evidence](day28/evidence/) |
| [Day 29](day29/) | three-minute demo, one-page case study, comprehension gate | [evidence](day29/evidence/) |
| [Day 30](day30/) | spoken defense, expert outreach, OSS contribution, launch gate | [evidence](day30/evidence/) |

</details>

---

## Method

FAULTLINE enforces strict evidentiary separation between generation and verification: user-visible correctness is established exclusively by deterministic oracles and programmatic assertions, never by uncalibrated model self-assessment. Every headline metric is tied to committed telemetry traces, pre-registered hypotheses, and seed-pinned execution environments.

---

## Three-minute staff-engineer path

1. Watch or run the [2:45 incident demo](day29/DEMO.md).
2. Trace the red-to-green fix in [Incident 2 postmortem](day25/postmortems/INCIDENT-2026-02-LLM-02.md).
3. Verify the claims in [REPRODUCE.md](REPRODUCE.md).

---

## Reproduce

All test suites and benchmark dry-runs execute locally without network access or paid API credentials:

```bash
make venv          # Create virtualenv and install pinned requirements
make test          # Run 528 Phase 1 unit/integration tests
make phase2-test   # Run 126 Phase 2 tests (P00-P08, P13, P15, P16)
make p06 ARGS=--dry-run   # Dry-run P06 multi-trial sweep
make p07 ARGS=--dry-run   # Dry-run P07 variance analysis
make p08 ARGS=--dry-run   # Dry-run P08 MCPTox evaluation
make p08-replay           # Replay cached MCPTox execution traces
```

---

## Layout

```text
faultline-ai-reliability/
├── publications/              # Peer-reviewed papers, TeX source, and build artifacts
│   ├── publication_01_passk_reliability/
│   └── publication_02_mcptox_contract/
├── projects/                  # Phase 2 experimental packages (P01–P16)
│   ├── _corpus/               # Canonical 350-scenario graph corpus
│   ├── p06_passk/             # Multi-trial reliability & trace store
│   └── p08_mcptox/            # MCP defense & provenance engine
├── faultline_p2/              # Core Phase 2 harness, agent loop, and OTel tooling
├── day01/ … day30/            # Phase 1 daily simulation modules and evidence
├── tests/phase2/              # Phase 2 pytest suite (126 tests)
├── research/                  # Publication 1 pre-registration, data, and red-team gates
└── research_pub02/            # Publication 2 pre-registration, data, and red-team gates
```

---

## Budget

Total API spend across all experimental sweeps is **$30.08 USD**, comfortably within the pre-registered **$150.00 USD** repository ceiling. Every API request is tracked in an append-only `ledger.jsonl` recording exact timestamp, model rung, input/output tokens, and dollar cost computed from pinned pricing tables.

---

## Limitations

This repository reflects the experimental findings of a single author across a controlled set of commercial model endpoints accessed through a single unified API gateway. Evaluator calibrations for qualitative classifications were performed on held-out splits without multi-annotator human consensus panels. Model responses and serving latency are subject to cloud provider infrastructure drift and nondeterministic GPU reduction scheduling. Findings should be validated across diverse gateways and multi-turn human task distributions.

---

## Cite

```text
Sawarkar, S. (2026). FAULTLINE: Research Workbench for Agent Reliability and Tool-Poisoning Defense.
https://github.com/samirsawarkar/faultline-ai-reliability
```

Publications:
- Sawarkar, S. (2026). "Multi-Trial Reliability and Failure Concentration in Multi-Hop AI Agents: Grounding Collapse, Failure Taxonomy, and Evaluator Calibration." FAULTLINE AI Reliability Engineering.
- Sawarkar, S. (2026). "Runtime Provenance Contracts for Mitigating Tool Poisoning in MCP Agents: A Paired Evaluation on MCPTox Across Six Models." FAULTLINE AI Reliability Engineering.

---

## License

[MIT](LICENSE) © 2026 Samir Sawarkar
