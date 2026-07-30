"""Figures are deterministic, accessible, and source-linked."""
from pathlib import Path

import pytest

from faultline_publication import build_figures
from faultline_publication.evidence import DAY, FIGURES, ROOT, load_json, sha256_file

FIGURE_SPEC = load_json(DAY / "figures.json")["figures"]


def test_exactly_five_publication_figures():
    assert len(FIGURE_SPEC) == 5


@pytest.mark.parametrize(
    "figure",
    FIGURE_SPEC,
    ids=[figure["id"] for figure in FIGURE_SPEC],
)
def test_figure_is_accessible_and_embeds_its_sources(figure):
    svg = (FIGURES / figure["filename"]).read_text(encoding="utf-8")
    assert 'role="img"' in svg
    assert 'aria-labelledby="title desc"' in svg
    assert '<title id="title">' in svg
    assert '<desc id="desc">' in svg
    assert "<metadata>" in svg
    assert figure["title"] in svg
    for source in figure["sources"]:
        assert source["artifact"] in svg


@pytest.mark.parametrize(
    "figure",
    FIGURE_SPEC,
    ids=[figure["id"] for figure in FIGURE_SPEC],
)
def test_caption_is_identical_in_article_and_caption_sheet(figure):
    article = (DAY / "ARTICLE.md").read_text(encoding="utf-8")
    captions = (DAY / "FIGURE-CAPTIONS.md").read_text(encoding="utf-8")
    assert figure["caption"] in article
    assert figure["caption"] in captions


def test_figure_generation_is_byte_deterministic():
    before = {
        figure["filename"]: sha256_file(FIGURES / figure["filename"])
        for figure in FIGURE_SPEC
    }
    first = build_figures()
    second = build_figures()
    after = {
        figure["filename"]: sha256_file(FIGURES / figure["filename"])
        for figure in FIGURE_SPEC
    }
    assert before == after
    assert first == second


def test_figures_have_no_remote_or_script_dependency():
    for figure in FIGURE_SPEC:
        svg = (FIGURES / figure["filename"]).read_text(encoding="utf-8")
        assert "<script" not in svg
        assert "http://" not in svg.replace('xmlns="http://www.w3.org/2000/svg"', "")
        assert "https://" not in svg
