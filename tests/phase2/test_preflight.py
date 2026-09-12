import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from projects.p00_preflight.run import (
    LADDER_SPEC,
    PreflightEntry,
    PreflightReport,
    format_markdown_table,
    get_price_table,
    probe_rung,
    run_preflight,
)


def test_ladder_spec_has_six_rungs():
    assert set(LADDER_SPEC.keys()) == {"R1", "R2", "R3", "R4", "R5", "R6"}
    pt = get_price_table()
    assert len(pt.rungs) == 6


def test_probe_rung_mock_live():
    mock_resp1 = MagicMock()
    mock_resp1.choices = [MagicMock(message=MagicMock(content="PONG"))]
    mock_resp1.model = "test-provider-v1"
    mock_resp1.usage.prompt_tokens = 20
    mock_resp1.usage.completion_tokens = 2

    mock_resp2 = MagicMock()
    mock_resp2.choices = [MagicMock(message=MagicMock(content="PONG"))]
    mock_resp2.model = "test-provider-v1"
    mock_resp2.usage.prompt_tokens = 20
    mock_resp2.usage.completion_tokens = 2

    with patch("litellm.completion", side_effect=[mock_resp1, mock_resp2]):
        entry = probe_rung("R1", LADDER_SPEC["R1"])
        assert entry.status == "live"
        assert entry.model_version == "test-provider-v1"
        assert entry.temp0_deterministic is True
        assert entry.call1_response == "PONG"
        assert entry.call2_response == "PONG"


def test_probe_rung_mock_failed():
    with patch("litellm.completion", side_effect=Exception("AuthenticationError: Missing API key")):
        entry = probe_rung("R2", LADDER_SPEC["R2"])
        assert entry.status == "failed"
        assert "AuthenticationError" in (entry.error or "")
        assert entry.temp0_deterministic is None


def test_run_preflight_end_to_end_mock(tmp_path):
    output_dir = tmp_path / "p00"
    ledger_path = tmp_path / "ledger.jsonl"

    def mock_completion(**kwargs):
        resp = MagicMock()
        resp.choices = [MagicMock(message=MagicMock(content="PONG"))]
        resp.model = kwargs["model"] + "@2026"
        resp.usage.prompt_tokens = 15
        resp.usage.completion_tokens = 2
        return resp

    with patch("litellm.completion", side_effect=mock_completion):
        report = run_preflight(
            confirmed=True,
            output_dir=output_dir,
            ledger_path=ledger_path,
        )

        assert report.total_rungs == 6
        assert report.live_rungs == 6
        assert report.failed_rungs == 0
        assert len(report.entries) == 6

        # Check files created
        assert (output_dir / "preflight.json").exists()
        assert (output_dir / "preflight_table.md").exists()

        table_md = (output_dir / "preflight_table.md").read_text()
        assert "| R1 |" in table_md
        assert "| R6 |" in table_md
