"""Tests for Project P3: Grounding Zero-Point."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from faultline_p2.agent.agent import run_agent
from faultline_p2.agent.contracts import ScenarioTask
from faultline_p2.agent.model import StubModel
from faultline_p2.env.corpus import build_corpus
from faultline_p2.oracle._day01_oracle import oracle_check
from faultline_p2.trace.store import TraceStore
from projects.p03_grounding.run import (
    build_results_from_trace,
    ensure_manifest,
    generate_figure,
)


def test_manifest_structure_and_disjointness():
    """Manifest must partition the 350 scenarios into 200 standard and 150 reserved hard."""
    manifest = ensure_manifest()
    corpus = build_corpus()

    assert manifest["spec_version"] == "2.0.0"
    assert manifest["corpus_hash"] == corpus.content_hash

    std_ids = set(manifest["pools"]["standard"]["scenario_ids"])
    res_ids = set(manifest["pools"]["reserved_hard"]["scenario_ids"])

    assert len(std_ids) == 200
    assert len(res_ids) == 150
    assert len(std_ids.intersection(res_ids)) == 0, "Standard and reserved pools must be disjoint"
    assert len(std_ids.union(res_ids)) == 350, "Manifest must cover all 350 corpus scenarios"

    # Check tier distributions
    std_scenarios = [s for s in corpus.scenarios if s.scenario_id in std_ids]
    res_scenarios = [s for s in corpus.scenarios if s.scenario_id in res_ids]

    t1_count = sum(1 for s in std_scenarios if s.tier == "T1")
    t2_count = sum(1 for s in std_scenarios if s.tier == "T2")
    t3_count = sum(1 for s in std_scenarios if s.tier == "T3")
    assert t1_count == 67
    assert t2_count == 67
    assert t3_count == 66

    assert all(s.tier == "T3" for s in res_scenarios), "Reserved pool must contain exclusively T3 scenarios"


def test_manifest_hash_reproducibility():
    """Manifest generation must be deterministic and hash-stable."""
    m1 = ensure_manifest()
    m2 = ensure_manifest()
    assert m1["manifest_sha256"] == m2["manifest_sha256"]
    assert m1["pools"]["standard"]["sha256"] == m2["pools"]["standard"]["sha256"]
    assert m1["pools"]["reserved_hard"]["sha256"] == m2["pools"]["reserved_hard"]["sha256"]


def test_p03_offline_solver_trace_and_results():
    """Offline solver execution produces valid spans and results.json structure with Wilson CIs."""
    corpus = build_corpus()
    store = TraceStore(":memory:")
    run_id = store.start_run()
    model = StubModel(behavior="solver")
    env = {"documents": corpus.documents}

    # Sample one scenario from each tier in standard pool
    std_scenarios = [s for s in corpus.scenarios if s.pool == "standard"]
    sample_scenarios = [
        next(s for s in std_scenarios if s.tier == "T1"),
        next(s for s in std_scenarios if s.tier == "T2"),
        next(s for s in std_scenarios if s.tier == "T3"),
    ]

    for sc in sample_scenarios:
        task = ScenarioTask(task_id=sc.scenario_id, prompt=sc.prompt, tier=sc.tier)
        outcome = run_agent(task, env, model, step_cap=12, trace_store=store, run_id=run_id)
        ans = outcome.answer if outcome.answer else ""
        verdict = oracle_check(
            {"id": sc.scenario_id, "answer": sc.final_answer, "required_source": sc.required_source},
            {"answer": ans, "cited_sources": outcome.cited_sources},
        )
        store.record_verdict(run_id, sc.scenario_id, verdict["passed"])

    store.end_run(run_id, "completed")
    results = build_results_from_trace(store)

    assert results["metadata"]["project"] == "P3"
    assert "pass@1" in results
    assert "tiers" in results
    assert "T1" in results["tiers"]
    assert "T2" in results["tiers"]
    assert "T3" in results["tiers"]
    assert results["tiers"]["T1"]["pass_rate"] == 1.0
    assert results["tiers"]["T2"]["pass_rate"] == 1.0
    assert results["tiers"]["T3"]["pass_rate"] == 1.0
    assert len(results["tiers"]["T1"]["wilson_ci"]) == 2
    assert results["tiers"]["T1"]["avg_steps"] > 0
    assert "hypotheses" in results


def test_p03_figure_generation(tmp_path):
    """Figure generator emits valid SVG with tier elements and labels."""
    results = {
        "metadata": {"model": "test-model", "reference": "MEC v1.0"},
        "tiers": {
            "T1": {"n": 67, "pass_rate": 0.94, "wilson_ci": [0.85, 0.98], "avg_steps": 4.1},
            "T2": {"n": 67, "pass_rate": 0.56, "wilson_ci": [0.44, 0.67], "avg_steps": 10.5},
            "T3": {"n": 66, "pass_rate": 0.12, "wilson_ci": [0.06, 0.22], "avg_steps": 11.8},
        },
    }
    fig_path = tmp_path / "test_figure.svg"
    generate_figure(results, fig_path)

    assert fig_path.is_file()
    content = fig_path.read_text(encoding="utf-8")
    assert "<svg" in content
    assert "</svg>" in content
    assert "T1 (1-hop)" in content
    assert "T2 (3-hop)" in content
    assert "T3 (5-hop)" in content
    assert "94.0%" in content
    assert "Day 3 Simulator Baseline" in content
