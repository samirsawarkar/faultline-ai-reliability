"""Replay-difference report — the mission's headline evidence.

For each provider it measures two very different questions, and keeps them
strictly separate so no claim exceeds what captured state supports:

  replay_exact   Does REPLAY (serving recorded bytes) reproduce the captured
                 trace? This is playback; it is exact for ANY provider.
  reexec_exact   Does RE-EXECUTING the program live (recomputing provider
                 outputs) reproduce the captured trace? This is TRUE
                 reproducibility; it holds ONLY for the deterministic simulator.

The gap between these two columns is the reproducibility boundary. A real
provider gets `replay_exact: true` (we can play back what we saw) but
`reexec_exact: false` (we cannot regenerate it) — and we never pretend otherwise.
"""
from __future__ import annotations

from typing import Any, Dict

from .capture import capture_run
from .diff import diff_summary
from .replay import replay_bundle

SEED = 6
TASK = "sum the archive"


def _scenario(provider: str) -> Dict[str, Any]:
    bundle = capture_run(provider, SEED, TASK)
    captured_trace = bundle["trace"]

    # 1) Replay: serve recorded outputs. Should reproduce the captured trace.
    replayed = replay_bundle(bundle)
    replay_diff = diff_summary(captured_trace, replayed["trace"])

    # 2) Re-execute live from the same inputs: recompute provider outputs.
    reexec_bundle = capture_run(provider, SEED, TASK)
    reexec_diff = diff_summary(captured_trace, reexec_bundle["trace"])

    # Record the PATHS that differ (structurally stable), not the volatile
    # values (nonces/sha256), so the committed report is byte-reproducible.
    reexec_paths = sorted({d["path"] for d in reexec_diff["diffs"]})

    return {
        "provider": provider,
        "replay_exact": replay_diff["equal"],
        "replay_diff_count": replay_diff["diff_count"],
        "reexec_exact": reexec_diff["equal"],
        "reexec_diff_count": reexec_diff["diff_count"],
        "reexec_diff_paths": reexec_paths,
        "calls_replayed": replayed["calls_consumed"],
    }


def build_report() -> Dict[str, Any]:
    sim = _scenario("simulator")
    flaky = _scenario("flaky")

    # The fail-condition guard, asserted as data: replay is exact for both;
    # re-execution is exact ONLY for the simulator.
    claims_hold = (
        sim["replay_exact"] and sim["reexec_exact"]
        and flaky["replay_exact"] and not flaky["reexec_exact"]
    )

    return {
        "seed": SEED,
        "task": TASK,
        "scenarios": [sim, flaky],
        "claims": {
            "replay_reproduces_captured_bytes": "always (playback of recorded calls)",
            "reexecution_reproduces_run": "only for the deterministic simulator",
            "cannot": [
                "regenerate a real provider's output by re-execution",
                "produce a real provider's output for an input we did not capture",
                "reproduce uncaptured entropy (sampling / hardware RNG / model drift)",
            ],
        },
        "claims_hold": claims_hold,
    }
