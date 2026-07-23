# FAULTLINE — thesis

**AI systems that answer from documents fail along predictable faultlines —
they return a plausible answer while citing the wrong source, no source, or a
source that never contained the fact — and today those failures are graded by
eyeballing, which is neither reproducible nor honest.** FAULTLINE replaces the
eyeball with a seeded, deterministic environment and a required-source oracle:
the same seed builds the same corpus and questions bit-for-bit on any machine,
and a pure-function oracle counts an answer as passing only when it is both
correct *and* grounded in the one document that actually holds the fact. Because
the ruler cannot drift and the judge cannot be bargained with, every number
FAULTLINE reports about where a system breaks is exactly reproducible — which is
the precondition for trusting any claim that one retrieval system is more
grounded than another.
