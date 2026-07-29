from pathlib import Path

from faultline_cold_repro import (
    audit_document,
    extract_cold_block,
    extract_expected_output,
    load_protocol,
)

ROOT = Path(__file__).resolve().parents[2]


def test_cold_block_is_one_exact_copyable_procedure():
    block = extract_cold_block()
    assert len(block.splitlines()) == 4
    assert block.splitlines()[-1] == "make cold-reproduce"


def test_protocol_url_revision_and_directory_are_in_the_block():
    protocol = load_protocol()
    block = extract_cold_block()
    assert protocol["repository_url"] in block
    assert f"--branch {protocol['release_revision']}" in block
    assert block.splitlines()[1].endswith(
        f'"$FAULTLINE_REPOSITORY_URL" {protocol["clone_directory"]}'
    )
    assert block.splitlines()[2] == f'cd {protocol["clone_directory"]}'


def test_expected_output_contains_every_registered_headline():
    expected = extract_expected_output()
    audit = audit_document()
    assert audit["passed"]
    assert expected.endswith("cold reproduction: PASS")
    assert expected.count("headline ") == 6


def test_document_audit_rejects_falling_forward_to_main(tmp_path):
    original = (ROOT / "REPRODUCE.md").read_text(encoding="utf-8")
    mutated = tmp_path / "REPRODUCE.md"
    mutated.write_text(
        original.replace("--branch v0.27.0-rc1", "--branch main", 1),
        encoding="utf-8",
    )
    audit = audit_document(mutated)
    assert not audit["passed"]
    assert not audit["checks"]["release_revision_exact"]
