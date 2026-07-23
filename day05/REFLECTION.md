# REFLECTION.md — five-minute mission reflection (Day 5)

**Mission.** Let a stranger reconstruct a failed run in minutes.
**Fail condition.** A stranger cannot reconstruct the run from the viewer. —
*Not triggered:* the incident narrative was written from the viewer alone, and
reconstruction survives every deletion scenario (`evidence/attack_report.json`,
`all_scenarios_reconstructable: true`).

**Do we need an LLM API now? No.** Day 5 is storage + viewer; `sqlite3` is
stdlib. Traces come from Day 4's deterministic pipeline, so the store, the SVG,
and the attack report all regenerate byte-for-byte.

**Mastery gate.**
- *Explain* — [LEARN-sqlite.md](LEARN-sqlite.md): why SQLite fits now and the exact
  conditions that force Postgres (concurrent writers, cross-host, strict types at
  scale, ingest volume).
- *Build* — [faultline_store/](faultline_store/): indexed SQLite store, terminal
  viewer, deterministic SVG, reconstruction.
- *Debug* — the viewer *is* the debugger: it names the root-cause span, the
  failing path, gaps, and orphans, straight from the store.
- *Measure* — reconstruction is index-backed (`SEARCH ... USING INDEX`, asserted
  in tests); the attack quantifies store-vs-rawlog scan cost; timing recorded in
  `reconstruction_timing.json`.
- *Defend* — [DECISIONS.md](DECISIONS.md): indices, denormalized status, graceful
  degradation, sibling-gap detection, and the SVG/db-regeneration choices.

**What I'd watch next.** Retention/partitioning once traces accumulate; a
`spans(trace_id, kind)` index if kind-filtered views appear; and the Postgres
migration the moment ingest goes multi-writer (the `TraceStore` seam is where it
happens).

**One honest limitation.** "Reconstruction timing" is real wall-clock but tiny
and machine-dependent, so it lives in its own non-diffed file; the *correctness*
of reconstruction — not its milliseconds — is what the tests and the byte-diffed
evidence guarantee.
