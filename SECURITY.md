# Security policy

## Scope

FAULTLINE is a synthetic research workbench. It should not contain production
credentials, private documents, personal data, or live provider tokens.

Security-sensitive areas include:

- dependency and GitHub Action pins;
- container provenance and non-root execution;
- trace payload redaction and path handling;
- command construction in reproduction scripts;
- evidence integrity and claim-source binding.

## Reporting a vulnerability

Please use GitHub’s private vulnerability reporting for this repository:

1. Open the repository’s **Security** tab.
2. Choose **Report a vulnerability**.
3. Include the affected revision, reproduction steps, impact, and any proposed
   containment.

Do not open a public issue for a vulnerability that could expose data, execute
untrusted input, or compromise the build.

## Supported version

Security fixes target the current `main` branch and the latest release
candidate. Historical day modules are preserved for reproducibility; when a
historical artifact is unsafe to execute, the remediation will be documented
without silently rewriting the original result.

## Build and data guarantees

- GitHub Actions are pinned to immutable commit SHAs.
- Python and OS dependencies used by the clean container are exactly pinned.
- The runtime user is non-root.
- `.git`, local environments, caches, and editor state are excluded from the
  container context.
- Seeds make experiments reproducible; they are not secrets or security
  boundaries.
- Committed traces are synthetic. Contributions must redact real prompts,
  documents, tokens, request identifiers, and provider metadata before commit.

The pinned build improves reproducibility, not supply-chain certainty by itself.
A production release process should additionally produce an SBOM, sign images
and provenance, scan dependencies, and define a patch-latency policy.
