import json
import sqlite3
import subprocess
import sys
from pathlib import Path

from faultline_p2.agent.contracts import LookupCall, SearchCall
from faultline_p2.attribute.attribution import attribute
from faultline_p2.attribute.oracle_toolbox import OracleToolBox
from faultline_p2.stats.intervals import wilson_interval


def test_oracle_toolbox_search_and_lookup():
    """(a) OracleToolBox.search returns traversal_sources for a nonsense query and lookup on them succeeds."""
    env = {
        "documents": [
            {"id": "doc-0001", "title": "Alpha Document", "text": "Content of document 1."},
            {"id": "doc-0002", "title": "Beta Document", "text": "Content of document 2 with key facts."},
            {"id": "doc-0003", "title": "Gamma Document", "text": "Content of document 3."},
        ]
    }
    traversal = ["doc-0002", "doc-0001"]
    tb = OracleToolBox(env=env, traversal_sources=traversal)

    # Search with nonsense query
    res = tb.search(SearchCall(query="gibberish totally unrelated nonsense"))
    assert res.ok
    assert len(res.candidates) == 2
    # Returned in traversal order
    assert [c.doc_id for c in res.candidates] == ["doc-0002", "doc-0001"]
    assert res.candidates[0].score == 3.0
    assert res.candidates[0].snippet == "Content of document 2 with key facts."

    # Lookup on returned candidates succeeds
    lookup_res1 = tb.lookup(LookupCall(doc_id="doc-0002"))
    assert lookup_res1.ok
    assert lookup_res1.text == "Content of document 2 with key facts."

    lookup_res2 = tb.lookup(LookupCall(doc_id="doc-0001"))
    assert lookup_res2.ok
    assert lookup_res2.text == "Content of document 1."


def test_attribution_table_and_infra_exclusion():
    """(b) attribute() on a hand-built 12-pair table gives exact counts, share, CI bounds and verdict,

    plus an infra_dead pair being dropped only in infra_excluded.
    """
    pairs = [
        # 6 retriever_owned (fail-A & pass-B)
        {"scenario_id": "s-1", "tier": "T1", "a_passed": False, "b_passed": True, "a_status": "answered", "b_status": "answered"},
        {"scenario_id": "s-2", "tier": "T1", "a_passed": False, "b_passed": True, "a_status": "answered", "b_status": "answered"},
        {"scenario_id": "s-3", "tier": "T2", "a_passed": False, "b_passed": True, "a_status": "step_limit_exceeded", "b_status": "answered"},
        {"scenario_id": "s-4", "tier": "T2", "a_passed": False, "b_passed": True, "a_status": "step_limit_exceeded", "b_status": "answered"},
        {"scenario_id": "s-5", "tier": "T3", "a_passed": False, "b_passed": True, "a_status": "malformed", "b_status": "answered"},
        {"scenario_id": "s-6", "tier": "T3", "a_passed": False, "b_passed": True, "a_status": "malformed", "b_status": "answered"},
        # 2 generator_owned (fail-A & fail-B)
        {"scenario_id": "s-7", "tier": "T2", "a_passed": False, "b_passed": False, "a_status": "answered", "b_status": "answered"},
        {"scenario_id": "s-8", "tier": "T3", "a_passed": False, "b_passed": False, "a_status": "answered", "b_status": "answered"},
        # 1 reverse (pass-A & fail-B)
        {"scenario_id": "s-9", "tier": "T1", "a_passed": True, "b_passed": False, "a_status": "answered", "b_status": "answered"},
        # 2 both_pass (pass-A & pass-B)
        {"scenario_id": "s-10", "tier": "T1", "a_passed": True, "b_passed": True, "a_status": "answered", "b_status": "answered"},
        {"scenario_id": "s-11", "tier": "T2", "a_passed": True, "b_passed": True, "a_status": "answered", "b_status": "answered"},
        # 1 infra_dead pair (fail-A & pass-B, a_infra_dead=True)
        {"scenario_id": "s-12", "tier": "T3", "a_passed": False, "b_passed": True, "a_status": "model_failure", "b_status": "answered", "a_infra_dead": True, "b_infra_dead": False},
    ]

    res = attribute(pairs)

    # 1. As-run checks (all 12 pairs included)
    as_run = res["as_run"]
    assert as_run["counts"]["retriever_owned"] == 7
    assert as_run["counts"]["generator_owned"] == 2
    assert as_run["counts"]["reverse"] == 1
    assert as_run["counts"]["both_pass"] == 2
    assert as_run["counts"]["n_failures_a"] == 9
    assert as_run["counts"]["total_pairs"] == 12

    expected_share_as_run = 7 / 9
    assert abs(as_run["retriever_share"] - expected_share_as_run) < 1e-9

    expected_ci_as_run = wilson_interval(7, 9)
    assert abs(as_run["wilson_ci"][0] - expected_ci_as_run[0]) < 1e-9
    assert abs(as_run["wilson_ci"][1] - expected_ci_as_run[1]) < 1e-9
    assert as_run["h8_verdict"] == "UNDECIDED"

    # 2. Infra-excluded checks (pair s-12 dropped, 11 pairs remain)
    infra_ex = res["infra_excluded"]
    assert infra_ex["counts"]["retriever_owned"] == 6
    assert infra_ex["counts"]["generator_owned"] == 2
    assert infra_ex["counts"]["reverse"] == 1
    assert infra_ex["counts"]["both_pass"] == 2
    assert infra_ex["counts"]["n_failures_a"] == 8
    assert infra_ex["counts"]["total_pairs"] == 11

    expected_share_infra = 6 / 8
    assert abs(infra_ex["retriever_share"] - expected_share_infra) < 1e-9

    expected_ci_infra = wilson_interval(6, 8)
    assert abs(infra_ex["wilson_ci"][0] - expected_ci_infra[0]) < 1e-9
    assert abs(infra_ex["wilson_ci"][1] - expected_ci_infra[1]) < 1e-9
    assert infra_ex["h8_verdict"] == "UNDECIDED"

    # Per-tier and per-a_status checks
    assert "T1" in as_run["per_tier"]
    assert "T2" in as_run["per_tier"]
    assert "T3" in as_run["per_tier"]
    assert "answered" in as_run["per_a_status"]
    assert "step_limit_exceeded" in as_run["per_a_status"]
    assert "malformed" in as_run["per_a_status"]


