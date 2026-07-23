# DECISIONS.md — Day 5 (trace store + viewer) decision log

Append-only. Date · id · decision · why · reversal cost.

---

### 2026-07-16 · D5-001 · Every reconstruction access pattern is indexed
**Decision.** Ship four indices (`trace+start`, `parent`, `status`,
`traces.status`) covering timeline, tree-walk, failure lookup, and failed-run
listing. Tests assert `EXPLAIN QUERY PLAN` says `USING INDEX`.
**Why.** The mission is "reconstruct in minutes." A stranger's queries must not
degrade to full scans as traces accumulate; an unindexed store is just a log
with extra steps.
**Reversal cost.** Dropping an index is one DDL line, but re-introduces scans.

### 2026-07-16 · D5-002 · Derive `traces.status` at ingest
**Decision.** Compute `ok|error` for the whole trace when ingesting and store it
on the `traces` row.
**Why.** "Which runs failed?" is the first question in an incident; answering it
should not require scanning the spans table. Denormalization is safe here because
a trace is immutable once ingested.
**Reversal cost.** Recompute from spans if the rule changes; cheap.

### 2026-07-16 · D5-003 · Reconstruction degrades gracefully, never dead-ends
**Decision.** Missing fields render as explicit `<missing>` placeholders; a
broken parent link falls back to sequence order and is flagged as an orphan; a
deleted sibling surfaces as a sequence gap. Reconstruction still names the
failure.
**Why.** The fail condition is "a stranger cannot reconstruct the run." Real
stores lose data; the viewer must stay useful under damage rather than crash or
mislead. Proven by the deletion attack over four scenarios.
**Reversal cost.** None desired.

### 2026-07-16 · D5-004 · Sibling-gap detection, not raw start_seq deltas
**Decision.** Detect a deleted span as a break between consecutive *siblings*
under one parent, not as any gap in the global start_seq sequence.
**Why.** Day-4's logical clock ticks on both entry and exit, so siblings
naturally start two ticks apart. A naive "delta > 1" flags every healthy trace.
Comparing siblings gives zero false positives on intact traces and still catches
real deletions.
**Reversal cost.** None; it's strictly more correct.

### 2026-07-16 · D5-005 · A deterministic SVG is the committed "screenshot"
**Decision.** Commit a dependency-free SVG render of the failed run as the visual
artifact; do not commit a PNG screenshot.
**Why.** A real screenshot is non-reproducible and needs a browser in CI. An SVG
is a viewable image, regenerates byte-for-byte, and CI can `git diff` it. Honest
label: it is a rendered snapshot of the viewer, not a photographed screen.
**Reversal cost.** Add a headless-browser PNG step later if a raster is required.

### 2026-07-16 · D5-006 · The on-disk .db is regenerated, not committed
**Decision.** `git`-ignore `evidence/trace.db`; commit the schema, the code, and
the text/SVG/JSON evidence; rebuild the db with `build_store.py`.
**Why.** SQLite file bytes depend on the engine version and aren't deterministic,
so a committed binary would churn and break byte-diff gates. The store's *value*
is the schema + queries, which are in code.
**Reversal cost.** Commit a SQL dump instead if a frozen fixture is ever needed.
