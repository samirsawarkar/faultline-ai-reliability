"""The versioned dataset — seeds, tiers, fault configs, and oracle-grounded labels.

A Sample is a fully-specified evaluation unit: a modality (F1-F6), whether a fault
is injected, its kind, a severity TIER, and a SEED. Its `expected_label` is the
ground truth grounded in the injection itself (fault family or "clean") — never a
detector's opinion. Its `sample_id` is the content hash of its config, so identity
is unambiguous, and its `split` is a pure function of that id, so splits are
deterministic and disjoint by construction.

The dataset VERSION is the content hash of the whole manifest (generator version +
every sample descriptor). Change any seed, tier, config, or label and the version
changes — which is what lets a result be bound to the exact data it was computed
against and what makes stale reuse detectable.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List

GENERATOR_VERSION = "dataset-1.0.0"
TEST_FRACTION_OUT_OF_5 = 2          # 2/5 = 40% held out as test


def _sha(obj: Any) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


@dataclass(frozen=True)
class Sample:
    sample_id: str
    modality: str          # F1..F6
    is_fault: bool
    kind: str              # fault kind, or "clean"
    severity: int          # difficulty tier
    seed: int
    expected_label: str    # modality if fault else "clean" (oracle-grounded truth)
    expected_faulty: bool
    split: str             # "train" | "test"

    def to_dict(self) -> Dict[str, Any]:
        return {"sample_id": self.sample_id, "modality": self.modality,
                "is_fault": self.is_fault, "kind": self.kind,
                "severity": self.severity, "seed": self.seed,
                "expected_label": self.expected_label,
                "expected_faulty": self.expected_faulty, "split": self.split}


# The frozen generator config: per modality, the fault kinds, tiers and seeds,
# plus how many clean negatives to test that modality's detector against.
DEFAULT_CONFIG: Dict[str, Dict[str, Any]] = {
    "F1": {"kinds": ["corrupt"], "severities": [1, 3, 5], "seeds": [1, 2], "clean": 3},
    "F2": {"kinds": ["latency"], "severities": [1, 3, 5], "seeds": [1, 2], "clean": 3},
    "F3": {"kinds": ["nonmultiple", "drift_value"], "severities": [3], "seeds": [1, 2], "clean": 3},
    "F4": {"kinds": ["provider_error"], "severities": [5], "seeds": [1, 2], "clean": 3},
    "F5": {"kinds": ["context_inconsistent", "context_drift"], "severities": [2], "seeds": [1, 2], "clean": 3},
    "F6": {"kinds": ["repetition", "budget_exhaustion"], "severities": [2], "seeds": [1, 2], "clean": 3},
}


def _sample_id(modality: str, is_fault: bool, kind: str, severity: int, seed: int) -> str:
    return _sha({"m": modality, "f": is_fault, "k": kind, "s": severity, "seed": seed})[:16]


def _make(modality: str, is_fault: bool, kind: str, severity: int, seed: int,
          split: str) -> Sample:
    return Sample(
        sample_id=_sample_id(modality, is_fault, kind, severity, seed),
        modality=modality, is_fault=is_fault, kind=kind, severity=severity,
        seed=seed, expected_label=modality if is_fault else "clean",
        expected_faulty=is_fault, split=split)


@dataclass
class Dataset:
    config: Dict[str, Any]
    samples: List[Sample]
    version: str

    def split(self, name: str) -> List[Sample]:
        return [s for s in self.samples if s.split == name]

    def manifest(self) -> Dict[str, Any]:
        splits = {"train": len(self.split("train")), "test": len(self.split("test"))}
        return {
            "dataset_version": self.version,
            "generator_version": GENERATOR_VERSION,
            "sample_count": len(self.samples),
            "split_sizes": splits,
            "split_method": f"stratified by (modality, is_fault); within each stratum, "
                            f"samples sorted by sample_id, the first "
                            f"{TEST_FRACTION_OUT_OF_5}/5 (>=1, <n) assigned to test. "
                            f"Deterministic and balanced across families.",
            "leakage_controls": [
                "sample_id = content hash of config (identity unambiguous)",
                "split is a deterministic, stratified, disjoint partition",
                "expected_label grounded in injection truth, never a detector",
                "dataset_version = content hash of this manifest (stale reuse detectable)",
            ],
            "config": self.config,
            "samples": [s.to_dict() for s in sorted(self.samples, key=lambda x: x.sample_id)],
        }


def build_dataset(config: Dict[str, Any] = None) -> Dataset:
    config = config if config is not None else DEFAULT_CONFIG

    # 1. enumerate proto-samples (no split yet), de-duplicated by content id
    protos: List[Dict[str, Any]] = []
    seen = set()

    def _add(modality, is_fault, kind, severity, seed):
        sid = _sample_id(modality, is_fault, kind, severity, seed)
        if sid in seen:
            return
        seen.add(sid)
        protos.append({"modality": modality, "is_fault": is_fault, "kind": kind,
                       "severity": severity, "seed": seed, "sample_id": sid})

    for modality, spec in config.items():
        for kind in spec["kinds"]:
            for severity in spec["severities"]:
                for seed in spec["seeds"]:
                    _add(modality, True, kind, severity, seed)
        for i in range(spec.get("clean", 0)):
            _add(modality, False, "clean", 0, 1000 + i)

    # 2. stratified split by (modality, kind): deterministic and balanced, so every
    #    fault KIND (including the semantic escapes) is represented in both splits.
    strata: Dict[tuple, List[Dict[str, Any]]] = {}
    for p in protos:
        strata.setdefault((p["modality"], p["kind"]), []).append(p)
    test_ids = set()
    for group in strata.values():
        group.sort(key=lambda p: p["sample_id"])
        n = len(group)
        test_n = min(n - 1, max(1, round(n * TEST_FRACTION_OUT_OF_5 / 5))) if n > 1 else 0
        for p in group[:test_n]:
            test_ids.add(p["sample_id"])

    # 3. materialize frozen samples
    samples = [_make(p["modality"], p["is_fault"], p["kind"], p["severity"],
                     p["seed"], "test" if p["sample_id"] in test_ids else "train")
               for p in protos]

    # 4. version = content hash of the manifest WITHOUT the version field
    manifest_no_version = Dataset(config=config, samples=samples, version="").manifest()
    manifest_no_version.pop("dataset_version")
    return Dataset(config=config, samples=samples, version=_sha(manifest_no_version)[:16])
