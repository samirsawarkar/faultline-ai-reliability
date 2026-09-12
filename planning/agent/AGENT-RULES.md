# Standing rules for the implementing agent

Read this at the start of every session. It is short because it is binding.

---

## 1. Days 1–30 are frozen

`day01/` … `day30/` are never edited, moved, renamed, deleted, or imported.
Read them as much as you like. Change nothing.

**The tripwire:** `make test` must stay green for the whole of Phase 2. If a
Phase 2 change turns it red, the Phase 2 change is wrong — revert it, do not
"fix" a day.

Copying a file out of a day into `faultline_p2/` is allowed and expected. It is
accompanied by a sha256 equality test against the original (see D1).

## 2. Contracts are read-only

`MEC.md` and `HYPOTHESES.md` are never edited after they are committed. If
reality disagrees with them, stop and report it. The owner writes an entry in
`AMENDMENTS.md`. You do not.

Never change silently. An undocumented deviation invalidates every number
downstream of it.

## 3. Never spend money without `--confirm`

Every paid call goes through the sweep runner. Print the dry-run cost estimate
first, every time, without being asked. Wait for the owner's explicit go.

A per-project cap is a **stop**, not a budget to borrow against. Reaching it
means: halt the sweep, write what completed, log it, report. Never continue into
another project's allocation.

## 4. The oracle is the authority

`oracle_check` is a pure function. It is never an LLM, never overridden, never
"adjusted" because real traces score badly. If real output doesn't grade
cleanly, the harness is wrong — not the oracle. That distinction is the reason
this project exists.

## 5. Report what happened

Tests fail → say so, with the output. A sweep half-completed → report it as half
completed. A gate not met → the project is not done. Never describe intended
behaviour as observed behaviour.

Verify before claiming. Run the command, read the output, then write the claim.

## 6. Scope

Do what the work order says. Nothing adjacent, nothing speculative. No
abstraction with one caller, no config for a value that never changes, no
scaffolding "for later".

Non-trivial logic leaves one runnable check behind — the smallest thing that
fails if the logic breaks.

## 7. Boundaries are typed

Pydantic v2, `extra="forbid"`, at every boundary where data enters or leaves a
module. This is a reliability project; untyped dict-passing is not acceptable
here even where it would work.

## 8. Determinism is a contract, not a goal

Anything seeded is byte-identical across processes and across machines, under
any `PYTHONHASHSEED`. Canonical JSON everywhere: `sort_keys`, ASCII, fixed
indent, LF, one trailing newline. No timestamps, no host info, no absolute
paths inside committed artifacts.

## 9. One project per session

Ship its five artifacts — `README.md`, `DECISIONS.md`, `results.json`,
one figure, one `make` target — plus raw traces, before starting the next.

## 10. When the rules and the work order disagree

`planning/cto/` outranks `planning/agent/`. `MEC.md` outranks both. Stop, say
which two things conflict, and wait.
