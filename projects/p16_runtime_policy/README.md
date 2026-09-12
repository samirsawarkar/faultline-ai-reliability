# P16: Runtime Policy Enforcement & False-Positive Cost

Evaluates deterministic runtime authorization policy enforcement for the FAULTLINE agent when operating under a fully compromised model.

---

## Core Security Guarantee

> **Authorization holds even when the model is fully compromised.**
> 
> Assuming an adversary completely controls model output, the runtime policy layer deterministically prevents forbidden operations from reaching the execution environment. This guarantee holds with **zero detectors running** — no prompt-injection classifiers, no probabilistic heuristics, and no text scoring.

The policy layer sits directly between the agent controller and the `ToolBox`, inspecting the structured tool call envelope before schema adaptation and before tool execution.

---

## Honest Scope Boundaries

This project builds and benchmarks **runtime authorization enforcement against an adversarial model**. It does **not** claim broader coverage:
- **Not a prompt-injection detector**: Prompt injection classifiers attempt probabilistic text-scoring of inputs. By contrast, runtime policy enforces structural, deterministic authorization at execution boundaries.
- **Not tool poisoning defense**: Tool poisoning and malicious documentation injections are evaluated in **P8**.
- **Not an adversarial input suite**: Adversarial prompt suites and jailbreak datasets are benchmarked in **P9**.

---

## Enforced Policy Rules

1. **Tool Allowlist & Deny-by-Default**: Only explicitly registered tools (`search`, `lookup`, `calc`) are permitted. Any unallowlisted tool name or malformed envelope is denied immediately.
2. **Doc ID Pattern Constraint**: Lookup targets must strictly adhere to the corpus identifier regex `r"^(doc-\d{4}|link-[a-f0-9]{12})$"`. Path traversal sequences (`../../etc/passwd`), protocol schemes, and malformed strings are blocked.
3. **Query Length Bound**: Search queries are capped at 200 characters to prevent buffer exhaustion and token-dump abuse.
4. **Per-Run Tool Call Budget**: Enforces a strict quota on tool invocations per task run, halting run loops and wear-down attempts.
5. **Typed Telemetry & Trace Auditability**: Every decision produces a typed `PolicyDecision(allowed, rule, reason, tool, arguments)` logged to `trace.db`.

---

## Empirical Benchmark Findings

Driven by `projects/p16_runtime_policy/run.py` (deterministic seed `42`):

### 1. Adversarial Enforcement Under Hostile Stub ($n=1,000$)
- **Overall Deny Rate**: **100.0%** ($1,000 / 1,000$)
- **95% Wilson Interval**: **[99.62%, 100.00%]**
- **Forbidden Operations Reaching ToolBox**: **EXACTLY ZERO** ($0 / 1,000$)

#### Breakdown by Policy Rule:
- **Allowlist Violations**: 200 / 200 denied (100.0% [98.12%, 100.00%])
- **Doc ID Traversal / Malformed**: 200 / 200 denied (100.0% [98.12%, 100.00%])
- **Oversized Query Length**: 200 / 200 denied (100.0% [98.12%, 100.00%])
- **Deny-by-Default / Malformed Envelope**: 200 / 200 denied (100.0% [98.12%, 100.00%])
- **Per-Run Budget Exceeded**: 200 / 200 excess calls denied (100.0% [98.12%, 100.00%])

### 2. False-Positive Cost on Legitimate P1 Traffic
A security guardrail with an unmeasured false-positive rate is unshippable. We ran legitimate traffic from the standard-pool scenarios using `StubModel(behavior="solver")`:
- **Legitimate Tool Calls Tested**: **2,004**
- **Legitimate Calls Wrongly Denied (False Positives)**: **0**
- **False-Positive Rate**: **0.0000%**
- **95% Wilson Interval**: **[0.0000%, 0.1913%]**
- **Scenarios Evaluated**: 312 runs (100.0% task success rate)

The policy imposes zero friction on legitimate multi-hop reasoning while establishing a 100% barrier against hostile actions.

---

## Reproduction

```bash
# Run the P16 benchmark
make p16

# Or execute directly with custom seed/call target:
.venv/bin/python projects/p16_runtime_policy/run.py --seed 42 --legit-calls 2000
```
