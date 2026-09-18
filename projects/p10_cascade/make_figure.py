"""Generate publication-quality Figure 10 for Project P10: Calibrated Cascade."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET


def generate_figure(
    results_path: Path,
    output_svg: Path,
    output_png: Path,
) -> None:
    with open(results_path, "r", encoding="utf-8") as f:
        res = json.load(f)

    all_test = res.get("all_test_metrics", {})
    side_by_side = res.get("side_by_side", {})
    p6_rep = res.get("p6_replicate", {})

    width = 1200
    height = 720

    svg = []
    svg.append(f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">')
    svg.append('  <rect width="100%" height="100%" fill="#ffffff" rx="8"/>')
    svg.append('  <style>')
    svg.append('    .title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 20px; font-weight: 700; fill: #111827; }')
    svg.append('    .subtitle { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 13px; fill: #4b5563; }')
    svg.append('    .panel-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 15px; font-weight: 700; fill: #1f2937; }')
    svg.append('    .panel-sub { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 11px; fill: #6b7280; }')
    svg.append('    .axis-label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 11px; font-weight: 600; fill: #4b5563; }')
    svg.append('    .tick-label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 10px; fill: #6b7280; }')
    svg.append('    .point-label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 11px; font-weight: 600; fill: #1f2937; }')
    svg.append('    .point-sub { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 10px; fill: #4b5563; }')
    svg.append('    .ceiling-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 11px; font-weight: 700; fill: #dc2626; }')
    svg.append('    .callout-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 12px; font-weight: 700; fill: #1e3a8a; }')
    svg.append('    .callout-body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 11px; fill: #1e40af; }')
    svg.append('  </style>')

    # Outer border
    svg.append(f'  <rect x="1" y="1" width="{width-2}" height="{height-2}" fill="none" stroke="#e5e7eb" stroke-width="1.5" rx="8"/>')

    # Main header
    svg.append(f'  <text x="{width/2}" y="36" class="title" text-anchor="middle">Figure 10: Calibrated Model Cascade &amp; Pareto Frontier</text>')
    svg.append(f'  <text x="{width/2}" y="56" class="subtitle" text-anchor="middle">Test Split Evaluation: Cheap Workhorse R2 (glm-5.3-flash) vs Frontier Anchor R4 (gpt-5.6-luna)</text>')

    # -------------------------------------------------------------
    # PANEL 1: Main Test Split Pareto Frontier (Left)
    # -------------------------------------------------------------
    p1_x = 40
    p1_y = 75
    p1_w = 710
    p1_h = 615

    svg.append(f'  <!-- PANEL 1: Test Split Frontier -->')
    svg.append(f'  <rect x="{p1_x}" y="{p1_y}" width="{p1_w}" height="{p1_h}" fill="#f9fafb" rx="6" stroke="#e5e7eb" stroke-width="1"/>')
    svg.append(f'  <text x="{p1_x+20}" y="{p1_y+26}" class="panel-title">A. Held-out Test Split Pareto Frontier (N=30)</text>')
    svg.append(f'  <text x="{p1_x+20}" y="{p1_y+42}" class="panel-sub">Evaluates deterministic escalation rules vs theoretical rescue ceiling; error bars show Wilson 95% CI</text>')

    plot_x0 = p1_x + 65
    plot_y0 = p1_y + 65
    plot_w = p1_w - 95
    plot_h = p1_h - 180

    def px1(cost: float) -> float:
        return plot_x0 + (cost / 0.070) * plot_w

    def py1(pass_rate: float) -> float:
        return plot_y0 + (1.0 - pass_rate) * plot_h

    # Gridlines and axes
    svg.append(f'  <!-- Plot 1 Grid & Axes -->')
    for tick_y in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        y_pos = py1(tick_y)
        svg.append(f'  <line x1="{plot_x0}" y1="{y_pos:.1f}" x2="{plot_x0+plot_w}" y2="{y_pos:.1f}" stroke="#e5e7eb" stroke-width="1"/>')
        svg.append(f'  <text x="{plot_x0-10}" y="{y_pos+4:.1f}" class="tick-label" text-anchor="end">{tick_y*100:.0f}%</text>')

    for tick_x in [0.00, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07]:
        x_pos = px1(tick_x)
        svg.append(f'  <line x1="{x_pos:.1f}" y1="{plot_y0}" x2="{x_pos:.1f}" y2="{plot_y0+plot_h}" stroke="#e5e7eb" stroke-width="1"/>')
        svg.append(f'  <text x="{x_pos:.1f}" y="{plot_y0+plot_h+16}" class="tick-label" text-anchor="middle">${tick_x:.2f}</text>')

    svg.append(f'  <line x1="{plot_x0}" y1="{plot_y0}" x2="{plot_x0}" y2="{plot_y0+plot_h}" stroke="#9ca3af" stroke-width="1.5"/>')
    svg.append(f'  <line x1="{plot_x0}" y1="{plot_y0+plot_h}" x2="{plot_x0+plot_w}" y2="{plot_y0+plot_h}" stroke="#9ca3af" stroke-width="1.5"/>')
    svg.append(f'  <text x="{plot_x0 + plot_w/2}" y="{plot_y0+plot_h+38}" class="axis-label" text-anchor="middle">Mean Cost per Scenario (USD)</text>')
    svg.append(f'  <text x="{plot_x0-42}" y="{plot_y0 + plot_h/2}" class="axis-label" text-anchor="middle" transform="rotate(-90 {plot_x0-42} {plot_y0 + plot_h/2})">Pass Rate (Oracle Grounded)</text>')

    # 1. Theoretical Test-Split Rescue Ceiling Line at 25/30 = 83.3%
    ceil_test = 25.0 / 30.0
    ceil_y = py1(ceil_test)
    svg.append(f'  <!-- Test-Split Rescue Ceiling Line (25/30 = 83.3%) -->')
    svg.append(f'  <line x1="{plot_x0}" y1="{ceil_y:.1f}" x2="{plot_x0+plot_w}" y2="{ceil_y:.1f}" stroke="#dc2626" stroke-width="2" stroke-dasharray="6,4"/>')
    # Right-aligned label above the right end of dashed line in open space
    ceil_label_x = plot_x0 + plot_w - 6
    ceil_label_y = ceil_y - 8
    svg.append(f'  <text x="{ceil_label_x:.1f}" y="{ceil_label_y:.1f}" class="ceiling-text" text-anchor="end">Test-split Ceiling: 25/30 = 83.3% [Full-100: 82.0%]</text>')

    # Background policies (all 50)
    svg.append(f'  <!-- Background Policies -->')
    for pol_name, met in all_test.items():
        cx = px1(met["mean_cost"])
        cy = py1(met["pass_rate"])
        svg.append(f'  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" fill="#9ca3af" fill-opacity="0.55"/>')

    # Frontier line connecting test frontier points
    fp1 = (px1(0.0078), py1(0.767))
    fp2 = (px1(0.0159), py1(0.800))
    fp3 = (px1(0.0193), py1(0.833))

    svg.append(f'  <!-- Frontier line -->')
    svg.append(f'  <polyline points="{fp1[0]:.1f},{fp1[1]:.1f} {fp2[0]:.1f},{fp2[1]:.1f} {fp3[0]:.1f},{fp3[1]:.1f}" fill="none" stroke="#2563eb" stroke-width="2.5" stroke-linecap="round"/>')

    # Wilson CI Error bars
    ci_points = [
        ("r2_only", 0.0078, 0.767, 0.591, 0.882, "#059669"),
        ("escalate_if_not_answered", 0.0159, 0.800, 0.627, 0.905, "#2563eb"),
        ("r4_only", 0.0634, 0.200, 0.095, 0.373, "#dc2626"),
    ]
    for name, c, p, clo, chi, col in ci_points:
        cx = px1(c)
        y_top = py1(chi)
        y_bot = py1(clo)
        svg.append(f'  <line x1="{cx:.1f}" y1="{y_top:.1f}" x2="{cx:.1f}" y2="{y_bot:.1f}" stroke="{col}" stroke-width="1.8"/>')
        svg.append(f'  <line x1="{cx-4:.1f}" y1="{y_top:.1f}" x2="{cx+4:.1f}" y2="{y_top:.1f}" stroke="{col}" stroke-width="1.8"/>')
        svg.append(f'  <line x1="{cx-4:.1f}" y1="{y_bot:.1f}" x2="{cx+4:.1f}" y2="{y_bot:.1f}" stroke="{col}" stroke-width="1.8"/>')

    # 1. R2-only Point & Callout (below-left)
    r2_cx, r2_cy = px1(0.0078), py1(0.767)
    svg.append(f'  <circle cx="{r2_cx:.1f}" cy="{r2_cy:.1f}" r="7" fill="#10b981" stroke="#047857" stroke-width="2"/>')
    r2_box_x = plot_x0 + 10
    r2_box_y = r2_cy + 32
    svg.append(f'  <line x1="{r2_cx:.1f}" y1="{r2_cy+7:.1f}" x2="{r2_box_x+60:.1f}" y2="{r2_box_y:.1f}" stroke="#059669" stroke-width="1" stroke-dasharray="2,2"/>')
    svg.append(f'  <rect x="{r2_box_x:.1f}" y="{r2_box_y:.1f}" width="125" height="30" fill="#ffffff" rx="4" stroke="#10b981" stroke-width="1"/>')
    svg.append(f'  <text x="{r2_box_x+62:.1f}" y="{r2_box_y+14:.1f}" class="point-label" fill="#047857" text-anchor="middle">R2-only (Baseline)</text>')
    svg.append(f'  <text x="{r2_box_x+62:.1f}" y="{r2_box_y+25:.1f}" class="point-sub" text-anchor="middle">76.7% @ $0.0078 (esc 0%)</text>')

    # 2. Chosen Cascades Point & Callout (above-right with leader line)
    casc_cx, casc_cy = px1(0.0159), py1(0.800)
    svg.append(f'  <circle cx="{casc_cx:.1f}" cy="{casc_cy:.1f}" r="7" fill="#2563eb" stroke="#1e40af" stroke-width="2"/>')
    casc_box_x = casc_cx + 25
    casc_box_y = casc_cy - 74
    svg.append(f'  <line x1="{casc_cx:.1f}" y1="{casc_cy-7:.1f}" x2="{casc_box_x+10:.1f}" y2="{casc_box_y+34:.1f}" stroke="#2563eb" stroke-width="1.2" stroke-dasharray="2,2"/>')
    svg.append(f'  <rect x="{casc_box_x:.1f}" y="{casc_box_y:.1f}" width="205" height="34" fill="#ffffff" rx="4" stroke="#2563eb" stroke-width="1"/>')
    svg.append(f'  <text x="{casc_box_x+10:.1f}" y="{casc_box_y+15:.1f}" class="point-label" fill="#1e40af">Chosen Cascades (t=23 / status)</text>')
    svg.append(f'  <text x="{casc_box_x+10:.1f}" y="{casc_box_y+28:.1f}" class="point-sub">80.0% @ $0.0159 (16.7% esc, +1 pass)</text>')

    # 3. Frontier High (steps>=21) - label placed neatly above-left
    fh_cx, fh_cy = px1(0.0193), py1(0.833)
    svg.append(f'  <circle cx="{fh_cx:.1f}" cy="{fh_cy:.1f}" r="5" fill="#6366f1" stroke="#4338ca" stroke-width="1.5"/>')
    svg.append(f'  <text x="{fh_cx-8:.1f}" y="{fh_cy-8:.1f}" class="point-sub" fill="#4338ca" font-weight="600" text-anchor="end">steps&gt;=21 (83.3%)</text>')

    # 4. R4-only (Dominated)
    r4_cx, r4_cy = px1(0.0634), py1(0.200)
    svg.append(f'  <circle cx="{r4_cx:.1f}" cy="{r4_cy:.1f}" r="7" fill="#ef4444" stroke="#b91c1c" stroke-width="2"/>')
    svg.append(f'  <rect x="{r4_cx-175:.1f}" y="{r4_cy+12:.1f}" width="170" height="30" fill="#ffffff" rx="4" stroke="#ef4444" stroke-width="1"/>')
    svg.append(f'  <text x="{r4_cx-90:.1f}" y="{r4_cy+26:.1f}" class="point-label" fill="#b91c1c" text-anchor="middle">R4-only (Frontier Anchor)</text>')
    svg.append(f'  <text x="{r4_cx-90:.1f}" y="{r4_cy+38:.1f}" class="point-sub" text-anchor="middle">20.0% @ $0.0634 (Dominated)</text>')

    # Deliverable Callout Box in Panel 1
    callout_y = plot_y0 + plot_h + 50
    svg.append(f'  <rect x="{p1_x+16}" y="{callout_y}" width="{p1_w-32}" height="38" fill="#eff6ff" rx="4" stroke="#bfdbfe" stroke-width="1"/>')
    svg.append(f'  <text x="{p1_x+26}" y="{callout_y+17}" class="callout-title">Deliverable Finding:</text>')
    svg.append(f'  <text x="{p1_x+26}" y="{callout_y+31}" class="callout-body">Cheap R2 is on the frontier. Escalating to frontier R4 buys one extra pass in thirty (+3.3pp) at 2.0x cost ($0.0159 vs $0.0078).</text>')

    # -------------------------------------------------------------
    # PANEL 2: P6 Replicate (Right)
    # -------------------------------------------------------------
    p2_x = 770
    p2_y = 75
    p2_w = 390
    p2_h = 615

    svg.append(f'  <!-- PANEL 2: P6 Replicate -->')
    svg.append(f'  <rect x="{p2_x}" y="{p2_y}" width="{p2_w}" height="{p2_h}" fill="#f9fafb" rx="6" stroke="#e5e7eb" stroke-width="1"/>')
    svg.append(f'  <text x="{p2_x+16}" y="{p2_y+26}" class="panel-title">B. P6 replicate, infra-excluded test split (n=107)</text>')
    svg.append(f'  <text x="{p2_x+16}" y="{p2_y+42}" class="panel-sub">P6 replicate (R4 incident-damaged)</text>')

    p2_plot_x0 = p2_x + 55
    p2_plot_y0 = p2_y + 65
    p2_plot_w = p2_w - 75
    p2_plot_h = p2_h - 180

    def px2(cost: float) -> float:
        return p2_plot_x0 + (cost / 0.070) * p2_plot_w

    def py2(pass_rate: float) -> float:
        return p2_plot_y0 + (1.0 - pass_rate) * p2_plot_h

    # Gridlines for Panel 2
    for tick_y in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        y_pos = py2(tick_y)
        svg.append(f'  <line x1="{p2_plot_x0}" y1="{y_pos:.1f}" x2="{p2_plot_x0+p2_plot_w}" y2="{y_pos:.1f}" stroke="#e5e7eb" stroke-width="1"/>')
        svg.append(f'  <text x="{p2_plot_x0-8}" y="{y_pos+4:.1f}" class="tick-label" text-anchor="end">{tick_y*100:.0f}%</text>')

    for tick_x in [0.00, 0.02, 0.04, 0.06]:
        x_pos = px2(tick_x)
        svg.append(f'  <line x1="{x_pos:.1f}" y1="{p2_plot_y0}" x2="{x_pos:.1f}" y2="{p2_plot_y0+p2_plot_h}" stroke="#e5e7eb" stroke-width="1"/>')
        svg.append(f'  <text x="{x_pos:.1f}" y="{p2_plot_y0+p2_plot_h+16}" class="tick-label" text-anchor="middle">${tick_x:.2f}</text>')

    svg.append(f'  <line x1="{p2_plot_x0}" y1="{p2_plot_y0}" x2="{p2_plot_x0}" y2="{p2_plot_y0+p2_plot_h}" stroke="#9ca3af" stroke-width="1.5"/>')
    svg.append(f'  <line x1="{p2_plot_x0}" y1="{p2_plot_y0+p2_plot_h}" x2="{p2_plot_x0+p2_plot_w}" y2="{p2_plot_y0+p2_plot_h}" stroke="#9ca3af" stroke-width="1.5"/>')
    svg.append(f'  <text x="{p2_plot_x0 + p2_plot_w/2}" y="{p2_plot_y0+p2_plot_h+38}" class="axis-label" text-anchor="middle">Mean Cost (USD)</text>')

    # Test split points:
    # r2_only: cost $0.0090, pass 0.579
    # steps_ge_24: cost $0.0124, pass 0.589
    # not_answered: cost $0.0299, pass 0.617
    # r4_only: cost $0.0621, pass 0.131
    p6_p1 = (px2(0.0090), py2(0.579))
    p6_p2 = (px2(0.0124), py2(0.589))
    p6_p3 = (px2(0.0299), py2(0.617))
    p6_r4 = (px2(0.0621), py2(0.131))

    svg.append(f'  <!-- P6 Frontier Line -->')
    svg.append(f'  <polyline points="{p6_p1[0]:.1f},{p6_p1[1]:.1f} {p6_p2[0]:.1f},{p6_p2[1]:.1f} {p6_p3[0]:.1f},{p6_p3[1]:.1f}" fill="none" stroke="#2563eb" stroke-width="2"/>')

    # Separated non-overlapping labels in Panel B:
    # 1. R2-only: label positioned ABOVE the point, centered
    svg.append(f'  <circle cx="{p6_p1[0]:.1f}" cy="{p6_p1[1]:.1f}" r="5.5" fill="#10b981" stroke="#047857" stroke-width="1.5"/>')
    svg.append(f'  <text x="{p6_p1[0]-6:.1f}" y="{p6_p1[1]-10:.1f}" class="point-sub" fill="#047857" font-weight="600" text-anchor="start">R2-only: 57.9%</text>')

    # 2. steps>=24: label positioned BELOW the point, shifted right
    svg.append(f'  <circle cx="{p6_p2[0]:.1f}" cy="{p6_p2[1]:.1f}" r="5" fill="#2563eb" stroke="#1e40af" stroke-width="1.5"/>')
    svg.append(f'  <text x="{p6_p2[0]+8:.1f}" y="{p6_p2[1]+16:.1f}" class="point-sub" fill="#1e40af" font-weight="600" text-anchor="start">steps&gt;=24: 58.9%</text>')

    # 3. not_answered: label positioned ABOVE the point
    svg.append(f'  <circle cx="{p6_p3[0]:.1f}" cy="{p6_p3[1]:.1f}" r="5" fill="#2563eb" stroke="#1e40af" stroke-width="1.5"/>')
    svg.append(f'  <text x="{p6_p3[0]:.1f}" y="{p6_p3[1]-10:.1f}" class="point-sub" fill="#1e40af" font-weight="600" text-anchor="middle">not_answered: 61.7%</text>')

    # 4. P6 R4-only point (0.0621, 0.131)
    svg.append(f'  <circle cx="{p6_r4[0]:.1f}" cy="{p6_r4[1]:.1f}" r="6" fill="#ef4444" stroke="#b91c1c" stroke-width="1.5"/>')
    svg.append(f'  <text x="{p6_r4[0]-10:.1f}" y="{p6_r4[1]-6:.1f}" class="point-sub" fill="#b91c1c" font-weight="600" text-anchor="end">R4-only: 13.1%</text>')
    svg.append(f'  <text x="{p6_r4[0]-10:.1f}" y="{p6_r4[1]+6:.1f}" class="point-sub" fill="#6b7280" text-anchor="end">(Dominated)</text>')

    # P6 Incident Warning Callout Box
    p6_box_y = p2_plot_y0 + p2_plot_h + 50
    svg.append(f'  <rect x="{p2_x+16}" y="{p6_box_y}" width="{p2_w-32}" height="38" fill="#fffbeb" rx="4" stroke="#fde68a" stroke-width="1"/>')
    svg.append(f'  <text x="{p2_x+24}" y="{p6_box_y+16}" class="callout-title" fill="#92400e">P6 Incident Damage:</text>')
    svg.append(f'  <text x="{p2_x+24}" y="{p6_box_y+30}" class="callout-body" fill="#b45309">95 of 450 R4 runs had completion_tokens=0. R2 dominates.</text>')

    svg.append('</svg>')

    svg_content = "\n".join(svg)

    # Validate XML with ElementTree
    try:
        ET.fromstring(svg_content)
        print("XML validation passed successfully.")
    except Exception as e:
        raise ValueError(f"Generated SVG is not valid XML: {e}")

    output_svg.write_text(svg_content, encoding="utf-8")
    print(f"Written valid SVG to {output_svg}")

    # Render PNG
    rendered = False
    chrome_path = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
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
    base_dir = Path("projects/p10_cascade")
    results_path = base_dir / "results.json"
    output_svg = base_dir / "figure.svg"
    output_png = base_dir / "figure.png"

    generate_figure(results_path, output_svg, output_png)


if __name__ == "__main__":
    main()
