# LEARN — assumption-free technical instructions

## Instructions are an interface

Technical instructions accept a starting state and should produce an observable
result. Hidden state is an undocumented parameter. Examples include an active
virtual environment, a remembered branch name, a running daemon, cached
credentials, a pre-existing directory, or knowing which warning is safe to
ignore.

A cold-reader test is therefore interface testing:

`declared prerequisites + copied commands → declared result`

If the reader must ask or choose, the interface is incomplete.

## Separate prerequisites from procedure

Prerequisites describe facts that must already be true. Procedure steps change
state. Mixing them makes failures hard to classify: “Docker failed” could mean
the binary is absent, the daemon is stopped, storage is exhausted, or the
registry is unreachable.

Day 27 names the client, daemon, resource, network, platform, and empty-directory
conditions before the clone command.

## Pin identity where identity matters

“Clone the repository” is incomplete research guidance because the default
branch moves. A reproduction document must identify the evidence-bearing
revision and tell readers what to do when it is unavailable. Falling forward to
`main` is not recovery; it changes the experiment.

## Expected output is part of the procedure

An exit code proves only that a program accepted its own execution. Research
reproduction needs an externally stated oracle. Day 27 prints all headline
values and compares each with the registered artifact value before returning
success.

## Troubleshooting must preserve the experiment

Weak troubleshooting says “try another version,” “clear some state,” or “edit
the config.” Those actions may make software run while invalidating the
evidence. Useful troubleshooting maps a recognizable symptom to an action that
restores a declared prerequisite without changing source, pins, seeds, or
results.

## Zero improvisations is measurable

An improvisation is any command, edit, choice, credential, path, version, or
interpretation needed to reach the result but absent from the document.
Questions and interventions are counted in the transcript. The acceptable final
count is zero; “the reader figured it out” is a failed instruction set.

## Limits of a cold-reader proof

One successful reader does not establish universal usability. It verifies the
declared host boundary and catches assumptions present in that attempt.
Different operating systems, corporate proxies, accessibility needs, and future
registry failures require additional readers and environments.
