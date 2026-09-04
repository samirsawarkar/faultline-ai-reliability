# Decisions for P02 OpenTelemetry GenAI Exporter

- **Pinned Semantic Conventions Provenance (v1.29.0 Hand Transcription)**: `faultline_p2/otel/registry/semconv_v1_29_0.json` is a **hand transcription** of the OpenTelemetry GenAI Semantic Conventions v1.29.0, authored locally within this repository. It was not fetched, attested, or pulled directly from upstream build pipelines. The upstream specification documentation transcribed is:
  `https://github.com/open-telemetry/semantic-conventions/blob/v1.29.0/docs/gen-ai/gen-ai-spans.md`
  While evaluating tests against a committed registry file prevents hardcoded test assertion drift, this local transcription carries the risk that any human error during transcription could cause the conformance test to pass against a flawed local schema.
- **Open Item — Upstream Registry Verification**: To establish true upstream provenance, this transcription requires formal verification by either:
  1. Automated fetching and diffing against upstream semantic-conventions release YAML artifacts in CI, or
  2. Cryptographically hash-pinning an official upstream OpenTelemetry registry schema release artifact.
  Until this verification step is implemented, conformance is validated against this repository's local transcription of the v1.29.0 specification.
- **OTLP JSON Emission Without New Dependencies**: `opentelemetry-sdk` was not installed in the repo virtualenv. Following the CTO directive, we did not invent a custom schema or add unpinned pip dependencies; instead, we implemented direct serialization to the official OpenTelemetry OTLP HTTP/JSON standard (`resourceSpans` / `scopeSpans` / `spans`) and verified structural correctness with `jsonschema>=4.26.0` (declared in `pyproject.toml`).
- **Three-Tier Nesting Hierarchy**: We structured spans into a strict three-tier causal hierarchy: `invoke_agent` (INTERNAL root) → `chat` (CLIENT model generation) → `execute_tool` (INTERNAL tool dispatch). Tool execution is nested directly under the `chat` span that prompted it, preserving causal provenance.
- **Zero-Spend Sink Verification Discipline**: We strictly distinguish verified sinks (in-memory OTel structures and standard OTLP JSON files) from unverified remote collectors (Langfuse, Arize Phoenix). In keeping with the project's $0 budget and zero-network policy, we make no claims regarding unexercised third-party platforms.
