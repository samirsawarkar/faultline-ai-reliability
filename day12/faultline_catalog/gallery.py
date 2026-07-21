"""The gallery — every fault linked fault -> trace -> detector -> metric.

Three renderings of one catalog: a JSON link table (machine), a Markdown gallery
(review), and a static HTML page (the market artifact). All are pure functions of
the catalog, so they regenerate byte-identically.
"""
from __future__ import annotations

from typing import Any, Dict, List


def gallery_links(catalog: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The core chain per fault: fault -> trace -> detector -> metric."""
    links = []
    for c in catalog["cards"]:
        links.append({
            "fault": c["id"],
            "name": c["name"],
            "producing_component": c["producing_component"],
            "trace": c["trace"]["artifact"],
            "detector": f'{c["detector"]["name"]} ({c["detector"]["nature"]})',
            "signal": c["detector"]["signal"],
            "metric": {"recall": c["metric"].get("detector_recall"),
                       "precision": c["metric"].get("detector_precision")},
            "recovery": c["recovery"]["strategy"],
        })
    return links


def render_markdown(catalog: Dict[str, Any]) -> str:
    lines = ["# FAULTLINE Fault Gallery (F1-F6)", "",
             "Every fault, linked **fault -> trace -> detector -> metric**. "
             "Generated from `catalog.json`; do not edit by hand.", "",
             "| Fault | Name | Producing component | Detector (nature) | Signal | "
             "Recall | Precision | Recovery | Trace |",
             "|---|---|---|---|---|---|---|---|---|"]
    for c in catalog["cards"]:
        m = c["metric"]
        lines.append(
            f'| **{c["id"]}** | {c["name"]} | {c["producing_component"]} | '
            f'{c["detector"]["name"]} ({c["detector"]["nature"]}) | '
            f'{c["detector"]["signal"]} | {m.get("detector_recall")} | '
            f'{m.get("detector_precision")} | {c["recovery"]["strategy"]} | '
            f'`{c["trace"]["artifact"]}` |')
    lines += ["", "## Cards", ""]
    for c in catalog["cards"]:
        lines += [
            f'### {c["id"]} — {c["name"]}', "",
            f'- **Family / component:** {c["family"]} / {c["producing_component"]}',
            f'- **Trigger:** {c["trigger"]}',
            f'- **Detector:** {c["detector"]["name"]} — *{c["detector"]["nature"]}* '
            f'(signal: `{c["detector"]["signal"]}`, measured in {c["metric"]["measured_in"]})',
            f'- **Recovery:** {c["recovery"]["strategy"]} '
            f'(planned: {c["recovery"]["planned_mechanism"]})',
            f'- **Metric:** recall {c["metric"].get("detector_recall")}, '
            f'precision {c["metric"].get("detector_precision")} — {c["metric"].get("note","")}',
            f'- **Trace:** `{c["trace"]["artifact"]}` '
            f'({c["trace"]["span_count"]} spans, {c["trace"]["ground_truth_entries"]} labelled)',
            f'- **Normalized spec:** `{c["spec"]}`', ""]
    return "\n".join(lines) + "\n"


def render_html(catalog: Dict[str, Any]) -> str:
    def esc(s: Any) -> str:
        return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

    cards_html = []
    for c in catalog["cards"]:
        m = c["metric"]
        cards_html.append(
            f'<article class="card {esc(c["detector"]["nature"])}">'
            f'<h2>{esc(c["id"])} · {esc(c["name"])}</h2>'
            f'<p class="comp">{esc(c["producing_component"])}</p>'
            f'<dl>'
            f'<dt>Trigger</dt><dd>{esc(c["trigger"])}</dd>'
            f'<dt>Detector</dt><dd>{esc(c["detector"]["name"])} '
            f'<span class="tag">{esc(c["detector"]["nature"])}</span> '
            f'— signal <code>{esc(c["detector"]["signal"])}</code></dd>'
            f'<dt>Recovery</dt><dd>{esc(c["recovery"]["strategy"])}</dd>'
            f'<dt>Metric</dt><dd>recall <b>{esc(m.get("detector_recall"))}</b>, '
            f'precision {esc(m.get("detector_precision"))} '
            f'<span class="src">({esc(m.get("measured_in"))})</span></dd>'
            f'<dt>Trace</dt><dd><code>{esc(c["trace"]["artifact"])}</code> '
            f'({esc(c["trace"]["span_count"])} spans)</dd>'
            f'</dl></article>')
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<title>FAULTLINE Fault Gallery (F1-F6)</title><style>"
        "body{font-family:system-ui,sans-serif;margin:2rem;background:#0b0d12;color:#e6e9ef}"
        "h1{font-weight:700}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:1rem}"
        ".card{border:1px solid #2a2f3a;border-radius:10px;padding:1rem;background:#141822}"
        ".card h2{margin:.2rem 0;font-size:1.1rem}.comp{color:#8b93a7;margin:.1rem 0 .6rem}"
        "dl{margin:0}dt{color:#8b93a7;font-size:.75rem;text-transform:uppercase;margin-top:.5rem}"
        "dd{margin:.1rem 0}code{background:#0b0d12;padding:.1rem .3rem;border-radius:4px}"
        ".tag{font-size:.7rem;padding:.1rem .4rem;border-radius:99px;background:#233;color:#7fd}"
        ".card.semantic .tag,.card.mixed .tag{background:#332;color:#fd7}"
        ".src{color:#8b93a7;font-size:.8rem}</style></head><body>"
        "<h1>FAULTLINE Fault Gallery — F1-F6</h1>"
        "<p>Six faults, each linked fault → trace → detector → metric. "
        "Deterministic detectors in green; semantic/mixed in amber.</p>"
        f'<div class="grid">{"".join(cards_html)}</div></body></html>\n')
