"""Detectors turn observables into signals — deterministically, and only from
what the system under test can see."""
from __future__ import annotations

from faultline_detect import (
    BASE_LATENCY,
    DEFAULT_BUDGET,
    duration_detect,
    f1_corruption_spec,
    f2_latency_spec,
    run,
    schema_detect,
)


def test_schema_detector_flags_corruption_and_raises_repair_signal():
    spec = f1_corruption_spec("*", 5, mode="drop", trigger="every_n", trigger_value="2", seed=1)
    obs, truth, _ = run([spec], 1)
    for o in obs:
        sig = schema_detect(o.seq, o.output)
        fired = truth.entries[o.seq].fired
        assert sig.repair_signal == fired          # invalid exactly on faulted calls
        assert sig.valid == (not fired)


def test_schema_detector_ignores_latency_faults():
    # stall leaves content valid; the schema detector must NOT flag it.
    spec = f2_latency_spec("*", 5, trigger="every_n", trigger_value="1", seed=1)
    obs, truth, _ = run([spec], 1)
    assert all(schema_detect(o.seq, o.output).valid for o in obs)


def test_duration_detector_is_budget_gated():
    # sev4 -> duration 50; caught under budget 45, missed under budget 60.
    spec = f2_latency_spec("*", 4, trigger="every_n", trigger_value="1", seed=1)
    obs, _, _ = run([spec], 1)
    d = obs[0].duration
    assert d == BASE_LATENCY + 40
    assert duration_detect(0, d, budget=45).timeout_signal is True
    assert duration_detect(0, d, budget=60).timeout_signal is False


def test_clean_calls_have_base_duration():
    obs, _, _ = run([], 1)
    assert all(o.duration == BASE_LATENCY for o in obs)
    assert all(not duration_detect(o.seq, o.duration).timeout_signal for o in obs)


def test_detectors_are_pure():
    obs, _, _ = run([f1_corruption_spec("*", 3, trigger="every_n", trigger_value="2")], 7)
    a = [schema_detect(o.seq, o.output).to_dict() for o in obs]
    b = [schema_detect(o.seq, o.output).to_dict() for o in obs]
    assert a == b
    assert DEFAULT_BUDGET == 45