def test_run_stub_mixed(tmp_path: Path):
    """(c) run.py --stub --scenarios 6 --pool mixed writes sweep_output files whose steps contain

    tool_call and observation, writes results.json, and leaves ledger.jsonl empty.
    """
    cmd = [
        sys.executable,
        "projects/p12_attribution/run.py",
        "--stub",
        "--scenarios", "6",
        "--pool", "mixed",
        "--rung", "R2",
        "--output-dir", str(tmp_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert proc.returncode == 0

    sweep_a = tmp_path / "sweep_output_R2_A.json"
    sweep_b = tmp_path / "sweep_output_R2_B.json"
    assert sweep_a.exists()
    assert sweep_b.exists()

    for sweep_file in (sweep_a, sweep_b):
        data = json.loads(sweep_file.read_text(encoding="utf-8"))
        assert len(data) == 6
        for run_outcome in data:
            steps = run_outcome.get("steps") or run_outcome.get("trace")
            assert steps is not None
            assert len(steps) > 0
            for st in steps:
                assert "tool_call" in st
                assert "observation" in st

    manifest_file = tmp_path / "manifest_R2.json"
    assert manifest_file.exists()

    results_file = tmp_path / "results_R2.json"
    assert results_file.exists()
    results_data = json.loads(results_file.read_text(encoding="utf-8"))
    assert results_data["n"] == 6
    assert results_data["rung"] == "R2"
    assert "as_run" in results_data
    assert "infra_excluded" in results_data
    assert "h8_verdict" in results_data

    ledger_file = tmp_path / "ledger.jsonl"
    assert not ledger_file.exists() or ledger_file.read_text().strip() == ""


def test_run_dry_run_without_confirm(tmp_path: Path):
    """(d) run.py --dry-run without --confirm exits non-zero-or-cleanly with zero ledger rows and no trace.db spans."""
    cmd = [
        sys.executable,
        "projects/p12_attribution/run.py",
        "--dry-run",
        "--output-dir", str(tmp_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode in (0, 1)

    ledger_file = tmp_path / "ledger.jsonl"
    if ledger_file.exists():
        assert ledger_file.read_text().strip() == ""

    trace_db = tmp_path / "trace.db"
    if trace_db.exists():
        conn = sqlite3.connect(str(trace_db))
        count = conn.execute("SELECT count(*) FROM spans").fetchone()[0]
        conn.close()
        assert count == 0


def test_retrieval_mechanism_hand_built():
    """Test analyze_retrieval_mechanism on hand-built traces (one never_surfaced, one surfaced_but_unused)."""
    from faultline_p2.attribute.attribution import analyze_retrieval_mechanism

    pairs = [
        {"scenario_id": "sc-1", "a_passed": False, "b_passed": True, "a_status": "step_cap"},
        {"scenario_id": "sc-2", "a_passed": False, "b_passed": True, "a_status": "answered"},
    ]

    traces_a = {
        # sc-1: needed "doc-0001", search returned "doc-9999" (never_surfaced)
        "sc-1": {
            "trace": [
                {
                    "action_type": "tool",
                    "observation": {
                        "tool": "search",
                        "candidates": [{"doc_id": "doc-9999", "title": "Other", "score": 1.0, "snippet": ""}],
                    },
                }
            ]
        },
        # sc-2: needed "doc-0002", search returned "doc-0002" but run failed (surfaced_but_unused)
        "sc-2": {
            "trace": [
                {
                    "action_type": "tool",
                    "observation": {
                        "tool": "search",
                        "candidates": [{"doc_id": "doc-0002", "title": "Target", "score": 3.0, "snippet": ""}],
                    },
                },
                {
                    "action_type": "answer",
                    "observation": None,
                },
            ]
        },
    }

    traversal_sources = {
        "sc-1": ["doc-0001"],
        "sc-2": ["doc-0002"],
    }

    mech = analyze_retrieval_mechanism(pairs, traces_a, traversal_sources)

    assert mech["never_surfaced"] == 1
    assert mech["surfaced_but_unused"] == 1
    assert mech["missing_doc_histogram"] == {"0": 1, "1": 1}
    assert mech["status_split"]["retriever_owned"] == {"step_cap": 1, "answered": 1}
    assert mech["status_split"]["generator_owned"] == {}
