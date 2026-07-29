import json
from pathlib import Path

from faultline_cold_repro import (
    extract_cold_block,
)
from faultline_cold_repro.protocol import sha256_text
from faultline_cold_repro.simulation import parse_snapshot_file_list

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "day27/evidence"


def test_snapshot_file_list_is_nul_safe_and_ignores_the_terminal_empty_item():
    paths = parse_snapshot_file_list(
        "README.md\0directory with spaces/result.json\0\0"
    )
    assert paths == [
        Path("README.md"),
        Path("directory with spaces/result.json"),
    ]


def test_saved_cold_start_report_passes_without_hidden_steps():
    report = json.loads(
        (EVIDENCE / "cold_start_report.json").read_text(encoding="utf-8")
    )
    assert report["passed"]
    assert report["exit_code"] == 0
    assert report["operator_improvisations"] == 0


def test_transcript_contains_all_headlines_and_no_absolute_workspace():
    transcript = (EVIDENCE / "COLD-START-TRANSCRIPT.txt").read_text(
        encoding="utf-8"
    )
    assert transcript.count("headline ") == 6
    assert "operator interventions during execution: 0" in transcript
    assert "/private/tmp/faultline-cold-reader-" not in transcript


def test_saved_report_identifies_the_exact_document_block():
    report = json.loads(
        (EVIDENCE / "cold_start_report.json").read_text(encoding="utf-8")
    )
    assert report["document_block_sha256"] == sha256_text(extract_cold_block())
    assert report["document_block_executed_verbatim"]
