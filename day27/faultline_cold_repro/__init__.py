"""Cold-reader reproduction protocol, execution, and evidence audits."""

from .audit import audit_document, audit_friction, audit_peer, audit_transcript
from .headlines import build_headline_result, render_headline_result
from .protocol import (
    ROOT,
    extract_cold_block,
    extract_expected_output,
    load_protocol,
)
from .report import build_report, render_checkpoint
from .simulation import prepare_snapshot, run_documented_cold_start

__all__ = [
    "ROOT",
    "audit_document",
    "audit_friction",
    "audit_peer",
    "audit_transcript",
    "build_headline_result",
    "build_report",
    "extract_cold_block",
    "extract_expected_output",
    "load_protocol",
    "prepare_snapshot",
    "render_checkpoint",
    "render_headline_result",
    "run_documented_cold_start",
]
