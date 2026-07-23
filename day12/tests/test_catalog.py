"""Six complete fault cards, normalized specs, and the gallery/taxonomy links."""
from __future__ import annotations

import dataclasses

import pytest

from faultline_catalog import (
    REQUIRED_CARD_FIELDS,
    SPEC_FIELDS,
    build_catalog,
    card_skeletons,
    gallery_links,
    taxonomy_by_component,
)
from faultline_catalog.catalog import _metrics

FAULT_IDS = {"F1", "F2", "F3", "F4", "F5", "F6"}


def test_catalog_has_six_complete_cards():
    cat = build_catalog()
    assert cat["fault_count"] == 6
    assert {c["id"] for c in cat["cards"]} == FAULT_IDS
    for c in cat["cards"]:
        for f in REQUIRED_CARD_FIELDS:
            assert c[f], f"{c['id']} missing {f}"


def test_every_spec_is_normalized_to_the_same_ten_fields():
    cat = build_catalog()
    for c in cat["cards"]:
        assert tuple(c["spec"].keys()) == SPEC_FIELDS
        assert len(c["spec"]) == 10


def test_missing_any_required_field_fails_validation():
    # This is the mission's fail condition: a card without trigger/trace/detector/
    # recovery/metric must be rejected.
    for missing in REQUIRED_CARD_FIELDS:
        card = card_skeletons()[0]
        card.metric = {"detector_recall": 1.0, "measured_in": "day09"}
        card.trace = {"artifact": "x"}
        setattr(card, missing, "" if isinstance(getattr(card, missing), str) else {})
        with pytest.raises(ValueError):
            card.validate()


def test_gallery_links_chain_fault_to_trace_to_detector_to_metric():
    cat = build_catalog()
    links = gallery_links(cat)
    assert {l["fault"] for l in links} == FAULT_IDS
    for l in links:
        assert l["trace"].endswith(".json")
        assert l["detector"] and l["signal"]
        assert l["metric"]["recall"] is not None


def test_taxonomy_groups_all_six_by_component_and_layer():
    tax = taxonomy_by_component(build_catalog())
    grouped = {f["fault"] for comp in tax["by_component"] for f in comp["faults"]}
    assert grouped == FAULT_IDS
    assert set(tax["by_layer"]["provider boundary"]) == {"F1", "F2", "F3", "F4"}
    assert set(tax["by_layer"]["agent internals"]) == {"F5", "F6"}


def test_metrics_match_source_days():
    m = _metrics()
    assert m["F6"]["detector_recall"] == 1.0        # deterministic, day11
    assert m["F5"]["detector_recall"] == 0.5        # semantic, day11
    assert m["F3"]["detector_recall"] == 0.6        # mixed, day10
    assert m["F4"]["detector_recall"] == 1.0        # explicit, day10


def test_catalog_is_deterministic():
    assert build_catalog() == build_catalog()
