"""Scoring, the semantic-escape isolation, and the deterministic-vs-semantic map.

The fail condition — "cannot separate deterministic from semantic detection" — is
met by proving the separation: F6 is closed by deterministic detectors (recall
1.0, zero escape) while F5's coherent drift escapes and is isolated as needing
semantic evaluation.
"""
from __future__ import annotations

from faultline_spectrum import build_map, build_report, score_f5, score_f6, semantic_escapes
from faultline_spectrum.experiment import f5_specs, f6_specs
from faultline_spectrum.runner import run_batch

SEED = 20260721


def test_report_is_deterministic():
    assert build_report() == build_report()


def test_f6_is_fully_deterministic_recall_1_no_escape():
    obs, truth = run_batch(f6_specs(), SEED, n_runs=8)
    c = score_f6(obs, truth)
    assert c.recall == 1.0 and c.fn == 0           # deterministic detectors close F6
    assert c.precision == 1.0


def test_f5_consistency_misses_coherent_drift():
    obs, truth = run_batch(f5_specs(), SEED, n_runs=8)
    c = score_f5(obs, truth)
    assert c.recall < 1.0 and c.fn > 0             # coherent drift escapes
    assert c.precision == 1.0


def test_semantic_escapes_are_isolated_with_oracle_evidence():
    obs, truth = run_batch(f5_specs(), SEED, n_runs=8)
    escapes = semantic_escapes(obs, truth)
    assert {e["injected_kind"] for e in escapes} == {"context_drift"}
    for e in escapes:
        assert e["consistency_check"] == "passed"
        assert e["oracle_verdict"] == "wrong"
        assert e["needs_semantic_eval"] is True
        assert e["got_context"] != e["expected_context"]


def test_map_separates_deterministic_from_semantic():
    m = build_map()
    assert m["separation_holds"] is True
    assert set(m["fully_deterministic_recall_1_no_escape"]) == {"F2", "F4", "F6"}
    assert "F5" in m["require_semantic_evaluation"]
    assert "F3" in m["require_semantic_evaluation"]


def test_map_covers_all_six_faults_with_a_nature():
    m = build_map()
    faults = {f["fault"]: f["nature"] for f in m["faults"]}
    assert set(faults) == {"F1", "F2", "F3", "F4", "F5", "F6"}
    assert faults["F6"] == "deterministic" and faults["F5"] == "semantic"
