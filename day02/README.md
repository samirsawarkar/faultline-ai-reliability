# FAULTLINE — Day 2

Build a small, bounded **single agent** we fully own — before any faults are
injected. The agent answers multi-hop questions over Day 1's frozen environment
using three typed tools, inside a reason → tool → observe loop with a hard step
cap, and returns a Pydantic-validated structured outcome the Day-2 verdict can
judge.

> **Mastery gate:** *explain*, *build*, *debug*, *measure*, *defend*. Map at the
> bottom.

## Fail conditions (and how each is made unreachable)

| The agent must not… | Why it can't |
| --- | --- |
| **hang** | the loop is `while steps < step_cap` — no `while True`; one tool call per step; at most `step_cap` iterations, then it returns (`agent.py`). |
| **bypass validation** | every tool call, tool result, task, and outcome is a Pydantic model with `extra="forbid"`; a bad task becomes a structured `INVALID` outcome, never an escaped exception (`contracts.py`, `agent.py`). |
| **return an unstructured outcome** | `Agent.run` is typed to return `AgentOutcome`, whose `model_validator` enforces cross-field invariants (SOLVED ⇒ has answer; `steps_used ≤ step_cap`). |

## What's here

```
faultline_agent/
  contracts.py   Pydantic models: tool calls/results, task, AgentStep, AgentOutcome
  tools.py       search / lookup / calc  (calc = whitelisted-AST safe arithmetic)
  agent.py       the bounded reason->tool->observe loop
  verdict.py     Day-2 oracle: correct AND grounded (semantic correctness)
  env_bridge.py  imports Day 1's build_env as ground truth
scripts/
  experiment_budget.py   under / boundary / over-budget -> budget_termination.json
  run_agent.py           full structured run + trace -> sample_run_seed7.json
  schema_vs_semantic.py  schema-valid-but-wrong outcomes -> schema_vs_semantic.json
tests/
  test_termination.py    the Day-2 gate: bounded loop, clean INCOMPLETE
  test_contracts.py      validation cannot be bypassed; outcome roundtrips
  test_tools.py          typed tools; calc refuses eval injection
  test_semantics.py      schema validity != correctness; agent is deterministic
evidence/
  budget_termination.json   the over-budget attack result
  sample_run_seed7.json     a full serialized outcome + trace
  schema_vs_semantic.json   three schema-valid outcomes, one actually correct
DECISIONS.md   decision log, D-008 … D-013 (continues Day 1)
LEARN.md       schema validity vs semantic correctness
MARKET.md      why the test subject is a single agent
```

## Quickstart

```
python -m venv .venv && ./.venv/bin/pip install pydantic pytest   # once
./.venv/bin/python -m pytest tests/ -q                 # 22 tests: the gate
./.venv/bin/python scripts/experiment_budget.py        # force over-budget
./.venv/bin/python scripts/run_agent.py                # structured run + trace
./.venv/bin/python scripts/schema_vs_semantic.py       # validity != correctness
```

Requires `pydantic` (v2) and `pytest`; consumes Day 1 via `../day01`.

## The task, and why it is shaped this way

One task family: **`archive_sum`** — "sum the archival-reference numbers of these
entities." It is deliberately multi-hop, so it exercises all three tools and its
step demand scales:

```
steps_demanded(k) = 2*k + 1      # search + lookup per entity, then one calc
```

With `step_cap = 12`: `k ≤ 5` is solvable (≤ 11 steps), `k ≥ 6` is over budget.
That single knob is how we drive the agent past its budget on demand and watch it
stop cleanly — the Day-2 attack.

## Mission status

- [x] reason → tool → observe loop with a hard step cap — `agent.py`
- [x] three typed tools (search, lookup, calc) — `tools.py`
- [x] validated structured answer — `AgentOutcome` in `contracts.py`
- [x] termination tests + forced over-budget → clean `INCOMPLETE` — `evidence/budget_termination.json`
- [x] schema-validity-vs-semantic-correctness study — `LEARN.md`, `evidence/schema_vs_semantic.json`
- [x] why single-agent — `MARKET.md`

**Fail condition (hang / bypass validation / unstructured outcome): not
triggered** — proven by `tests/` and the committed evidence.

## Mastery map

- **Explain** → this README, `LEARN.md`
- **Build** → `faultline_agent/`
- **Debug** → `agent.py` (the structural termination argument), `tools.py` (safe calc)
- **Measure** → `verdict.py`, `evidence/`
- **Defend** → `DECISIONS.md`, `MARKET.md`
