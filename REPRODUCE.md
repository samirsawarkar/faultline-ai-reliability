# Reproduce FAULTLINE headline results from a cold start

This is the complete clone-to-number procedure for release candidate
`v0.27.0-rc1`. It assumes no existing checkout, Python environment, package
cache, or project knowledge.

## What this reproduces

The command below regenerates and checks every headline result in the root
README:

| result | expected value |
|---|---|
| tool-hop reliability | measured `0.818`; naive `0.91833`; first interval separation at `3` hops |
| frozen detector evaluation | F1 `0.842105` over `17` samples |
| fallback availability and quality | availability `0.6667 → 1.0`; strict answered quality `1.0 → 0.75` |
| winning cascade policy | success `0.9325`; mean cost `1.4656`; p95 latency `50.0` |
| replay-verified postmortems | `2` incidents red → green; Checkpoint `25` passes |
| repository test gate | `433/433` tests pass |

Each value is compared with the JSON pointer registered in
`day26/readme_claims.json`. A successful-looking command is not accepted when a
headline number differs.

## Required starting state

Use an empty parent directory on one of these supported hosts:

- macOS or Linux on `amd64` or `arm64`;
- Git `2.39` or newer;
- GNU Make `3.81` or newer;
- Docker Engine or Docker Desktop with a running Linux-container daemon;
- at least 2 CPU cores, 4 GiB memory, and 5 GiB free disk available to Docker;
- outbound HTTPS access to GitHub, Docker Hub, Debian mirrors, and PyPI.

No Python installation, virtual environment, cloud credentials, API keys, or
project-specific environment variables are required. Windows readers should use
WSL2 with Docker integration; native PowerShell is outside this procedure's
tested boundary.

Confirm the three host tools before cloning:

```sh
git --version
make --version
docker version
```

If `docker version` shows only a client or reports that it cannot connect, start
Docker Desktop or the Docker daemon before continuing.

## Exact cold-start procedure

Copy this block without editing it. `FAULTLINE_REPOSITORY_URL` has a public
default; the override exists so mirrors and the documented cold-start test can
use the identical commands.

<!-- COLD-START:BEGIN -->
```sh
export FAULTLINE_REPOSITORY_URL="${FAULTLINE_REPOSITORY_URL:-https://github.com/samirsawarkar/faultline-ai-reliability.git}"
git clone --config advice.detachedHead=false --branch v0.27.0-rc1 --depth 1 "$FAULTLINE_REPOSITORY_URL" faultline-ai-reliability
cd faultline-ai-reliability
make cold-reproduce
```
<!-- COLD-START:END -->

Do not create a virtual environment, install Python packages on the host, edit a
seed, or copy evidence from another checkout. The Make target builds the pinned
Linux image and runs the generators inside it.

## Required terminal result

The final lines must be exactly:

```text
headline tool_hops: Measured success 0.818 versus naive 0.91833; first interval separation at 3 hops
headline frozen_eval: Frozen test evaluation: F1 0.842105 over 17 samples
headline fallback_quality: Availability 0.6667 → 1.0 while strict quality among answers 1.0 → 0.75
headline q5_policy: Reference P4: success 0.9325, mean cost 1.4656, p95 latency 50.0
headline postmortems: 2 incidents replay red → green; Checkpoint 25 passes
headline tests: 433 tests collected and passed
reader questions: 0
operator improvisations: 0
cold reproduction: PASS
```

Anything else—especially a different number, a missing headline, a nonzero
question/improvisation count, or a failed image build—is a failed reproduction.

## What the one command does

`make cold-reproduce`:

1. checks that Docker and its daemon are available;
2. builds the digest-pinned Python `3.12.4` image from this checkout;
3. runs all isolated tests during image construction;
4. regenerates the five research result families inside the image;
5. resolves every README number through its registered result artifact;
6. prints the exact result block above and exits nonzero on any mismatch.

The build downloads only declared image, operating-system, and Python package
inputs. It does not contact an AI provider or use production data.

## Troubleshooting without improvising

| symptom | documented action |
|---|---|
| `Remote branch v0.27.0-rc1 not found` | Confirm the URL is exactly the public default above. The release has not been published to that mirror; stop rather than switching to `main`. |
| `Cannot connect to the Docker daemon` | Start Docker Desktop or the system Docker service, rerun `docker version`, then repeat the exact procedure in a new empty directory. |
| `no space left on device` | Make at least 5 GiB available to Docker, then repeat in a new empty directory. |
| image manifest or package download fails | Restore outbound HTTPS/DNS access to the listed registries; do not substitute an unpinned base or package version. |
| an expected number differs | Preserve the terminal output and stop. Do not edit README or JSON evidence to match. |
| clone destination already exists | Choose a new empty parent directory. Do not reuse or repair the partial checkout for cold evidence. |

## Evidence and limits

The maintained cold-start transcript, friction history, peer attempt, and
machine-readable gate are under `day27/evidence/`. They prove this documented
path against the seeded repository experiments. They do not prove production
provider behavior, future registry availability, or untested host platforms.
