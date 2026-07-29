# FAULTLINE — Day 27: cold-reader reproduction

Prove that someone without repository history can move from a public clone to
the headline numbers without undocumented knowledge.

> **Fail condition:** cold reproduction requires an undocumented command,
> choice, path, version, credential, edit, or interpretation.

## Primary artifact

[REPRODUCE.md](../REPRODUCE.md) is the complete reader interface. It declares the
starting state, pins `v0.27.0-rc1`, supplies one copyable block, prints all six
headline results, and gives experiment-preserving failure actions.

The cold harness parses that block from the document and executes it in a new
temporary directory. It does not maintain a second hidden command list.

## Evidence

| artifact | question answered |
|---|---|
| `evidence/COLD-START-TRANSCRIPT.txt` | What commands and outputs occurred? |
| `evidence/cold_start_report.json` | Did the exact block pass with zero questions and improvisations? |
| `evidence/FRICTION-LOG.md` | Which ambiguities were found and repaired? |
| `evidence/peer_attempt.json` | Was an independent no-context attempt requested, and what happened? |
| `evidence/CHECKPOINT-27.md` | Did every mission and fail-condition gate pass? |

## Implementation

```text
faultline_cold_repro/
  protocol.py    extract the executable and expected-output blocks
  headlines.py   regenerate and verify registered README claims
  simulation.py  build a candidate snapshot and execute a fresh clone
  audit.py       document, transcript, friction, and peer gates
  report.py      Checkpoint 27 aggregation
scripts/
  cold_reproduce.sh
  reproduce_headlines.py
  prepare_snapshot.py
  simulate_cold_reader.py
  audit_reproduction.py
  make_evidence.py
tests/
evidence/
```

## Mastery gate — all five

- **Can explain** — every prerequisite and expected value is explicit.
- **Can build** — a cold clone reaches the numbers with one Make command.
- **Can debug** — ambiguity becomes a numbered friction defect and documented
  action.
- **Can measure** — questions and improvisations are both zero.
- **Can defend** — exact transcript, independent peer attempt, and Checkpoint 27.
