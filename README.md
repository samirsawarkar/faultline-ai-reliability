# FAULTLINE

**A reproducible workbench for measuring where document-grounded AI systems break — built in public, one disciplined day at a time.**

[![CI](https://github.com/samirsawarkar/faultline-ai-reliability/actions/workflows/ci.yml/badge.svg)](https://github.com/samirsawarkar/faultline-ai-reliability/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-236%20passing-brightgreen.svg)](#quickstart)

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
| **Every number has an interval** | Success rates carry Wilson 95% CIs, and claims like "naive compounding is wrong" are made precise as the first hop where the naive and measured intervals are disjoint (n=3) — never a bare point estimate. |
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
| **[07](day7/)** | Q1 — reliability vs required tool hops | ✅ Done | hop-count sweep, per-step accounting, measured-vs-naive curve with Wilson CIs, Checkpoint 7 |
| **[08](day8/)** | Reproducible fault injection + independent ground truth | ✅ Done | 10-field fault spec, deterministic triggers, out-of-band truth log, cross-seed integrity attack (0 leaks) |
| **[09](day9/)** | F1/F2 fault families + deterministic detectors, scored vs truth | ✅ Done | schema + latency-budget detectors, severity sweep with precision/recall against the injection log, fault cards |
| **[10](day10/)** | F3/F4 — schema-valid wrong data vs explicit provider errors | ✅ Done | correctness oracle, semantic invariant, mixed classifier, false-negative analysis (40% of wrong-data escapes), circuit-breaker signal |
| **[11](day11/)** | F5/F6 — completing the six-fault spectrum | ✅ Done | context corruption (semantic) + loop exhaustion (deterministic), F1–F6 deterministic-vs-semantic map, committed Q2 split hypothesis |
| **[12](day12/)** | Fault catalog + gallery | ✅ Done | six complete fault cards (trigger/trace/detector/recovery/metric), gallery (JSON/MD/HTML), reproducibility + ground-truth integrity audit, taxonomy by producing component |
| **[13](day13/)** | Evaluation harness + versioned dataset | ✅ Done | content-addressed dataset version, deterministic stratified splits, immutable oracle-grounded eval results, contamination + stale-reuse attacks, dataset card |
| 14–50 | Intervals, recovery, cascade, and hardening | 🔜 Planned | building on the frozen days above |

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
├── day7/                 Q1: reliability vs required tool hops (stdlib only)
│   ├── faultline_hops/   simulator, sweep+accounting, stats (Wilson), model, figure, observability
│   ├── scripts/          run_q1 (results + figure + investigation)
│   ├── tests/            sweep/stats/model/observability gate (18 tests)
│   ├── evidence/         q1_results.json, measured_vs_naive.svg, investigation.json
│   └── CHECKPOINT-7 / LEARN-compounding / DECISIONS / REFLECTION.md
├── day8/                 reproducible fault injection + independent ground truth (stdlib only)
│   ├── faultline_inject/ spec (10 fields), triggers, faults, truth log, boundary, integrity
│   ├── scripts/          make_evidence (spec + integrity report + labelled fault trace)
│   ├── tests/            spec/triggers/boundary/integrity gate (45 tests)
│   ├── evidence/         injector_spec.json, integrity_report.json, fault_trace.json
│   └── CHECKPOINT-8 / LEARN-chaos / DECISIONS / REFLECTION.md
├── day9/                 F1/F2 fault families + detectors, scored vs truth (stdlib only)
│   ├── faultline_detect/ schema, latency, detectors, injectors, runner, score, experiment, cards
│   ├── scripts/          make_evidence (fault cards + detector sweep + scored runs + traces)
│   ├── tests/            schema/detectors/score/experiment gate (22 tests)
│   ├── evidence/         fault_cards.json, detector_sweep.json, scored_runs.json, trace_f1/f2.json
│   └── CHECKPOINT-9 / LEARN-validation-latency / DECISIONS / REFLECTION.md
├── day10/                F3/F4 — schema-valid wrong vs provider errors (stdlib only)
│   ├── faultline_contracts/ oracle, corruptions, invariant+classifier, breaker, runner, score
│   ├── scripts/          make_evidence (cards + contract report + false negatives + traces)
│   ├── tests/            oracle/corruption/classifier/score gate (18 tests)
│   ├── evidence/         contract_report.json, false_negatives.json, classifier_boundaries.json, trace_f3/f4.json
│   └── CHECKPOINT-10 / LEARN-semantic-invariants / DECISIONS / REFLECTION.md
├── day11/                F5/F6 — completing the six-fault spectrum (stdlib only)
│   ├── faultline_spectrum/ task/loop, F5/F6 injectors, detectors, runner, score, spectrum_map
│   ├── scripts/          make_evidence (map + Q2 hypothesis + escape examples + traces)
│   ├── tests/            task/detectors/score/map gate (12 tests)
│   ├── evidence/         deterministic_vs_semantic_map.json, q2_split_hypothesis.json, escape_examples.json, trace_f5/f6.json
│   └── CHECKPOINT-11 / LEARN-context-termination / DECISIONS / REFLECTION.md
├── day12/                fault catalog + gallery (stdlib only)
│   ├── faultline_catalog/ cards, catalog, traces, gallery, taxonomy, audit
│   ├── scripts/          make_evidence (catalog + gallery + audit + taxonomy + traces)
│   ├── tests/            catalog/audit gate (12 tests)
│   ├── evidence/         catalog.json, GALLERY.md, catalog.html, audit_report.json, taxonomy.json, traces/F1-F6.json
│   └── CHECKPOINT-12 / LEARN-taxonomy / DECISIONS / REFLECTION.md
├── day13/                evaluation harness + versioned dataset (stdlib only)
│   ├── faultline_eval/   dataset (versioned+splits), predict, runner, leakage, card
│   ├── scripts/          eval.py (reproducible command), make_evidence
│   ├── tests/            dataset/eval/leakage gate (14 tests)
│   ├── evidence/         manifest.json, splits.json, eval_result.json, leakage_report.json, DATASET_CARD.md
│   └── CHECKPOINT-13 / LEARN-eval-infra / DECISIONS / REFLECTION.md
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
make test                                        # full gate: 236 tests, day1–day13

# Re-prove the headline claims yourself:
make determinism      # Day 1: byte-identical env across processes/hashseeds
make attack           # Day 2: forced over-budget task → clean INCOMPLETE
make day4-traces      # Day 4: 100 forced failures → all complete error spans
make day5-evidence    # Day 5: reconstruct a failed run; survive deletions
make day6-replay      # Day 6: capture, replay exactly, report the boundary
make day7-q1          # Day 7: measure reliability vs hops; naive falsified at n=3
make day8-inject      # Day 8: inject faults across seeds; identical triggers, 0 label leaks
make day9-detect      # Day 9: sweep severity; score F1/F2 detectors vs injection truth
make day10-contracts  # Day 10: F3/F4; which wrong values escape contract validation
make day11-spectrum   # Day 11: F5/F6; deterministic-vs-semantic map + Q2 hypothesis
make day12-catalog    # Day 12: fault catalog + gallery + reproducibility/integrity audit
make day13-eval       # Day 13: run the versioned, leakage-resistant eval (test split)
```

Requires Python ≥ 3.9. Days 1 and 4–13 need no third-party packages; Days 2–3
need `pydantic` v2 (see `requirements.txt`).

## License

[MIT](LICENSE) © 2026 Samir Sawarkar
