# LEARN — fault injection vs random chaos

Day 8's mission is to *inject reproducible component faults with ground-truth
labels*. It is worth being precise about how that differs from the thing it is
most often confused with — chaos engineering — because the difference is the
whole reason FAULTLINE injects faults at all.

## Two disciplines that look alike

**Chaos engineering** (Netflix's Chaos Monkey and its descendants) perturbs a
*production or staging* system — kill an instance, add packet loss, spike CPU —
and watches whether the system as a whole stays healthy. Its perturbations are
often **randomized** and **unlabelled**: the point is resilience under
*realistic, unpredictable* stress, and the "result" is a human or an alerting
system noticing (or not noticing) degradation. Randomness is a feature: it
surfaces failure modes nobody thought to script.

**Fault injection for measurement** (what Day 8 builds, and what the software
fault-injection and mutation-testing literature formalizes) perturbs a system to
*measure a specific property* — here, whether a detector or an oracle catches a
known fault. Its perturbations must be **reproducible** and **labelled**: you
have to know exactly what you injected, where, and when, or you cannot score what
caught it. Randomness without a seed is the enemy: it makes a result impossible
to reproduce or attribute.

They are complementary, not rivals. Chaos asks *"is the system resilient to the
unexpected?"* Fault injection asks *"can my instrument detect the known?"* You
cannot answer the second with chaos, because chaos deliberately withholds the
answer key.

## Why measurement needs the three things chaos can skip

**1. A deterministic trigger.** If a fault fires "sometimes," two runs of the
same experiment disagree and neither is citable. Day 8's triggers are pure
functions of `(spec, run_seed, seq, input_digest)`. Even the `probabilistic`
trigger is *seeded*: a fixed fraction fire, and *which* ones is reproducible.
"Probabilistic" here means a controlled distribution, not entropy — the opposite
of Chaos Monkey's wall-clock randomness.

**2. An independent ground-truth label.** To grade a detector you need a `y` that
is not derivable from the `X` the detector sees. Day 8 writes the label from the
*injection decision*, before any output exists, into a log the system under test
never reads. If the label instead lived in the output ("here's your result, and
by the way it's corrupted"), any detector would score 100% by reading the tag —
a measurement of nothing. This is exactly the train/test hygiene of supervised
learning: keep the labels out of the features.

**3. A bounded, declarable fault space.** Chaos can be open-ended because it is
not trying to compute a number. A measurement needs a *closed* taxonomy so
coverage is meaningful: Day 8's six modes and four triggers, each in one 10-field
spec, mean "we tested faults A, B, C" is a precise, diffable claim.

## The `stall` mode as the crisp example

`stall` produces output **byte-identical** to a clean call and moves only a
separate cost meter. Under chaos you would inject latency and watch dashboards;
here, the stalled call is *content-indistinguishable* from a clean one, which
proves the point that makes the whole exercise honest: **no function of the
observable output can recover the label** — the truth is only in the log. If
ground truth could be read from the sample, there would be nothing to measure.

## The trap this guards against

The failure mode is subtle and common: build a fault injector that "helpfully"
annotates the faulted output so downstream code can react. That single
convenience destroys the ability to *evaluate* downstream code, because it can
now cheat. Day 8 treats that as the fail condition (D8-004, D8-006): the label is
independent, out of band, and provably absent from every observable surface
(0 leaks across 5 seeds in `integrity_report.json`). Fault injection earns the
right to be called measurement precisely by refusing to leak.

## References worth reading next

- Fault injection foundations: Hsueh, Tsai & Iyer, *Fault Injection Techniques
  and Tools* (IEEE Computer, 1997).
- Mutation testing (deliberate, labelled faults to score a test suite's
  sensitivity): Jia & Harman, *An Analysis and Survey of the Development of
  Mutation Testing* (2011).
- Chaos engineering, for contrast: Basiri et al., *Chaos Engineering* (IEEE
  Software, 2016) and the Principles of Chaos Engineering.
