# LEARN — technical demo pacing for a busy staff engineer

## A demo is a decision path

A research walkthrough usually follows implementation order. A staff-engineer
demo should follow the decision they must make:

```text
identity → failure → causal evidence → intervention → durable proof
```

FAULTLINE names those beats RUN, FAULT, TRACE, RECOVER, and REPLAY. Each beat gets
one headline, at most three screen lines, and one spoken paragraph.

## The 165-second pacing budget

| beat | start | job |
|---|---:|---|
| RUN | 00:00 | freeze incident, seed, configuration, and regression |
| FAULT | 00:24 | show where recovery—not only the provider—failed |
| TRACE | 00:58 | connect observed events into one causal chain |
| RECOVER | 01:34 | show the smallest system controls that change the path |
| REPLAY | 02:12 | prove red→green durability and state the boundary |

The viewer should hear the proof twice: once before the demo and once at replay.
Everything between those sentences must explain why the change is causal.

## Five numbers are enough

Numbers earn space only when they answer a distinct review question:

- **identity:** did we replay the same incident?
- **before:** what user-visible failure occurred?
- **after:** did the fix finish inside the envelope?
- **cost:** did recovery buy success by overspending?
- **stability:** did the result persist?

Additional metrics remain linked in the full evidence but do not occupy the
one-page path.

## Comprehension versus extraction

An automated reader proxy can verify that:

- a proof sentence is easy to locate;
- required concepts appear in that sentence;
- word and estimated reading-time budgets hold;
- the production caveat survives compression.

It cannot verify that a human agrees with the causal interpretation, remembers
it later, or reads at the assumed pace. That distinction belongs in the evidence,
not only in internal notes.

## The last line matters

A strong demo ends with a claim boundary, not applause. For this incident:

> Same incident, seed, configuration, and test: legacy stayed red, fixed stayed
> green. This proves the corrective control in the simulator; production
> provider independence remains unproven.

That sentence is short enough to repeat in an architecture review and precise
enough to challenge.
