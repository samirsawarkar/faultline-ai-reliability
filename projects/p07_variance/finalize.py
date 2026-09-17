"""Finalize Project P07 Variance Results.

Reads trace.db and ledger.jsonl, computes statistical metrics, and writes results.json.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import statistics
import sys

from faultline_p2.stats.intervals import wilson_interval
from faultline_p2.stats.paired import mcnemar


def main() -> None:
    base_dir = Path("projects/p07_variance")
    db_path = base_dir / "trace.db"
    ledger_path = base_dir / "ledger.jsonl"
    manifest_path = base_dir / "manifest.json"
    results_path = base_dir / "results.json"

    # 1. Query per-run rows
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    query = """
        SELECT provider, model_version, run_id, scenario_id, MAX(verdict) AS v, MAX(latency_ms) AS lat
        FROM spans WHERE timestamp > '2026-09-14T06' AND provider IN ('aicredits','agy_cli')
        GROUP BY provider, model_version, run_id, scenario_id
    """
    rows = cur.execute(query).fetchall()
    conn.close()

    # Map provider 'aicredits' -> endpoint 'aicredits', 'agy_cli' -> 'agy'
    provider_map = {
        "aicredits": "aicredits",
        "agy_cli": "agy",
    }

    runs_by_endpoint: dict[str, list[dict]] = {
        "aicredits": [],
        "agy": [],
    }

    run_ids_all: set[str] = set()
    run_ids_by_endpoint: dict[str, set[str]] = {
        "aicredits": set(),
        "agy": set(),
    }

    for row in rows:
        provider, model_version, run_id, scenario_id, v, lat = row
        ep = provider_map.get(provider)
        if not ep:
            continue
        passed = (v == "PASS" or v == 1 or v == "1" or v is True)
        runs_by_endpoint[ep].append({
            "run_id": run_id,
            "scenario_id": scenario_id,
            "model_version": model_version,
            "passed": passed,
            "latency_s": float(lat) / 1000.0,
        })
        run_ids_all.add(run_id)
        run_ids_by_endpoint[ep].add(run_id)

    n_aicredits = len(runs_by_endpoint["aicredits"])
    passed_aicredits = sum(1 for r in runs_by_endpoint["aicredits"] if r["passed"])

    n_agy = len(runs_by_endpoint["agy"])
    passed_agy = sum(1 for r in runs_by_endpoint["agy"] if r["passed"])

    # Contingency on shared scenario_id
    aicredits_scenarios = {r["scenario_id"]: r["passed"] for r in runs_by_endpoint["aicredits"]}
    agy_scenarios = {r["scenario_id"]: r["passed"] for r in runs_by_endpoint["agy"]}
    all_scenarios = sorted(set(aicredits_scenarios.keys()) | set(agy_scenarios.keys()))

    both = 0
    aicredits_only = 0
    agy_only = 0
    neither = 0

    for sid in all_scenarios:
        ai_p = aicredits_scenarios.get(sid, False)
        agy_p = agy_scenarios.get(sid, False)
        if ai_p and agy_p:
            both += 1
        elif ai_p and not agy_p:
            aicredits_only += 1
        elif not ai_p and agy_p:
            agy_only += 1
        else:
            neither += 1

    # Verification:
    # Expected: aicredits n=150 passed=144; agy n=150 passed=134; contingency on shared scenario_id: both=130, aicredits_only=14, agy_only=4, neither=2.
    # If your numbers differ, print them and exit 1.
    if (
        n_aicredits != 150
        or passed_aicredits != 144
        or n_agy != 150
        or passed_agy != 134
        or both != 130
        or aicredits_only != 14
        or agy_only != 4
        or neither != 2
    ):
        print("ERROR: Observed numbers differ from expected!")
        print(f"aicredits: n={n_aicredits}, passed={passed_aicredits}")
        print(f"agy: n={n_agy}, passed={passed_agy}")
        print(f"contingency: both={both}, aicredits_only={aicredits_only}, agy_only={agy_only}, neither={neither}")
        sys.exit(1)

    # 2. Read manifest.json for manifest_sha256
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_sha256 = manifest_data.get("manifest_sha256")

    # 3. Read ledger.jsonl for spend
    total_spend_usd = 0.0
    spend_by_endpoint = {"aicredits": 0.0, "agy": 0.0}

    with open(ledger_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            entry = json.loads(line)
            rid = entry.get("run_id")
            if rid in run_ids_all:
                usd = float(entry.get("usd", 0.0))
                total_spend_usd += usd
                if rid in run_ids_by_endpoint["aicredits"]:
                    spend_by_endpoint["aicredits"] += usd
                if rid in run_ids_by_endpoint["agy"]:
                    spend_by_endpoint["agy"] += usd

    # 4. Latency percentiles
    ai_latencies = sorted(r["latency_s"] for r in runs_by_endpoint["aicredits"])
    agy_latencies = sorted(r["latency_s"] for r in runs_by_endpoint["agy"])

    p50_aicredits = round(statistics.median(ai_latencies), 4)
    p95_aicredits = round(statistics.quantiles(ai_latencies, n=100)[94], 4)

    p50_agy = round(statistics.median(agy_latencies), 4)
    p95_agy = round(statistics.quantiles(agy_latencies, n=100)[94], 4)

    ratio_p50 = round(p50_agy / p50_aicredits, 4)
    ratio_p95 = round(p95_agy / p95_aicredits, 4)

    # 5. McNemar test
    mcnemar_res = mcnemar(aicredits_only, agy_only)
    exact_p = mcnemar_res.get("exact_p_value")

    # 6. Build endpoints dict
    endpoints = {
        "aicredits": {
            "model_name": runs_by_endpoint["aicredits"][0]["model_version"],
            "n": n_aicredits,
            "passed": passed_aicredits,
            "pass_rate": round(passed_aicredits / n_aicredits, 4),
            "wilson_ci": [round(x, 4) for x in wilson_interval(passed_aicredits, n_aicredits)],
            "latency_p50_s": p50_aicredits,
            "latency_p95_s": p95_aicredits,
            "spend_usd": round(spend_by_endpoint["aicredits"], 6),
        },
        "agy": {
            "model_name": runs_by_endpoint["agy"][0]["model_version"],
            "n": n_agy,
            "passed": passed_agy,
            "pass_rate": round(passed_agy / n_agy, 4),
            "wilson_ci": [round(x, 4) for x in wilson_interval(passed_agy, n_agy)],
            "latency_p50_s": p50_agy,
            "latency_p95_s": p95_agy,
            "spend_usd": round(spend_by_endpoint["agy"], 6),
        },
    }

    # 7. Construct results dictionary
    timestamp_utc = datetime.now(timezone.utc).isoformat()

    results = {
        "timestamp_utc": timestamp_utc,
        "manifest_sha256": manifest_sha256,
        "total_spend_usd": round(total_spend_usd, 6),
        "endpoints": endpoints,
        "contingency": {
            "both_pass": both,
            "aicredits_only": aicredits_only,
            "agy_only": agy_only,
            "neither": neither,
        },
        "mcnemar": mcnemar_res,
        "h6": {
            "criterion_disjoint_ci": "NOT MET: Wilson intervals overlap on [0.9155, 0.9333]",
            "paired_mcnemar": f"SIGNIFICANT: exact p={exact_p}, 14 aicredits-only vs 4 agy-only discordant pairs, favouring aicredits",
            "power_note": "Observed gap 6.67pp is below the MEC 10pp declared power. Reported as a detected difference with that caveat; never as no difference.",
        },
        "latency": {
            "aicredits": {
                "p50_s": p50_aicredits,
                "p95_s": p95_aicredits,
            },
            "agy": {
                "p50_s": p50_agy,
                "p95_s": p95_agy,
            },
            "ratio_agy_over_aicredits": {
                "p50": ratio_p50,
                "p95": ratio_p95,
            },
        },
    }

    results_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Successfully finalized results into {results_path}")


if __name__ == "__main__":
    main()
