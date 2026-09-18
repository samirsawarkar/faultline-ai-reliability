"""Build golden scenario set and tolerance bands for P11 Release Gate.

Extracts baseline runs from:
1-3: P6 trials k1, k2, k3 (from projects/p06_passk/trace.db, run_id 'p06_r2_7e0a1b79')
4:   P12 Arm A (from projects/p12_attribution/sweep_output_R2_A.json)

Writes:
- projects/p11_release_gate/golden.json
- projects/p11_release_gate/band.json
- projects/p11_release_gate/band_stub.json
"""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any, Dict

from faultline_p2.agent.agent import run_agent
from faultline_p2.agent.contracts import ScenarioTask
from faultline_p2.agent.model import StubModel
from faultline_p2.env.corpus import build_corpus
from faultline_p2.gate.band import from_runs
from faultline_p2.gate.golden import select
from faultline_p2.oracle._day01_oracle import oracle_check

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = Path(__file__).resolve().parent


def extract_p6_trials(trace_db_path: Path, run_id: str = "p06_r2_7e0a1b79") -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Extract k1, k2, k3 trial runs from P6 SQLite trace store."""
    if not trace_db_path.exists():
        raise FileNotFoundError(f"Trace database not found: {trace_db_path}")

    conn = sqlite3.connect(str(trace_db_path))
    cur = conn.cursor()
    cur.execute(
        """
        SELECT scenario_id, MAX(rowid) as max_rowid, MAX(verdict) as max_verdict
        FROM spans
        WHERE run_id = ?
        GROUP BY scenario_id
        """,
        (run_id,),
    )
    rows = cur.fetchall()

    k_trials: Dict[str, Dict[str, Dict[str, Any]]] = {
        "p06_k1": {},
        "p06_k2": {},
        "p06_k3": {},
    }

    for full_sid, max_rowid, max_v in rows:
        cur.execute("SELECT tool_name, termination_reason FROM spans WHERE rowid = ?", (max_rowid,))
        tool_name, term_reason = cur.fetchone()
        status = "answered" if tool_name == "answer" else (term_reason or "unknown")
        grounded = max_v == 1

        run_info = {"grounded": grounded, "status": status}
        if full_sid.endswith("_k1"):
            base_sid = full_sid[:-3]
            k_trials["p06_k1"][base_sid] = run_info
        elif full_sid.endswith("_k2"):
            base_sid = full_sid[:-3]
            k_trials["p06_k2"][base_sid] = run_info
        elif full_sid.endswith("_k3"):
            base_sid = full_sid[:-3]
            k_trials["p06_k3"][base_sid] = run_info

    conn.close()
    return k_trials


def extract_p12_arm_a(sweep_json_path: Path) -> Dict[str, Dict[str, Any]]:
    """Extract P12 Arm A runs from sweep output JSON."""
    if not sweep_json_path.exists():
        raise FileNotFoundError(f"P12 sweep output not found: {sweep_json_path}")

    with open(sweep_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    p12_runs: Dict[str, Dict[str, Any]] = {}
    for item in data:
        sid = item.get("scenario_id") or item.get("task_id")
        if sid:
            p12_runs[sid] = {
                "grounded": bool(item.get("grounded", False)),
                "status": item.get("status", "unknown"),
            }
    return p12_runs


def extract_sweep_output(sweep_json_path: Path) -> Dict[str, Dict[str, Any]]:
    """Extract scenario runs from a sweep output JSON file."""
    if not sweep_json_path.exists():
        return {}
    with open(sweep_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    runs: Dict[str, Dict[str, Any]] = {}
    for item in data:
        sid = item.get("scenario_id") or item.get("task_id")
        if sid:
            runs[sid] = {
                "grounded": bool(item.get("grounded", False)),
                "status": item.get("status", "unknown"),
            }
    return runs


def generate_stub_solver_runs(corpus: Any, golden_ids: list[str]) -> Dict[str, Dict[str, Any]]:
    """Generate deterministic stub runs on golden scenarios for CI $0 drills."""
    scenario_map = {s.scenario_id: s for s in corpus.scenarios}
    golden_scenarios = [scenario_map[sid] for sid in golden_ids if sid in scenario_map]
    env = {"documents": corpus.documents}

    stub = StubModel(behavior="solver", scenarios=golden_scenarios)
    stub_runs: Dict[str, Dict[str, Any]] = {}

    for s in golden_scenarios:
        task = ScenarioTask(task_id=s.scenario_id, prompt=s.prompt, tier=s.tier)
        outcome = run_agent(task=task, env=env, model=stub, step_cap=24)
        q_dict = {
            "id": s.scenario_id,
            "answer": s.final_answer,
            "required_source": s.required_source,
        }
        r_dict = {
            "answer": outcome.answer or "",
            "cited_sources": outcome.cited_sources,
        }
        verdict = oracle_check(q_dict, r_dict)
        passed = bool(verdict.get("passed", False))
        stub_runs[s.scenario_id] = {
            "grounded": passed,
            "status": outcome.status.value,
        }

    return stub_runs


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    corpus = build_corpus()

    # 1. Select golden scenarios (n=30, pool='reserved')
    golden_ids, manifest_sha256 = select(corpus.scenarios, n=30, pool="reserved")
    golden_data = {
        "golden_ids": golden_ids,
        "ids": golden_ids,
        "manifest_sha256": manifest_sha256,
        "n": len(golden_ids),
        "pool": "reserved",
    }
    golden_path = OUTPUT_DIR / "golden.json"
    with open(golden_path, "w", encoding="utf-8") as f:
        json.dump(golden_data, f, indent=2)
    print(f"Golden set written to {golden_path} (n={len(golden_ids)}, sha256={manifest_sha256})")

    # 2. Extract baseline runs
    trace_db_path = REPO_ROOT / "projects" / "p06_passk" / "trace.db"
    p6_trials = extract_p6_trials(trace_db_path)

    p12_json_path = REPO_ROOT / "projects" / "p12_attribution" / "sweep_output_R2_A.json"
    p12_arm_a = extract_p12_arm_a(p12_json_path)

    sources_v1: Dict[str, Dict[str, Dict[str, Any]]] = {
        "p06_k1": p6_trials["p06_k1"],
        "p06_k2": p6_trials["p06_k2"],
        "p06_k3": p6_trials["p06_k3"],
        "p12_a": p12_arm_a,
    }

    # 3. Compute 4-source baseline band (v1)
    band_v1 = from_runs(sources_v1, golden_ids)
    band_v1["manifest_sha256"] = manifest_sha256
    band_v1_path = OUTPUT_DIR / "band_v1.json"
    with open(band_v1_path, "w", encoding="utf-8") as f:
        json.dump(band_v1, f, indent=2)
    print(f"Band v1 (4 sources) written to {band_v1_path}")

    # Check for fifth source: projects/p11_release_gate/sweep_output_R2.json ('p11_r2_fresh')
    r2_fresh_path = OUTPUT_DIR / "sweep_output_R2.json"
    sources_v2 = dict(sources_v1)
    if r2_fresh_path.exists():
        r2_fresh_runs = extract_sweep_output(r2_fresh_path)
        if len(r2_fresh_runs) >= len(golden_ids):
            sources_v2["p11_r2_fresh"] = r2_fresh_runs

    # Compute Band v2 (5 sources if sweep_output_R2.json is available)
    band_v2 = from_runs(sources_v2, golden_ids)
    band_v2["manifest_sha256"] = manifest_sha256

    print(f"\nBaseline pass rates on golden 30 ({len(sources_v2)} sources):")
    for src_name, src_metrics in band_v2["sources"].items():
        pass_cnt = src_metrics["pass_count"]
        p_rate = src_metrics["pass_rate"]
        m_cnt = src_metrics["malformed_count"]
        m_rate = src_metrics["malformed_rate"]
        print(f"  {src_name}: passed {pass_cnt}/30 = {p_rate:.4f}, malformed {m_cnt}/30 = {m_rate:.4f}")

    print("\nTolerance Band:")
    print(f"  pass_rate: min={band_v2['pass_rate']['min']:.4f}, max={band_v2['pass_rate']['max']:.4f}, mean={band_v2['pass_rate']['mean']:.4f} (sources: {band_v2['pass_rate']['sources']})")
    print(f"  malformed_rate: max={band_v2['malformed_rate']['max']:.4f}")
    rule = band_v2["tolerance_rule"]
    print(f"  tolerance_rule: pass_threshold={rule['min_pass_threshold']:.4f}, fail_threshold={rule['fail_pass_threshold']:.4f}, malformed_threshold={rule['max_malformed_threshold']:.4f}")

    band_path = OUTPUT_DIR / "band.json"
    with open(band_path, "w", encoding="utf-8") as f:
        json.dump(band_v2, f, indent=2)
    print(f"Live band written to {band_path}")

    # Ensure report files note band_file: band_v1.json
    for r in ["R1", "R4", "R2"]:
        rep_p = OUTPUT_DIR / f"report_{r}.json"
        if rep_p.exists():
            with open(rep_p, "r", encoding="utf-8") as f:
                r_data = json.load(f)
            if r_data.get("band_file") != "band_v1.json":
                r_data["band_file"] = "band_v1.json"
                with open(rep_p, "w", encoding="utf-8") as f:
                    json.dump(r_data, f, indent=2)

    # 4. Generate stub solver runs and build band_stub.json
    print("\nGenerating stub solver baseline for CI drills...")
    stub_runs = generate_stub_solver_runs(corpus, golden_ids)
    band_stub = from_runs({"stub_solver": stub_runs}, golden_ids)
    band_stub["manifest_sha256"] = manifest_sha256

    band_stub_path = OUTPUT_DIR / "band_stub.json"
    with open(band_stub_path, "w", encoding="utf-8") as f:
        json.dump(band_stub, f, indent=2)
    print(f"Stub band written to {band_stub_path}")


if __name__ == "__main__":
    main()
