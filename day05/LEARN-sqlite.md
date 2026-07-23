# LEARN-sqlite.md — SQLite limits, and when Postgres becomes necessary

Notes from studying SQLite's design, mapped to the trace store.

## Why SQLite is right for a trace store (now)

- **Embedded, zero-ops.** The database is a single file opened in-process. A
  stranger reconstructs a run with `sqlite3 trace.db` and no server, no port, no
  credentials — which is exactly the "reconstruct in minutes" goal.
- **Indexes are real B-trees.** `EXPLAIN QUERY PLAN` shows our lookups as
  `SEARCH ... USING INDEX`, not `SCAN`. Finding the failure in a trace is O(log n),
  not a log grep.
- **Reads scale fine.** Many concurrent readers are cheap; a trace store is
  read-mostly after ingest.

## The limits that actually bite

1. **One writer at a time.** SQLite locks at the *database* level for writes
   (WAL mode allows readers during a write, but still a single writer). Fine for
   one ingest process; a fleet of agents all writing spans concurrently will
   serialize and eventually contend.
2. **No network access.** It's a library, not a service. Sharing a store across
   machines means shipping a file or bolting on a server — the moment you want
   "many producers, central store," SQLite is the wrong shape.
3. **Coarse concurrency / no per-row MVCC.** Postgres readers never block writers
   and vice-versa at row granularity; SQLite's whole-DB write lock does not give
   you that under load.
4. **Weaker types & constraints by default.** Dynamic typing, and features like
   strict typing, rich `JSONB`, partial/expression indexes at scale, materialized
   views, and concurrent index builds are Postgres territory.
5. **Practical size/throughput ceiling.** SQLite happily holds many GB, but
   high-rate ingestion, retention/partitioning, and heavy analytical queries over
   very large span volumes are where a server-class engine earns its keep.

## The decision rule

> Stay on SQLite while the store is **single-writer, single-host, read-mostly,
> and bounded in size.** Move to Postgres when any one of these breaks:
> concurrent writers from multiple processes/hosts, cross-machine access, strict
> types/constraints and richer indexing at scale, or ingestion volume that a
> single writer can't keep up with.

For FAULTLINE today — one deterministic ingest, local reconstruction — SQLite is
not a compromise; it's the correct tool. The store code hides SQL behind
`TraceStore`, so the migration path is "reimplement the same methods against
Postgres," not a rewrite of the viewer or reconstruction.
