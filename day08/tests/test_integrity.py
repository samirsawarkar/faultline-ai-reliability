"""Injection integrity: identical triggers across seeds, no label leakage.

This is the Day-8 fail condition made executable — injected faults must have
deterministic triggers AND independent truth labels.
"""
from __future__ import annotations

import faultline_trace as ft  # Day 4 (path added by faultline_inject.integrity)

from faultline_inject import (
    FaultSpec,
    SPEC_VERSION,
    assert_deterministic,
    build_report,
    default_calls,
    leakage_scan,
    run_boundary,
)


def scenario():
    return [
        FaultSpec("F-idx", "*", "corrupt", 3, "call_index", "4", 1, 1.0,
                  "fault:corrupt", SPEC_VERSION),
        FaultSpec("F-evn", "tool.verify", "truncate", 2, "every_n", "2", 2, 1.0,
                  "fault:truncate", SPEC_VERSION),
        FaultSpec("F-prb", "tool.retrieve", "stall", 4, "probabilistic", "", 9, 0.5,
                  "fault:stall", SPEC_VERSION),
    ]


SEEDS = [20260718, 1, 42, 777, 100000]


def test_same_seed_is_byte_identical():
    assert_deterministic(scenario(), run_seed=20260718, calls=default_calls(), repeats=4)


def test_report_all_seeds_reproducible():
    rep = build_report(scenario(), SEEDS)
    assert rep["all_seeds_reproducible"] is True


def test_deterministic_triggers_are_seed_independent():
    rep = build_report(scenario(), SEEDS)
    assert rep["deterministic_triggers_seed_independent"] is True


def test_probabilistic_trigger_varies_across_seeds():
    rep = build_report(scenario(), SEEDS)
    assert rep["probabilistic_trigger_varies_across_seeds"] is True


def test_no_label_leakage_across_all_seeds():
    rep = build_report(scenario(), SEEDS)
    assert rep["no_label_leakage"] is True
    assert rep["label_leaks_total"] == 0


def test_leakage_scan_would_catch_a_planted_leak():
    # sanity: the scanner is not vacuous — if a label were in the output, it fires.
    out, truth, _ = run_boundary(scenario(), 20260718, default_calls())
    assert leakage_scan(out, truth) == []
    poisoned = out + ["fault:corrupt"]           # simulate a leak
    assert "fault:corrupt" in leakage_scan(poisoned, truth)


def test_stall_output_matches_clean_so_content_cannot_reveal_truth():
    # A stalled call's OUTPUT is identical to a clean call's, so no function of
    # the output content can recover the label — the truth must come from the log.
    specs = [FaultSpec("S", "*", "stall", 3, "call_index", "0", 1, 1.0,
                       "fault:stall", SPEC_VERSION)]
    faulted, truth_f, cost = run_boundary(specs, 1, default_calls(1))
    clean, truth_c, _ = run_boundary([], 1, default_calls(1))
    assert faulted == clean                       # indistinguishable content
    assert truth_f.entries[0].fired and not truth_c.entries[0].fired
    assert cost > 0


def test_labelled_trace_reconstructs_without_leaking():
    # Build a real Day-4 trace alongside the truth log; the label joins by
    # span_id, never appears in the span.
    specs = scenario()
    tracer = ft.Tracer(20260718)
    out, truth, _ = run_boundary(specs, 20260718, default_calls(), tracer=tracer)
    trace = tracer.to_dict()
    assert leakage_scan(out, truth, trace=trace) == []
    # every fired truth entry links to a real span in the trace
    span_ids = {s["span_id"] for s in trace["spans"]}
    for e in truth.entries:
        assert e.span_id in span_ids
