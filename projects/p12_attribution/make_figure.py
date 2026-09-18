"""Generate publication-standard figure for Project P12: Failure Attribution."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET


def generate_figure(
    r2_path: Path,
    r4_path: Path,
    output_svg: Path,
    output_png: Path,
    output_pdf: Path,
) -> None:
    with open(r2_path, "r", encoding="utf-8") as f:
        r2 = json.load(f)
    with open(r4_path, "r", encoding="utf-8") as f:
        r4 = json.load(f)

    # Dynamic numbers read directly from JSON
    r2_counts = r2["as_run"]["counts"]
    r2_n = r2["n"]
    r2_both_pass = r2_counts["both_pass"]
    r2_retriever_owned = r2_counts["retriever_owned"]
    r2_generator_owned = r2_counts["generator_owned"]
    r2_reverse = r2_counts["reverse"]
    r2_failures_a = r2_counts["n_failures_a"]
    r2_share = r2["as_run"]["retriever_share"]
    r2_ci = r2["as_run"]["wilson_ci"]
    r2_verdict = r2["h8_verdict"]

    r4_counts = r4["as_run"]["counts"]
    r4_n = r4["n"]
    r4_both_pass = r4_counts["both_pass"]
    r4_retriever_owned = r4_counts["retriever_owned"]
    r4_generator_owned = r4_counts["generator_owned"]
    r4_reverse = r4_counts["reverse"]
    r4_failures_a = r4_counts["n_failures_a"]
    r4_share = r4["as_run"]["retriever_share"]
    r4_ci = r4["as_run"]["wilson_ci"]
    r4_verdict = r4["h8_verdict"]

    width = 1600
    height = 700

    # Okabe-Ito / scientific palette
    c_both = "#009E73"     # Bluish green
    c_retr = "#0072B2"     # Blue
    c_gen = "#D55E00"      # Vermilion
    c_rev = "#E69F00"      # Amber
    c_text = "#1e293b"     # Slate 800
    c_muted = "#64748b"    # Slate 500
    c_grid = "#f1f5f9"     # Slate 100
    c_axis = "#94a3b8"     # Slate 400

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">')
    svg.append(f'  <rect width="{width}" height="{height}" fill="#ffffff"/>')

    # Main title
    svg.append('  <!-- Title -->')
    svg.append(f'  <text x="50" y="45" font-family="Helvetica, Arial, sans-serif" font-size="18" font-weight="600" fill="{c_text}">Failure attribution and oracle retrieval ablation across model rungs</text>')

    # -------------------------------------------------------------
    # PANEL (a): Paired outcomes per rung
    # -------------------------------------------------------------
    svg.append('  <!-- Panel (a) -->')
    svg.append(f'  <text x="50" y="85" font-family="Helvetica, Arial, sans-serif" font-size="14" font-weight="600" fill="{c_text}">(a) Paired outcomes per rung</text>')

    # Legend for Panel (a)
    leg_y = 115
    svg.append(f'  <rect x="50" y="{leg_y}" width="13" height="13" fill="{c_both}"/>')
    svg.append(f'  <text x="68" y="{leg_y + 11}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_text}">Both pass</text>')

    svg.append(f'  <rect x="165" y="{leg_y}" width="13" height="13" fill="{c_retr}"/>')
    svg.append(f'  <text x="183" y="{leg_y + 11}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_text}">Retriever-owned</text>')

    svg.append(f'  <rect x="315" y="{leg_y}" width="13" height="13" fill="{c_gen}"/>')
    svg.append(f'  <text x="333" y="{leg_y + 11}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_text}">Generator-owned</text>')

    svg.append(f'  <rect x="465" y="{leg_y}" width="13" height="13" fill="{c_rev}"/>')
    svg.append(f'  <text x="483" y="{leg_y + 11}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_text}">Reverse</text>')

    # Grid and x-axis for Panel (a)
    bar_x0 = 190.0
    bar_w = 560.0
    bar_h = 46.0

    ticks_a = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    for t in ticks_a:
        tx = bar_x0 + t * bar_w
        svg.append(f'  <line x1="{tx:.1f}" y1="160" x2="{tx:.1f}" y2="480" stroke="{c_grid}" stroke-width="1"/>')
        svg.append(f'  <text x="{tx:.1f}" y="498" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_muted}" text-anchor="middle">{int(t * 100)}%</text>')

    svg.append(f'  <line x1="{bar_x0}" y1="480" x2="{bar_x0 + bar_w}" y2="480" stroke="{c_axis}" stroke-width="1"/>')
    svg.append(f'  <text x="{bar_x0 + bar_w / 2:.1f}" y="526" font-family="Helvetica, Arial, sans-serif" font-size="12" fill="{c_muted}" text-anchor="middle">Share of paired scenarios</text>')

    # R2 Stacked Bar
    r2_y = 220.0
    svg.append(f'  <text x="{bar_x0 - 15}" y="{r2_y + 20:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="12" font-weight="600" fill="{c_text}" text-anchor="end">R2: GLM 5.3 Flash</text>')
    svg.append(f'  <text x="{bar_x0 - 15}" y="{r2_y + 36:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_muted}" text-anchor="end">(n={r2_n})</text>')

    w_both_r2 = (r2_both_pass / r2_n) * bar_w
    w_retr_r2 = (r2_retriever_owned / r2_n) * bar_w
    w_rev_r2 = (r2_reverse / r2_n) * bar_w
    w_gen_r2 = (r2_generator_owned / r2_n) * bar_w

    cur_x = bar_x0
    # Both pass
    svg.append(f'  <rect x="{cur_x:.1f}" y="{r2_y}" width="{w_both_r2:.1f}" height="{bar_h}" fill="{c_both}"/>')
    svg.append(f'  <text x="{cur_x + w_both_r2 / 2:.1f}" y="{r2_y + 28}" font-family="Helvetica, Arial, sans-serif" font-size="12" font-weight="600" fill="#ffffff" text-anchor="middle">{r2_both_pass} ({r2_both_pass / r2_n * 100:.1f}%)</text>')
    cur_x += w_both_r2

    # Retriever owned
    svg.append(f'  <rect x="{cur_x:.1f}" y="{r2_y}" width="{w_retr_r2:.1f}" height="{bar_h}" fill="{c_retr}"/>')
    svg.append(f'  <text x="{cur_x + w_retr_r2 / 2:.1f}" y="{r2_y + 28}" font-family="Helvetica, Arial, sans-serif" font-size="12" font-weight="600" fill="#ffffff" text-anchor="middle">{r2_retriever_owned} ({r2_retriever_owned / r2_n * 100:.1f}%)</text>')
    cur_x += w_retr_r2

    # Reverse
    svg.append(f'  <rect x="{cur_x:.1f}" y="{r2_y}" width="{w_rev_r2:.1f}" height="{bar_h}" fill="{c_rev}"/>')
    # Leader line above for reverse
    rev_mid = cur_x + w_rev_r2 / 2
    svg.append(f'  <polyline points="{rev_mid:.1f},{r2_y} {rev_mid - 15:.1f},{r2_y - 25} {rev_mid - 45:.1f},{r2_y - 25}" fill="none" stroke="{c_axis}" stroke-width="1"/>')
    svg.append(f'  <text x="{rev_mid - 50:.1f}" y="{r2_y - 21}" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="600" fill="{c_rev}" text-anchor="end">reverse: {r2_reverse} ({r2_reverse / r2_n * 100:.1f}%)</text>')
    cur_x += w_rev_r2

    # Generator owned
    svg.append(f'  <rect x="{cur_x:.1f}" y="{r2_y}" width="{w_gen_r2:.1f}" height="{bar_h}" fill="{c_gen}"/>')
    # Leader line below for generator owned
    gen_mid = cur_x + w_gen_r2 / 2
    svg.append(f'  <polyline points="{gen_mid:.1f},{r2_y + bar_h} {gen_mid + 15:.1f},{r2_y + bar_h + 25} {gen_mid + 45:.1f},{r2_y + bar_h + 25}" fill="none" stroke="{c_axis}" stroke-width="1"/>')
    svg.append(f'  <text x="{gen_mid + 50:.1f}" y="{r2_y + bar_h + 29}" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="600" fill="{c_gen}" text-anchor="start">generator-owned: {r2_generator_owned} ({r2_generator_owned / r2_n * 100:.1f}%)</text>')

    # R4 Stacked Bar
    r4_y = 370.0
    svg.append(f'  <text x="{bar_x0 - 15}" y="{r4_y + 20:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="12" font-weight="600" fill="{c_text}" text-anchor="end">R4: GPT 5.6 Luna</text>')
    svg.append(f'  <text x="{bar_x0 - 15}" y="{r4_y + 36:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_muted}" text-anchor="end">(pilot, n={r4_n})</text>')

    w_both_r4 = (r4_both_pass / r4_n) * bar_w
    w_retr_r4 = (r4_retriever_owned / r4_n) * bar_w

    cur_x = bar_x0
    # Both pass
    svg.append(f'  <rect x="{cur_x:.1f}" y="{r4_y}" width="{w_both_r4:.1f}" height="{bar_h}" fill="{c_both}"/>')
    svg.append(f'  <text x="{cur_x + w_both_r4 / 2:.1f}" y="{r4_y + 28}" font-family="Helvetica, Arial, sans-serif" font-size="12" font-weight="600" fill="#ffffff" text-anchor="middle">{r4_both_pass} ({r4_both_pass / r4_n * 100:.1f}%)</text>')
    cur_x += w_both_r4

    # Retriever owned
    svg.append(f'  <rect x="{cur_x:.1f}" y="{r4_y}" width="{w_retr_r4:.1f}" height="{bar_h}" fill="{c_retr}"/>')
    svg.append(f'  <text x="{cur_x + w_retr_r4 / 2:.1f}" y="{r4_y + 28}" font-family="Helvetica, Arial, sans-serif" font-size="12" font-weight="600" fill="#ffffff" text-anchor="middle">{r4_retriever_owned} ({r4_retriever_owned / r4_n * 100:.1f}%)</text>')
    cur_x += w_retr_r4

    svg.append(f'  <text x="{bar_x0 + bar_w + 12:.1f}" y="{r4_y + 28}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_muted}">gen: {r4_generator_owned}, rev: {r4_reverse}</text>')

    # -------------------------------------------------------------
    # PANEL (b): Retriever share of arm-A failures
    # -------------------------------------------------------------
    svg.append('  <!-- Panel (b) -->')
    svg.append(f'  <text x="890" y="85" font-family="Helvetica, Arial, sans-serif" font-size="14" font-weight="600" fill="{c_text}">(b) Retriever share of arm-A failures</text>')

    b_x0 = 1000.0
    b_w = 440.0
    ticks_b = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

    for t in ticks_b:
        tx = b_x0 + t * b_w
        svg.append(f'  <line x1="{tx:.1f}" y1="160" x2="{tx:.1f}" y2="480" stroke="{c_grid}" stroke-width="1"/>')
        svg.append(f'  <text x="{tx:.1f}" y="498" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_muted}" text-anchor="middle">{t:.1f}</text>')

    svg.append(f'  <line x1="{b_x0}" y1="480" x2="{b_x0 + b_w}" y2="480" stroke="{c_axis}" stroke-width="1"/>')
    svg.append(f'  <text x="{b_x0 + b_w / 2:.1f}" y="526" font-family="Helvetica, Arial, sans-serif" font-size="12" fill="{c_muted}" text-anchor="middle">Retriever share (retriever-owned / arm-A failures)</text>')

    # Horizontal guides
    svg.append(f'  <line x1="{b_x0}" y1="243" x2="{b_x0 + b_w}" y2="243" stroke="{c_grid}" stroke-width="1"/>')
    svg.append(f'  <line x1="{b_x0}" y1="393" x2="{b_x0 + b_w}" y2="393" stroke="{c_grid}" stroke-width="1"/>')

    # H8 Threshold dashed line at 0.5
    h8_x = b_x0 + 0.5 * b_w
    svg.append(f'  <line x1="{h8_x:.1f}" y1="150" x2="{h8_x:.1f}" y2="480" stroke="#dc2626" stroke-width="1.5" stroke-dasharray="5,4"/>')
    svg.append(f'  <text x="{h8_x:.1f}" y="142" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="600" fill="#dc2626" text-anchor="middle">H8 threshold (0.50)</text>')

    # Row 1: R2
    svg.append(f'  <text x="{b_x0 - 15}" y="238" font-family="Helvetica, Arial, sans-serif" font-size="12" font-weight="600" fill="{c_text}" text-anchor="end">R2: GLM 5.3 Flash</text>')
    svg.append(f'  <text x="{b_x0 - 15}" y="254" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_muted}" text-anchor="end">{r2_retriever_owned}/{r2_failures_a} failures</text>')

    pt_r2 = b_x0 + r2_share * b_w
    ci_low_r2 = b_x0 + r2_ci[0] * b_w
    ci_high_r2 = b_x0 + r2_ci[1] * b_w

    svg.append(f'  <line x1="{ci_low_r2:.1f}" y1="243" x2="{ci_high_r2:.1f}" y2="243" stroke="{c_text}" stroke-width="1.5"/>')
    svg.append(f'  <line x1="{ci_low_r2:.1f}" y1="236" x2="{ci_low_r2:.1f}" y2="250" stroke="{c_text}" stroke-width="1.5"/>')
    svg.append(f'  <line x1="{ci_high_r2:.1f}" y1="236" x2="{ci_high_r2:.1f}" y2="250" stroke="{c_text}" stroke-width="1.5"/>')
    svg.append(f'  <circle cx="{pt_r2:.1f}" cy="243" r="5.5" fill="{c_retr}" stroke="{c_text}" stroke-width="1.5"/>')

    svg.append(f'  <text x="{ci_high_r2 + 14:.1f}" y="239" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="600" fill="{c_text}">{r2_share:.3f} [{r2_ci[0]:.3f}, {r2_ci[1]:.3f}]</text>')
    svg.append(f'  <text x="{ci_high_r2 + 14:.1f}" y="255" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="600" fill="#059669">H8 {r2_verdict}</text>')

    # Row 2: R4
    svg.append(f'  <text x="{b_x0 - 15}" y="388" font-family="Helvetica, Arial, sans-serif" font-size="12" font-weight="600" fill="{c_text}" text-anchor="end">R4: GPT 5.6 Luna (pilot)</text>')
    svg.append(f'  <text x="{b_x0 - 15}" y="404" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_muted}" text-anchor="end">{r4_retriever_owned}/{r4_failures_a} failures</text>')

    pt_r4 = b_x0 + r4_share * b_w
    ci_low_r4 = b_x0 + r4_ci[0] * b_w
    ci_high_r4 = b_x0 + r4_ci[1] * b_w

    svg.append(f'  <line x1="{ci_low_r4:.1f}" y1="393" x2="{ci_high_r4:.1f}" y2="393" stroke="{c_text}" stroke-width="1.5"/>')
    svg.append(f'  <line x1="{ci_low_r4:.1f}" y1="386" x2="{ci_low_r4:.1f}" y2="400" stroke="{c_text}" stroke-width="1.5"/>')
    svg.append(f'  <line x1="{ci_high_r4:.1f}" y1="386" x2="{ci_high_r4:.1f}" y2="400" stroke="{c_text}" stroke-width="1.5"/>')
    svg.append(f'  <circle cx="{pt_r4:.1f}" cy="393" r="5.5" fill="{c_retr}" stroke="{c_text}" stroke-width="1.5"/>')

    svg.append(f'  <text x="{ci_high_r4 + 14:.1f}" y="389" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="600" fill="{c_text}">{r4_share:.3f} [{r4_ci[0]:.3f}, {r4_ci[1]:.3f}]</text>')
    svg.append(f'  <text x="{ci_high_r4 + 14:.1f}" y="405" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="600" fill="{c_muted}">{r4_verdict} (pilot)</text>')

    # Footer
    svg.append('  <!-- Footer -->')
    svg.append(f'  <line x1="50" y1="655" x2="{width - 50}" y2="655" stroke="#e2e8f0" stroke-width="1"/>')
    svg.append(f'  <text x="50" y="675" font-family="Helvetica, Arial, sans-serif" font-size="11.5" fill="{c_muted}">FAULTLINE P12 · P6 reserved hard pool · arm B = oracle retrieval (traversal_sources) · Wilson 95% CIs · McNemar exact p = 1.94e-6 (R2)</text>')

    svg.append('</svg>')

    svg_content = "\n".join(svg)

    # Validate XML
    ET.fromstring(svg_content)

    output_svg.write_text(svg_content, encoding="utf-8")
    print(f"Generated valid SVG: {output_svg}")

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
    base = Path("projects/p12_attribution")
    r2_path = base / "results_R2.json"
    r4_path = base / "results_R4.json"
    output_svg = base / "figure.svg"
    output_png = base / "figure.png"
    output_pdf = base / "figure.pdf"

    generate_figure(r2_path, r4_path, output_svg, output_png, output_pdf)


if __name__ == "__main__":
    main()
