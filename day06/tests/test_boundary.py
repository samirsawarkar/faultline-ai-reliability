"""The reproducibility boundary — and the guard on over-claiming (fail cond.)."""
from __future__ import annotations

from faultline_replay import build_report, capture_run, diff_summary, replay_bundle


def test_real_provider_replays_but_does_not_reexecute():
    """A flaky (real-provider stand-in) run can be PLAYED BACK exactly, but
    RE-EXECUTING it live diverges — because its output depends on uncaptured
    entropy. This is the boundary the mission must not cross."""
    bundle = capture_run("flaky", 6, "sum the archive")

    # Playback of recorded calls reproduces the captured trace exactly.
    replayed = replay_bundle(bundle)
    assert diff_summary(bundle["trace"], replayed["trace"])["equal"]

    # Re-executing live does NOT reproduce it.
    reexec = capture_run("flaky", 6, "sum the archive")
    assert not diff_summary(bundle["trace"], reexec["trace"])["equal"]


def test_report_claims_hold_and_are_bounded():
    r = build_report()
    assert r["claims_hold"] is True
    sim = next(s for s in r["scenarios"] if s["provider"] == "simulator")
    flaky = next(s for s in r["scenarios"] if s["provider"] == "flaky")
    assert sim["replay_exact"] and sim["reexec_exact"]
    assert flaky["replay_exact"] and not flaky["reexec_exact"]
    assert flaky["reexec_diff_count"] > 0
    # the report explicitly enumerates what captured state CANNOT reproduce
    assert r["claims"]["cannot"]


def test_report_is_process_deterministic():
    """Same fresh-process report content is byte-stable (diff paths, not values)."""
    import json
    a = json.dumps(build_report(), sort_keys=True)
    # a second build in the SAME process advances the entropy counter, so diff
    # PATHS stay identical even though the underlying nonce values moved on.
    b = build_report()
    a_paths = json.loads(a)["scenarios"][1]["reexec_diff_paths"]
    assert b["scenarios"][1]["reexec_diff_paths"] == a_paths
