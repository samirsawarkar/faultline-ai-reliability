"""The publication must fail closed on unsupported or drifted prose."""
from pathlib import Path

import pytest

from faultline_publication.audit import (
    _audit_bindings,
    _unbound_numeric_tokens,
    audit_publication,
)
from faultline_publication import evidence
from faultline_publication.evidence import DAY, EVIDENCE, ROOT, load_json

CLAIM_SPEC = load_json(DAY / "claims.json")
CLAIMS_WITH_BINDINGS = [
    claim for claim in CLAIM_SPEC["claims"] if claim["bindings"]
]


def test_publication_audit_is_green():
    audit = audit_publication()
    assert audit["passed"] is True
    assert audit["errors"] == []


def test_every_substantive_paragraph_is_registered():
    audit = audit_publication()
    assert audit["checks"]["all_substantive_prose_registered"] is True
    assert audit["claim_count"] == 29


def test_findings_recommendations_and_synthesis_have_limitations():
    governed = {"finding", "recommendation", "synthesis"}
    for claim in CLAIM_SPEC["claims"]:
        if claim["kind"] in governed:
            assert claim["limitations"], claim["id"]


def test_all_sources_are_committed_results_at_head():
    audit = audit_publication()
    assert audit["sources"]
    assert all(source["committed_at_head"] for source in audit["sources"].values())
    methods = {
        source["provenance_method"] for source in audit["sources"].values()
    }
    expected = "git_head" if (ROOT / ".git").exists() else "committed_manifest"
    assert methods == {expected}


def test_clean_image_can_verify_sources_from_committed_manifest(monkeypatch):
    artifact = "day07/evidence/q1_results.json"
    recorded = load_json(EVIDENCE / "claim_audit.json")["sources"][artifact]
    monkeypatch.setattr(evidence, "_git_source_identity", lambda artifact: None)
    identity = evidence.source_identity(artifact)
    assert identity == {
        "git_blob_at_head": recorded["git_blob_at_head"],
        "provenance_method": "committed_manifest",
        "verified": True,
    }


def test_publication_bundle_has_content_hashes():
    artifacts = audit_publication()["publication_artifacts"]
    assert set(artifacts) == {
        "article_sha256",
        "claim_ledger_sha256",
        "figure_spec_sha256",
        "caption_sheet_sha256",
    }
    assert all(len(value) == 64 for value in artifacts.values())


@pytest.mark.parametrize(
    "claim",
    CLAIMS_WITH_BINDINGS,
    ids=[claim["id"] for claim in CLAIMS_WITH_BINDINGS],
)
def test_every_numeric_binding_resolves_exactly(claim):
    records, errors = _audit_bindings(claim["bindings"])
    assert errors == []
    assert records and all(record["matched"] for record in records)
    assert all(record["token"] in claim["text"] for record in records)


def test_every_visible_result_number_has_a_binding():
    for claim in CLAIM_SPEC["claims"]:
        assert _unbound_numeric_tokens(claim["text"], claim["bindings"]) == []
    for limitation in CLAIM_SPEC["limitations"]:
        assert _unbound_numeric_tokens(
            limitation["text"], limitation["bindings"]
        ) == []


def test_a_numeric_drift_is_rejected():
    bad = [{
        "token": "9.999",
        "artifact": "day07/evidence/q1_results.json",
        "pointer": "/single_hop_reliability/p1",
        "format": ".3f",
    }]
    records, errors = _audit_bindings(bad)
    assert records[0]["matched"] is False
    assert errors and "expected token" in errors[0]


@pytest.mark.parametrize(
    "limitation",
    CLAIM_SPEC["limitations"],
    ids=[item["id"] for item in CLAIM_SPEC["limitations"]],
)
def test_every_limitation_is_published_verbatim(limitation):
    article = (DAY / "ARTICLE.md").read_text(encoding="utf-8")
    assert limitation["text"] in article
    assert f'<a id="limitation-{limitation["id"].lower()}"></a>' in article
    _, errors = _audit_bindings(limitation["bindings"])
    assert errors == []


def test_claim_sources_are_inside_repository():
    for claim in CLAIM_SPEC["claims"]:
        for source in claim["sources"]:
            path = (ROOT / source["artifact"]).resolve()
            assert path.is_file()
            assert path.is_relative_to(ROOT.resolve())
