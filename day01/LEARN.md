# LEARN.md — Day 1 study notes

Two ideas, kept because they are the load-bearing ones for everything later.

## 1. Deterministic seeding — how, and where it silently breaks

**How it works.** A pseudo-random generator is a state machine. Seed it and you
fix the starting state; the sequence of draws is then a pure function of the
seed. `random.Random(seed)` uses the Mersenne Twister, whose algorithm is
specified and stable across CPython versions and operating systems, so
`Random(7)` yields the same stream on my laptop and on CI.

**Where determinism silently leaks (and how we closed each):**
- **Hash-order iteration.** Iterating a `set` or relying on `dict` insertion
  quirks can vary with `PYTHONHASHSEED`. → We never iterate a `set` to build
  output; we sort attribute keys explicitly, and we *test* under
  `PYTHONHASHSEED=0/1/random`.
- **Serialization drift.** Default JSON key order follows construction; floats,
  encodings, and trailing newlines vary. → `canonical_bytes` pins `sort_keys`,
  `ensure_ascii`, `indent`, and a single `\n`.
- **Ambient entropy.** Timestamps, hostnames, absolute paths, `time()`,
  unseeded `random`. → None appear in the environment object.
- **Version drift.** A different RNG or Python could move the stream. → Pinned
  by `SPEC_VERSION` + committed `evidence/seed_digests.tsv` as a tripwire.

The test `test_byte_identical_across_fresh_processes_and_hashseeds` is the proof:
regenerate 20 seeds in fresh interpreters with different hash seeds → identical
bytes.

## 2. Why an oracle beats eyeballing

Eyeballing fails on four axes at once:
- **Not reproducible** — two reviewers (or the same reviewer twice) disagree.
- **Not scalable** — you cannot hand-grade thousands of items per seed.
- **Not honest under pressure** — it's easy to unconsciously give credit for a
  right-looking answer that was never actually grounded.
- **Not comparable over time** — yesterday's leniency contaminates today's delta.

An oracle is a *pure function*: same input → same verdict, forever, for free. It
lets us encode the stance we actually care about — **grounding** — as a rule
(`passed = correct AND cited_required`) rather than a vibe. The cost is that the
oracle itself must be trustworthy, which is exactly why we hand-check 10 cases
against human-obvious expectations and keep that check as an enforced script.

**One-line takeaway:** seeding makes the *world* reproducible; the oracle makes
the *judgment* reproducible. You need both before any downstream number means
anything.
