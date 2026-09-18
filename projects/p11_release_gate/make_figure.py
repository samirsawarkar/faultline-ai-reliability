"""Generate publication-quality figure for Project P11: Release Gate."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

from faultline_p2.stats.intervals import wilson_interval

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BASE_DIR = Path(__file__).resolve().parent


def generate_figure(
    band_path: Path,
    report_r1_path: Path,
    report_r4_path: Path,
    report_r2_path: Path,
    ledger_path: Path,
    output_svg: Path,
    output_png: Path,
    output_pdf: Path,
) -> None:
    with open(band_path, "r", encoding="utf-8") as f:
        band = json.load(f)
    with open(report_r1_path, "r", encoding="utf-8") as f:
        r1 = json.load(f)
    with open(report_r4_path, "r", encoding="utf-8") as f:
        r4 = json.load(f)
    with open(report_r2_path, "r", encoding="utf-8") as f:
        r2 = json.load(f)

    # Compute ledger spend
    total_spend = 0.0
    with open(ledger_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                total_spend += entry.get("usd", 0.0)

    # Band statistics
    band_sources = band["sources"]
    min_pass = band["pass_rate"]["min"]
    max_pass = band["pass_rate"]["max"]
    pass_thresh = band["tolerance_rule"]["min_pass_threshold"]
    fail_thresh = band["tolerance_rule"]["fail_pass_threshold"]
    manifest_sha = band.get("manifest_sha256", "e79897ea42129ccd4fe38ce3e0a8f7ec0b321aa8be0f7a3899036f5148dcb06f")
    manifest_prefix = manifest_sha[:10]

    # Baseline sources
    baselines = [
        ("p06_k1", "P6 pass^k trial 1 (R2)", band_sources["p06_k1"]["pass_rate"]),
        ("p06_k2", "P6 pass^k trial 2 (R2)", band_sources["p06_k2"]["pass_rate"]),
        ("p06_k3", "P6 pass^k trial 3 (R2)", band_sources["p06_k3"]["pass_rate"]),
        ("p12_a", "P12 attribution arm A (R2)", band_sources["p12_a"]["pass_rate"]),
        ("p11_r2_fresh", "P11 live run (R2 fresh)", band_sources["p11_r2_fresh"]["pass_rate"]),
    ]

    # Candidate runs
    candidates = [
        {
            "name": "R1 qwen3.7-flash",
            "label": f"R1 qwen3.7-flash — FAIL (malformed {r1['metrics']['malformed_count']}/30)",
            "pass_count": r1["metrics"]["pass_count"],
            "pass_rate": r1["metrics"]["pass_rate"],
            "verdict": r1["verdict"],
            "spend": r1["spend"]["total_usd"],
            "ci": wilson_interval(r1["metrics"]["pass_count"], 30, confidence=0.95),
        },
        {
            "name": "R4 gpt-5.6-luna",
            "label": "R4 gpt-5.6-luna — FAIL (step-cap 18/30)",
            "pass_count": r4["metrics"]["pass_count"],
            "pass_rate": r4["metrics"]["pass_rate"],
            "verdict": r4["verdict"],
            "spend": r4["spend"]["total_usd"],
            "ci": wilson_interval(r4["metrics"]["pass_count"], 30, confidence=0.95),
        },
        {
            "name": "R2 glm-5.3-flash fresh",
            "label": "R2 glm-5.3-flash fresh — PASS",
            "pass_count": r2["metrics"]["pass_count"],
            "pass_rate": r2["metrics"]["pass_rate"],
            "verdict": r2["verdict"],
            "spend": r2["spend"]["total_usd"],
            "ci": wilson_interval(r2["metrics"]["pass_count"], 30, confidence=0.95),
        },
    ]

    width = 1400
    height = 760

    # Colors (Okabe-Ito / scientific palette)
    c_pass = "#009E73"     # Bluish green
    c_fail = "#D55E00"     # Vermilion
    c_base = "#0072B2"     # Blue for baselines
    c_band = "#e0f2fe"     # Soft sky blue for band
    c_band_stroke = "#bae6fd"
    c_warn = "#fef08a"     # Yellow tint for warn zone
    c_text = "#1e293b"     # Slate 800
    c_muted = "#64748b"    # Slate 500
    c_grid = "#f1f5f9"     # Slate 100
    c_axis = "#94a3b8"     # Slate 400

    x0 = 300.0
    plot_w = 750.0
    y_top = 145.0
    y_bottom = 635.0

    def to_x(val: float) -> float:
        return x0 + val * plot_w

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">')
    svg.append(f'  <rect width="{width}" height="{height}" fill="#ffffff"/>')

    # Title block
    svg.append('  <!-- Header -->')
    svg.append(f'  <text x="50" y="45" font-family="Helvetica, Arial, sans-serif" font-size="20" font-weight="700" fill="{c_text}">Project P11: Release Gate Evaluation Against Tolerance Band</text>')
    svg.append(f'  <text x="50" y="72" font-family="Helvetica, Arial, sans-serif" font-size="13" fill="{c_muted}">Empirical pass rates on n=30 golden scenarios, 5-source R2 variance band [0.6000, 0.8667], and candidate gates</text>')

    # Shaded band region [min_pass, max_pass]
    band_x_left = to_x(min_pass)
    band_x_right = to_x(max_pass)
    band_w = band_x_right - band_x_left
    svg.append(f'  <!-- Shaded Band Region -->')
    svg.append(f'  <rect x="{band_x_left:.1f}" y="{y_top}" width="{band_w:.1f}" height="{y_bottom - y_top}" fill="{c_band}" stroke="{c_band_stroke}" stroke-width="1"/>')
    # Band label stacked on line 2 above shaded region
    svg.append(f'  <text x="{band_x_left + band_w / 2:.1f}" y="125" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="600" fill="{c_base}" text-anchor="middle">Observed R2 band [{min_pass:.4f}, {max_pass:.4f}]</text>')

    # Grid vertical lines
    for i in range(11):
        tick_val = i / 10.0
        tx = to_x(tick_val)
        svg.append(f'  <line x1="{tx:.1f}" y1="{y_top}" x2="{tx:.1f}" y2="{y_bottom}" stroke="{c_grid}" stroke-width="1"/>')
        svg.append(f'  <text x="{tx:.1f}" y="{y_bottom + 18}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_muted}" text-anchor="middle">{tick_val:.1f}</text>')

    # Threshold lines
    x_fail = to_x(fail_thresh)
    x_pass = to_x(pass_thresh)

    # Fail threshold vertical line & label on Line 1 (y=105)
    svg.append(f'  <line x1="{x_fail:.1f}" y1="{y_top}" x2="{x_fail:.1f}" y2="{y_bottom}" stroke="{c_fail}" stroke-width="2" stroke-dasharray="6,4"/>')
    svg.append(f'  <text x="{x_fail - 6:.1f}" y="105" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="600" fill="{c_fail}" text-anchor="end">FAIL Threshold (&lt; {fail_thresh:.4f})</text>')

    # Pass threshold vertical line & label on Line 1 (y=105)
    svg.append(f'  <line x1="{x_pass:.1f}" y1="{y_top}" x2="{x_pass:.1f}" y2="{y_bottom}" stroke="{c_pass}" stroke-width="2" stroke-dasharray="6,4"/>')
    svg.append(f'  <text x="{x_pass + 6:.1f}" y="105" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="600" fill="{c_pass}" text-anchor="start">PASS Threshold (&#x2265; {pass_thresh:.4f})</text>')

    # X-axis line
    svg.append(f'  <line x1="{x0}" y1="{y_bottom}" x2="{x0 + plot_w}" y2="{y_bottom}" stroke="{c_axis}" stroke-width="1.5"/>')
    svg.append(f'  <text x="{x0 + plot_w / 2:.1f}" y="{y_bottom + 42}" font-family="Helvetica, Arial, sans-serif" font-size="13" font-weight="600" fill="{c_text}" text-anchor="middle">Pass Rate on Golden Scenario Set (n=30)</text>')

    # Group 1: 5 Baseline Rows
    svg.append('  <!-- Baseline Header -->')
    svg.append(f'  <text x="50" y="135" font-family="Helvetica, Arial, sans-serif" font-size="12" font-weight="700" fill="{c_muted}">R2 baseline sources</text>')

    base_y_start = 175.0
    base_spacing = 40.0
    for idx, (b_id, b_label, b_val) in enumerate(baselines):
        by = base_y_start + idx * base_spacing
        bx = to_x(b_val)
        svg.append(f'  <!-- Baseline {b_id} -->')
        svg.append(f'  <text x="{x0 - 15}" y="{by + 4}" font-family="Helvetica, Arial, sans-serif" font-size="12" fill="{c_text}" text-anchor="end">{b_label}</text>')
        # Reference guide line
        svg.append(f'  <line x1="{x0}" y1="{by}" x2="{x0 + plot_w}" y2="{by}" stroke="{c_grid}" stroke-width="1" stroke-dasharray="2,4"/>')
        # Hollow marker
        svg.append(f'  <circle cx="{bx:.1f}" cy="{by:.1f}" r="7" fill="#ffffff" stroke="{c_base}" stroke-width="2.5"/>')
        # Value label
        svg.append(f'  <text x="{bx + 12:.1f}" y="{by + 4}" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="600" fill="{c_base}">{b_val:.4f} ({int(round(b_val * 30))}/30)</text>')

    # Divider between baselines and candidates
    div_y = 370.0
    svg.append(f'  <line x1="50" y1="{div_y}" x2="{x0 + plot_w}" y2="{div_y}" stroke="{c_axis}" stroke-width="1" stroke-dasharray="4,4"/>')
    svg.append(f'  <text x="50" y="{div_y + 24}" font-family="Helvetica, Arial, sans-serif" font-size="12" font-weight="700" fill="{c_muted}">Candidate gate runs (Wilson 95% CI)</text>')

    # Group 2: 3 Candidate Rows
    cand_y_start = 440.0
    cand_spacing = 70.0
    for idx, cand in enumerate(candidates):
        cy = cand_y_start + idx * cand_spacing
        cx = to_x(cand["pass_rate"])
        ci_low_x = to_x(cand["ci"][0])
        ci_high_x = to_x(cand["ci"][1])
        c_color = c_pass if cand["verdict"] == "PASS" else c_fail

        svg.append(f'  <!-- Candidate {cand["name"]} -->')
        svg.append(f'  <text x="{x0 - 15}" y="{cy + 4}" font-family="Helvetica, Arial, sans-serif" font-size="12" font-weight="600" fill="{c_text}" text-anchor="end">{cand["label"]}</text>')
        # Guide line
        svg.append(f'  <line x1="{x0}" y1="{cy}" x2="{x0 + plot_w}" y2="{cy}" stroke="{c_grid}" stroke-width="1" stroke-dasharray="2,4"/>')
        # Wilson whisker line
        svg.append(f'  <line x1="{ci_low_x:.1f}" y1="{cy}" x2="{ci_high_x:.1f}" y2="{cy}" stroke="{c_color}" stroke-width="2.5"/>')
        # Whisker caps
        svg.append(f'  <line x1="{ci_low_x:.1f}" y1="{cy - 6}" x2="{ci_low_x:.1f}" y2="{cy + 6}" stroke="{c_color}" stroke-width="2.5"/>')
        svg.append(f'  <line x1="{ci_high_x:.1f}" y1="{cy - 6}" x2="{ci_high_x:.1f}" y2="{cy + 6}" stroke="{c_color}" stroke-width="2.5"/>')
        # Filled point marker
        svg.append(f'  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="8" fill="{c_color}" stroke="#ffffff" stroke-width="2"/>')
        # Value & CI callout label (to the right of whisker, well within 350px right margin)
        ci_text = f"{cand['pass_rate']:.4f} ({cand['pass_count']}/30) [95% CI: {cand['ci'][0]:.2f}, {cand['ci'][1]:.2f}] &#x2022; ${cand['spend']:.4f}"
        svg.append(f'  <text x="{ci_high_x + 12:.1f}" y="{cy + 4}" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="600" fill="{c_color}">{ci_text}</text>')

    # Footer
    svg.append('  <!-- Footer -->')
    footer_text = (
        f"Golden manifest sha: {manifest_prefix}... | Rule: PASS if pass &#x2265; {pass_thresh:.4f} &amp; malformed &#x2264; 0.0333; "
        f"FAIL if pass &lt; {fail_thresh:.4f}; else WARN | Gate sweep spend: ${total_spend:.4f} USD ($5.00 cap)"
    )
    svg.append(f'  <text x="50" y="725" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_muted}">{footer_text}</text>')
    svg.append('</svg>')

    svg_content = "\n".join(svg)

    # Validate XML
    try:
        ET.fromstring(svg_content)
    except Exception as e:
        raise ValueError(f"Generated SVG XML is invalid: {e}")

    output_svg.write_text(svg_content, encoding="utf-8")
    print(f"Generated valid SVG: {output_svg} ({output_svg.stat().st_size} bytes)")

    # Render 2x PNG via headless Chrome
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    cmd_png = [
        chrome_path,
        "--headless",
        "--disable-gpu",
        "--force-device-scale-factor=2",
        f"--screenshot={output_png.resolve()}",
        f"--window-size={width},{height}",
        output_svg.resolve().as_uri(),
    ]
    res_png = subprocess.run(cmd_png, capture_output=True, timeout=20)
    if res_png.returncode != 0:
        raise RuntimeError(f"Chrome PNG generation failed: {res_png.stderr.decode('utf-8', errors='ignore')}")
    print(f"Generated 2x PNG: {output_png} ({output_png.stat().st_size} bytes)")

    # Render 1-page PDF via headless Chrome
    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@page {{ size: {width}px {height}px; margin: 0; }}
html, body {{ margin: 0; padding: 0; width: {width}px; height: {height}px; overflow: hidden; }}
svg {{ display: block; width: {width}px; height: {height}px; }}
</style>
</head>
<body>
{svg_content}
</body>
</html>"""
    tmp_html = output_svg.parent / f"_temp_{output_svg.stem}.html"
    try:
        tmp_html.write_text(html_content, encoding="utf-8")
        cmd_pdf = [
            chrome_path,
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={output_pdf.resolve()}",
            tmp_html.resolve().as_uri(),
        ]
        res_pdf = subprocess.run(cmd_pdf, capture_output=True, timeout=20)
        if res_pdf.returncode != 0:
            raise RuntimeError(f"Chrome PDF generation failed: {res_pdf.stderr.decode('utf-8', errors='ignore')}")
        pdf_bytes = output_pdf.read_bytes()
        if not pdf_bytes.startswith(b"%PDF"):
            raise ValueError(f"Generated file {output_pdf} does not start with %PDF")
        print(f"Generated 1-page PDF: {output_pdf} ({len(pdf_bytes)} bytes)")
    finally:
        if tmp_html.exists():
            tmp_html.unlink()


def main() -> None:
    band_path = BASE_DIR / "band.json"
    r1_path = BASE_DIR / "report_R1.json"
    r4_path = BASE_DIR / "report_R4.json"
    r2_path = BASE_DIR / "report_R2.json"
    ledger_path = BASE_DIR / "ledger.jsonl"

    out_svg = BASE_DIR / "figure.svg"
    out_png = BASE_DIR / "figure.png"
    out_pdf = BASE_DIR / "figure.pdf"

    generate_figure(band_path, r1_path, r4_path, r2_path, ledger_path, out_svg, out_png, out_pdf)


if __name__ == "__main__":
    main()
