"""Fail closed when a publication claim, caption, result, or limitation drifts."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from .evidence import (
    DAY,
    FIGURES,
    ROOT,
    load_json,
    resolve_pointer,
    sha256_file,
    source_identity,
)

CLAIM_RE = re.compile(r"<!-- CLAIM:(C\d{2}) -->\n([^\n]+(?:\n(?!\n)[^\n]+)*)")
FIGURE_RE = re.compile(r"<!-- FIGURE:(figure-\d) -->")
NUMBER_RE = re.compile(r"(?<![\w])\d+(?:\.\d+)?(?:e[+-]?\d+)?(?![\w])")
PRESENTATION_CONSTANTS = {"95", "100"}


def _binding_value(binding: Dict[str, Any]) -> str:
    document = load_json(ROOT / binding["artifact"])
    value = resolve_pointer(document, binding["pointer"])
    formatting = binding.get("format")
    if formatting:
        return format(value, formatting)
    return str(value)


def _audit_bindings(bindings: Iterable[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    records: List[Dict[str, Any]] = []
    errors: List[str] = []
    for binding in bindings:
        try:
            rendered = _binding_value(binding)
        except (FileNotFoundError, KeyError, IndexError, TypeError, ValueError) as exc:
            errors.append(
                f"{binding['artifact']}#{binding['pointer']}: cannot resolve ({exc})"
            )
            continue
        record = dict(binding)
        record["resolved"] = rendered
        record["matched"] = rendered == binding["token"]
        records.append(record)
        if rendered != binding["token"]:
            errors.append(
                f"{binding['artifact']}#{binding['pointer']}: expected token "
                f"{binding['token']!r}, resolved {rendered!r}"
            )
    return records, errors


def _unbound_numeric_tokens(text: str, bindings: Iterable[Dict[str, Any]]) -> List[str]:
    """Return visible result-like numbers without an explicit source binding."""
    cleaned = re.sub(r"\]\([^)]*\)", "]", text)
    cleaned = re.sub(r"\b[QPF]\d+\b", "", cleaned)
    cleaned = re.sub(r"\bp\d+\b", "", cleaned)
    cleaned = re.sub(r"\bFigure \d+\b", "", cleaned)
    visible = set(NUMBER_RE.findall(cleaned))
    declared = {binding["token"] for binding in bindings}
    return sorted(visible - declared - PRESENTATION_CONSTANTS)


def _audit_sources(paths: Iterable[str]) -> Tuple[Dict[str, Any], List[str]]:
    records: Dict[str, Any] = {}
    errors: List[str] = []
    for artifact in sorted(set(paths)):
        path = ROOT / artifact
        if not path.is_file():
            errors.append(f"missing source artifact: {artifact}")
            continue
        identity = source_identity(artifact)
        records[artifact] = {
            "sha256": sha256_file(path),
            "git_blob_at_head": identity["git_blob_at_head"],
            "committed_at_head": identity["verified"],
            "provenance_method": identity["provenance_method"],
        }
        if not identity["verified"]:
            errors.append(f"source is not committed at HEAD: {artifact}")
    return records, errors


def audit_publication() -> Dict[str, Any]:
    article = (DAY / "ARTICLE.md").read_text(encoding="utf-8")
    claim_spec = load_json(DAY / "claims.json")
    figure_spec = load_json(DAY / "figures.json")
    claims = {claim["id"]: claim for claim in claim_spec["claims"]}
    limitations = {item["id"]: item for item in claim_spec["limitations"]}
    errors: List[str] = []

    article_claims: Dict[str, str] = {}
    for match in CLAIM_RE.finditer(article):
        claim_id, text = match.groups()
        if claim_id in article_claims:
            errors.append(f"duplicate article marker: {claim_id}")
        article_claims[claim_id] = text

    publication_body = article.split("## Reproduce and audit", 1)[0]
    unregistered_prose: List[str] = []
    for block in publication_body.split("\n\n"):
        stripped = block.strip()
        if not stripped:
            continue
        exempt = (
            stripped.startswith("#")
            or stripped.startswith("*FAULTLINE")
            or stripped.startswith("<!-- CLAIM:")
            or stripped.startswith("<!-- FIGURE:")
            or stripped.startswith("![")
            or stripped.startswith("Figure ")
            or stripped.startswith("<a id=")
            or re.match(r"^\d+\. ", stripped) is not None
        )
        if not exempt:
            unregistered_prose.append(stripped)
    if unregistered_prose:
        errors.append(
            "unregistered substantive prose: "
            + " | ".join(text[:80] for text in unregistered_prose)
        )
    if set(article_claims) != set(claims):
        missing = sorted(set(claims) - set(article_claims))
        extra = sorted(set(article_claims) - set(claims))
        if missing:
            errors.append(f"claims missing from article: {missing}")
        if extra:
            errors.append(f"unregistered article claims: {extra}")

    binding_records: Dict[str, Any] = {}
    limitation_binding_records: Dict[str, Any] = {}
    binding_error_count = 0
    numeric_coverage_errors: List[str] = []
    source_paths: List[str] = []
    for claim_id, claim in claims.items():
        if article_claims.get(claim_id) != claim["text"]:
            errors.append(f"article text drift: {claim_id}")
        source_paths.extend(source["artifact"] for source in claim["sources"])
        if claim["kind"] in {"finding", "synthesis", "recommendation"} and not claim["limitations"]:
            errors.append(f"{claim_id} has no honest limitation")
        unknown = sorted(set(claim["limitations"]) - set(limitations))
        if unknown:
            errors.append(f"{claim_id} references unknown limitations: {unknown}")
        records, binding_errors = _audit_bindings(claim.get("bindings", []))
        binding_records[claim_id] = records
        binding_error_count += len(binding_errors)
        errors.extend(f"{claim_id}: {message}" for message in binding_errors)
        for record in records:
            if record["token"] not in claim["text"]:
                errors.append(f"{claim_id}: bound token {record['token']!r} absent from claim")
        unbound = _unbound_numeric_tokens(claim["text"], claim.get("bindings", []))
        if unbound:
            message = f"{claim_id}: unbound numeric tokens {unbound}"
            numeric_coverage_errors.append(message)
            errors.append(message)

    for limitation_id, limitation in limitations.items():
        marker = f'<a id="limitation-{limitation_id.lower()}"></a>'
        if marker not in article or limitation["text"] not in article:
            errors.append(f"limitation missing or drifted in article: {limitation_id}")
        source_paths.extend(source["artifact"] for source in limitation["sources"])
        records, binding_errors = _audit_bindings(limitation.get("bindings", []))
        limitation_binding_records[limitation_id] = records
        binding_error_count += len(binding_errors)
        errors.extend(f"{limitation_id}: {message}" for message in binding_errors)
        unbound = _unbound_numeric_tokens(
            limitation["text"], limitation.get("bindings", [])
        )
        if unbound:
            message = f"{limitation_id}: unbound numeric tokens {unbound}"
            numeric_coverage_errors.append(message)
            errors.append(message)

    figure_records: Dict[str, Any] = {}
    article_figure_ids = FIGURE_RE.findall(article)
    figures = figure_spec["figures"]
    if not 4 <= len(figures) <= 5:
        errors.append(f"publication must contain 4-5 figures, found {len(figures)}")
    if article_figure_ids != [figure["id"] for figure in figures]:
        errors.append("article figure order/registration drift")
    captions_document = (DAY / "FIGURE-CAPTIONS.md").read_text(encoding="utf-8")
    for figure in figures:
        figure_id = figure["id"]
        path = FIGURES / figure["filename"]
        source_paths.extend(source["artifact"] for source in figure["sources"])
        if not path.is_file():
            errors.append(f"missing figure: {path.relative_to(ROOT)}")
            continue
        svg = path.read_text(encoding="utf-8")
        if figure["title"] not in svg:
            errors.append(f"{figure_id}: SVG title drift")
        if figure["caption"] not in article or figure["caption"] not in captions_document:
            errors.append(f"{figure_id}: standalone caption missing or drifted")
        records, binding_errors = _audit_bindings(figure.get("bindings", []))
        binding_error_count += len(binding_errors)
        errors.extend(f"{figure_id}: {message}" for message in binding_errors)
        for record in records:
            if record["token"] not in figure["caption"]:
                errors.append(
                    f"{figure_id}: bound token {record['token']!r} absent from caption"
                )
        unbound = _unbound_numeric_tokens(
            figure["caption"], figure.get("bindings", [])
        )
        if unbound:
            message = f"{figure_id}: unbound numeric tokens {unbound}"
            numeric_coverage_errors.append(message)
            errors.append(message)
        expected_sources = sorted(source["artifact"] for source in figure["sources"])
        if not all(source in svg for source in expected_sources):
            errors.append(f"{figure_id}: SVG metadata lacks a declared source")
        figure_records[figure_id] = {
            "sha256": sha256_file(path),
            "bindings": records,
            "sources": expected_sources,
        }

    source_records, source_errors = _audit_sources(source_paths)
    errors.extend(source_errors)
    checks = {
        "all_claims_registered_once": set(article_claims) == set(claims),
        "all_substantive_prose_registered": not unregistered_prose,
        "claim_text_matches_article": all(
            article_claims.get(claim_id) == claim["text"]
            for claim_id, claim in claims.items()
        ),
        "every_finding_has_source": all(claim["sources"] for claim in claims.values()),
        "every_finding_has_limitation": all(
            claim["limitations"]
            for claim in claims.values()
            if claim["kind"] in {"finding", "synthesis", "recommendation"}
        ),
        "all_numeric_bindings_resolve": binding_error_count == 0,
        "every_numeric_token_bound": not numeric_coverage_errors,
        "source_results_committed": all(
            record["committed_at_head"] for record in source_records.values()
        ),
        "four_to_five_figures": 4 <= len(figures) <= 5,
        "figures_source_linked": all(
            figure_id in figure_records for figure_id in [figure["id"] for figure in figures]
        ),
        "standalone_captions_present": all(
            figure["caption"] in article and figure["caption"] in captions_document
            for figure in figures
        ),
        "findings_first": article.index("## Findings first") < article.index("## Method"),
        "limitations_explicit": all(
            limitation["text"] in article for limitation in limitations.values()
        ),
    }
    return {
        "article": "day28/ARTICLE.md",
        "publication_artifacts": {
            "article_sha256": sha256_file(DAY / "ARTICLE.md"),
            "claim_ledger_sha256": sha256_file(DAY / "claims.json"),
            "figure_spec_sha256": sha256_file(DAY / "figures.json"),
            "caption_sheet_sha256": sha256_file(DAY / "FIGURE-CAPTIONS.md"),
        },
        "claim_count": len(claims),
        "limitation_count": len(limitations),
        "figure_count": len(figures),
        "checks": checks,
        "claims": {
            claim_id: {
                "kind": claim["kind"],
                "sources": claim["sources"],
                "limitations": claim["limitations"],
                "bindings": binding_records[claim_id],
                "matched": article_claims.get(claim_id) == claim["text"],
            }
            for claim_id, claim in claims.items()
        },
        "limitations": {
            limitation_id: {
                "sources": limitation["sources"],
                "bindings": limitation_binding_records[limitation_id],
                "published": limitation["text"] in article,
            }
            for limitation_id, limitation in limitations.items()
        },
        "figures": figure_records,
        "sources": source_records,
        "errors": errors,
        "passed": all(checks.values()) and not errors,
    }
