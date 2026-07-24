"""FAULTLINE Day 15: Q2 — per-fault precision, recall and confusion vs injection truth.

Runs every detector over the Day-13 labelled set and reports per-class confusion
matrices with Wilson intervals (Day 14), grouped deterministic vs semantic (Day 11),
with every false positive and false negative investigated trace by trace — never
hidden behind an aggregate.

Public surface:
    q2:         build_report, run_outcomes, DETERMINISTIC_GROUP, SEMANTIC_GROUP
    investigate: trace_sample, collect_failures
    tables:     render_q2_markdown
"""
from . import investigate, q2, tables
from .investigate import collect_failures, trace_sample
from .q2 import DETERMINISTIC_GROUP, SEMANTIC_GROUP, build_report, run_outcomes
from .tables import render_q2_markdown

__all__ = [
    "build_report", "run_outcomes", "DETERMINISTIC_GROUP", "SEMANTIC_GROUP",
    "trace_sample", "collect_failures", "render_q2_markdown",
    "q2", "investigate", "tables",
]
