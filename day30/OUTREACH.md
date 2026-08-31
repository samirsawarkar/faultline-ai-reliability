# Eight evidence-led outreach messages

These are tailored drafts for public maintainer channels. A message is marked
`sent` only after a durable public URL is recorded; prepared text is not
misrepresented as outreach.

## OUT-01 · OpenTelemetry GenAI Semantic Conventions

- Channel: maintainer discussion
- Target: https://github.com/open-telemetry/semantic-conventions-genai
- Status: `draft`
- Intended ask: review the provenance vocabulary

OpenTelemetry GenAI Semantic Conventions maintainers — I built a seeded reliability study where fallback made availability look healthy while 30 of 40 fallback answers were silently degraded. The useful trace fields were route provenance, recovery mechanism, quality verdict, budget state, and the link from recovery to the initiating fault. The evidence is synthetic, so I am not proposing a standard from one simulator. Would you review the provenance vocabulary and tell me which parts already map cleanly to current semantic conventions, and which should remain application attributes? The short incident and trace path are here: https://github.com/samirsawarkar/faultline-ai-reliability/blob/codex/day29-evidence-briefing/day29/CASE-STUDY.md

## OUT-02 · Arize Phoenix

- Channel: maintainer discussion
- Target: https://github.com/Arize-ai/phoenix/discussions
- Status: `draft`
- Intended ask: review the replay pattern

Arize Phoenix maintainers — FAULTLINE turns one traced incident into a before/after evaluation: the same seed, configuration, regression predicate, and span assertions remain fixed while the policy version changes. The trace replay stays red under legacy recovery and green under the fix across 20 repetitions. This is simulator evidence, not a claim about production route independence. Would you review the replay pattern as a possible compact Phoenix example: trace selection, evaluation assertion, policy comparison, then stability replay? I am looking for guidance before proposing docs or code. The two-minute evidence path is here: https://github.com/samirsawarkar/faultline-ai-reliability/blob/codex/day29-evidence-briefing/day29/DEMO.md

## OUT-03 · Langfuse

- Channel: maintainer discussion
- Target: https://github.com/langfuse/langfuse/discussions
- Status: `draft`
- Intended ask: review the dashboard counterexample

Langfuse maintainers — I have a compact counterexample for trace dashboards: fallback lifted request availability to 1.0, but strict quality among answered requests fell to 0.75. The trace remains useful only when route provenance and a separately validated quality score travel with the response. The population is constructed and synthetic, so the rates should not be generalized. Would you review the dashboard counterexample and say whether a small public recipe should model availability, quality, and fallback provenance as three distinct fields? The audited article and source results are linked here: https://github.com/samirsawarkar/faultline-ai-reliability/blob/codex/day29-evidence-briefing/day28/ARTICLE.md

## OUT-04 · LangGraph

- Channel: maintainer discussion
- Target: https://github.com/langchain-ai/langgraph/discussions
- Status: `draft`
- Intended ask: review the bounded-recovery example

LangGraph maintainers — a six-mechanism fault matrix exposed 47 recovery-induced harms, including false repetition positives, premature ceilings, and wrong fallback answers. The composition that survived review was an outer step-and-cost envelope, then detection, narrow recovery, quality validation, and explicit success, containment, or escalation. This comes from paired synthetic graph runs, not production workloads. Would you review the bounded-recovery example and advise whether its assertions fit a LangGraph testing guide: shared seeds, per-node budgets, repetition recovery, and separately measured induced failures? The mechanism matrix is summarized here: https://github.com/samirsawarkar/faultline-ai-reliability/blob/codex/day29-evidence-briefing/day22/README.md

## OUT-05 · PydanticAI

- Channel: maintainer issue or discussion
- Target: https://github.com/pydantic/pydantic-ai/issues
- Status: `draft`
- Intended ask: review the ceiling contract

PydanticAI maintainers — FAULTLINE’s recovery experiments treat tool calls as budgeted actions, not an unbounded loop. In the correlated-fault slice, three attempts produced 2.37 times attempt amplification, so the policy checks the next step and cost ceiling before execution and allows only one repetition replan. The numbers come from a virtual-latency simulator, not deployed agents. Would you review the ceiling contract and say whether a focused example would help users distinguish usage limits, retry limits, and repetition recovery? I would wait for maintainer direction before opening a patch. Evidence and limitations: https://github.com/samirsawarkar/faultline-ai-reliability/blob/codex/day29-evidence-briefing/day28/ARTICLE.md

## OUT-06 · Ragas

- Channel: maintainer discussion
- Target: https://github.com/vibrantlabsai/ragas/discussions
- Status: `draft`
- Intended ask: review the judge-validation checklist

Ragas maintainers — I validated a narrow deterministic judge before using it on fallback answers. It reached kappa 0.5 against human labels, yet agreement was zero on one borderline-token slice; the judge therefore stayed advisory and outside core success. The validation set has only 24 synthetic examples, so this is a reporting pattern rather than a benchmark claim. Would you review the judge-validation checklist: independent labels, per-slice agreement, false-accept audit, positional-bias test, and an explicit forbidden-use verdict? The complete caveat and result binding are here: https://github.com/samirsawarkar/faultline-ai-reliability/blob/codex/day29-evidence-briefing/day28/ARTICLE.md

## OUT-07 · Tenacity

- Channel: maintainer issue or discussion
- Target: https://github.com/jd/tenacity/issues
- Status: `draft`
- Intended ask: review the retry-budget note

Tenacity maintainers — a paired retry experiment gives a concise operational warning: the last acceptable independent-fault point was three attempts at 1.9 times amplification, but correlated faults moved the cap to two because the same retry work hit the impaired component. These are simulator-specific ceilings, not recommended library defaults. Would you review the retry-budget note and advise whether a small documentation contribution about attempt amplification, shared-outage correlation, and global latency budgets would fit Tenacity’s scope? I would keep it framework-neutral and make no policy prescription. Evidence and uncertainty are here: https://github.com/samirsawarkar/faultline-ai-reliability/blob/codex/day29-evidence-briefing/day19/README.md

## OUT-08 · OpenAI Evals

- Channel: issue and documentation pull request
- Target: https://github.com/openai/evals/issues/1586
- Status: `draft`
- Intended ask: review the installation clarification

OpenAI Evals maintainers — while packaging FAULTLINE’s 44-example detector evaluation for cold reproduction, I hit the ambiguity described in issue 1586: the README’s pip guidance says “do not contribute,” while the real distinction is running pre-built evals versus developing custom evals from an editable install. I prepared the requested one-sentence clarification against the current README and no behavior change. The FAULTLINE dataset is synthetic and is not part of the proposed patch. Would you review the installation clarification if I open the one-line documentation PR? Reproduction context: https://github.com/samirsawarkar/faultline-ai-reliability/blob/codex/day29-evidence-briefing/REPRODUCE.md
