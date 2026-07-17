"""Triggers are pure, reproducible, and honest about seed-dependence."""
from __future__ import annotations

from faultline_inject import FaultSpec, SPEC_VERSION, component_matches, fires


def spec(trigger, trigger_value, rate=1.0, seed=7, component="*"):
    return FaultSpec(
        fault_id="F", component=component, mode="stall", severity=1,
        trigger=trigger, trigger_value=trigger_value, seed=seed, rate=rate,
        label="fault:stall", spec_version=SPEC_VERSION,
    ).validate()


def test_component_match_and_wildcard():
    assert component_matches(spec("call_index", "0", component="*"), "tool.x")
    assert component_matches(spec("call_index", "0", component="tool.x"), "tool.x")
    assert not component_matches(spec("call_index", "0", component="tool.x"), "tool.y")


def test_call_index_fires_only_on_that_index():
    s = spec("call_index", "3")
    fired = [seq for seq in range(8) if fires(s, run_seed=1, seq=seq, input_digest="d")]
    assert fired == [3]


def test_every_n_fires_on_multiples():
    s = spec("every_n", "2")
    fired = [seq for seq in range(8) if fires(s, run_seed=1, seq=seq, input_digest="d")]
    assert fired == [0, 2, 4, 6]


def test_input_match_fires_on_prefix():
    s = spec("input_match", "ab")
    assert fires(s, 1, 0, "abcdef")
    assert not fires(s, 1, 0, "xyz")


def test_deterministic_triggers_ignore_seed():
    # call_index / every_n / input_match must fire identically for any run_seed.
    for s in (spec("call_index", "2"), spec("every_n", "3"), spec("input_match", "a")):
        for seq in range(6):
            base = fires(s, 0, seq, "abc")
            for seed in (1, 999, 20260718):
                assert fires(s, seed, seq, "abc") == base


def test_probabilistic_is_reproducible_and_seed_sensitive():
    s = spec("probabilistic", "", rate=0.5, seed=7)
    pattern_a = [fires(s, 111, seq, "d") for seq in range(40)]
    pattern_a2 = [fires(s, 111, seq, "d") for seq in range(40)]
    pattern_b = [fires(s, 222, seq, "d") for seq in range(40)]
    assert pattern_a == pattern_a2          # reproducible within a seed
    assert pattern_a != pattern_b           # varies across seeds
    # roughly `rate` of calls fire (loose bound; 40 draws)
    assert 8 <= sum(pattern_a) <= 32


def test_probabilistic_rate_zero_and_one():
    never = spec("probabilistic", "", rate=0.0)
    always = spec("probabilistic", "", rate=1.0)
    assert not any(fires(never, 5, seq, "d") for seq in range(20))
    assert all(fires(always, 5, seq, "d") for seq in range(20))
