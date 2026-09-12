# Start here — what all the letters and numbers mean

You are the owner. This file explains the whole system in plain language.
Nothing here is technical. Read it once and the rest of the repo makes sense.

---

## The one-paragraph version

FAULTLINE Phase 2 measures how reliably AI models answer questions when they
have to look things up across several documents. Days 1–30 built the measuring
instruments against a fake environment. Phase 2 points those instruments at real
models and real money. Because the whole point is *trustworthy measurement*, we
write down what we're going to measure **before** we measure it — so we can't
fool ourselves later.

---

## The four letters

| Letter | Means | Example | Who writes it |
|---|---|---|---|
| **P** | **Project** — one experiment or one piece of software | P1, P6, P13 | the coding agent builds it |
| **H** | **Hypothesis** — a prediction made *before* the experiment | H1, H4 | you (owner) |
| **A** | **Amendment** — a change to a frozen rule, with the reason | A-001, A-002 | you (owner) |
| **D** | **Decision** — a choice someone made, and why | D1, D-003 | both — see below |

### Why there are two kinds of D (my mistake, being fixed)

- **D1 … D7** — *program* decisions. Big ones about how the whole project runs.
  Live in `planning/cto/PHASE2-BUILD.md`. Example: **D5** = "name the package
  `faultline_p2` so it doesn't clash with day01's."
- **D-001 … D-004** — *engineering* decisions. Small ones about how one piece of
  code works. Live in `DECISIONS.md` at the repo root. Example: **D-003** =
  "search returns a 500-character snippet, because that's enough to answer a
  question but not enough to dump the whole corpus."

Same letter, two meanings. Confusing. **Proposal: rename the engineering ones to
`E-001`…`E-004`.** One letter, one meaning. Say the word and I'll do it.

---

## The projects

Twelve were planned. Four more are proposed to fill gaps a hiring manager would
notice.

| | Name | What it does | Status |
|---|---|---|---|
| P0 | pre-flight | Checks each AI model works and what it really costs | built, blocked on API keys |
| **P1** | real-agent-baseline | First real run: 100 questions, one cheap model | **rehearsed on a fake model, ready** |
| P2 | otel-exporter | Makes our traces readable by standard tools | not started |
| P3 | grounding-zero-point | The first number you can defend: 200 questions, two models | not started |
| P4 | failure-taxonomy | You read 150 real failures by hand and name the patterns | not started |
| P5 | judge-validation | Prove the automatic grader agrees with a human | not started |
| **P6** | passk-decay | **The headline.** Does retrying actually help? | not started |
| P7 | provider-variance | Same model, three vendors — do they give the same answers? | not started |
| P8 | mcptox-bounded | Security: can a poisoned tool hijack our agent? | not started |
| P9 | redteam-regression | Attack suite; every successful attack becomes a test | not started |
| P10 | calibrated-cascade | Use cheap model, escalate to expensive only when needed | not started |
| P11 | release-gate | CI that blocks a bad model upgrade | not started |
| P12 | failure-attribution | Is it the search that's broken, or the model? | not started |
| P13 | slo-and-incident | *proposed* — alerts, and one real incident writeup | not started |
| P14 | structured-output | *proposed* — how often do models break a strict format? | not started |
| P15 | resilience | *proposed* — timeouts, retries, circuit breakers | not started |
| P16 | runtime-policy | *proposed* — permission rules that hold even if the model is tricked | not started |

---

## The files, and what each is for

**Contracts — frozen, never edited**

| File | What it is |
|---|---|
| `MEC.md` | The Master Experiment Contract. Every rule of the experiment: the questions, the models, the statistics, the budget. Frozen 2026-09-01. |
| `HYPOTHESES.md` | The eight predictions, written before any data existed. The git commit date is the proof they came first. |
| `AMENDMENTS.md` | Every change to the two files above, with the reason. Two so far. |

**Planning — how the work gets done**

| File | What it is |
|---|---|
| `planning/START-HERE.md` | This file |
| `planning/cto/PHASE2-PLAN.md` | Your original plan, saved word for word |
| `planning/cto/PHASE2-BUILD.md` | The build order, decisions D1–D7, and a brief for each project |
| `planning/agent/AGENT-RULES.md` | Rules the coding agent follows every session |
| `planning/agent/WEEK0.md`, `WEEK1.md`, `*-FIX.md` | The work orders it has executed |

**The code**

| Folder | What it is |
|---|---|
| `day01/` … `day30/` | Phase 1. **Frozen. Never touched.** Read-only history. |
| `faultline_p2/` | The instruments: the questions, the grader, the agent, statistics, cost control |
| `projects/` | The experiments |

---

## The two amendments so far, in plain English

**A-001** — We wrote the agent's instruction prompt and locked it. It was
deliberately left blank when the contract was frozen rather than filling it with
a fake placeholder.

**A-002** — The agent was allowed 8 steps to answer a question. But a hard
question needs 9 documents, and each document took 2 steps to find and read. So
**every hard question was impossible**, and 283 of 350 questions could never have
been answered. That was my error. The fix: let search return a preview of the
document so one step is enough, and raise the limit to 12.

Nothing had run yet, so it cost nothing. If it had been found after the big
experiment, it would have cost $45 and a false conclusion.

---

## Where we are right now

- **Spent: $0 of $150.** No AI model has been called yet.
- **Built:** the questions (350, verified honest after four rebuilds), the
  grader, the agent, the statistics, the cost limiter, and a full rehearsal of
  P1 against a fake model.
- **Blocked on:** API keys. Pre-flight found zero working models.
- **Next:** you add keys → pre-flight measures real prices → P1 runs for about
  **12 cents**.

**17 commits exist only on your drive.** `git push` before anything else.

---

## How to read a status update from me

- "**P6 at $50 against a $45 cap**" → the big experiment now costs more than
  budgeted, because we measured real token use instead of guessing.
- "**A-003**" → a change I want to make to a frozen rule, needing your approval.
- "**0/998**" → a test result. Zero failures out of 998 checks.
- "**Wilson CI**" → the error bar. "70% ± 8%" instead of a bare "70%".

If a number appears without an error bar, ask me why.
