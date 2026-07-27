# LEARN — retry amplification

Day 18 made retry *bounded*. Day 19 asks the harder question: even bounded, when
does retrying stop being worth it? The answer is "sooner than the success curve
suggests," because retry has costs the success rate hides — and under correlated
failure it has a cost that feeds back on itself.

## The success rate is the wrong number to optimize

Plot success vs retry budget K and it rises, so "more retries = better" looks
obvious. But success is a concave, saturating curve: each extra attempt only helps
the requests that (a) can still succeed and (b) haven't yet. Meanwhile two costs
rise *without* saturating:

- **Cost / amplification** — total attempts per request. Every failing request
  retries to the budget, so a persistent-failure fraction turns K into a near-linear
  multiplier on load. Here K=6 means 2.5x the work of K=1 for a +0.38 success gain
  that mostly landed by K=3.
- **Tail latency** — a request that retries K times waits for K attempts plus K−1
  backoffs. The requests that retry the most are exactly the slow/failing ones, so
  they define the p95/p99. Mean latency barely moves; the tail moves a lot (here p99
  goes 10 → 196 as K goes 1 → 6).

So the honest objective is not success but success **subject to** a cost ceiling and
a tail-latency budget. The crossover is where the marginal success per marginal cost
falls below a threshold; the recommended budget is the knee that is still under both
ceilings. Optimizing success alone is precisely the mission's fail condition: you buy
a few more successes at an unacceptable tail.

## Retry amplification and the retry storm

The dangerous regime is **correlated failure**: when a shared dependency has a bad
moment, many requests fail *together*, and retrying does nothing for them — the
outage is still there. Now retries are pure amplification:

1. Success is flat (the outage is retry-proof), so the numerator doesn't move.
2. Every failing request retries to the budget, so total load scales with K.
3. That extra load hits the *already-struggling* dependency, slowing it further,
   which causes more timeouts, which trigger more retries — a **retry storm**.

FAULTLINE models this with a load→latency term: as average attempts rise above 1,
a queue delay is added to *every* request, so p99 grows super-linearly (here to 257,
2.5x the independent case). The classic production incident is exactly this: a blip
becomes an outage because the clients' retries DDoS the recovering service.

The mitigations, in order:

- **Cap K low** (2–3), because the marginal success is tiny past that anyway.
- **Backoff + jitter** (Day 18) to spread the retries out in time.
- **A retry budget / circuit breaker** (Mission 20): stop retrying once the failure
  rate says the dependency is down, so retries can't feed the storm. This is why the
  correlated recommendation here is K=2 *and* "breaker required" — bounding K is
  necessary but not sufficient when failures correlate.

## The through-line

Day 18 proved recovery can be bounded and safe; Day 19 proves that "bounded" still
needs a *budget chosen against cost and tail*, not against success. The recommended
region is small, capped by ceilings, and explicitly hands the correlated case to the
circuit breaker — the honest answer to "how many times should we retry?"

## References worth reading next

- Google SRE Book — *Handling Overload* and retry budgets (the amplification / DDoS-
  yourself failure mode).
- AWS — *Timeouts, retries and backoff with jitter* (why jitter, why cap).
- Nygard, *Release It!* — Circuit Breaker and Bulkhead as the correlated-failure fix.
