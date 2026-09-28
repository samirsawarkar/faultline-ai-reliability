"""Tests for P18 CEO Audit selection, page generator, and evaluation scoring."""
import html
import json
import re
from pathlib import Path
import pytest


from projects.p18_trace_triage.select_audit import (
    select_audit_sample,
    evaluate_rules_for_manifest,
    load_judge_labels,
)
from projects.p18_trace_triage.build_audit_page import (
    generate_audit_html_content,
    T1_DEF,
    T2_DEF,
    T3_DEF,
    T4_DEF,
)
from projects.p18_trace_triage.score_audit import (
    score_audit,
    compute_binary_metrics,
)


def test_audit_manifest_deterministic_and_unique():
    """Requirement: selection is deterministic and has exactly 100 unique runs, 50 per stratum."""
    manifest_path = Path("projects/p18_trace_triage/manifest.json")
    labels_path = Path("projects/p18_trace_triage/labels.jsonl")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    labels = load_judge_labels(labels_path)
    rule_evals = evaluate_rules_for_manifest(manifest)

    # Run selection twice to verify determinism
    res1 = select_audit_sample(manifest, labels, rule_evals, seed=42)
    res2 = select_audit_sample(manifest, labels, rule_evals, seed=42)

    assert json.dumps(res1, sort_keys=True) == json.dumps(res2, sort_keys=True), "Selection is not deterministic"

    runs = res1["runs"]
    assert len(runs) == 100, f"Expected 100 runs, got {len(runs)}"

    sids = [r["session_id"] for r in runs]
    assert len(set(sids)) == 100, "Duplicate session_ids detected in audit sample"

    # Strata counts
    strata = [r["stratum"] for r in runs]
    assert strata.count("A_random") == 50, f"Expected 50 in Stratum A, got {strata.count('A_random')}"
    assert strata.count("B_enriched") == 50, f"Expected 50 in Stratum B, got {strata.count('B_enriched')}"

    # Verify Stratum A inclusion probability
    for r in runs:
        if r["stratum"] == "A_random":
            assert r["inclusion_probability"] == 50 / 400
            assert r["group"] == "random"

    # Verify Stratum B groups
    groups = [r["group"] for r in runs if r["stratum"] == "B_enriched"]
    assert groups.count("T4_pos") == 8
    assert groups.count("T2_pos_or_disagree") == 12
    assert groups.count("T3_pos") == 15
    assert groups.count("T1_pos_or_disagree") == 15

    # Check sha256 present
    assert "manifest_sha256" in res1
    assert len(res1["manifest_sha256"]) == 64


def test_audit_html_no_leakage_and_no_external_urls():
    """Requirement: generated HTML contains no judge label/reasoning strings, no 'Success:'/'Status:', and no http(s):// URLs."""
    fixture_manifest = {
        "runs": [
            {
                "session_id": "test_sid_001",
                "benchmark": "swebench",
                "split": "train",
                "stratum": "A_random",
                "group": "random",
                "inclusion_probability": 0.125,
            },
            {
                "session_id": "test_sid_002",
                "benchmark": "tau2_airline",
                "split": "test",
                "stratum": "B_enriched",
                "group": "T4_pos",
                "inclusion_probability": 1.0,
            },
        ]
    }

    # Custom mock spans loader returning clean traces without URLs or outcome strings
    def mock_spans_loader(run_meta):
        sid = run_meta["session_id"]
        return [
            {
                "attributes": {
                    "gen_ai.input.messages": json.dumps([
                        {"role": "user", "parts": [{"type": "text", "content": f"Task instructions for {sid}"}]}
                    ]),
                    "gen_ai.output.messages": json.dumps([
                        {
                            "role": "assistant",
                            "parts": [{"type": "text", "content": "Analyzing files"}],
                        }
                    ]),
                }
            }
        ]

    html_out = generate_audit_html_content(fixture_manifest, spans_loader=mock_spans_loader)

    # 1. No external URLs (no http:// or https://)
    url_pattern = re.compile(r"https?://")
    matches = url_pattern.findall(html_out)
    assert len(matches) == 0, f"Found external URLs in generated HTML: {matches}"

    # 2. No Success: or Status:
    assert "Success:" not in html_out, "Found 'Success:' in generated HTML"
    assert "Status:" not in html_out, "Found 'Status:' in generated HTML"

    # 3. No stratum names or inclusion probability
    assert "A_random" not in html_out
    assert "B_enriched" not in html_out
    assert "inclusion_probability" not in html_out
    assert "T4_pos" not in html_out
    assert "T2_pos_or_disagree" not in html_out

    # 4. Verbatim PREREG definitions present
    assert html.escape(T1_DEF) in html_out
    assert html.escape(T2_DEF) in html_out
    assert html.escape(T3_DEF) in html_out
    assert html.escape(T4_DEF) in html_out

    # 5. UI elements present
    assert "textContent" in html_out
    assert "export-btn" in html_out
    assert "import-btn" in html_out
    assert "audit_labels.json" in html_out


