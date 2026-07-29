"""Regenerate deterministic Day-24 policy, paired, attack, and Q5 evidence."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in ("", "../day14", "../day23"):
    sys.path.insert(0, str((ROOT / rel).resolve()))

from faultline_q5 import build_report, render_q5  # noqa: E402

EVIDENCE = ROOT / "evidence"


def _dump(path: Path, obj) -> None:
    path.write_text(
        json.dumps(obj, sort_keys=True, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    EVIDENCE.mkdir(exist_ok=True)
    report = build_report()
    experiment = report["experiment"]
    _dump(
        EVIDENCE / "policy_comparison.json",
        {
            "config": experiment["config"],
            "population": experiment["population"],
            "policy_definitions": experiment["policy_definitions"],
            "policy_metrics": experiment["policy_metrics"],
            "selection": experiment["selection"],
            "fail_condition_guard": report["fail_condition_guard"],
        },
    )
    _dump(
        EVIDENCE / "paired_statistics.json",
        {
            "paired_vs_no_recovery": experiment["paired_vs_no_recovery"],
            "paired_dominance_vs_other_eligible": experiment["selection"][
                "paired_dominance_vs_other_eligible"
            ],
        },
    )
    _dump(EVIDENCE / "winner_attack.json", report["winner_attack"])
    _dump(EVIDENCE / "q5_recommendation.json", report["q5_recommendation"])
    (EVIDENCE / "Q5_RECOMMENDATION.md").write_text(
        render_q5(report), encoding="utf-8"
    )

    winner = report["q5_recommendation"]["winner"]
    metrics = experiment["policy_metrics"][winner]
    print("Day 24 evidence written:")
    print(
        f"  winner: {winner}; success={metrics['user_visible_correct_success']['rate']}"
    )
    print(
        f"  efficiency: {metrics['success_per_cost']['value']} success/cost; "
        f"{metrics['success_per_100_latency']['value']} success/100 latency"
    )
    print(
        f"  cost={metrics['mean_cost']['value']}; "
        f"p95 latency={metrics['p95_latency']['value']}"
    )
    print(f"  gate={report['fail_condition_guard']['passed']}")


if __name__ == "__main__":
    main()
