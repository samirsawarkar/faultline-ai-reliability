"""Generate publication-standard figure for Project P9: Redteam Regression."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET


def generate_figure(
    results_path: Path,
    output_svg: Path,
    output_png: Path,
    output_pdf: Path,
) -> None:
    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    per_cat = data["per_category"]
    pooled = data["pooled"]

    width = 1600
    height = 820

    # Okabe-Ito / scientific palette
    c_arma = "#D55E00"      # Vermilion for Arm A
    c_armb = "#0072B2"      # Blue for Arm B
    c_mention = "#CC79A7"   # Purple-Pink for Mentioned
    c_text = "#1e293b"      # Slate 800
    c_muted = "#64748b"     # Slate 500
    c_grid = "#f1f5f9"      # Slate 100
    c_axis = "#94a3b8"      # Slate 400
    c_div = "#e2e8f0"       # Slate 200

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">')
    svg.append(f'  <rect width="{width}" height="{height}" fill="#ffffff"/>')

    # Main title (one title line)
    svg.append('  <!-- Title -->')
    svg.append(f'  <text x="50" y="45" font-family="Helvetica, Arial, sans-serif" font-size="18" font-weight="600" fill="{c_text}">Adversarial prompt injection attack success and surface penetration across threat categories</text>')

    # -------------------------------------------------------------
    # PANEL (a): Attack success rate (ASR) by threat category
    # -------------------------------------------------------------
    p_a_x = 50
    p_a_y = 85
    plot_a_x0 = 220.0
    plot_a_w = 460.0
    max_scale_a = 0.50

    svg.append('  <!-- Panel (a) -->')
    svg.append(f'  <text x="{p_a_x}" y="{p_a_y}" font-family="Helvetica, Arial, sans-serif" font-size="14" font-weight="600" fill="{c_text}">(a) Attack success rate (ASR) by threat category</text>')

    # Legend for Panel (a)
    leg_y = 115
    svg.append(f'  <rect x="{p_a_x}" y="{leg_y}" width="13" height="13" fill="{c_arma}"/>')
    svg.append(f'  <text x="{p_a_x + 18}" y="{leg_y + 11}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_text}">Arm A (baseline)</text>')

    svg.append(f'  <rect x="{p_a_x + 160}" y="{leg_y}" width="13" height="13" fill="{c_armb}"/>')
    svg.append(f'  <text x="{p_a_x + 178}" y="{leg_y + 11}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_text}">Arm B (runtime policy)</text>')

    # Grid ticks for Panel (a)
    ticks_a = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
    grid_top = 150
    grid_bottom = 680
    for t in ticks_a:
        tx = plot_a_x0 + (t / max_scale_a) * plot_a_w
        svg.append(f'  <line x1="{tx:.1f}" y1="{grid_top}" x2="{tx:.1f}" y2="{grid_bottom}" stroke="{c_grid}" stroke-width="1"/>')
        svg.append(f'  <text x="{tx:.1f}" y="{grid_bottom + 18}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_muted}" text-anchor="middle">{int(t * 100)}%</text>')

    svg.append(f'  <line x1="{plot_a_x0}" y1="{grid_bottom}" x2="{plot_a_x0 + plot_a_w}" y2="{grid_bottom}" stroke="{c_axis}" stroke-width="1"/>')
    svg.append(f'  <text x="{plot_a_x0 + plot_a_w / 2:.1f}" y="{grid_bottom + 38}" font-family="Helvetica, Arial, sans-serif" font-size="12" fill="{c_muted}" text-anchor="middle">Attack success rate (ASR)</text>')

    # Group 1: Structural categories
    struct_cats = [
        ("budget_loop", "Budget loop"),
        ("query_dump", "Query dump"),
        ("tool_exfil_path", "Tool exfil path"),
        ("unlisted_tool", "Unlisted tool"),
    ]

    cur_y = 150
    svg.append(f'  <text x="50" y="{cur_y}" font-family="Helvetica, Arial, sans-serif" font-size="11" font-style="italic" fill="{c_muted}">zero attempted in arm A; blocked by policy in arm B</text>')
    cur_y += 18

    for cat_key, cat_label in struct_cats:
        cdata = per_cat[cat_key]
        a_asr = cdata["A"]["asr"]
        a_ci = cdata["A"]["wilson_ci"]
        b_asr = cdata["B"]["asr"]
        b_ci = cdata["B"]["wilson_ci"]

        svg.append(f'  <text x="{plot_a_x0 - 15}" y="{cur_y + 13}" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="500" fill="{c_text}" text-anchor="end">{cat_label}</text>')

        # Arm A bar
        w_a = (a_asr / max_scale_a) * plot_a_w
        svg.append(f'  <rect x="{plot_a_x0}" y="{cur_y + 2}" width="{max(w_a, 1.5):.1f}" height="7" fill="{c_arma}"/>')
        # Whiskers
        ci_a0 = plot_a_x0 + (a_ci[0] / max_scale_a) * plot_a_w
        ci_a1 = plot_a_x0 + (a_ci[1] / max_scale_a) * plot_a_w
        svg.append(f'  <line x1="{ci_a0:.1f}" y1="{cur_y + 5.5}" x2="{ci_a1:.1f}" y2="{cur_y + 5.5}" stroke="{c_text}" stroke-width="1.2"/>')
        svg.append(f'  <line x1="{ci_a0:.1f}" y1="{cur_y + 3}" x2="{ci_a0:.1f}" y2="{cur_y + 8}" stroke="{c_text}" stroke-width="1.2"/>')
        svg.append(f'  <line x1="{ci_a1:.1f}" y1="{cur_y + 3}" x2="{ci_a1:.1f}" y2="{cur_y + 8}" stroke="{c_text}" stroke-width="1.2"/>')

        # Arm B bar
        w_b = (b_asr / max_scale_a) * plot_a_w
        svg.append(f'  <rect x="{plot_a_x0}" y="{cur_y + 12}" width="{max(w_b, 1.5):.1f}" height="7" fill="{c_armb}"/>')
        ci_b0 = plot_a_x0 + (b_ci[0] / max_scale_a) * plot_a_w
        ci_b1 = plot_a_x0 + (b_ci[1] / max_scale_a) * plot_a_w
        svg.append(f'  <line x1="{ci_b0:.1f}" y1="{cur_y + 15.5}" x2="{ci_b1:.1f}" y2="{cur_y + 15.5}" stroke="{c_text}" stroke-width="1.2"/>')
        svg.append(f'  <line x1="{ci_b0:.1f}" y1="{cur_y + 13}" x2="{ci_b0:.1f}" y2="{cur_y + 18}" stroke="{c_text}" stroke-width="1.2"/>')
        svg.append(f'  <line x1="{ci_b1:.1f}" y1="{cur_y + 13}" x2="{ci_b1:.1f}" y2="{cur_y + 18}" stroke="{c_text}" stroke-width="1.2"/>')

        lbl_x = plot_a_x0 + (max(a_ci[1], b_ci[1]) / max_scale_a) * plot_a_w + 10
        svg.append(f'  <text x="{lbl_x:.1f}" y="{cur_y + 8}" font-family="Helvetica, Arial, sans-serif" font-size="10" fill="{c_arma}">A: {a_asr*100:.1f}% [{a_ci[0]*100:.1f}%, {a_ci[1]*100:.1f}%]</text>')
        svg.append(f'  <text x="{lbl_x:.1f}" y="{cur_y + 18}" font-family="Helvetica, Arial, sans-serif" font-size="10" fill="{c_armb}">B: {b_asr*100:.1f}% [{b_ci[0]*100:.1f}%, {b_ci[1]*100:.1f}%]</text>')

        cur_y += 36

    # Group 2: Semantic categories
    cur_y += 8
    svg.append(f'  <line x1="{plot_a_x0 - 150}" y1="{cur_y - 4}" x2="{plot_a_x0 + plot_a_w}" y2="{cur_y - 4}" stroke="{c_div}" stroke-width="1" stroke-dasharray="2,2"/>')
    cur_y += 8

    semantic_cats = [
        ("abstain_dos", "Abstain DoS"),
        ("json_breakout", "JSON breakout"),
        ("role_override", "Role override"),
        ("answer_hijack", "Answer hijack"),
        ("hop_redirect", "Hop redirect"),
        ("citation_forgery", "Citation forgery"),
    ]

    for cat_key, cat_label in semantic_cats:
        cdata = per_cat[cat_key]
        a_asr = cdata["A"]["asr"]
        a_ci = cdata["A"]["wilson_ci"]
        b_asr = cdata["B"]["asr"]
        b_ci = cdata["B"]["wilson_ci"]

        svg.append(f'  <text x="{plot_a_x0 - 15}" y="{cur_y + 13}" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="500" fill="{c_text}" text-anchor="end">{cat_label}</text>')

        w_a = (a_asr / max_scale_a) * plot_a_w
        svg.append(f'  <rect x="{plot_a_x0}" y="{cur_y + 2}" width="{max(w_a, 1.5):.1f}" height="7" fill="{c_arma}"/>')
        ci_a0 = plot_a_x0 + (a_ci[0] / max_scale_a) * plot_a_w
        ci_a1 = plot_a_x0 + (a_ci[1] / max_scale_a) * plot_a_w
        svg.append(f'  <line x1="{ci_a0:.1f}" y1="{cur_y + 5.5}" x2="{ci_a1:.1f}" y2="{cur_y + 5.5}" stroke="{c_text}" stroke-width="1.2"/>')
        svg.append(f'  <line x1="{ci_a0:.1f}" y1="{cur_y + 3}" x2="{ci_a0:.1f}" y2="{cur_y + 8}" stroke="{c_text}" stroke-width="1.2"/>')
        svg.append(f'  <line x1="{ci_a1:.1f}" y1="{cur_y + 3}" x2="{ci_a1:.1f}" y2="{cur_y + 8}" stroke="{c_text}" stroke-width="1.2"/>')

        w_b = (b_asr / max_scale_a) * plot_a_w
        svg.append(f'  <rect x="{plot_a_x0}" y="{cur_y + 12}" width="{max(w_b, 1.5):.1f}" height="7" fill="{c_armb}"/>')
        ci_b0 = plot_a_x0 + (b_ci[0] / max_scale_a) * plot_a_w
        ci_b1 = plot_a_x0 + (b_ci[1] / max_scale_a) * plot_a_w
        svg.append(f'  <line x1="{ci_b0:.1f}" y1="{cur_y + 15.5}" x2="{ci_b1:.1f}" y2="{cur_y + 15.5}" stroke="{c_text}" stroke-width="1.2"/>')
        svg.append(f'  <line x1="{ci_b0:.1f}" y1="{cur_y + 13}" x2="{ci_b0:.1f}" y2="{cur_y + 18}" stroke="{c_text}" stroke-width="1.2"/>')
        svg.append(f'  <line x1="{ci_b1:.1f}" y1="{cur_y + 13}" x2="{ci_b1:.1f}" y2="{cur_y + 18}" stroke="{c_text}" stroke-width="1.2"/>')

        lbl_x = plot_a_x0 + (max(a_ci[1], b_ci[1]) / max_scale_a) * plot_a_w + 10
        svg.append(f'  <text x="{lbl_x:.1f}" y="{cur_y + 8}" font-family="Helvetica, Arial, sans-serif" font-size="10" fill="{c_arma}">A: {a_asr*100:.1f}% [{a_ci[0]*100:.1f}%, {a_ci[1]*100:.1f}%]</text>')
        svg.append(f'  <text x="{lbl_x:.1f}" y="{cur_y + 18}" font-family="Helvetica, Arial, sans-serif" font-size="10" fill="{c_armb}">B: {b_asr*100:.1f}% [{b_ci[0]*100:.1f}%, {b_ci[1]*100:.1f}%]</text>')

        cur_y += 36

    # Group 3: Pooled row at the bottom
    cur_y += 6
    svg.append(f'  <line x1="{plot_a_x0 - 150}" y1="{cur_y - 4}" x2="{plot_a_x0 + plot_a_w}" y2="{cur_y - 4}" stroke="{c_axis}" stroke-width="1"/>')
    cur_y += 6

    p_a_asr = pooled["A"]["asr"]
    p_a_ci = pooled["A"]["wilson_ci"]
    p_b_asr = pooled["B"]["asr"]
    p_b_ci = pooled["B"]["wilson_ci"]

    svg.append(f'  <text x="{plot_a_x0 - 15}" y="{cur_y + 13}" font-family="Helvetica, Arial, sans-serif" font-size="12" font-weight="600" fill="{c_text}" text-anchor="end">Pooled (10 categories)</text>')

    w_p_a = (p_a_asr / max_scale_a) * plot_a_w
    svg.append(f'  <rect x="{plot_a_x0}" y="{cur_y + 2}" width="{max(w_p_a, 1.5):.1f}" height="8" fill="{c_arma}"/>')
    ci_pa0 = plot_a_x0 + (p_a_ci[0] / max_scale_a) * plot_a_w
    ci_pa1 = plot_a_x0 + (p_a_ci[1] / max_scale_a) * plot_a_w
    svg.append(f'  <line x1="{ci_pa0:.1f}" y1="{cur_y + 6}" x2="{ci_pa1:.1f}" y2="{cur_y + 6}" stroke="{c_text}" stroke-width="1.3"/>')
    svg.append(f'  <line x1="{ci_pa0:.1f}" y1="{cur_y + 3}" x2="{ci_pa0:.1f}" y2="{cur_y + 9}" stroke="{c_text}" stroke-width="1.3"/>')
    svg.append(f'  <line x1="{ci_pa1:.1f}" y1="{cur_y + 3}" x2="{ci_pa1:.1f}" y2="{cur_y + 9}" stroke="{c_text}" stroke-width="1.3"/>')

    w_p_b = (p_b_asr / max_scale_a) * plot_a_w
    svg.append(f'  <rect x="{plot_a_x0}" y="{cur_y + 13}" width="{max(w_p_b, 1.5):.1f}" height="8" fill="{c_armb}"/>')
    ci_pb0 = plot_a_x0 + (p_b_ci[0] / max_scale_a) * plot_a_w
    ci_pb1 = plot_a_x0 + (p_b_ci[1] / max_scale_a) * plot_a_w
    svg.append(f'  <line x1="{ci_pb0:.1f}" y1="{cur_y + 17}" x2="{ci_pb1:.1f}" y2="{cur_y + 17}" stroke="{c_text}" stroke-width="1.3"/>')
    svg.append(f'  <line x1="{ci_pb0:.1f}" y1="{cur_y + 14}" x2="{ci_pb0:.1f}" y2="{cur_y + 20}" stroke="{c_text}" stroke-width="1.3"/>')
    svg.append(f'  <line x1="{ci_pb1:.1f}" y1="{cur_y + 14}" x2="{ci_pb1:.1f}" y2="{cur_y + 20}" stroke="{c_text}" stroke-width="1.3"/>')

    lbl_x = plot_a_x0 + (max(p_a_ci[1], p_b_ci[1]) / max_scale_a) * plot_a_w + 10
    svg.append(f'  <text x="{lbl_x:.1f}" y="{cur_y + 9}" font-family="Helvetica, Arial, sans-serif" font-size="10.5" font-weight="600" fill="{c_arma}">A: {p_a_asr*100:.1f}% [{p_a_ci[0]*100:.1f}%, {p_a_ci[1]*100:.1f}%]</text>')
    svg.append(f'  <text x="{lbl_x:.1f}" y="{cur_y + 20}" font-family="Helvetica, Arial, sans-serif" font-size="10.5" font-weight="600" fill="{c_armb}">B: {p_b_asr*100:.1f}% [{p_b_ci[0]*100:.1f}%, {p_b_ci[1]*100:.1f}%]</text>')

    # -------------------------------------------------------------
    # PANEL (b): Surface penetration vs. compromise (semantic categories)
    # -------------------------------------------------------------
    p_b_x = 780
    p_b_y = 85
    plot_b_x0 = 930.0
    plot_b_w = 460.0
    max_scale_b = 1.0

    svg.append('  <!-- Panel (b) -->')
    svg.append(f'  <text x="{p_b_x}" y="{p_b_y}" font-family="Helvetica, Arial, sans-serif" font-size="14" font-weight="600" fill="{c_text}">(b) Surface penetration vs compromise (semantic categories)</text>')

    # Legend for Panel (b)
    svg.append(f'  <rect x="{p_b_x}" y="{leg_y}" width="13" height="13" fill="{c_mention}"/>')
    svg.append(f'  <text x="{p_b_x + 18}" y="{leg_y + 11}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_text}">mentioned injected string</text>')

    svg.append(f'  <rect x="{p_b_x + 190}" y="{leg_y}" width="13" height="13" fill="{c_arma}"/>')
    svg.append(f'  <text x="{p_b_x + 208}" y="{leg_y + 11}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_text}">compromised (arm A)</text>')

    svg.append(f'  <rect x="{p_b_x + 360}" y="{leg_y}" width="13" height="13" fill="{c_armb}"/>')
    svg.append(f'  <text x="{p_b_x + 378}" y="{leg_y + 11}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_text}">compromised (arm B)</text>')

    # Grid ticks for Panel (b)
    ticks_b = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    for t in ticks_b:
        tx = plot_b_x0 + t * plot_b_w
        svg.append(f'  <line x1="{tx:.1f}" y1="{grid_top}" x2="{tx:.1f}" y2="{grid_bottom}" stroke="{c_grid}" stroke-width="1"/>')
        svg.append(f'  <text x="{tx:.1f}" y="{grid_bottom + 18}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_muted}" text-anchor="middle">{int(t * 100)}%</text>')

    svg.append(f'  <line x1="{plot_b_x0}" y1="{grid_bottom}" x2="{plot_b_x0 + plot_b_w}" y2="{grid_bottom}" stroke="{c_axis}" stroke-width="1"/>')
    svg.append(f'  <text x="{plot_b_x0 + plot_b_w / 2:.1f}" y="{grid_bottom + 38}" font-family="Helvetica, Arial, sans-serif" font-size="12" fill="{c_muted}" text-anchor="middle">Share of scenarios</text>')

    cur_by = 175
    row_b_h = 76

    for cat_key, cat_label in semantic_cats:
        cdata = per_cat[cat_key]
        m_a = cdata["A"]["mention_rate"]
        m_b = cdata["B"]["mention_rate"]
        asr_a = cdata["A"]["asr"]
        asr_b = cdata["B"]["asr"]

        # Category label
        svg.append(f'  <text x="{plot_b_x0 - 35}" y="{cur_by + 26}" font-family="Helvetica, Arial, sans-serif" font-size="12" font-weight="600" fill="{c_text}" text-anchor="end">{cat_label}</text>')

        # Arm A sub-row
        svg.append(f'  <text x="{plot_b_x0 - 12}" y="{cur_by + 13}" font-family="Helvetica, Arial, sans-serif" font-size="10.5" fill="{c_muted}" text-anchor="end">arm A</text>')
        # Two thin bars for Arm A: mentioned vs compromised
        w_ma = m_a * plot_b_w
        w_aa = asr_a * plot_b_w
        svg.append(f'  <rect x="{plot_b_x0}" y="{cur_by + 4}" width="{max(w_ma, 1.5):.1f}" height="6" fill="{c_mention}"/>')
        svg.append(f'  <rect x="{plot_b_x0}" y="{cur_by + 12}" width="{max(w_aa, 1.5):.1f}" height="6" fill="{c_arma}"/>')

        txt_a = f"{m_a*100:.0f}% mentioned  ·  {asr_a*100:.0f}% compromised"
        lbl_x_a = plot_b_x0 + max(w_ma, w_aa) + 10
        svg.append(f'  <text x="{lbl_x_a:.1f}" y="{cur_by + 14}" font-family="Helvetica, Arial, sans-serif" font-size="10" fill="{c_text}">{txt_a}</text>')

        # Arm B sub-row
        svg.append(f'  <text x="{plot_b_x0 - 12}" y="{cur_by + 37}" font-family="Helvetica, Arial, sans-serif" font-size="10.5" fill="{c_muted}" text-anchor="end">arm B</text>')
        w_mb = m_b * plot_b_w
        w_ab = asr_b * plot_b_w
        svg.append(f'  <rect x="{plot_b_x0}" y="{cur_by + 28}" width="{max(w_mb, 1.5):.1f}" height="6" fill="{c_mention}"/>')
        svg.append(f'  <rect x="{plot_b_x0}" y="{cur_by + 36}" width="{max(w_ab, 1.5):.1f}" height="6" fill="{c_armb}"/>')

        txt_b = f"{m_b*100:.0f}% mentioned  ·  {asr_b*100:.0f}% compromised"
        lbl_x_b = plot_b_x0 + max(w_mb, w_ab) + 10
        svg.append(f'  <text x="{lbl_x_b:.1f}" y="{cur_by + 38}" font-family="Helvetica, Arial, sans-serif" font-size="10" fill="{c_text}">{txt_b}</text>')

        # Light divider between categories
        svg.append(f'  <line x1="{plot_b_x0 - 140}" y1="{cur_by + 56}" x2="{plot_b_x0 + plot_b_w}" y2="{cur_by + 56}" stroke="{c_grid}" stroke-width="1"/>')

        cur_by += row_b_h

    # -------------------------------------------------------------
    # FOOTER (one grey footer line)
    # -------------------------------------------------------------
    svg.append('  <!-- Footer -->')
    svg.append(f'  <line x1="50" y1="765" x2="{width - 50}" y2="765" stroke="{c_div}" stroke-width="1"/>')
    svg.append(f'  <text x="50" y="785" font-family="Helvetica, Arial, sans-serif" font-size="11.5" fill="{c_muted}">FAULTLINE P9 · R2 z-ai/glm-5.3-flash · 20 scenarios × 10 categories × 2 arms · Wilson 95% CIs · $0.6305</text>')

    svg.append('</svg>')

    svg_content = "\n".join(svg)

    # Validate XML structure
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
    base = Path("projects/p09_redteam")
    results_path = base / "results.json"
    output_svg = base / "figure.svg"
    output_png = base / "figure.png"
    output_pdf = base / "figure.pdf"

    generate_figure(results_path, output_svg, output_png, output_pdf)


if __name__ == "__main__":
    main()
