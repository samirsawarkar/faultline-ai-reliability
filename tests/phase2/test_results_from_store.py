import json
import sqlite3
from pathlib import Path
from faultline_p2.trace.store import TraceStore
from faultline_p2.stats.intervals import wilson_interval
from projects.p01_baseline.run import build_results_from_trace


def test_build_results_from_trace_store_isolated(tmp_path):
    """Assert results are reconstructed from trace.db alone and select only the specified run."""
    db_path = tmp_path / "test_trace.db"
    store = TraceStore(str(db_path))

    # Create Run 1 (prior run)
    run1 = store.start_run()
    store.log_span(
        run_id=run1, scenario_id="s-old", tier="T1", step_index=1,
        model_name="stub", provider="local", model_version="1.0",
        prompt_tokens=100, completion_tokens=10
    )
    store.record_verdict(run1, "s-old", False)
    store.end_run(run1, "completed")

    # Create Run 2 (current sweep run)
    run2 = store.start_run()
    # Scenario 1 (T1, passed, 2 steps)
    store.log_span(
        run_id=run2, scenario_id="s-001", tier="T1", step_index=1,
        model_name="stub", provider="local", model_version="1.0",
        tool_name="search", prompt_tokens=200, completion_tokens=20
    )
    store.log_span(
        run_id=run2, scenario_id="s-001", tier="T1", step_index=2,
        model_name="stub", provider="local", model_version="1.0",
        tool_name="answer", prompt_tokens=300, completion_tokens=30,
        termination_reason="ANSWERED"
    )
    store.record_verdict(run2, "s-001", True)

    # Scenario 2 (T1, failed, 1 step)
    store.log_span(
        run_id=run2, scenario_id="s-002", tier="T1", step_index=1,
        model_name="stub", provider="local", model_version="1.0",
        prompt_tokens=150, completion_tokens=15,
        termination_reason="STEP_CAP"
    )
    store.record_verdict(run2, "s-002", False)

    # Scenario 3 (T2, passed, 3 steps)
    store.log_span(
        run_id=run2, scenario_id="s-003", tier="T2", step_index=1,
        model_name="stub", provider="local", model_version="1.0",
        prompt_tokens=500, completion_tokens=50
    )
    store.log_span(
        run_id=run2, scenario_id="s-003", tier="T2", step_index=2,
        model_name="stub", provider="local", model_version="1.0",
        prompt_tokens=600, completion_tokens=60
    )
    store.log_span(
        run_id=run2, scenario_id="s-003", tier="T2", step_index=3,
        model_name="stub", provider="local", model_version="1.0",
        prompt_tokens=700, completion_tokens=70,
        termination_reason="ANSWERED"
    )
    store.record_verdict(run2, "s-003", True)
    store.end_run(run2, "completed")
    store.close()

    # Discard in-memory objects completely and rebuild results from store alone
    reconstructed = build_results_from_trace(db_path, run_id=run2)

    # Verify run 1 data was excluded: total scenarios in run 2 should be 3
    t1 = reconstructed["tiers"]["T1"]
    assert t1["n"] == 2
    assert t1["pass_rate"] == 0.5
    assert t1["wilson_ci"] == list(wilson_interval(1, 2))
    assert t1["avg_steps"] == 1.5  # (2 + 1) / 2
    assert t1["avg_tokens"]["prompt"] == int((500 + 150) / 2)  # 325
    assert t1["avg_tokens"]["completion"] == int((50 + 15) / 2)  # 32

    t2 = reconstructed["tiers"]["T2"]
    assert t2["n"] == 1
    assert t2["pass_rate"] == 1.0
    assert t2["avg_steps"] == 3.0
    assert t2["avg_tokens"]["prompt"] == 1800
    assert t2["avg_tokens"]["completion"] == 180

    assert reconstructed["pass@1"]["score"] == 2 / 3
    assert reconstructed["pass@1"]["wilson_ci"] == list(wilson_interval(2, 3))


def test_p01_committed_trace_matches_results():
    """Verify that projects/p01_baseline/results.json matches the store reconstruction."""
    trace_path = Path("projects/p01_baseline/trace.db")
    results_path = Path("projects/p01_baseline/results.json")
    if not trace_path.exists() or not results_path.exists():
        return

    with open(results_path) as f:
        expected = json.load(f)

    reconstructed = build_results_from_trace(trace_path)
    assert reconstructed["pass@1"]["score"] == expected["pass@1"]["score"]
    assert reconstructed["pass@1"]["wilson_ci"] == expected["pass@1"]["wilson_ci"]
    for tier in ["T1", "T2", "T3"]:
        if tier in expected["tiers"]:
            assert tier in reconstructed["tiers"]
            assert reconstructed["tiers"][tier]["n"] == expected["tiers"][tier]["n"]
            assert reconstructed["tiers"][tier]["pass_rate"] == expected["tiers"][tier]["pass_rate"]
            assert reconstructed["tiers"][tier]["wilson_ci"] == expected["tiers"][tier]["wilson_ci"]
            assert reconstructed["tiers"][tier]["avg_steps"] == expected["tiers"][tier]["avg_steps"]
            assert reconstructed["tiers"][tier]["avg_tokens"] == expected["tiers"][tier]["avg_tokens"]
