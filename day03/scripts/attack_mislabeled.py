"""Attack: mislabeled inputs must not silently corrupt the baseline.

Two probes:
  1. Tier mislabeling — file a batch of HARD tasks under the EASY label. If the
     pipeline trusted the declared label, EASY's success rate would crater
     (contaminated by tasks that are actually over budget). The runner instead
     recomputes each task's *actual* tier from its hop count and flags the
     mismatch, so the honest per-actual-tier number is recoverable.
  2. Malformed tasks — feed the agent junk. Each must come back as a structured
     INVALID outcome (never a crash), so a bad input is recorded, not fatal.

Writes evidence/mislabel_attack.json.
"""
import json
from pathlib import Path

import _bootstrap  # noqa: F401

from faultline_baseline import BaselineConfig, Sampler, Tier, run_one, run_tier
from faultline_baseline._bridge import Agent, load_env
from faultline_baseline.runner import aggregate_tier

EVIDENCE = Path(__file__).resolve().parents[1] / "evidence"


def _spec(config, tier):
    return next(s for s in config.tiers if s.tier is tier)


def main() -> None:
    config = BaselineConfig(n_per_tier=200)
    sampler = Sampler(config.master_seed)
    easy_spec, hard_spec = _spec(config, Tier.EASY), _spec(config, Tier.HARD)

    # --- probe 1: contaminate the EASY-declared bucket with HARD tasks -------
    genuine_easy = [run_one(sampler, easy_spec, i, config) for i in range(100)]
    hard_as_easy = [run_one(sampler, hard_spec, i, config, declared_tier=Tier.EASY)
                    for i in range(100)]
    contaminated = genuine_easy + hard_as_easy

    naive_bucket = [r for r in contaminated if r.declared_tier is Tier.EASY]
    naive_rate = sum(r.success for r in naive_bucket) / len(naive_bucket)

    flagged = [r for r in contaminated if r.mislabeled]
    honest_easy = [r for r in contaminated if r.actual_tier is Tier.EASY]
    honest_rate = sum(r.success for r in honest_easy) / len(honest_easy)

    clean_easy = run_tier(sampler, easy_spec, config)
    clean_rate = aggregate_tier(Tier.EASY, clean_easy, config.wilson_z).success_rate

    # --- probe 2: malformed tasks must degrade to structured INVALID ---------
    env = load_env(7)
    agent = Agent(env, step_cap=config.step_cap)
    malformed = [
        {"task_id": "m1", "entities": []},
        {"task_id": "m2", "entities": "not-a-list"},
        {"task_id": "m3"},
        {"task_id": "m4", "entities": [123, 456]},
        {"task_id": "m5", "entities": ["X"], "sneaky_field": True},
    ]
    malformed_results = []
    for m in malformed:
        out = agent.run(m)
        malformed_results.append({"input": m, "status": out.status.value})

    report = {
        "tier_mislabeling": {
            "declared_bucket": "easy",
            "n_in_bucket": len(naive_bucket),
            "n_mislabeled_detected": len(flagged),
            "naive_rate_if_labels_trusted": round(naive_rate, 6),
            "honest_rate_by_actual_tier": round(honest_rate, 6),
            "clean_baseline_easy_rate": clean_rate,
            "honest_matches_clean": abs(honest_rate - clean_rate) < 1e-9,
        },
        "malformed_inputs": {
            "n": len(malformed_results),
            "all_invalid": all(r["status"] == "invalid" for r in malformed_results),
            "results": malformed_results,
        },
    }
    (EVIDENCE / "mislabel_attack.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n")

    tm = report["tier_mislabeling"]
    print("PROBE 1 — tier mislabeling")
    print(f"  mislabeled detected : {tm['n_mislabeled_detected']}/{tm['n_in_bucket']}")
    print(f"  naive rate (trusted): {tm['naive_rate_if_labels_trusted']:.3f}  <- corrupted")
    print(f"  honest rate (actual): {tm['honest_rate_by_actual_tier']:.3f}")
    print(f"  clean baseline easy : {tm['clean_baseline_easy_rate']:.3f}")
    print(f"  honest == clean     : {tm['honest_matches_clean']}")
    print("\nPROBE 2 — malformed inputs")
    print(f"  all degrade to INVALID (no crash): {report['malformed_inputs']['all_invalid']}")
    print(f"\nwrote {(EVIDENCE / 'mislabel_attack.json').relative_to(EVIDENCE.parents[2])}")

    assert tm["n_mislabeled_detected"] == 100, "failed to detect all mislabeled tasks"
    assert tm["honest_matches_clean"], "honest regrouping did not recover clean rate"
    assert report["malformed_inputs"]["all_invalid"], "a malformed input was not INVALID"


if __name__ == "__main__":
    main()