def test_score_audit_confusion_counts():
    """Requirement: score_audit on a small fixture gives the expected confusion counts."""
    audit_manifest = {
        "runs": [
            {"session_id": "sid_1", "stratum": "A_random"},
            {"session_id": "sid_2", "stratum": "A_random"},
            {"session_id": "sid_3", "stratum": "B_enriched"},
            {"session_id": "sid_4", "stratum": "B_enriched"},
        ]
    }

    # CEO labels:
    # sid_1: T1='yes' (gt True)
    # sid_2: T1='no' (gt False)
    # sid_3: T1='unsure' (excluded)
    # sid_4: T1='yes' (gt True)
    audit_labels = {
        "sid_1": {"T1": "yes", "T2": "no", "T3": "no", "T4": "no"},
        "sid_2": {"T1": "no", "T2": "yes", "T3": "no", "T4": "no"},
        "sid_3": {"T1": "unsure", "T2": "no", "T3": "yes", "T4": "no"},
        "sid_4": {"T1": "yes", "T2": "no", "T3": "no", "T4": "yes"},
    }

    # Judge labels:
    # sid_1: True -> pred True, gt True -> TP
    # sid_2: False -> pred False, gt False -> TN
    # sid_3: True -> unsure, excluded
    # sid_4: False -> pred False, gt True -> FN
    judge_labels = {
        "sid_1": {"evaluation": {"T1": {"label": True}, "T2": {"label": False}, "T3": {"label": False}, "T4": {"label": False}}},
        "sid_2": {"evaluation": {"T1": {"label": False}, "T2": {"label": True}, "T3": {"label": False}, "T4": {"label": False}}},
        "sid_3": {"evaluation": {"T1": {"label": True}, "T2": {"label": False}, "T3": {"label": True}, "T4": {"label": False}}},
        "sid_4": {"evaluation": {"T1": {"label": False}, "T2": {"label": False}, "T3": {"label": False}, "T4": {"label": True}}},
    }

    # Code rules for T1:
    # sid_1: False -> pred False, gt True -> FN
    # sid_2: False -> pred False, gt False -> TN
    # sid_3: True -> unsure, excluded
    # sid_4: True -> pred True, gt True -> TP
    rule_evals = {
        "sid_1": {"T1": False, "T2": False},
        "sid_2": {"T1": False, "T2": True},
        "sid_3": {"T1": True, "T2": False},
        "sid_4": {"T1": True, "T2": False},
    }

    results = score_audit(
        audit_labels=audit_labels,
        audit_manifest=audit_manifest,
        judge_labels=judge_labels,
        rule_evals=rule_evals,
    )

    # Check All 100 enriched metrics for T1
    all_t1_judge = results["all_100_enriched"]["T1"]["judge_vs_ceo"]
    assert all_t1_judge["total_evaluated"] == 3
    assert all_t1_judge["unsure_count"] == 1
    assert all_t1_judge["tp"] == 1
    assert all_t1_judge["fp"] == 0
    assert all_t1_judge["tn"] == 1
    assert all_t1_judge["fn"] == 1
    assert all_t1_judge["tpr"] == 0.5  # 1 / 2
    assert all_t1_judge["tnr"] == 1.0  # 1 / 1

    all_t1_rule = results["all_100_enriched"]["T1"]["rule_vs_ceo"]
    assert all_t1_rule["total_evaluated"] == 3
    assert all_t1_rule["unsure_count"] == 1
    assert all_t1_rule["tp"] == 1
    assert all_t1_rule["fp"] == 0
    assert all_t1_rule["tn"] == 1
    assert all_t1_rule["fn"] == 1
    assert all_t1_rule["tpr"] == 0.5
    assert all_t1_rule["tnr"] == 1.0

    # Check Stratum A unbiased metrics for T1 (only sid_1 and sid_2)
    stra_t1_judge = results["stratum_a_unbiased"]["T1"]["judge_vs_ceo"]
    assert stra_t1_judge["total_evaluated"] == 2
    assert stra_t1_judge["unsure_count"] == 0
    assert stra_t1_judge["tp"] == 1
    assert stra_t1_judge["fp"] == 0
    assert stra_t1_judge["tn"] == 1
    assert stra_t1_judge["fn"] == 0
    assert stra_t1_judge["tpr"] == 1.0
    assert stra_t1_judge["tnr"] == 1.0


