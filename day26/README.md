# FAULTLINE — Day 26: self-explaining reproducibility

Make the research evidence understandable from the result backward, runnable with
one command, reproducible in a pinned clean container, and continuously checked.

> **Fail condition:** a README number cannot be traced to a script and result.
> **Status: not triggered.** Six headline rows are registered in
> `readme_claims.json`; every displayed value resolves through a JSON pointer to
> a committed artifact, an existing generator, and a Make target. Tampering with
> a displayed value turns the audit red.

## Results first

The repository README now opens with the research questions and measured answers,
not the implementation chronology. Each row provides:

- the question;
- the exact displayed result;
- a machine-readable result artifact;
- its generating script;
- the command that reproduces it.

The executable traceability output is
`evidence/readme_traceability.json`.

## One-command profiles

| command | purpose |
|---|---|
| `make reproduce` | every isolated day test, frozen eval, fast experiment subset, README audit, Checkpoint 26 |
| `make reproduce-fast` | CI-sized test profile plus the same eval, experiments, and claim audit |
| `make container-reproduce` | build the digest-pinned clean image, read its internal attestation, write container proof |
| `make release-check` | require clean-container proof and final Checkpoint 26 |

The full test runner writes a timing-free report so the evidence remains
byte-stable across machines. Test suites remain isolated per day to avoid Python
module-name collisions across the cumulative repository.

## Clean-container contract

The root `Dockerfile`:

- uses the exact Python tag and multi-architecture manifest digest in
  `pins.json`;
- installs the pinned pip version;
- installs only the fully resolved exact dependency lock;
- fixes locale, hash seed, and source-date environment;
- copies no host virtual environment, cache, or Git metadata;
- switches to a non-root user;
- runs `make reproduce` during the image build.

A successful image build is therefore a reproduction result, not merely a
packaging result.

## Research CI

The workflow has three independent gates:

1. full tests on the exact Python patch-version matrix;
2. frozen evaluation, fast deterministic experiments, README traceability, and
   evidence-diff check;
3. a clean Docker build whose Dockerfile runs the full reproduction.

Third-party actions are pinned to immutable commit SHAs.

## Fast experiment subset

The fast profile regenerates representative evidence from three distinct layers:

- tool-hop reliability and confidence-interval divergence;
- paired fallback availability and semantic quality;
- trace-linked incident fixes and cross-process red→green replay.

The runner hashes every selected evidence tree before and after regeneration and
fails on any byte drift.

## What's here

```text
faultline_repro/
  utils.py       canonical JSON pointer and digest helpers
  audit.py       README, pin, Docker, Make, and CI contracts
  report.py      Checkpoint 26 aggregation and renderer
scripts/
  run_test_gate.py
  verify_eval.py
  run_fast_experiments.py
  audit_readme.py
  container_reproduce.py
  container_attestation.py
  make_evidence.py
tests/           traceability, pin, build, CI, and report gates
evidence/
  test_report.json
  fast_test_report.json
  eval_verification.json
  fast_experiment_report.json
  readme_traceability.json
  container_verification.json
  reproduction_report.json
  CHECKPOINT-26.md
pins.json · readme_claims.json
```

## Mastery gate — all five

- **Can explain** — navigate from question to result, assumptions, generator, and
  evidence.
- **Can build** — produce a pinned non-root clean image and deterministic
  one-command profiles.
- **Can debug** — identify whether tests, eval, experiment bytes, README claims,
  pins, or container caused a red gate.
- **Can measure** — preserve test counts, eval IDs, artifact digests, and
  checkpoint states without timing noise.
- **Can defend** — pin all moving inputs, reject unregistered numbers, run
  independent CI gates, and tag only after clean reproduction.
