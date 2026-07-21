"""FAULTLINE Day 12: the fault catalog + gallery.

Consolidates F1-F6 (Days 8-11) into one defensible, reproducible specification:
six complete fault cards (each with trigger/trace/detector/recovery/metric), a
gallery linking fault -> trace -> detector -> metric, a reproducibility +
ground-truth integrity audit, and a failure taxonomy by producing component.

Public surface:
    cards:     FaultCard, card_skeletons, SPEC_FIELDS, REQUIRED_CARD_FIELDS
    catalog:   build_catalog
    traces:    canonical_trace, all_traces
    gallery:   gallery_links, render_markdown, render_html
    taxonomy:  taxonomy_by_component
    audit:     run_audit
"""
from . import audit, catalog, gallery, taxonomy, traces
from .cards import REQUIRED_CARD_FIELDS, SPEC_FIELDS, FaultCard, card_skeletons
from .audit import run_audit
from .catalog import build_catalog
from .gallery import gallery_links, render_html, render_markdown
from .taxonomy import taxonomy_by_component
from .traces import all_traces, canonical_trace

__all__ = [
    "FaultCard", "card_skeletons", "SPEC_FIELDS", "REQUIRED_CARD_FIELDS",
    "build_catalog", "canonical_trace", "all_traces",
    "gallery_links", "render_markdown", "render_html",
    "taxonomy_by_component", "run_audit",
    "cards", "catalog", "traces", "gallery", "taxonomy", "audit",
]
