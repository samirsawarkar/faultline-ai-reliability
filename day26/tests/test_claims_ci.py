"""Results-first README, generator linkage, Make, and CI contracts."""
import json
from pathlib import Path

from faultline_repro import audit_ci_contract, audit_readme_claims

ROOT = Path(__file__).resolve().parents[2]


def test_results_first_readme_claims_resolve_to_scripts_and_results():
    audit = audit_readme_claims()
    assert audit["passed"]
    assert audit["checks"]["results_first"]
    assert audit["checks"]["no_unregistered_result_rows"]


def test_readme_audit_rejects_a_tampered_number(tmp_path):
    original = (ROOT / "README.md").read_text(encoding="utf-8")
    tampered = tmp_path / "README.md"
    tampered.write_text(
        original.replace("Measured success 0.818", "Measured success 0.819", 1),
        encoding="utf-8",
    )
    audit = audit_readme_claims(tampered)
    assert not audit["passed"]
    assert not audit["checks"]["every_manifest_claim_passes"]


def test_every_claim_has_an_existing_generator_and_result_artifact():
    manifest = json.loads(
        (ROOT / "day26/readme_claims.json").read_text(encoding="utf-8")
    )
    for claim in manifest["claims"]:
        assert (ROOT / claim["generator"]).is_file()
        for value in claim["values"]:
            assert (ROOT / value["artifact"]).is_file()


def test_research_ci_runs_tests_eval_fast_experiments_and_container():
    audit = audit_ci_contract()
    assert audit["passed"]
    assert all(audit["checks"].values())


def test_makefile_exposes_one_command_and_release_gates():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    for target in (
        "reproduce:",
        "reproduce-fast:",
        "container-reproduce:",
        "release-check:",
        "readme-audit:",
        "eval-verify:",
        "experiment-fast:",
    ):
        assert target in makefile


def test_dependency_lock_contains_no_compatible_ranges():
    for raw in (ROOT / "requirements.txt").read_text().splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            assert line.count("==") == 1
            assert not any(op in line for op in (">=", "<=", "~=", "!="))
