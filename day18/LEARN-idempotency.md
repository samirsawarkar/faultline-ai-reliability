# LEARN — idempotency and bounded recovery

Day 18 adds the first *recovery* to the project, and the lesson is that recovery is
where reliability engineering most often shoots itself in the foot. Three ideas keep
retry from becoming a new outage: bounding, backoff+jitter, and idempotency.

## Retry is dangerous by default

The naive fix for a flaky call is "try again." Unbounded, that is three separate
outages waiting to happen:

1. **The hang.** `while not ok: retry()` never returns on a persistent fault.
2. **The cost blow-up.** Each retry costs money/latency/tokens; without a budget a
   single stuck request can consume the whole system's capacity.
3. **The retry storm.** Every client retrying in lockstep after a blip creates a
   synchronized thundering herd that keeps the dependency down.

So bounded recovery is defined by its envelope first: a finite `max_attempts`, a
cost budget, a latency budget, and a hard cap no caller can exceed. The engine is
*terminal by construction* — it always reaches one of `recovered`,
`exhausted_attempts`, `aborted_cost_budget`, `aborted_latency_budget`. An exhaustion
is a clean, explainable outcome, not a hang.

## Backoff and jitter

Two refinements make retry a good citizen. **Exponential backoff** (delay
`base·2^attempt`, capped) gives a struggling dependency room to recover instead of
hammering it. **Jitter** — randomizing each delay within its cap — de-synchronizes
many retriers so they don't all fire at the same instant; "full jitter" (uniform in
`[0, cap]`) is the AWS-recommended default. FAULTLINE seeds the jitter so a run is
reproducible, but the shape is the real thing.

## Idempotency: the difference between bounded and correct

Here is the subtle one. Suppose the operation has a side effect — a write, a charge,
an email. Retry it three times and the side effect happens three times. The retry was
*bounded* (three, not infinite) and still *wrong*. Bounding controls how many times
you try; it does nothing about whether trying twice is safe.

The fix is **idempotency**: give each logical operation a key, apply the side effect
on the first execution, and on every repeat return the recorded result *without*
re-applying it. Then "at least once" delivery becomes "effectively once." FAULTLINE's
ledger demonstrates it directly: three duplicate deliveries produce **one** side
effect with the ledger and **three** without. This is why the mission's fail
condition lists "unsafe to repeat" alongside "unbounded" — a retry you cannot safely
repeat is not recovery, it is amplification.

The engineering rule: **only retry idempotent operations, or make them idempotent
with a key before you retry.** A pure read is trivially safe; a write needs a key; a
non-idempotent external effect (charge a card) needs the provider's idempotency
support or it must not be blindly retried.

## Recovery is not free — measure the trade

Even correct, bounded, idempotent recovery has a cost: on a fault it *cannot* fix
(persistent), it spends its whole budget for no benefit — latency and cost added,
success unchanged. So recovery buys a success-rate gain only where faults are
transient, and it should be measured (paired vs no-recovery) and paired with a
circuit breaker (Mission 20) that stops throwing good budget after bad. The honest
report shows both the win (transient faults rescued, McNemar-significant) and the
bill (budget burned on the persistent ones).

## References worth reading next

- AWS Architecture Blog, *Exponential Backoff and Jitter* (the "full jitter" result).
- Nygard, *Release It!* — Timeouts, Retries, and the Circuit Breaker pattern.
- Helland, *Idempotence Is Not a Medical Condition* (2012); the idempotency-key
  pattern used by payment APIs (e.g. Stripe).
- Google SRE Book — retry budgets and the "retry amplification" failure mode.
