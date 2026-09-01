# Week 1 — corrective work order

**Read first:** `AGENT-RULES.md`, then `AMENDMENTS.md` **A-002**, then `MEC.md`.
**Budget: $0.** Still no network call.
**Accepted from W1:** contracts, the loop skeleton, and the termination-branch tests.
**Rejected:** the stub, the model seam, the trace wiring, and the retrieval constraint.

The contract changed under you. A-002 raises the step cap to 12 and changes the tool
contract, because the corpus needed 9 retrievals for a T3 against a cap of 8 — 283 of 350
scenarios were unsolvable by construction. That was my error, not yours. Everything below
follows from it.

---

## X1 · Apply A-002 to the tools

**`search`** now returns, per candidate: `doc_id`, `title`, `score`, and a **bounded text
snippet** containing the matched region. Pick the bound, state it in `DECISIONS.md`, and
keep it small enough that search cannot be used to dump the corpus. One search must be
enough to read the fact a document holds.

**`lookup`** resolves only documents surfaced by a prior `search` **in the same run**.
Fact IDs are `doc-0000`…`doc-0359` and enumerable; content-reachability must be enforced
by the tool, not by the step cap being small.

**Step cap is 12**, everywhere, from the contract.

**Acceptance**
1. `lookup` on a well-formed ID never surfaced by a search in that run returns
   `ok=False`. This is the test I asked for in W1.1 and that shipped inverted — the
   previous `test_lookup_accepts_both_id_types` asserted the opposite and must go.
2. A snippet is sufficient to answer: for a sampled T1 scenario, the snippet returned by
   searching the fact's text contains the answer token.

---

## X2 · A stub that actually solves the task

The current stub matches the prompt string and returns the answer on call one. I measured
it: 50 runs, `steps_used` 0 for all 50, **zero tool calls**, trace length 0. The loop, the
tools, and retrieval were never exercised. "350 scenarios end to end" was not true.

Build a **solver** stub that traverses honestly: search for the entity, read the snippet,
extract the answer, search the link record, follow it to the next entity, repeat, then
answer citing the final hop's `required_source`. It uses only what a real model would see
— tool results — and never reads the `Scenario` object for anything but the initial prompt.

Keep the other behaviours (wrong citation, wrong answer, malformed, step-cap loop, hard
failure) as separate stubs.

**Acceptance**
1. All 350 scenarios solved by the solver stub, offline, with the transport patched to
   raise.
2. **Paste the `steps_used` distribution by tier.** T1 should be ~2, T2 ~6, T3 ~10. A
   distribution of zeros means nothing ran.
3. Total tool calls across the sweep, non-zero and consistent with those step counts.
4. Oracle-graded results: 350/350 pass. Grounding is genuinely exercised because the
   citation now comes from traversal, not from the answer key.

---

## X3 · The model seam

`LiteLLMModel.generate` currently imports litellm and unconditionally raises. Implement it
properly: build the request, call LiteLLM, parse the response into `ModelResponse`, and
surface provider, model version, token counts, and latency for the trace.

Do not call it. Do not test it against a network. An implemented seam that is never
invoked is the deliverable; a function that can never work is not.

**Acceptance:** a test constructing `LiteLLMModel` and asserting the request it *would*
send — model name, temperature 0.0, max_tokens 2048, message shape — without dispatching it.

---

## X4 · Wire the trace store into the loop

`run_agent` does not reference `TraceStore` at all. It currently writes nothing.

Every step writes a span as it happens — never buffered to the end. Every span carries
scenario id, tier, step index, tool name, model name, provider, model version,
quantization if reported, prompt and completion tokens, latency, and termination reason.
Provider and version are in the MEC because P7 depends on them.

**Acceptance:** kill a real `run_agent` sweep mid-flight and show the partial trace is
present, parseable, and its last span says why it stopped. The previous test wrote two
rows by hand from a script and proved nothing about the agent.

---

## X5 · Rename `SOLVED`, record the answer step

`SOLVED` is returned for any answer, including a wrong one — the current test asserts a
wrong answer is `SOLVED`. In every downstream results file that will read as success.
Rename to **`ANSWERED`**. Correctness is the oracle's verdict and belongs nowhere else.

The answering step is also never recorded: `steps_used = step_idx - 1` and the final
action never enters the trace. P4 codes failure modes by reading traces, and the last
action is the one that matters most. Record it.

---

## X6 · Measure tokens per run

The MEC's budget assumed 10k input / 2.5k output per run, costed before a multi-step
agent existed. With 12 steps of accumulating context that number is a guess.

Have the solver stub emit realistic message payloads and report **actual prompt and
completion token counts per run, by tier**, using a real tokenizer. This is A-002's open
obligation and it gates P6's $45 allocation.

---

## Gate

Paste output for:

1. `lookup` refusing an ID not surfaced by search
2. 350 scenarios solved offline by the solver stub, with the `steps_used` distribution
   **by tier** and total tool calls
3. 350/350 oracle-graded passes, and a wrong-citation stub graded FAIL
4. The would-send assertion for the LiteLLM seam
5. A killed `run_agent` sweep leaving a readable partial trace with a termination reason
6. Token counts per run by tier
7. `make test` green day01–day30, root `pytest` green

Then stop. P1 is this harness pointed at a live endpoint, and it needs keys and my
`--confirm`.
