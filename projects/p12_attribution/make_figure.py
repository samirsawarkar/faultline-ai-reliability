"""Generate publication-quality Figure 12 for Project P12: Failure Attribution."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET


def generate_figure(
    r2_path: Path,
    r4_path: Path,
    output_svg: Path,
    output_png: Path,
) -> None:
    with open(r2_path, "r", encoding="utf-8") as f:
        r2 = json.load(f)
    with open(r4_path, "r", encoding="utf-8") as f:
        r4 = json.load(f)

    r2_counts = r2["as_run"]["counts"]
    r2_share = r2["as_run"]["retriever_share"]
    r2_ci = r2["as_run"]["wilson_ci"]
    r2_verdict = r2["h8_verdict"]
    r2_mech = r2.get("mechanism", {})

    r4_counts = r4["as_run"]["counts"]
    r4_share = r4["as_run"]["retriever_share"]
    r4_ci = r4["as_run"]["wilson_ci"]
    r4_verdict = r4["h8_verdict"]
    r4_mech = r4.get("mechanism", {})

    width = 1200
    height = 680

    svg = []
    svg.append(f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">')
    svg.append('  <rect width="100%" height="100%" fill="#ffffff" rx="8"/>')
    svg.append('  <style>')
    svg.append('    .title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 20px; font-weight: 700; fill: #111827; }')
    svg.append('    .subtitle { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 13px; fill: #4b5563; }')
    svg.append('    .panel-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 15px; font-weight: 700; fill: #1f2937; }')
    svg.append('    .sec-hdr { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 12px; font-weight: 700; fill: #374151; }')
    svg.append('    .axis-label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 11px; fill: #4b5563; }')
    svg.append('    .val-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 12px; font-weight: 700; }')
    svg.append('    .grid-cell-hdr { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 11px; font-weight: 600; fill: #4b5563; }')
    svg.append('    .grid-cell-val { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 16px; font-weight: 800; }')
    svg.append('    .badge-hdr { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 12px; font-weight: 700; }')
    svg.append('    .badge-body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 11px; fill: #374151; }')
    svg.append('  </style>')

    # Outer border
    svg.append(f'  <rect x="1" y="1" width="{width-2}" height="{height-2}" fill="none" stroke="#e5e7eb" stroke-width="1.5" rx="8"/>')

    # Main header
    svg.append(f'  <text x="{width/2}" y="36" class="title" text-anchor="middle">Figure 12: Grounding Failure Attribution &amp; Oracle Retrieval Analysis</text>')
    svg.append(f'  <text x="{width/2}" y="58" class="subtitle" text-anchor="middle">Matched-Pair Attribution: Arm A (Standard Substring Search) vs Arm B (Oracle Retrieval Traversal Sources)</text>')

    # Helper function for rendering a rung panel
    def render_panel(x: int, y: int, p_width: int, p_height: int, rung: str, title: str, subtitle: str, counts: dict, share: float, ci: list, verdict: str, mech: dict):
        svg.append(f'  <!-- PANEL {rung} -->')
        svg.append(f'  <rect x="{x}" y="{y}" width="{p_width}" height="{p_height}" fill="#f9fafb" rx="6" stroke="#e5e7eb" stroke-width="1"/>')
        svg.append(f'  <text x="{x+16}" y="{y+26}" class="panel-title">{title}</text>')
        svg.append(f'  <text x="{x+16}" y="{y+44}" class="axis-label" fill="#6b7280">{subtitle}</text>')

        # 1. 2x2 Outcome Grid
        grid_top = y + 60
        grid_w = p_width - 32
        cell_w = (grid_w - 10) / 2
        cell_h = 64

        # Cell 1: Both Pass (N11)
        c1_x = x + 16
        c1_y = grid_top
        svg.append(f'  <rect x="{c1_x}" y="{c1_y}" width="{cell_w}" height="{cell_h}" fill="#ecfdf5" rx="4" stroke="#a7f3d0" stroke-width="1"/>')
        svg.append(f'  <text x="{c1_x+10}" y="{c1_y+20}" class="grid-cell-hdr" fill="#065f46">BOTH PASS (A+ &amp; B+)</text>')
        svg.append(f'  <text x="{c1_x+10}" y="{c1_y+44}" class="grid-cell-val" fill="#047857">{counts["both_pass"]} <tspan font-size="12px" font-weight="500">({counts["both_pass"]/counts["total_pairs"]:.1%})</tspan></text>')

        # Cell 2: Retriever-Owned (N01) - Focus cell
        c2_x = c1_x + cell_w + 10
        c2_y = grid_top
        svg.append(f'  <rect x="{c2_x}" y="{c2_y}" width="{cell_w}" height="{cell_h}" fill="#eff6ff" rx="4" stroke="#bfdbfe" stroke-width="1.5"/>')
        svg.append(f'  <text x="{c2_x+10}" y="{c2_y+20}" class="grid-cell-hdr" fill="#1e40af">RETRIEVER-OWNED (A- &amp; B+)</text>')
        svg.append(f'  <text x="{c2_x+10}" y="{c2_y+44}" class="grid-cell-val" fill="#1d4ed8">{counts["retriever_owned"]} <tspan font-size="12px" font-weight="500">({counts["retriever_owned"]/counts["total_pairs"]:.1%})</tspan></text>')

        # Cell 3: Reverse (N10)
        c3_x = c1_x
        c3_y = grid_top + cell_h + 8
        svg.append(f'  <rect x="{c3_x}" y="{c3_y}" width="{cell_w}" height="{cell_h}" fill="#fffbeb" rx="4" stroke="#fde68a" stroke-width="1"/>')
        svg.append(f'  <text x="{c3_x+10}" y="{c3_y+20}" class="grid-cell-hdr" fill="#92400e">REVERSE (A+ &amp; B-)</text>')
        svg.append(f'  <text x="{c3_x+10}" y="{c3_y+44}" class="grid-cell-val" fill="#b45309">{counts["reverse"]} <tspan font-size="12px" font-weight="500">({counts["reverse"]/counts["total_pairs"]:.1%})</tspan></text>')

        # Cell 4: Generator-Owned (N00)
        c4_x = c2_x
        c4_y = c3_y
        svg.append(f'  <rect x="{c4_x}" y="{c4_y}" width="{cell_w}" height="{cell_h}" fill="#fef2f2" rx="4" stroke="#fecaca" stroke-width="1"/>')
        svg.append(f'  <text x="{c4_x+10}" y="{c4_y+20}" class="grid-cell-hdr" fill="#991b1b">GENERATOR-OWNED (A- &amp; B-)</text>')
        svg.append(f'  <text x="{c4_x+10}" y="{c4_y+44}" class="grid-cell-val" fill="#b91c1c">{counts["generator_owned"]} <tspan font-size="12px" font-weight="500">({counts["generator_owned"]/counts["total_pairs"]:.1%})</tspan></text>')

        # 2. Retriever Share & Wilson CI Interval
        ci_top = c3_y + cell_h + 26
        svg.append(f'  <text x="{x+16}" y="{ci_top}" class="sec-hdr">Retriever Share of Grounding Failures (Wilson 95% CI vs 50% Threshold)</text>')

        scale_left = x + 35
        scale_w = grid_w - 45
        scale_y = ci_top + 42

        # Baseline axis line [0.0, 1.0]
        svg.append(f'  <line x1="{scale_left}" y1="{scale_y}" x2="{scale_left+scale_w}" y2="{scale_y}" stroke="#d1d5db" stroke-width="2"/>')
        for pct, label in [(0.0, "0%"), (0.25, "25%"), (0.50, "50% (H8)"), (0.75, "75%"), (1.0, "100%")]:
            tx = scale_left + pct * scale_w
            svg.append(f'  <line x1="{tx}" y1="{scale_y-5}" x2="{tx}" y2="{scale_y+5}" stroke="#9ca3af" stroke-width="1"/>')
            svg.append(f'  <text x="{tx}" y="{scale_y+18}" class="axis-label" text-anchor="middle" font-weight="{"700" if pct==0.5 else "400"}">{label}</text>')

        # 50% Threshold vertical dashed reference line
        mid_x = scale_left + 0.5 * scale_w
        svg.append(f'  <line x1="{mid_x}" y1="{scale_y-25}" x2="{mid_x}" y2="{scale_y+20}" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="4,3"/>')

        # CI interval whisker
        ci_lo_x = scale_left + ci[0] * scale_w
        ci_hi_x = scale_left + ci[1] * scale_w
        dot_x = scale_left + share * scale_w

        bar_color = "#1d4ed8" if verdict == "SUPPORTED" else "#6b7280"
        svg.append(f'  <line x1="{ci_lo_x}" y1="{scale_y-10}" x2="{ci_hi_x}" y2="{scale_y-10}" stroke="{bar_color}" stroke-width="3"/>')
        svg.append(f'  <line x1="{ci_lo_x}" y1="{scale_y-17}" x2="{ci_lo_x}" y2="{scale_y-3}" stroke="{bar_color}" stroke-width="3"/>')
        svg.append(f'  <line x1="{ci_hi_x}" y1="{scale_y-17}" x2="{ci_hi_x}" y2="{scale_y-3}" stroke="{bar_color}" stroke-width="3"/>')
        # Point estimate dot
        svg.append(f'  <circle cx="{dot_x}" cy="{scale_y-10}" r="6" fill="{bar_color}"/>')

        # Interval label
        svg.append(f'  <text x="{dot_x}" y="{scale_y-22}" class="val-text" fill="{bar_color}" text-anchor="middle">{share:.1%} [{ci[0]:.1%}, {ci[1]:.1%}]</text>')

        # 3. Decision & Mechanism Box
        box_y = scale_y + 42
        box_h = 165
        is_supp = verdict == "SUPPORTED"
        badge_bg = "#eff6ff" if is_supp else "#f3f4f6"
        badge_border = "#93c5fd" if is_supp else "#d1d5db"
        badge_txt = "#1e40af" if is_supp else "#374151"

        svg.append(f'  <rect x="{x+16}" y="{box_y}" width="{grid_w}" height="{box_h}" fill="{badge_bg}" rx="6" stroke="{badge_border}" stroke-width="1.5"/>')
        svg.append(f'  <text x="{x+30}" y="{box_y+24}" class="badge-hdr" fill="{badge_txt}">H8 VERDICT: {verdict.upper()}</text>')

        if is_supp:
            v_desc = f"Supported: Wilson CI [{ci[0]:.1%}, {ci[1]:.1%}] strictly exceeds 50% generator boundary."
        else:
            v_desc = f"Undecided: Wilson CI [{ci[0]:.1%}, {ci[1]:.1%}] spans 50% threshold due to pilot sample size."
        svg.append(f'  <text x="{x+30}" y="{box_y+44}" class="badge-body" font-weight="600">{v_desc}</text>')

        # Mechanism Details
        nev = mech.get("never_surfaced", 0)
        tot_fail = counts["retriever_owned"]
        nev_pct = (nev / tot_fail * 100) if tot_fail > 0 else 0.0
        used = mech.get("surfaced_but_unused", 0)
        used_pct = (used / tot_fail * 100) if tot_fail > 0 else 0.0

        svg.append(f'  <text x="{x+30}" y="{box_y+70}" class="badge-body">• <tspan font-weight="700">Root Cause Decomposition:</tspan> {nev}/{tot_fail} ({nev_pct:.1f}%) never surfaced chain document.</text>')
        svg.append(f'  <text x="{x+30}" y="{box_y+90}" class="badge-body">• <tspan font-weight="700">Surfaced but Unused:</tspan> {used}/{tot_fail} ({used_pct:.1f}%) surfaced all documents but model failed to cite/answer.</text>')

        arm_m = mech.get("arm_means", {})
        ma = arm_m.get("A", {})
        mb = arm_m.get("B", {})
        svg.append(f'  <text x="{x+30}" y="{box_y+115}" class="badge-body">• <tspan font-weight="700">Execution Burden:</tspan> Arm A mean {ma.get("mean_spans", 0)} spans/run ({ma.get("mean_total_tokens", 0):.0f} tokens);</text>')
        svg.append(f'  <text x="{x+30}" y="{box_y+135}" class="badge-body">  Arm B oracle mean {mb.get("mean_spans", 0)} spans/run ({mb.get("mean_total_tokens", 0):.0f} tokens) — answers directly from snippets.</text>')

    # Panel A: R2 (Left)
    p_w = 540
    p_h = 575
    render_panel(
        x=40, y=75, p_width=p_w, p_height=p_h,
        rung="R2",
        title="Rung R2: Cheap Workhorse (GLM 5.3 Flash, N=150)",
        subtitle="150 Matched Scenarios, Step Cap 24, Spend $1.47",
        counts=r2_counts,
        share=r2_share,
        ci=r2_ci,
        verdict=r2_verdict,
        mech=r2_mech,
    )

    # Panel B: R4 (Right)
    render_panel(
        x=620, y=75, p_width=p_w, p_height=p_h,
        rung="R4",
        title="Rung R4: Frontier Pilot (GPT 5.6 Luna, pilot, n=10)",
        subtitle="10 Matched Scenarios, Step Cap 24, Spend $0.46",
        counts=r4_counts,
        share=r4_share,
        ci=r4_ci,
        verdict=r4_verdict,
        mech=r4_mech,
    )

    svg.append('</svg>')
    svg_content = "\n".join(svg)

    output_svg.write_text(svg_content, encoding="utf-8")
    print(f"Wrote SVG figure to {output_svg}")

    # Validate XML
    ET.fromstring(svg_content)
    print("XML validation: PASSED (valid SVG XML)")

    # Render PNG
    chrome_path = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    rendered = False
    if chrome_path.exists():
        try:
            cmd = [
                str(chrome_path),
                "--headless",
                "--disable-gpu",
                f"--screenshot={output_png}",
                f"--window-size={width},{height}",
                str(output_svg.resolve()),
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"Rendered PNG via Chrome headless to {output_png}")
            rendered = True
        except Exception as e:
            print(f"Notice: Chrome headless render: {e}")

    if not rendered:
        try:
            subprocess.run(["qlmanage", "-t", "-s", "2400", "-o", "/tmp", str(output_svg)], check=True, capture_output=True)
            tmp_png = Path(f"/tmp/{output_svg.name}.png")
            if tmp_png.exists():
                shutil.copyfile(tmp_png, output_png)
                print(f"Rendered PNG via qlmanage to {output_png}")
        except Exception as e:
            print(f"Notice: qlmanage PNG render: {e}")


def main():
    base_dir = Path("projects/p12_attribution")
    r2_path = base_dir / "results_R2.json"
    r4_path = base_dir / "results_R4.json"
    output_svg = base_dir / "figure.svg"
    output_png = base_dir / "figure.png"

    generate_figure(r2_path, r4_path, output_svg, output_png)


if __name__ == "__main__":
    main()
