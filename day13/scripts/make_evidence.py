"""Regenerate Day 13 evidence (deterministic; byte-reproducible in CI).

Writes under day13/evidence/:
  manifest.json        the versioned dataset manifest (seeds, tiers, configs, labels)
  splits.json          the train/test split (ids per split + sizes + method)
  eval_result.json     the immutable eval result on the test split (bound to versions)
  leakage_report.json  split disjointness + label non-leakage + the two attacks
  DATASET_CARD.md      the dataset card (datasheet + reproducible eval command)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in ("", "../day08", "../day09", "../day10", "../day11"):
    sys.path.insert(0, str((ROOT / rel).resolve()))

from faultline_eval import audit, build_dataset, dataset_card, evaluate, validate_result  # noqa: E402

EVIDENCE = ROOT / "evidence"


def _dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, sort_keys=True, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8")


def main() -> None:
    EVIDENCE.mkdir(exist_ok=True)
    ds = build_dataset()
    result = evaluate(ds, "test")

    _dump(EVIDENCE / "manifest.json", ds.manifest())
    _dump(EVIDENCE / "splits.json", {
        "dataset_version": ds.version,
        "sizes": {"train": len(ds.split("train")), "test": len(ds.split("test"))},
        "method": ds.manifest()["split_method"],
        "train": sorted(s.sample_id for s in ds.split("train")),
        "test": sorted(s.sample_id for s in ds.split("test")),
    })
    _dump(EVIDENCE / "eval_result.json", {
        "freshness_against_own_dataset": validate_result(result, ds),
        **result.to_dict(),
    })
    _dump(EVIDENCE / "leakage_report.json", audit(ds))
    (EVIDENCE / "DATASET_CARD.md").write_text(dataset_card(ds), encoding="utf-8")

    a = audit(ds)
    print("Day 13 evidence written:")
    print(f"  dataset_version    : {ds.version}")
    print(f"  samples (train/test): {len(ds.split('train'))}/{len(ds.split('test'))}")
    print(f"  test recall/precision: {result.overall['recall']} / {result.overall['precision']}")
    print(f"  leakage audit passed: {a['passed']}")
    print(f"    split_disjoint          : {a['split_disjoint']}")
    print(f"    contamination detected  : {a['contamination_attack']['detected_after']}")
    print(f"    stale reuse blocked     : {a['stale_reuse_attack']['stale_reuse_blocked']}")
    print(f"    no label leakage        : {a['label_leakage']['no_label_leakage']}")


if __name__ == "__main__":
    main()
