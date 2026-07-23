"""FAULTLINE Day 6: exact replay of captured simulator runs, and an honest
account of what real providers cannot reproduce.

    capture_run(provider, seed, task)  -> replay bundle (dict)
    replay_bundle(bundle)              -> {trace, final_state, calls_consumed}
    diff_summary(a, b)                 -> {equal, diff_count, diffs}
    build_report()                     -> replay-difference report
    save / load / bundle_digest        -> bundle I/O
"""
from .bundle import (
    BUNDLE_FORMAT,
    VersionMismatch,
    bundle_digest,
    canonical_bytes,
    check_versions,
    load,
    runtime_environment,
    save,
)
from .capture import capture_run
from .diff import diff, diff_summary
from .program import ToolFailure
from .providers import FlakyProvider, ReplayDivergence, SimulatorProvider
from .replay import replay_bundle
from .report import build_report

__all__ = [
    "capture_run",
    "replay_bundle",
    "diff",
    "diff_summary",
    "build_report",
    "save",
    "load",
    "bundle_digest",
    "canonical_bytes",
    "check_versions",
    "runtime_environment",
    "VersionMismatch",
    "ReplayDivergence",
    "ToolFailure",
    "SimulatorProvider",
    "FlakyProvider",
    "BUNDLE_FORMAT",
]
