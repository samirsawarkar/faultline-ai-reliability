# FAULTLINE

**A reproducible research workbench for finding where document-grounded AI systems fail—and testing whether recovery actually improves the user outcome.**

[![CI](https://github.com/samirsawarkar/faultline-ai-reliability/actions/workflows/ci.yml/badge.svg)](https://github.com/samirsawarkar/faultline-ai-reliability/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-433%20passing-brightgreen.svg)](day26/evidence/test_report.json)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Phase 1** established the simulation foundations, failure taxonomy, and recovery mechanisms across 30 reproducible days. **Phase 2** measures real-world LLM agent reliability against live model APIs on a canonical 350-scenario multi-hop corpus.

---

### Grounding Zero-Point (Phase 2 / Project P3)

Real agent grounded pass rate on multi-hop document retrieval degrades steeply as required retrieval depth increases: **100.0%** $\to$ **61.2%** $\to$ **7.6%** on R2 (`glm-5.3-flash`), **20.9%** $\to$ **4.5%** $\to$ **0.0%** on R4 (`gpt-5.6-luna`), and **73.1%** $\to$ **26.9%** $\to$ **1.5%** on R6 (`deepseek-v4-pro`).

![Grounding Zero-Point](projects/p03_grounding/figure.svg)

```bash
pip install -e .
make p03  # runs P3 Grounding Zero-Point reproduction
```

---

## Start here

**Hiring or evaluating this work?** Read the
[one-minute engineering brief](HIRING-MANAGER.md), then inspect the
[architecture and decision boundaries](ARCHITECTURE.md). Together they show the
problem, the measurable outcomes, the system design, the tradeoffs, and the
claims this repository deliberately does not make.

**Reproducing or reviewing the research?** Follow
[REPRODUCE.md](REPRODUCE.md). Every headline below is bound to a committed JSON
value and generating command; CI rejects drift.

## Three-minute staff-engineer path

1. Watch or run the [2:45 incident demo](day29/DEMO.md).
2. Read the [one-page case study](day29/CASE-STUDY.md).
3. Inspect the [system architecture](ARCHITECTURE.md) and its reliability
   invariants.
4. Open the [Q1–Q5 technical article](day28/ARTICLE.md) only when you need the
   full evidence argument.
5. Use the [staff-level defense](day30/DEFENSE.md) to challenge every core
   decision and limitation.

The short path shows one complete chain—run → fault → trace → recover → replay—
and states both what FAULTLINE proved and what remains unproven in production.

## Results

<!-- RESULTS:START -->
| Question | Result | Evidence and generating script | Reproduce |
|---|---|---|---|
| When does required tool depth break the naive reliability model? | **Measured success 0.818 versus naive 0.91833; first interval separation at 3 hops** | [result](day07/evidence/investigation.json) · [script](day07/scripts/run_q1.py) | `make day07-q1` |
| Does the frozen detector evaluation reproduce? | **Frozen test evaluation: F1 0.842105 over 17 samples** | [result](day13/evidence/eval_result.json) · [script](day13/scripts/make_evidence.py) | `make day13-evidence` |
| Does fallback preserve availability without preserving quality? | **Availability 0.6667 → 1.0 while strict quality among answers 1.0 → 0.75** | [result](day21/evidence/availability_quality_comparison.json) · [script](day21/scripts/make_evidence.py) | `make day21-q4` |
| Which reference cascade policy wins on correct success, cost, and latency? | **Reference P4: success 0.9325, mean cost 1.4656, p95 latency 50.0** | [result](day24/evidence/policy_comparison.json) · [script](day24/scripts/make_evidence.py) | `make day24-q5` |
| Do incident fixes fail before and stay fixed afterward? | **2 incidents replay red → green; Checkpoint 25 passes** | [result](day25/evidence/checkpoint_25.json) · [script](day25/scripts/make_evidence.py) | `make day25-postmortems` |
| Does the complete repository gate pass? | **433 tests collected and passed** | [result](day26/evidence/test_report.json) · [script](day26/scripts/run_test_gate.py) | `make reproduce` |
<!-- RESULTS:END -->

Every result cell above is executable metadata, not hand-maintained prose.
[The traceability manifest](day26/readme_claims.json) binds each displayed number
to a JSON pointer, source artifact, generator, and command. CI fails when any
value drifts or a result row lacks a registration.

## Method

FAULTLINE uses seeded simulators, an oracle that keeps correctness separate from
schema validity, complete failure traces, paired experiments, uncertainty
intervals, and replay-verified incident fixes.

The research loop is:

```text
question → frozen seeds/config → paired experiment → result artifact
         → attack → trace-linked fix → red/green replay → CI
```

The important boundary is user-visible correctness. Availability, containment,
and a plausible answer are recorded separately and never promoted to success.

## One-command reproduction

Cold readers should start with [REPRODUCE.md](REPRODUCE.md). It contains the
complete public clone command, exact release revision, host requirements,
expected numbers, and failure actions; its command block is executed verbatim by
the Day 27 cold-start test.

From a checkout with Python available:

```bash
make venv
make reproduce
```

`make reproduce` runs every isolated test suite, re-executes the frozen
evaluation, regenerates a fast representative experiment subset, verifies
byte-identical evidence, audits every results-table number, and writes
[Checkpoint 26](day26/evidence/CHECKPOINT-26.md).

For the pinned clean-room build:

```bash
make container-reproduce
```

The [Dockerfile](Dockerfile) pins its Python base by tag and multi-architecture
digest, installs the fully resolved [dependency lock](requirements.txt), runs the
full reproduction while building, then exposes the fast gate as its default
command.

The CI-sized host command is:

```bash
make reproduce-fast
```

## Reproducibility contract

- Runtime, package, build-action, image-digest, and seed pins live in
  [pins.json](day26/pins.json).
- Every dependency is an exact equality in [requirements.txt](requirements.txt);
  compatible ranges are rejected.
- Every headline result links to both its machine-readable artifact and
  generating script.
- Experiments use explicit seeds and a fixed Python hash seed.
- The fast subset regenerates tool-hop, fallback-quality, and postmortem evidence
  and compares hashes before and after.
- CI runs the full tests across the pinned Python patch matrix, the frozen
  evaluation and fast experiments, the README audit, and the clean Docker build.
- Release readiness is executable in
  [reproduction_report.json](day26/evidence/reproduction_report.json).

## Research modules

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

Each module carries its own question, method, tests, evidence, decision log, and
mastery gate. Start with the results table; descend into a module only when you
need its assumptions or failure analysis.

## Release candidate

Environment identities remain declared in [pins.json](day26/pins.json). The
cold-reader revision and public source are declared in
[protocol.json](day27/protocol.json). `v0.27.0-rc1` is tagged only after the clean
container, exact headline output, and Checkpoint 27 are green.

## Engineering standards

[Architecture](ARCHITECTURE.md) ·
[Contributing](CONTRIBUTING.md) ·
[Security](SECURITY.md) ·
[Reproduction](REPRODUCE.md)

## License

[MIT](LICENSE) © 2026 Samir Sawarkar
