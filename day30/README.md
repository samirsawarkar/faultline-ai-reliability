# FAULTLINE — Day 30: defense, expert outreach, and launch

Day 30 closes the program with a fail-closed launch gate.

> **Defense result:** ten skeptical staff-level answers now pass the same
> decision → evidence → tradeoff → limitation → reversal rubric after the weak
> baseline answers failed.
>
> **External result:** eight public-channel messages and one issue-backed OSS
> patch are ready. They are not counted as sent or opened without durable URLs.

## Required evidence

| artifact | result |
|---|---|
| [mock-defense.m4a](evidence/mock-defense.m4a) | 402.6-second spoken mock defense |
| [mock-defense-transcript.md](evidence/mock-defense-transcript.md) | ten complete closed-book answers |
| [defense_report.json](evidence/defense_report.json) | ten weak answers red → ten repaired answers green |
| [OUTREACH.md](OUTREACH.md) | eight evidence-led, target-specific drafts |
| [openai/evals contribution packet](oss/openai-evals-1586/README.md) | one-line issue-backed documentation patch |
| [FIRST-72-HOURS.md](FIRST-72-HOURS.md) | three launch windows with gates and rollback |
| [CHECKPOINT-30.md](CHECKPOINT-30.md) | honest pass/pending state |

The spoken recording is synthetic narration. It proves that the prepared
answers can be delivered aloud without implementation code; it does not prove
the repository author's unaided oral proficiency.

## Run it

```bash
make day30-evidence
make test-day30
```

`day30-evidence` intentionally exits non-zero until two selective outreach
messages have durable receipts and one OSS contribution has a public URL.
Prepared copy is not delivery evidence.

On macOS, regenerate the audio with:

```bash
make day30-defense
```

The transcript and audio checksum are bound in
`evidence/defense_recording.json`. Audio regeneration is platform-specific;
auditing the committed recording is not.

## Defense model

Every final answer must contain all five elements:

1. the decision;
2. a verified result;
3. the tradeoff;
4. the honest limitation;
5. the evidence that would reverse the decision.

The answers cite result concepts and numbers, never implementation symbols or
line numbers. The weakest baseline concept was model-form uncertainty: Q1 said
later hops could be harder but did not quantify divergence or state when the
exchangeability assumption could return.

## External-action boundary

- Eight drafts exist; zero are labelled sent without public receipts.
- One genuine issue-backed contribution packet exists; it is labelled prepared,
  not opened.
- Checkpoint 30 remains pending on those two external facts.

This boundary prevents a polished draft from being reported as market or OSS
impact.

## Mastery gate — all five

- **Can explain** — ten answers lead with the decision and user-visible outcome.
- **Can build** — recording, scoring, outreach, OSS, launch, and checkpoint
  artifacts are generated and audited.
- **Can debug** — weak answers identify the missing concept and record the
  repair.
- **Can measure** — every answer binds to committed results; external receipts
  are counted separately.
- **Can defend** — the spoken mock answers every core objection and limitation
  without opening code.
