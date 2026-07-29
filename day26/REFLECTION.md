# REFLECTION — five-minute mission reflection (Day 26)

**Mission.** Make evidence self-explanatory, one-command runnable, and
continuously checked.

**The strongest change.** README claims are now data dependencies. A reviewer can
move from a displayed result to an exact JSON value and regenerate it with the
adjacent command.

**The build lesson.** Exact top-level dependencies were not enough. The release
lock includes transitive packages, the base image uses a manifest digest, CI
runtimes use patch versions, and actions use commit SHAs.

**The research-CI lesson.** Tests alone do not catch a stale chart, changed eval
result, or hand-edited README number. The fast gate crosses all three boundaries.

**The debug lesson.** Separate reports answer which layer failed: test inventory,
frozen eval, experiment bytes, README traceability, container contract, or
container execution.

**The honesty check.** A Dockerfile is not clean-reproduction evidence until it
has actually built and its internal attestation has been read. The release tag is
blocked on that proof.

**Mastery gate.**

- *Explain* — results-first root README and traceability chain.
- *Build* — Dockerfile, exact pins, Make profiles, and CI jobs.
- *Debug* — independent deterministic reports per layer.
- *Measure* — counts, result IDs, JSON pointers, and evidence-tree digests.
- *Defend* — [CHECKPOINT-26.md](CHECKPOINT-26.md), immutable pins, clean build,
  and post-proof tag order.
