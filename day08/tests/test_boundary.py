"""The boundary wrapper injects the right effect and labels it out of band."""
from __future__ import annotations

import json

import pytest

from faultline_inject import (
    DemoChannel,
    FaultSpec,
    GroundTruthLog,
    InjectedFaultError,
    InjectingChannel,
    SPEC_VERSION,
)


def spec(mode, severity=3, trigger="call_index", trigger_value="0",
         component="*", rate=1.0, fault_id="F", label=None):
    return FaultSpec(
        fault_id=fault_id, component=component, mode=mode, severity=severity,
        trigger=trigger, trigger_value=trigger_value, seed=7, rate=rate,
        label=label or f"fault:{mode}", spec_version=SPEC_VERSION,
    )


def call_once(specs, payload=None):
    payload = payload or {"step": "retrieve", "index": 0}
    ch = InjectingChannel(DemoChannel(), specs, run_seed=1)
    out = ch.call("tool.retrieve", payload)
    return out, ch


def test_no_specs_is_clean_passthrough():
    clean = DemoChannel().call("tool.retrieve", {"step": "retrieve", "index": 0})
    out, ch = call_once([])
    assert out == clean
    assert ch.truth.fired_seqs() == []
    assert ch.truth.entries[0].label == "clean"


def test_corrupt_changes_a_numeric_value_deterministically():
    out, _ = call_once([spec("corrupt", severity=3)])
    assert out["value"] == 10 + 3 * 111       # (0+1)*10 + severity*111
    assert out["tokens"] == [0, 1, 2, 3]       # untouched


def test_stall_leaves_content_identical_but_bumps_cost():
    clean = DemoChannel().call("tool.retrieve", {"step": "retrieve", "index": 0})
    out, ch = call_once([spec("stall", severity=4)])
    assert out == clean                        # content indistinguishable
    assert ch.cost_units == 40                 # only the side channel moved


def test_truncate_and_duplicate_and_drop():
    out_t, _ = call_once([spec("truncate", severity=2)])
    assert len(out_t["tokens"]) < 4 and out_t["tokens"] == [0, 1, 2][:len(out_t["tokens"])]
    out_d, _ = call_once([spec("duplicate", severity=2)])
    assert out_d["tokens"] == [0, 1] + [0, 1, 2, 3]
    out_x, _ = call_once([spec("drop")])
    assert out_x["tokens"] == [] and out_x["value"] == 0


def test_error_mode_raises_and_is_still_labelled():
    ch = InjectingChannel(DemoChannel(), [spec("error")], run_seed=1)
    with pytest.raises(InjectedFaultError):
        ch.call("tool.retrieve", {"step": "retrieve", "index": 0})
    assert ch.truth.entries[0].fired is True
    assert ch.truth.entries[0].mode == "error"


def test_truth_log_is_a_complete_contiguous_labelling():
    specs = [spec("corrupt", trigger="every_n", trigger_value="2")]
    ch = InjectingChannel(DemoChannel(), specs, run_seed=1)
    for i in range(6):
        ch.call("tool.retrieve", {"step": "retrieve", "index": i})
    assert [e.seq for e in ch.truth.entries] == list(range(6))  # contiguous
    assert ch.truth.fired_seqs() == [0, 2, 4]                    # every 2nd call


def test_component_scoping_only_faults_targeted_calls():
    specs = [spec("corrupt", component="tool.sum", trigger="every_n", trigger_value="1")]
    ch = InjectingChannel(DemoChannel(), specs, run_seed=1)
    r = ch.call("tool.retrieve", {"step": "retrieve", "index": 0})
    s = ch.call("tool.sum", {"step": "sum", "index": 1})
    assert not ch.truth.entries[0].fired          # retrieve untouched
    assert ch.truth.entries[1].fired              # sum faulted
    assert r["value"] == 10 and s["value"] != 20


def test_first_matching_spec_wins():
    specs = [spec("stall", fault_id="A", label="fault:stall"),
             spec("corrupt", fault_id="B", label="fault:corrupt")]
    _, ch = call_once(specs)
    assert ch.truth.entries[0].fault_id == "A"    # declaration order breaks ties


def test_trace_span_carries_output_not_label():
    import faultline_trace as ft
    tracer = ft.Tracer(1)
    ch = InjectingChannel(DemoChannel(), [spec("corrupt")], run_seed=1, tracer=tracer)
    ch.call("tool.retrieve", {"step": "retrieve", "index": 0})
    trace_json = json.dumps(tracer.to_dict())
    assert "fault:corrupt" not in trace_json      # label never in the trace
    assert "corrupt" not in trace_json            # nor the mode word
    spans = tracer.to_dict()["spans"]
    assert all(s["end_seq"] is not None for s in spans)  # complete spans


def test_error_span_is_a_complete_error_span():
    import faultline_trace as ft
    tracer = ft.Tracer(1)
    ch = InjectingChannel(DemoChannel(), [spec("error")], run_seed=1, tracer=tracer)
    with pytest.raises(InjectedFaultError):
        ch.call("tool.retrieve", {"step": "retrieve", "index": 0})
    span = tracer.to_dict()["spans"][0]
    assert span["status"] == "error" and span["end_seq"] is not None
    assert span["error"] is not None
