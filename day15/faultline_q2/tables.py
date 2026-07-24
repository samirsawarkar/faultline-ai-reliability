"""Render the Q2 tables — per-class, grouped, and with links to failing examples."""
from __future__ import annotations

from typing import Any, Dict, List


def render_q2_markdown(report: Dict[str, Any], failures: List[Dict[str, Any]]) -> str:
    pc = report["per_class_confusion"]
    aw = report["aggregation_warning"]
    L: List[str] = [
        f"# Q2 — Detection accuracy per fault (dataset `{report['dataset_version']}`, "
        f"split=`{report['split']}`, n={report['n_samples']})", "",
        "Measured against injection truth. Read **per class** — the aggregate below "
        "is shown only to demonstrate what it hides.", "",
        "## Per-class confusion + 95% Wilson intervals", "",
        "| Fault | TP | FP | FN | TN | recall | recall 95% CI | precision | precision 95% CI |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for m in sorted(pc):
        c = pc[m]
        L.append(f"| {m} | {c['tp']} | {c['fp']} | {c['fn']} | {c['tn']} | "
                 f"{c['recall']} | {c['recall_ci95']} | {c['precision']} | {c['precision_ci95']} |")
    L += ["", "## Deterministic vs semantic groups", "",
          "| Group | recall | recall 95% CI | FP | FN |", "|---|---|---|---|---|"]
    members = {"deterministic": "F2, F4, F6", "semantic": "F1, F3, F5"}
    for g in ("deterministic", "semantic"):
        c = report["groups"][g]
        L.append(f"| {g} ({members[g]}) | {c['recall']} | {c['recall_ci95']} | "
                 f"{c['fp']} | {c['fn']} |")
    L += [
        "", "## What the aggregate hides", "",
        f"- **micro recall** (all samples pooled): **{aw['micro_recall']}**",
        f"- **macro recall** (mean of per-class): **{aw['macro_recall']}**",
        f"- per-class recall: `{aw['per_class_recall']}`",
        "",
        "The single micro number would let a reader believe detection is uniform. It "
        "is not: recall ranges across families, and the difference between micro and "
        "macro is the fingerprint of that imbalance.", "",
        "## False positives / false negatives (nothing hidden)", "",
        f"- false positives: **{report['no_hiding']['total_false_positives']}**",
        f"- false negatives: **{report['no_hiding']['total_false_negatives']}** "
        f"(irreducible semantic escapes: {report['no_hiding']['fn_taxonomy']['irreducible_semantic_escape']}, "
        f"threshold-reducible: {report['no_hiding']['fn_taxonomy']['threshold_reducible']})",
        f"- reconciled (failures listed == FP+FN): **{report['no_hiding']['reconciled']}**", "",
        "### Each failing example (with trace)", "",
        "| Sample | Fault | kind | sev | outcome | why | trace |",
        "|---|---|---|---|---|---|---|",
    ]
    for f in failures:
        L.append(f"| `{f['sample_id']}` | {f['modality']} | {f['kind']} | {f['severity']} | "
                 f"{f['outcome']} | {f['why']} | [`{f['trace_artifact']}`]({f['trace_artifact']}) |")
    L += ["", "## Q2 finding", "", report["q2_findings"]["conclusion"], ""]
    return "\n".join(L) + "\n"
