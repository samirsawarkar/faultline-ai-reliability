"""Unit tests for Project P8: MCPTox Evaluation."""
from __future__ import annotations

import json
from pathlib import Path

from inspect_ai.dataset import MemoryDataset, Sample

from projects.p08_mcptox.run import run_dry_run


def test_p08_mcptox_dry_run_in_process(monkeypatch, tmp_path: Path):
    """Verify in-process dry-run generates manifest.json with 300 sample IDs and exits 0."""
    synthetic_samples = []
    for i in range(1312):
        sample = Sample(
            id=f"mcptox_syn_{i:04d}",
            input=f"Benign user query {i}",
            metadata={
                "system_prompt": f"System prompt instructions for server {i % 5}",
                "poisoned_tool_name": f"poisoned_tool_{i}",
                "poisoned_tool_description": f"Hidden malicious command {i}",
                "legitimate_tools": [f"legit_tool_a_{i}", f"legit_tool_b_{i}"],
                "paradigm": f"Template-{(i % 3) + 1}",
                "security_risk": f"Risk-{(i % 4) + 1}",
                "server_name": f"Server-{(i % 10) + 1}",
            },
        )
        synthetic_samples.append(sample)

    dataset = MemoryDataset(samples=synthetic_samples, name="synthetic_mcptox")
    monkeypatch.setattr(
        "projects.p08_mcptox.run.load_mcptox_dataset",
        lambda *args, **kwargs: dataset,
    )

    ret = run_dry_run(output_dir=tmp_path)
    assert ret == 0

    manifest_path = tmp_path / "manifest.json"
    assert manifest_path.exists()

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert "ids" in manifest
    assert len(manifest["ids"]) == 300
    assert len(manifest["sample_ids"]) == 300
    assert manifest["n"] == 300
    assert manifest["mec_version"] == "v1.3"
    assert len(manifest["counts"]["subsample"]["paradigm"]) > 0
    assert len(manifest["counts"]["full"]["paradigm"]) > 0
