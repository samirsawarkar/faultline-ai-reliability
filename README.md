# FAULTLINE

**A reproducible workbench for measuring where document-grounded AI systems break — built in public, one disciplined day at a time.**

[![CI](https://github.com/samirsawarkar/faultline-ai-reliability/actions/workflows/ci.yml/badge.svg)](https://github.com/samirsawarkar/faultline-ai-reliability/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-95%20passing-brightgreen.svg)](#quickstart)

---

## The thesis

AI systems that answer from documents fail along **predictable faultlines** —
they return a plausible answer while citing the wrong source, no source, or a
source that never contained the fact — and today those failures are graded by
*eyeballing*, which is neither reproducible nor honest.

FAULTLINE replaces the eyeball with a **seeded, deterministic environment** and a
**required-source oracle**: the same seed builds the same corpus and questions
bit-for-bit on any machine, and a pure-function oracle counts an answer as
passing only when it is both *correct* **and** *grounded* in the one document
that actually holds the fact. Because the ruler cannot drift and the judge cannot
be bargained with, every number FAULTLINE reports is exactly reproducible — the
precondition for trusting any claim that one system is more grounded than another.

## Why this repo exists

This is an **AI reliability engineering** portfolio built as a 50-day arc. Each
day is a small, self-contained, fully-owned increment that holds itself to the
standards below — not a demo, but a specimen you could put under a microscope.

### Reliability standards this repo holds itself to

| Standard | How it shows up |
| --- | --- |
| **Determinism as a gate** | Seeded RNG only; no wall-clock, no hash-order iteration. Same seed → byte-identical output, re-proven in CI across 3 Python versions and multiple processes. |
| **An honest oracle** | Correctness is a *pure function*, not a judgment call. A right answer with a wrong/absent citation does **not** pass. |
| **Typed contracts** | Every agent boundary is a Pydantic model with `extra="forbid"`; malformed input becomes a structured outcome, never an escaped exception. |
| **Bounded execution** | The agent loop cannot hang — termination is structural (a step cap in the loop shape), not a hoped-for timeout. |
| **Two-layer judging** | Schema validity (is it well-formed?) is kept separate from semantic correctness (is it right?). Both are required; neither is sufficient. |
| **Failures leave a record** | Every risky operation is a span written at entry and closed in `finally`; a crash cannot escape without a complete error span (re-proven over 100 forced failures). |
| **Redaction at the trace layer** | Spans store leak-free payload references; secrets are masked even inside captured error messages — the injected secret never reaches a committed trace. |
| **Reconstructable under data loss** | Runs persist in an indexed SQLite store; a stranger reconstructs the failure from the viewer alone, and it still names the root cause after fields or whole spans are deleted. |
| **Claims never exceed evidence** | Replay separates playback from re-execution: captured simulator runs replay *and* re-execute byte-identically, while a real-provider stand-in is reported as playback-only — the reproducibility boundary is documented, not overstated. |
| **Evidence, not assertions** | Every claim ships a committed, regenerable artifact under `dayN/evidence/`. |
| **Decision logs** | Every non-obvious choice is recorded with its *why* and its *reversal cost* (`DECISIONS.md`, globally numbered D-001…). |
| **Green CI** | Unit tests **and** the determinism proof **and** the fault attack run on every push. |

## The 50-day arc

| Day | Focus | Status | Key artifacts |
| --- | --- | --- | --- |
| **[01](day1/)** | Deterministic environment + required-source oracle | ✅ Done | seeded corpus, `oracle_check`, cross-process determinism proof |
| **[02](day2/)** | Bounded, deterministic single agent + typed contracts | ✅ Done | reason→tool→observe loop, 3 typed tools, forced over-budget attack |
| **[03](day3/)** | The zero point: baseline across difficulty tiers | ✅ Done | seeded batch runner, Wilson intervals, success-vs-hops figure, reproducibility gate |
| **[04](day4/)** | Tracing: linked spans that survive failures | ✅ Done | entry-written/`finally`-closed spans, redaction policy, 100-run forced-failure gate |
| **[05](day5/)** | Reconstruct a failed run in minutes | ✅ Done | indexed SQLite trace store, timeline viewer, SVG snapshot, deletion-survival attack |
| **[06](day6/)** | Exact replay + reproducibility boundary | ✅ Done | replay bundle, deterministic replay harness, playback-vs-reexecution difference report |
| 07–50 | Fault injection, measurement, and hardening | 🔜 Planned | building on the frozen days above |

> The arc is deliberately cumulative: Day 2's agent runs against Day 1's frozen
> environment, and later days inject faults into this fully-owned baseline. That
> coupling is exactly why FAULTLINE is **one monorepo**, not fifty fragments.

## Repository map

```
faultline-ai-reliability/
├── day1/                 deterministic env + oracle (stdlib only)
│   ├── faultline/        env.py (generator), oracle.py (the judge)
│   ├── scripts/          determinism + hand-check experiments
│   ├── tests/            the Day-1 gate (11 tests)
│   ├── evidence/         digests, determinism report, sample env
│   └── THESIS / MEASUREMENT / DECISIONS / LEARN.md
├── day2/                 bounded single agent + Pydantic contracts
│   ├── faultline_agent/  contracts, tools, agent loop, verdict
│   ├── scripts/          over-budget attack, structured run, validity-vs-correctness
│   ├── tests/            the Day-2 gate (22 tests)
│   ├── evidence/         budget termination, sample run, schema-vs-semantic
│   └── README / DECISIONS / LEARN / MARKET.md
├── day3/                 the zero point: reproducible baseline across tiers
│   ├── faultline_baseline/  config, tiers, accounting, Wilson stats, runner, SVG
│   ├── scripts/          build_baseline, attack_mislabeled
│   ├── tests/            the reproducibility gate (19 tests)
│   ├── evidence/         baseline.json, success_vs_hops.svg, mislabel_attack.json
│   └── README / DECISIONS / LEARN-wilson / CHECKPOINT-3.md
├── day4/                 tracing: linked spans that survive failures (stdlib only)
│   ├── faultline_trace/  schema, tracer, redaction, audit, instrumented pipeline
│   ├── scripts/          make_traces (example traces + 100-run failure report)
│   ├── tests/            the forced-failure gate (19 tests)
│   ├── evidence/         trace_normal.json, trace_failed.json, forced_failure_report.json
│   └── README / SPAN_SCHEMA / REDACTION / DECISIONS / LEARN-otel / REFLECTION.md
├── day5/                 SQLite trace store + timeline viewer (stdlib only)
│   ├── faultline_store/  store+indices, reconstruct, terminal viewer, SVG, attack
│   ├── scripts/          build_store, timeline (CLI), make_evidence
│   ├── tests/            store/reconstruct/attack gate (13 tests)
│   ├── evidence/         failed_run.svg, timeline_failed.txt, attack_report.json, incident_narrative.md
│   └── README / LEARN-sqlite / DECISIONS / REFLECTION.md
├── day6/                 replay bundle + deterministic replay harness (stdlib only)
│   ├── faultline_replay/ bundle, providers (record/replay), capture, replay, diff, report
│   ├── scripts/          make_evidence, replay_demo (CLI)
│   ├── tests/            exact-replay + boundary + guards gate (11 tests)
│   ├── evidence/         bundle_simulator.json, replay_simulator.json, replay_report.json
│   └── README / LIMITATIONS / LEARN-reproducibility / DECISIONS / REFLECTION.md
├── .github/workflows/    CI: tests + determinism proof + fault attacks
├── requirements.txt      pinned deps (pydantic, pytest)
└── Makefile              make venv && make test
```

Each day carries its own README and a **mastery gate** — you should be able to
*explain*, *build*, *debug*, *measure*, and *defend* everything in it.

## Quickstart

```bash
# Day 1 is standard-library only:
cd day1 && python3 -m pytest tests/ -q          # 11 tests

# Day 2 adds pydantic — from the repo root:
make venv                                        # .venv from pinned deps
make test                                        # full gate: 95 tests, day1–day6

# Re-prove the headline claims yourself:
make determinism      # Day 1: byte-identical env across processes/hashseeds
make attack           # Day 2: forced over-budget task → clean INCOMPLETE
make day4-traces      # Day 4: 100 forced failures → all complete error spans
make day5-evidence    # Day 5: reconstruct a failed run; survive deletions
make day6-replay      # Day 6: capture, replay exactly, report the boundary
```

Requires Python ≥ 3.9. Days 1, 4, 5, and 6 need no third-party packages; Days
2–3 need `pydantic` v2 (see `requirements.txt`).

## License

[MIT](LICENSE) © 2026 Samir Sawarkar
