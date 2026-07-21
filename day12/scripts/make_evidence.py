"""Regenerate Day 12 evidence (deterministic; byte-reproducible in CI).

Writes under day12/evidence/:
  catalog.json                 the six normalized, complete fault cards
  GALLERY.md                   the gallery (fault -> trace -> detector -> metric)
  catalog.html                 the static HTML gallery (market artifact)
  audit_report.json            reproducibility + ground-truth integrity audit
  taxonomy.json                failure taxonomy by producing component
  traces/F1.json … F6.json     one labelled trace per fault
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in ("", "../day4", "../day8", "../day9", "../day10", "../day11"):
    sys.path.insert(0, str((ROOT / rel).resolve()))

from faultline_catalog import (  # noqa: E402
    build_catalog,
    canonical_trace,
    render_html,
    render_markdown,
    run_audit,
    taxonomy_by_component,
)

EVIDENCE = ROOT / "evidence"
TRACES = EVIDENCE / "traces"


def _dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, sort_keys=True, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8")


def main() -> None:
    EVIDENCE.mkdir(exist_ok=True)
    TRACES.mkdir(exist_ok=True)

    catalog = build_catalog()
    _dump(EVIDENCE / "catalog.json", catalog)
    (EVIDENCE / "GALLERY.md").write_text(render_markdown(catalog), encoding="utf-8")
    (EVIDENCE / "catalog.html").write_text(render_html(catalog), encoding="utf-8")
    _dump(EVIDENCE / "taxonomy.json", taxonomy_by_component(catalog))

    for fid in ("F1", "F2", "F3", "F4", "F5", "F6"):
        _dump(TRACES / f"{fid}.json", canonical_trace(fid))

    audit = run_audit()
    _dump(EVIDENCE / "audit_report.json", audit)

    print("Day 12 evidence written:")
    print(f"  fault cards            : {catalog['fault_count']}")
    print(f"  audit passed           : {audit['audit_passed']}")
    print(f"    all reproducible     : {audit['all_reproducible']}")
    print(f"    no label leakage     : {audit['no_label_leakage']}")
    print(f"    all cards complete   : {audit['all_cards_complete']}")
    print(f"    detectors vs truth   : {audit['all_detectors_scored_vs_truth']}")


if __name__ == "__main__":
    main()
