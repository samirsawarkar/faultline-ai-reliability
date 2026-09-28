"""Deterministic selection of 100-run CEO audit sample for P18.

Stratum A (random): 50 runs uniformly at random from the 400, proportional by split.
  Inclusion probability = 50 / 400 = 0.125.
Stratum B (enriched): 50 runs from the remaining 350, selected by priority:
  1. All T4 judge-positives (8 runs, p = 1.0)
  2. All T2 judge-positives and T2 disagreements (12 runs, p = 1.0)
  3. Half remaining (15) T3 judge-positives (15 / 22, p = 0.681818)
  4. Half remaining (15) T1 judge-positives or disagreements (15 / 54, p = 0.277778)

Both strata are merged and presented in one shuffled order (seed 42) so strata
are not visible during audit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))



def evaluate_rules_for_manifest(manifest: Dict[str, Any]) -> Dict[str, Dict[str, bool]]:
    """Evaluate T1 and T2 code rules on all runs in manifest."""
    from projects.p18_trace_triage.adapter import load_run_spans
    from projects.p18_trace_triage.rules import (
        eval_unrecovered_tool_error,
        eval_repeated_call_no_progress,
    )

    rule_evals: Dict[str, Dict[str, bool]] = {}
    for r in manifest["runs"]:
        sid = r["session_id"]
        spans = load_run_spans(r)
        r1, _, _ = eval_unrecovered_tool_error(spans)
        r2, _, _ = eval_repeated_call_no_progress(spans)
        rule_evals[sid] = {"T1": bool(r1), "T2": bool(r2)}
    return rule_evals


def load_judge_labels(labels_path: Path) -> Dict[str, Dict[str, Any]]:
    """Load judge evaluations from labels.jsonl."""
    labels: Dict[str, Dict[str, Any]] = {}
    with open(labels_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            sid = rec.get("session_id") or rec.get("run_id")
            if sid and "evaluation" in rec:
                labels[sid] = rec["evaluation"]
    return labels


def select_audit_sample(
    manifest: Dict[str, Any],
    labels: Dict[str, Dict[str, Any]],
    rule_evals: Dict[str, Dict[str, bool]],
    seed: int = 42,
) -> Dict[str, Any]:
    """Select the 100 audit runs across Stratum A and Stratum B.

    Returns the complete audit manifest dictionary.
    """
    rng = random.Random(seed)

    # Stratum A: 50 runs uniformly at random from 400, proportional by split
    # Proportions: train=236/400 (59%), test=104/400 (26%), dev=60/400 (15%)
    # Target allocations: train=30, test=13, dev=7 (sum = 50)
    split_targets = {"train": 30, "test": 13, "dev": 7}
    runs_by_split: Dict[str, List[Dict[str, Any]]] = {"train": [], "test": [], "dev": []}

    for r in sorted(manifest["runs"], key=lambda x: x["session_id"]):
        sp = r.get("split", "train")
        runs_by_split.setdefault(sp, []).append(r)

    stratum_a: List[Dict[str, Any]] = []
    stratum_a_sids = set()

    for sp in ["train", "test", "dev"]:
        target_cnt = split_targets.get(sp, 0)
        cands = sorted(runs_by_split[sp], key=lambda x: x["session_id"])
        sampled = rng.sample(cands, target_cnt)
        for r in sampled:
            item = dict(r)
            item["stratum"] = "A_random"
            item["group"] = "random"
            item["inclusion_probability"] = 50 / 400  # 0.125
            stratum_a.append(item)
            stratum_a_sids.add(item["session_id"])

    # Pool of remaining 350 runs for Stratum B
    remaining = [
        r for r in manifest["runs"]
        if r["session_id"] not in stratum_a_sids
    ]
    remaining = sorted(remaining, key=lambda x: x["session_id"])

    # Stratum B: 50 runs chosen by priority order
    # Priority 1: all T4 judge-positives
    g1_cands = [
        r for r in remaining
        if labels[r["session_id"]]["T4"]["label"]
    ]
    g1_sids = {r["session_id"] for r in g1_cands}
    g1_sampled = []
    for r in g1_cands:
        item = dict(r)
        item["stratum"] = "B_enriched"
        item["group"] = "T4_pos"
        item["inclusion_probability"] = 1.0
        g1_sampled.append(item)

    # Priority 2: all T2 judge-positives and T2 disagreements
    g2_cands = [
        r for r in remaining
        if r["session_id"] not in g1_sids and (
            labels[r["session_id"]]["T2"]["label"]
            or labels[r["session_id"]]["T2"]["label"] != rule_evals[r["session_id"]]["T2"]
        )
    ]
    g2_sids = {r["session_id"] for r in g2_cands}
    g2_sampled = []
    for r in g2_cands:
        item = dict(r)
        item["stratum"] = "B_enriched"
        item["group"] = "T2_pos_or_disagree"
        item["inclusion_probability"] = 1.0
        g2_sampled.append(item)

    slots_remaining = 50 - len(g1_sampled) - len(g2_sampled)
    half_slots = slots_remaining // 2

    # Priority 3: half T3 judge-positives
    g3_cands = [
        r for r in remaining
        if r["session_id"] not in g1_sids
        and r["session_id"] not in g2_sids
        and labels[r["session_id"]]["T3"]["label"]
    ]
    g3_sids = {r["session_id"] for r in g3_cands}
    g3_sampled = []
    g3_selected = rng.sample(g3_cands, half_slots)
    p3 = round(half_slots / len(g3_cands), 6)
    for r in g3_selected:
        item = dict(r)
        item["stratum"] = "B_enriched"
        item["group"] = "T3_pos"
        item["inclusion_probability"] = p3
        g3_sampled.append(item)

    # Priority 4: half T1 (judge-positive or disagreement)
    g4_cands = [
        r for r in remaining
        if r["session_id"] not in g1_sids
        and r["session_id"] not in g2_sids
        and r["session_id"] not in g3_sids
        and (
            labels[r["session_id"]]["T1"]["label"]
            or labels[r["session_id"]]["T1"]["label"] != rule_evals[r["session_id"]]["T1"]
        )
    ]
    g4_sampled = []
    g4_selected = rng.sample(g4_cands, half_slots)
    p4 = round(half_slots / len(g4_cands), 6)
    for r in g4_selected:
        item = dict(r)
        item["stratum"] = "B_enriched"
        item["group"] = "T1_pos_or_disagree"
        item["inclusion_probability"] = p4
        g4_sampled.append(item)

    stratum_b = g1_sampled + g2_sampled + g3_sampled + g4_sampled
    all_audit_runs = stratum_a + stratum_b
    assert len(all_audit_runs) == 100, f"Expected 100 runs, got {len(all_audit_runs)}"
    assert len({r["session_id"] for r in all_audit_runs}) == 100, "Duplicate session_ids in audit sample"

    # Present 100 runs in one shuffled order (seed 42) so strata are not visible
    shuffle_rng = random.Random(seed)
    shuffled_runs = list(all_audit_runs)
    shuffle_rng.shuffle(shuffled_runs)

    # Record position index 1-indexed
    for idx, r in enumerate(shuffled_runs, start=1):
        r["audit_position"] = idx

    group_counts = {
        "A_random": len(stratum_a),
        "B_T4_pos": len(g1_sampled),
        "B_T2_pos_or_disagree": len(g2_sampled),
        "B_T3_pos": len(g3_sampled),
        "B_T1_pos_or_disagree": len(g4_sampled),
    }

    manifest_content = {
        "spec_version": "1.0.0",
        "seed": seed,
        "total_audit_runs": len(shuffled_runs),
        "strata_counts": {
            "A_random": len(stratum_a),
            "B_enriched": len(stratum_b),
        },
        "group_counts": group_counts,
        "runs": shuffled_runs,
    }

    # Compute deterministic SHA256 of canonical JSON
    canonical_bytes = json.dumps(manifest_content, indent=2, sort_keys=True).encode("utf-8")
    content_sha256 = hashlib.sha256(canonical_bytes).hexdigest()
    manifest_content["manifest_sha256"] = content_sha256

    return manifest_content


def main():
    parser = argparse.ArgumentParser(description="Select P18 CEO Audit Sample")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("projects/p18_trace_triage/manifest.json"),
    )
    parser.add_argument(
        "--labels",
        type=Path,
        default=Path("projects/p18_trace_triage/labels.jsonl"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("projects/p18_trace_triage/audit_manifest.json"),
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    with open(args.manifest, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    labels = load_judge_labels(args.labels)
    rule_evals = evaluate_rules_for_manifest(manifest)

    audit_manifest = select_audit_sample(
        manifest=manifest,
        labels=labels,
        rule_evals=rule_evals,
        seed=args.seed,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(audit_manifest, f, indent=2, sort_keys=True)

    print(f"Generated {args.output}")
    print(f"Total audit runs: {audit_manifest['total_audit_runs']}")
    print(f"Strata: {audit_manifest['strata_counts']}")
    print(f"Group counts: {audit_manifest['group_counts']}")
    print(f"SHA-256: {audit_manifest['manifest_sha256']}")


if __name__ == "__main__":
    main()
