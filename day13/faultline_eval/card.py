"""Dataset card — a datasheet for the evaluation dataset (the market artifact)."""
from __future__ import annotations

from typing import Any, Dict

from .dataset import Dataset


def dataset_card(dataset: Dataset) -> str:
    m = dataset.manifest()
    by_mod: Dict[str, Dict[str, int]] = {}
    for s in dataset.samples:
        b = by_mod.setdefault(s.modality, {"fault": 0, "clean": 0})
        b["fault" if s.is_fault else "clean"] += 1

    lines = [
        f"# FAULTLINE Evaluation Dataset — `{dataset.version}`", "",
        "A versioned, leakage-resistant, oracle-grounded evaluation dataset over "
        "the six-fault spectrum (F1-F6).", "",
        "## Version & provenance", "",
        f"- **dataset_version:** `{dataset.version}` (content hash of this manifest)",
        f"- **generator_version:** `{m['generator_version']}`",
        f"- **samples:** {m['sample_count']}  "
        f"(train {m['split_sizes']['train']} / test {m['split_sizes']['test']})",
        f"- **split method:** {m['split_method']}", "",
        "## Composition (samples per modality)", "",
        "| Modality | fault | clean |", "|---|---|---|",
    ]
    for mod in sorted(by_mod):
        lines.append(f"| {mod} | {by_mod[mod]['fault']} | {by_mod[mod]['clean']} |")
    lines += [
        "", "## Fields (per sample)", "",
        "`sample_id` (content hash of config) · `modality` (F1-F6) · `is_fault` · "
        "`kind` · `severity` (tier) · `seed` · `expected_label` (oracle-grounded) · "
        "`expected_faulty` · `split`.", "",
        "## Leakage controls", "",
    ]
    for c in m["leakage_controls"]:
        lines.append(f"- {c}")
    lines += [
        "", "## Intended use", "",
        "Measure detection accuracy of the F1-F6 detectors against injection truth "
        "on the held-out **test** split. Labels are grounded in the injection oracle, "
        "not in any detector. Results are bound to this `dataset_version`; a result "
        "computed against a different version is rejected as stale.", "",
        "## Reproducible eval command", "",
        "```", "python day13/scripts/eval.py --split test", "```", "",
        "Deterministic: no wall clock, no RNG outside seeded fault injection.", "",
    ]
    return "\n".join(lines) + "\n"
