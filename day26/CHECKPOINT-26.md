# CHECKPOINT-26 — self-explaining, runnable, continuous evidence

**Mission.** Make the evidence self-explanatory, one-command runnable, and
continuously checked.

**Required evidence.** Results-first README, Dockerfile, Makefile, pinned
versions, and green CI.

**Fail condition.** A README number cannot be traced to a script and result.

## Evidence contract

The root results table is backed by `day26/readme_claims.json`. Each registration
contains:

- the exact README result text;
- one or more displayed values;
- a source artifact;
- a JSON pointer;
- the expected typed value;
- a generator;
- a reproduction command.

`day26/scripts/audit_readme.py` verifies all registrations and rejects any
unregistered result row. A test mutates a displayed number and proves the audit
turns red.

## Reproduction commands

| scope | command | generated proof |
|---|---|---|
| full host | `make reproduce` | full test report, eval proof, experiment hashes, README audit |
| CI-sized host | `make reproduce-fast` | fast test report plus the same research checks |
| clean image | `make container-reproduce` | container attestation |
| release | `make release-check` | final Checkpoint 26 |

## Pinning

`day26/pins.json` is the canonical input manifest. It fixes:

- exact Python patch versions for CI and the container;
- pip;
- every direct and transitive Python dependency;
- the Docker tag and multi-architecture digest;
- third-party GitHub Actions by full commit SHA;
- experiment master/base seeds and hash-seed replay values;
- the release-candidate name.

The audit refuses compatible dependency ranges.

## Continuous checks

Research CI independently runs:

- the full test gate across every pinned Python runtime;
- the frozen evaluation and result-ID comparison;
- a fast byte-identical experiment subset;
- README number traceability;
- a clean-container build;
- a committed-evidence diff.

## Release gate

The release candidate may be tagged only after:

- `make reproduce` passes;
- the clean-container attestation passes;
- every Checkpoint 26 boolean is true;
- the intended commit contains all evidence referenced by the README.

The machine-readable state is in `evidence/reproduction_report.json`; the
rendered state is in `evidence/CHECKPOINT-26.md`.

## Mastery gate — all five

- **Can explain** — results precede implementation, with explicit provenance.
- **Can build** — one-command host and clean-container reproduction.
- **Can debug** — independent gates isolate the failing research layer.
- **Can measure** — deterministic counts, IDs, JSON pointers, and tree digests.
- **Can defend** — immutable pins, clean context, CI, evidence diff, and
  post-reproduction tag.