def test_score_audit_exclude_option_and_custom_rater():
    """Verify that --exclude omits specified sessions from all rates, reports count, and prints custom rater in header."""
    from projects.p18_trace_triage.score_audit import format_score_table

    audit_manifest = {
        "runs": [
            {"session_id": "sid_1", "stratum": "A_random"},
            {"session_id": "sid_2", "stratum": "A_random"},
            {"session_id": "sid_3", "stratum": "B_enriched"},
            {"session_id": "sid_4", "stratum": "B_enriched"},
        ]
    }

    audit_labels = {
        "sid_1": {"T1": "yes"},
        "sid_2": {"T1": "no"},
        "sid_3": {"T1": "unsure"},
        "sid_4": {"T1": "yes"},
    }

    judge_labels = {
        "sid_1": {"evaluation": {"T1": {"label": True}}},
        "sid_2": {"evaluation": {"T1": {"label": False}}},
        "sid_3": {"evaluation": {"T1": {"label": True}}},
        "sid_4": {"evaluation": {"T1": {"label": False}}},
    }

    # When excluding sid_4 (which was FN in all_100_enriched):
    results = score_audit(
        audit_labels=audit_labels,
        audit_manifest=audit_manifest,
        judge_labels=judge_labels,
        exclude_ids=["sid_4"],
        rater="Claude Opus 5.5",
    )

    assert results["rater"] == "Claude Opus 5.5"
    assert results["excluded_count"] == 1
    assert results["excluded_ids"] == ["sid_4"]

    # Now all_100_enriched only has sid_1, sid_2, sid_3
    # sid_1: judge True, gt True -> TP
    # sid_2: judge False, gt False -> TN
    # sid_3: unsure
    t1_judge = results["all_100_enriched"]["T1"]["judge_vs_ceo"]
    assert t1_judge["total_evaluated"] == 2
    assert t1_judge["tp"] == 1
    assert t1_judge["fp"] == 0
    assert t1_judge["tn"] == 1
    assert t1_judge["fn"] == 0  # sid_4 was the FN, now excluded!
    assert t1_judge["tpr"] == 1.0
    assert t1_judge["tnr"] == 1.0

    # Verify table formatting
    table = format_score_table(results)
    assert "CLAUDE OPUS 5.5 GROUND TRUTH" in table
    assert "Rater: Claude Opus 5.5" in table
    assert "Excluded runs (1): sid_4" in table

