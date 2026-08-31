# DECISIONS — Day 30 defense and launch

Append-only. Date · id · decision · why · reversal cost.

---

### 2026-07-30 · D30-001 · Define ten core defense questions

**Decision.** Cover depth, detection, judge validity, retry correlation,
fallback quality, recovery composition, multi-objective selection, policy
external validity, cascade causality, and replay-verified fixes.

**Why.** Together they span the Q1–Q5 argument and the evidence system that makes
the findings actionable.

**Reversal cost.** Low; a new core claim must add a scored question and evidence
binding.

### 2026-07-30 · D30-002 · Score answers on five spoken elements

**Decision.** Require decision, result, tradeoff, limitation, and reversal
trigger, plus a code-free speaking surface.

**Why.** A number without a decision is trivia; a decision without a limitation
is marketing.

**Reversal cost.** Low; the rubric is explicit and versioned.

### 2026-07-30 · D30-003 · Preserve weak baselines

**Decision.** Score initial short answers red and repaired answers green.

**Why.** The repair should expose what was learned, not merely replace the weak
answer.

**Reversal cost.** None; additional attempts are additive.

### 2026-07-30 · D30-004 · Record synthetic narration honestly

**Decision.** Commit a spoken recording and transcript, while setting
`human_participant=false`.

**Why.** The artifact proves the complete defense is speakable and reviewable,
but cannot substitute for a human closed-book attempt.

**Reversal cost.** None; a human recording can replace or supplement it.

### 2026-07-30 · D30-005 · Target public maintainer channels

**Decision.** Tailor eight messages to project communities rather than scrape
personal contact details.

**Why.** Public channels create durable, consent-aware technical context and
reduce unsolicited personal outreach.

**Reversal cost.** Low; maintainers can redirect each message.

### 2026-07-30 · D30-006 · One narrow OSS contribution is enough

**Decision.** Prepare the issue-backed `openai/evals` documentation clarification
instead of manufacturing two unrelated patches.

**Why.** The mission permits one or two contributions; genuine scope matters
more than count.

**Reversal cost.** None; a second contribution needs its own issue match and
validation.

### 2026-07-30 · D30-007 · External receipts are fail-closed

**Decision.** Drafts do not count as sent, and a patch packet does not count as
opened.

**Why.** Checkpoint 30 measures expert exposure, not preparation activity.

**Reversal cost.** None; durable URLs flip the recorded state.

### 2026-07-30 · D30-008 · Launch in three gated windows

**Decision.** Prove public reproduction, then perform selective outreach, then
convert objections into owned work.

**Why.** This keeps distribution from outrunning evidence quality.

**Reversal cost.** Low; gates can pause the next window without rewriting prior
evidence.
