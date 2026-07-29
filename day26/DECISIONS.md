# DECISIONS.md — Day 26 reproducibility decision log

Append-only. Date · id · decision · why · reversal cost.

---

### 2026-08-05 · D26-001 · Put measured questions and answers first
**Decision.** The root README opens with the result table before method or module
chronology.
**Why.** A reviewer should learn what was measured before learning how the
repository is organized.
**Reversal cost.** None; module documentation remains linked.

### 2026-08-05 · D26-002 · Register every headline value
**Decision.** Bind README result text to typed JSON pointers, artifacts,
generators, and commands.
**Why.** Links alone do not detect stale prose. The manifest makes drift
executable.
**Reversal cost.** Low; new result rows add registrations.

### 2026-08-05 · D26-003 · Keep per-day test isolation
**Decision.** The full test reporter invokes each day suite in a fresh subprocess.
**Why.** Cumulative modules reuse package names and path setup. Isolation matches
the established Make gate and avoids import-cache coupling.
**Reversal cost.** Medium; a future packaging migration could enable one pytest
process.

### 2026-08-05 · D26-004 · Remove timing from committed reports
**Decision.** Store status and counts, not elapsed wall time.
**Why.** Timing varies by host and does not support the correctness claim.
**Reversal cost.** None; CI logs retain operational duration.

### 2026-08-05 · D26-005 · Pin the multi-architecture image manifest
**Decision.** Use an exact Python tag plus OCI manifest digest.
**Why.** A tag alone can move; an architecture-specific digest would make the
Dockerfile non-portable across the supported build hosts.
**Reversal cost.** Low; intentional base updates change one reviewed pin.

### 2026-08-05 · D26-006 · Fully resolve transitive Python packages
**Decision.** Keep exact equality pins for every installed package.
**Why.** Top-level pins can still resolve different transitive code later.
**Reversal cost.** Medium; upgrades require regenerating and testing the lock.

### 2026-08-05 · D26-007 · Make image construction execute the research
**Decision.** `docker build` runs the full reproduction as a non-root user.
**Why.** A buildable image that has not reproduced the findings is only packaging
evidence.
**Reversal cost.** Medium; build time is intentionally higher.

### 2026-08-05 · D26-008 · Split CI into independent scientific gates
**Decision.** Full tests, research reproduction, and clean-container build are
separate jobs.
**Why.** Independent failure signals make drift easier to locate and prevent one
large script from hiding which contract failed.
**Reversal cost.** Low; job scopes can evolve independently.

### 2026-08-05 · D26-009 · Tag only the reproduced commit
**Decision.** Create `v0.26.0-rc1` only after host, container, and final checkpoint
are green.
**Why.** The tag is a claim about a commit; it must not precede its evidence.
**Reversal cost.** None before publication; published tags should remain immutable.

### 2026-08-05 · D26-010 · Treat `make` as an explicit image dependency
**Decision.** Install the exact Debian package version in the slim image.
**Why.** The first clean build proved the host tool was absent from the declared
environment. The one-command contract must include its command runner.
**Reversal cost.** Low; a base-image update must verify the package pin.

### 2026-08-05 · D26-011 · Include CI configuration in the clean context
**Decision.** Exclude Git history but copy `.github/workflows`.
**Why.** The reproduction audits the continuous-check contract itself. Removing
the workflow made that claim unverifiable inside the image.
**Reversal cost.** None; workflow files are small deterministic build inputs.

### 2026-08-05 · D26-012 · Canonicalize derived statistical floats
**Decision.** Serialize McNemar statistics at 15 significant decimal digits.
**Why.** The clean Python 3.12 image and the Python 3.9 host produced the same
statistical conclusion but differed by one final `libm` bit. A canonical
precision keeps evidence byte-stable across every supported CI runtime without
changing a reported decision or retaining false machine precision.
**Reversal cost.** Medium; changing the precision requires regenerating every
artifact that contains McNemar statistics.
