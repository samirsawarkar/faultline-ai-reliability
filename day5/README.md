# FAULTLINE — Day 5: reconstruct a failed run in minutes

Store Day-4 spans in SQLite, index them, and give a stranger a timeline viewer
that reconstructs a failed run — even after fields or spans are deleted.

> **Fail condition:** a stranger cannot reconstruct the run from the viewer.
> **Status: not triggered** — the incident narrative is written from the viewer
> alone, and reconstruction survives every deletion scenario
> (`evidence/attack_report.json` → `all_scenarios_reconstructable: true`).

## What's here

```
faultline_store/
  schema_sql.py   tables + 4 indices (timeline, tree, failure, failed-runs)
  store.py        TraceStore: ingest Day-4 spans; index-backed queries
  reconstruct.py  "what failed, where" from the store; degrades gracefully
  viewer.py       terminal timeline viewer (deterministic)
  render.py       dependency-free SVG snapshot of a trace
  attack.py       delete fields/spans; measure reconstruction vs raw logs
  ingest.py       generate Day-4 traces (ok + failed) and load them
scripts/
  build_store.py  materialize evidence/trace.db
  timeline.py     CLI viewer (--ok / --db / --trace)
  make_evidence.py regenerate all evidence
tests/
  test_store.py       ingest + every query hits an index (EXPLAIN asserts it)
  test_reconstruct.py root-cause, failing path, deterministic viewer
  test_attack.py      graceful degradation under deletion
evidence/
  failed_run.svg          the visual a stranger opens
  timeline_failed.txt     terminal viewer output
  attack_report.json      deletion scenarios + store-vs-rawlog scan cost
  incident_narrative.md   the run reconstructed from the viewer alone
  reconstruction_timing.json  wall-clock (not diff-gated)
SPAN via Day 4 · LEARN-sqlite.md · DECISIONS.md · REFLECTION.md
```

## Quickstart

```
python -m pytest tests/ -q          # 13 tests: store + reconstruct + attack
python scripts/timeline.py          # view the failed run in the terminal
python scripts/build_store.py       # write evidence/trace.db
python scripts/make_evidence.py     # regenerate all evidence (deterministic)
```

Standard library only (`sqlite3`); traces come from Day 4. No LLM — see
REFLECTION.md.

## The failed run, reconstructed

```
TRACE trace-00000007   status=ERROR   spans=4
 1-8  |########################| X agent [agent]
          -> RiskyToolError: tool sum exploded (token=***REDACTED*** at index 1
 2-3  |   ###                  | .   model.plan [model]
 4-5  |          ###           | .   tool.retrieve [tool]
 6-7  |                 ###    | X   tool.sum [tool]
failing path: agent > tool.sum
root-cause span(s): tool.sum
```

Every query behind this is `SEARCH ... USING INDEX`, not a scan. Delete the error
message, an intermediate span, or the root span, and the viewer still names
`tool.sum` as the failure — with `<missing>`, gap, and orphan markers where data
was lost.

## Mastery map

- **Explain** → `LEARN-sqlite.md` (SQLite limits, when Postgres is required)
- **Build** → `faultline_store/`
- **Debug** → the viewer names root cause, path, gaps, orphans
- **Measure** → indexed queries + `attack_report.json` scan costs
- **Defend** → `DECISIONS.md`
