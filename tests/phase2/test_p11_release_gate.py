"""Unit and integration tests for P11 Release Gate."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from faultline_p2.env.corpus import build_corpus
from faultline_p2.gate.band import from_runs
from faultline_p2.gate.gate import evaluate
from faultline_p2.gate.golden import select

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_golden_selection_deterministic() -> None:
    corpus = build_corpus()
    ids1, sha1 = select(corpus.scenarios, n=30, pool="reserved")
    ids2, sha2 = select(corpus.scenarios, n=30, pool="reserved")

    assert ids1 == ids2
    assert len(ids1) == 30
    assert sha1 == sha2
    assert sha1 == "e79897ea42129ccd4fe38ce3e0a8f7ec0b321aa8be0f7a3899036f5148dcb06f"

    golden_file = REPO_ROOT / "projects" / "p11_release_gate" / "golden.json"
    assert golden_file.exists()
    golden_data = json.loads(golden_file.read_text(encoding="utf-8"))
    assert golden_data["golden_ids"] == ids1
    assert golden_data["manifest_sha256"] == sha1


def test_band_rule_thresholds() -> None:
    golden_ids = [f"s-{i:02d}" for i in range(1, 11)]  # n = 10

    # src1: 7 passed, 0 malformed (pass=0.7, malformed=0.0)
    # src2: 6 passed, 1 malformed (pass=0.6, malformed=0.1)
    runs_by_source = {
        "src1": {sid: {"grounded": i <= 7, "status": "answered"} for i, sid in enumerate(golden_ids, 1)},
        "src2": {sid: {"grounded": i <= 6, "status": "malformed" if i == 10 else "answered"} for i, sid in enumerate(golden_ids, 1)},
    }
    band = from_runs(runs_by_source, golden_ids)

    # min_pass = 0.60, max_malformed = 0.10, slack = 0.10, fail_slack = 0.30
    # pass_threshold = 0.50, fail_threshold = 0.30, malformed_threshold = 0.20
    assert band["pass_rate"]["min"] == 0.60
    assert band["malformed_rate"]["max"] == 0.10

    # 1. Candidate pass rate 0.50, malformed 0.10 -> PASS
    c1 = {sid: {"grounded": i <= 5, "status": "malformed" if i == 10 else "answered"} for i, sid in enumerate(golden_ids, 1)}
    r1 = evaluate(c1, band)
    assert r1["verdict"] == "PASS"

    # 2. Candidate pass rate 0.40, malformed 0.00 -> WARN (below pass_threshold 0.50, above fail 0.30)
    c2 = {sid: {"grounded": i <= 4, "status": "answered"} for i, sid in enumerate(golden_ids, 1)}
    r2 = evaluate(c2, band)
    assert r2["verdict"] == "WARN"

    # 3. Candidate pass rate 0.80, malformed 0.30 -> WARN (malformed > 0.20 threshold)
    c3 = {sid: {"grounded": i <= 8, "status": "malformed" if i in [8, 9, 10] else "answered"} for i, sid in enumerate(golden_ids, 1)}
    r3 = evaluate(c3, band)
    assert r3["verdict"] == "WARN"

    # 4. Candidate pass rate 0.20 -> FAIL (below fail_threshold 0.30)
    c4 = {sid: {"grounded": i <= 2, "status": "answered"} for i, sid in enumerate(golden_ids, 1)}
    r4 = evaluate(c4, band)
    assert r4["verdict"] == "FAIL"


def test_gate_regressions_list() -> None:
    golden_ids = ["s-01", "s-02", "s-03"]
    runs_by_source = {
        "src1": {
            "s-01": {"grounded": True, "status": "answered"},
            "s-02": {"grounded": True, "status": "answered"},
            "s-03": {"grounded": True, "status": "answered"},
        },
        "src2": {
            "s-01": {"grounded": True, "status": "answered"},
            "s-02": {"grounded": True, "status": "answered"},
            "s-03": {"grounded": False, "status": "answered"},
        },
    }
    band = from_runs(runs_by_source, golden_ids)

    candidate = {
        "s-01": {"grounded": False, "status": "answered"},  # Regression: every baseline passed s-01
        "s-02": {"grounded": True, "status": "answered"},
        "s-03": {"grounded": False, "status": "answered"},  # Not a regression: src2 failed s-03
    }
    res = evaluate(candidate, band)
    assert res["regressions"] == ["s-01"]
    assert res["per_scenario_diff"] == ["s-01"]


def test_run_py_stubs(tmp_path: Path) -> None:
    run_py = REPO_ROOT / "projects" / "p11_release_gate" / "run.py"
    golden_json = REPO_ROOT / "projects" / "p11_release_gate" / "golden.json"
    band_stub_json = REPO_ROOT / "projects" / "p11_release_gate" / "band_stub.json"

    # 1. Stub solver: expect PASS, exit 0
    cmd_pass = [
        sys.executable,
        str(run_py),
        "--model", "stub:solver",
        "--band", str(band_stub_json),
        "--golden", str(golden_json),
        "--output-dir", str(tmp_path / "out_pass"),
    ]
    p_pass = subprocess.run(cmd_pass, capture_output=True, text=True)
    assert p_pass.returncode == 0, f"Expected 0, stderr: {p_pass.stderr}"

    report_pass = json.loads((tmp_path / "out_pass" / "report.json").read_text(encoding="utf-8"))
    assert report_pass["verdict"] == "PASS"
    assert report_pass["metrics"]["pass_count"] == 30

    # 2. Stub wrong_answer: expect FAIL, exit 2
    cmd_fail = [
        sys.executable,
        str(run_py),
        "--model", "stub:wrong_answer",
        "--band", str(band_stub_json),
        "--golden", str(golden_json),
        "--output-dir", str(tmp_path / "out_fail"),
    ]
    p_fail = subprocess.run(cmd_fail, capture_output=True, text=True)
    assert p_fail.returncode == 2, f"Expected 2, stderr: {p_fail.stderr}"

    report_fail = json.loads((tmp_path / "out_fail" / "report.json").read_text(encoding="utf-8"))
    assert report_fail["verdict"] == "FAIL"
    assert report_fail["metrics"]["pass_count"] == 0


def test_dry_run_makes_no_ledger_row(tmp_path: Path) -> None:
    run_py = REPO_ROOT / "projects" / "p11_release_gate" / "run.py"
    golden_json = REPO_ROOT / "projects" / "p11_release_gate" / "golden.json"
    band_json = REPO_ROOT / "projects" / "p11_release_gate" / "band.json"

    cmd_dry = [
        sys.executable,
        str(run_py),
        "--model", "R2",
        "--band", str(band_json),
        "--golden", str(golden_json),
        "--dry-run",
        "--output-dir", str(tmp_path),
    ]
    p_dry = subprocess.run(cmd_dry, capture_output=True, text=True)
    assert p_dry.returncode == 0, f"Expected 0, stderr: {p_dry.stderr}"
    assert not (tmp_path / "ledger.jsonl").exists()


def test_band_v1_and_v2_properties() -> None:
    band_v1_file = REPO_ROOT / "projects" / "p11_release_gate" / "band_v1.json"
    band_v2_file = REPO_ROOT / "projects" / "p11_release_gate" / "band.json"

    assert band_v1_file.exists()
    assert band_v2_file.exists()

    b1 = json.loads(band_v1_file.read_text(encoding="utf-8"))
    b2 = json.loads(band_v2_file.read_text(encoding="utf-8"))

    assert b1["pass_rate"]["sources"] == 4
    assert b1["pass_rate"]["min"] == 0.60
    assert b1["pass_rate"]["max"] == 0.80

    assert b2["pass_rate"]["sources"] == 5
    assert b2["pass_rate"]["min"] == 0.60
    assert abs(b2["pass_rate"]["max"] - 0.8667) < 1e-3

    # Thresholds are identical because min pass rate is unchanged
    assert b1["tolerance_rule"]["min_pass_threshold"] == b2["tolerance_rule"]["min_pass_threshold"]
    assert b1["tolerance_rule"]["fail_pass_threshold"] == b2["tolerance_rule"]["fail_pass_threshold"]
    assert b1["tolerance_rule"]["max_malformed_threshold"] == b2["tolerance_rule"]["max_malformed_threshold"]


def test_concurrency_flag(tmp_path: Path) -> None:
    run_py = REPO_ROOT / "projects" / "p11_release_gate" / "run.py"
    golden_json = REPO_ROOT / "projects" / "p11_release_gate" / "golden.json"
    band_stub_json = REPO_ROOT / "projects" / "p11_release_gate" / "band_stub.json"

    # Verify stub run works with --concurrency 4 (should enforce sequential 1 worker for stub)
    cmd = [
        sys.executable,
        str(run_py),
        "--model", "stub:solver",
        "--band", str(band_stub_json),
        "--golden", str(golden_json),
        "--concurrency", "4",
        "--output-dir", str(tmp_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Expected 0, stderr: {res.stderr}"
    assert "concurrency: 1" in res.stdout  # stubs stay sequential
    assert (tmp_path / "report.json").exists()
