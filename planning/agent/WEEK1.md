# Week 1 — the agent harness, built offline

**Read first:** `planning/agent/AGENT-RULES.md`, then `MEC.md`.
**Budget: $0.** Nothing in this work order touches a network. Not one call.
**Why now:** the ladder is frozen PROVISIONAL because pre-flight authenticated zero
rungs. Everything P1 needs *except* the model can be built and fully tested without one.
When keys arrive, P1 is one command — not a week of work.

`faultline_p2/agent/` and `faultline_p2/trace/` are empty `__init__.py` stubs today. They
are the whole of P1. Build them against a stub model, prove the loop end to end on all
350 scenarios, and leave exactly one seam where a real model plugs in.

---

## W1.1 · The three tools

Read `day02/faultline_agent/` first. MEC v1.0 says the tools are "identical to day02
signatures" — match them, do not invent new ones. If a day02 signature cannot carry the
Phase 2 corpus (link documents, `traversal_sources`), say so and propose the minimum
change rather than silently diverging.

**Binding retrieval constraint, from MEC v1.0.** Retrieval matches on content. Document
IDs are opaque to the agent, and no ID may encode scenario identity or hop position. A
tool that lets the model enumerate or guess document IDs reintroduces at runtime the
shortcut the corpus design spent four rebuilds removing.

Typed with Pydantic v2, `extra="forbid"`, both directions.

**Acceptance:** a test proving the retrieval tool cannot return a document by ID guess —
give it a well-formed ID it was not led to by content and assert it gets nothing.

---

## W1.2 · The bounded loop

Reason → tool → observe. Step cap **8**, from the MEC. Temperature 0.0, max_tokens 2048.

The model is called through **one** function with a narrow signature. That function is
the only place in the package that knows LiteLLM exists. Everything else is testable
without a network.

The loop must terminate cleanly on: answer produced, step cap reached, tool error,
malformed model output, and model call failure. Each termination reason is a named value
recorded in the trace — not an exception that escapes, and not a silent `None`.

**Acceptance:** every termination reason is exercised by a test. A step cap that is only
ever tested by not hitting it is untested.

---

## W1.3 · The stub model

A deterministic, offline model implementing the same seam as the real one. It must be
able to produce, on demand: a correct grounded answer, a correct answer with a wrong
citation, a wrong answer, a malformed response, a tool-call loop that hits the step cap,
and a hard failure.

This is not a mock for one test. It is how the entire harness is verified before a dollar
is spent, and it is what P11's CI gate will run on later.

**Acceptance:** all 350 scenarios run end to end against the stub, with zero network
access. Assert that — patch the transport so any outbound call raises, and let the suite
prove itself offline.

---

## W1.4 · The trace store

Spans that survive failure. A run that crashes mid-flight still leaves a readable trace —
write as you go, never buffer to the end.

Each span records: scenario id, tier, step index, tool name, model name, provider, model
version, quantization if reported, prompt and completion tokens, latency, and termination
reason. Provider and version are in the MEC because P7 depends on them; a span missing
them is a bug, not an omission.

Read `day04/faultline_trace/` and `day05/faultline_store/` before designing this. Match
their shape where it fits. P2 will later emit these as OTel GenAI spans, so keep the
field names close to `gen_ai.*` where the mapping is obvious.

**Acceptance:** kill a run mid-sweep; the partial trace is present, parseable, and its
last span says why it stopped.

---

## W1.5 · Oracle wiring

Grade stub runs with `faultline_p2.oracle.oracle_check`, unmodified. Pass condition:
answer correct AND cites the one source holding the fact — the final hop's
`required_source`, not `traversal_sources`.

**Acceptance:** a stub run that answers correctly but cites a link document is graded
FAIL. If it passes, the grounding condition is not being enforced and every downstream
number is worthless.

---

## W1.6 · The system prompt

Author it. Freeze it. Record its sha256.

This is the one field MEC v1.0 leaves open, and setting it bumps the contract to **v1.1**.
Write `AMENDMENTS.md` entry `A-001` recording the hash, the date, and that no prior result
is affected because none exists yet.

Keep it minimal and describe only the task and the tool protocol. It must not hint at
hop structure, mention link documents, or suggest a retrieval strategy — the corpus is
supposed to measure whether the model figures that out.

---

## Gate

Report with pasted output:

1. All 350 scenarios run end to end against the stub, **offline**, with the outbound
   transport patched to raise
2. Every termination reason exercised by a test
3. The ID-guess test: retrieval refuses a document not reached by content
4. The grounding test: correct answer + link-document citation grades FAIL
5. A killed mid-sweep run leaving a readable partial trace
6. System prompt sha256, and `AMENDMENTS.md` A-001 committed
7. `make test` green day01–day30, root `pytest` green

**Then stop.** P1 is the same harness pointed at a real endpoint, gated on live keys and
my `--confirm`. Do not make a network call.
