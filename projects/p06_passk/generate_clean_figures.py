"""Script to generate unclipped, publication-grade figure_cost_vs_passk.svg and PNG."""
import subprocess
import shutil
from pathlib import Path

def build_cost_vs_passk_svg() -> str:
    width = 1160
    height = 700
    
    # Coordinates
    x_left = 170
    x_right = 1080
    chart_w = x_right - x_left  # 910
    
    y_top = 110
    y_bottom = 530
    chart_h = y_bottom - y_top  # 420
    
    # Scale mappings
    # X: 0% to 30% pass^3
    def map_x(pct: float) -> float:
        return x_left + (pct / 0.30) * chart_w
        
    # Y: $0.00 to $0.30 cost per grounded answer
    def map_y(cost: float) -> float:
        return y_bottom - (cost / 0.30) * chart_h

    svg = []
    svg.append(f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">')
    svg.append('  <rect width="100%" height="100%" fill="#ffffff" rx="8"/>')
    svg.append('  <style>')
    svg.append('    .title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 21px; font-weight: 700; fill: #111827; }')
    svg.append('    .subtitle { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 13.5px; fill: #4b5563; }')
    svg.append('    .axis-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 13px; font-weight: 600; fill: #374151; }')
    svg.append('    .axis { stroke: #9ca3af; stroke-width: 1.5; }')
    svg.append('    .grid { stroke: #f3f4f6; stroke-dasharray: 4,4; stroke-width: 1.2; }')
    svg.append('    .tick-label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 12px; fill: #4b5563; font-weight: 500; }')
    svg.append('    .card-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 13px; font-weight: 700; }')
    svg.append('    .card-metric { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 12px; fill: #1f2937; }')
    svg.append('    .card-meta { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 11px; fill: #6b7280; }')
    svg.append('    .badge-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 10.5px; font-weight: 700; }')
    svg.append('    .arrow-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 12px; font-weight: 700; fill: #059669; }')
    svg.append('    .legend-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 12px; fill: #374151; font-weight: 500; }')
    svg.append('  </style>')
    svg.append(f'  <rect x="1" y="1" width="{width-2}" height="{height-2}" fill="none" stroke="#e5e7eb" stroke-width="1.5" rx="8"/>')
    
    # Title & Subtitle
    svg.append(f'  <text x="{width/2}" y="42" class="title" text-anchor="middle">Figure 6: Cost per Grounded Answer vs. Empirical Joint Reliability (pass³)</text>')
    svg.append(f'  <text x="{width/2}" y="68" class="subtitle" text-anchor="middle">The Economic Workhorse Inversion: Workhorse (R2) Achieves 11.3× Higher Reliability at 18.3× Lower Cost</text>')

    # Background quadrant shading
    # Optimal quadrant (bottom right)
    opt_x = map_x(0.12)
    opt_y = map_y(0.15)
    svg.append(f'  <!-- Sweet spot quadrant -->')
    svg.append(f'  <rect x="{opt_x}" y="{opt_y}" width="{x_right - opt_x}" height="{y_bottom - opt_y}" fill="#f0fdf4" opacity="0.65" rx="6"/>')
    svg.append(f'  <text x="{x_right - 20}" y="{y_bottom - 15}" class="badge-text" fill="#16a34a" text-anchor="end">PARETO OPTIMAL: High Reliability / Low Cost</text>')

    # Fragile quadrant (top left)
    frag_w = opt_x - x_left
    frag_h = opt_y - y_top
    svg.append(f'  <!-- Fragile quadrant -->')
    svg.append(f'  <rect x="{x_left}" y="{y_top}" width="{frag_w}" height="{frag_h}" fill="#fef2f2" opacity="0.65" rx="6"/>')
    svg.append(f'  <text x="{x_left + 16}" y="{y_top + 22}" class="badge-text" fill="#dc2626" text-anchor="start">HIGH FRAGILITY: Low Reliability / High Cost</text>')

    # Y-axis grid & labels
    for c_val in [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]:
        y_pos = map_y(c_val)
        svg.append(f'  <line x1="{x_left}" y1="{y_pos}" x2="{x_right}" y2="{y_pos}" class="grid"/>')
        svg.append(f'  <text x="{x_left - 15}" y="{y_pos + 4}" class="tick-label" text-anchor="end">${c_val:.2f}</text>')

    # X-axis grid & labels
    for p_val in [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]:
        x_pos = map_x(p_val)
        svg.append(f'  <line x1="{x_pos}" y1="{y_top}" x2="{x_pos}" y2="{y_bottom}" class="grid"/>')
        svg.append(f'  <text x="{x_pos}" y="{y_bottom + 22}" class="tick-label" text-anchor="middle">{int(p_val*100)}%</text>')

    # Solid Axes
    svg.append(f'  <line x1="{x_left}" y1="{y_bottom}" x2="{x_right}" y2="{y_bottom}" class="axis"/>')
    svg.append(f'  <line x1="{x_left}" y1="{y_top}" x2="{x_left}" y2="{y_bottom}" class="axis"/>')

    # Axis Titles (generous spacing so NO clipping occurs)
    svg.append(f'  <text x="{(x_left + x_right)/2}" y="{y_bottom + 48}" class="axis-title" text-anchor="middle">Empirical Joint Reliability (pass³, k=3 on 150 Hard T3 Scenarios)</text>')
    svg.append(f'  <text x="65" y="{(y_top + y_bottom)/2}" class="axis-title" text-anchor="middle" transform="rotate(-90 65 {(y_top + y_bottom)/2})">Cost per Grounded Answer (USD)</text>')

    # Definitions for arrows and drop shadow
    svg.append('  <defs>')
    svg.append('    <marker id="arrow-emerald" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">')
    svg.append('      <path d="M 0 1 L 10 5 L 0 9 z" fill="#059669"/>')
    svg.append('    </marker>')
    svg.append('    <filter id="shadow" x="-10%" y="-10%" width="130%" height="130%">')
    svg.append('      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.12"/>')
    svg.append('    </filter>')
    svg.append('  </defs>')

    # Inversion curve arrow
    # R4 point: pass^3 = 0.02, cost = $0.2682
    r4_x = map_x(0.02)
    r4_y = map_y(0.2682)
    # R2 point: pass^3 = 0.2267, cost = $0.0147
    r2_x = map_x(0.2267)
    r2_y = map_y(0.0147)

    svg.append(f'  <!-- Inversion Trajectory Arrow -->')
    ctrl_x = (r4_x + r2_x) / 2 + 30
    ctrl_y = (r4_y + r2_y) / 2 - 20
    svg.append(f'  <path d="M {r4_x + 18} {r4_y + 12} Q {ctrl_x} {ctrl_y} {r2_x - 18} {r2_y - 12}" fill="none" stroke="#059669" stroke-width="2.5" stroke-dasharray="6,4" marker-end="url(#arrow-emerald)"/>')
    
    # Trajectory badge
    badge_x = (r4_x + r2_x) / 2 - 30
    badge_y = (r4_y + r2_y) / 2 - 40
    svg.append(f'  <rect x="{badge_x}" y="{badge_y}" width="220" height="28" rx="14" fill="#ecfdf5" stroke="#a7f3d0" stroke-width="1.2" filter="url(#shadow)"/>')
    svg.append(f'  <text x="{badge_x + 110}" y="{badge_y + 18}" class="arrow-text" text-anchor="middle">18.3× Cost Reduction →</text>')

    # --- R4 PLOT ---
    # R4 CI: [0.0068, 0.0571]
    r4_ci_lo = map_x(0.0068)
    r4_ci_hi = map_x(0.0571)
    svg.append(f'  <!-- R4 CI Whisker -->')
    svg.append(f'  <line x1="{r4_ci_lo}" y1="{r4_y}" x2="{r4_ci_hi}" y2="{r4_y}" stroke="#b91c1c" stroke-width="2" stroke-linecap="round"/>')
    svg.append(f'  <line x1="{r4_ci_lo}" y1="{r4_y - 6}" x2="{r4_ci_lo}" y2="{r4_y + 6}" stroke="#b91c1c" stroke-width="2" stroke-linecap="round"/>')
    svg.append(f'  <line x1="{r4_ci_hi}" y1="{r4_y - 6}" x2="{r4_ci_hi}" y2="{r4_y + 6}" stroke="#b91c1c" stroke-width="2" stroke-linecap="round"/>')
    
    # R4 Point
    svg.append(f'  <!-- R4 Point -->')
    svg.append(f'  <circle cx="{r4_x}" cy="{r4_y}" r="10" fill="#ef4444" stroke="#991b1b" stroke-width="2.5" filter="url(#shadow)"/>')

    # R4 Callout Card
    card_r4_x = r4_x + 35
    card_r4_y = r4_y - 50
    svg.append(f'  <!-- R4 Callout Card -->')
    svg.append(f'  <rect x="{card_r4_x}" y="{card_r4_y}" width="265" height="100" rx="6" fill="#ffffff" stroke="#f87171" stroke-width="1.5" filter="url(#shadow)"/>')
    svg.append(f'  <rect x="{card_r4_x}" y="{card_r4_y}" width="265" height="5" rx="2" fill="#ef4444"/>')
    svg.append(f'  <text x="{card_r4_x + 14}" y="{card_r4_y + 24}" class="card-title" fill="#991b1b">R4: OpenAI Frontier (gpt-5.6-luna)</text>')
    svg.append(f'  <text x="{card_r4_x + 14}" y="{card_r4_y + 44}" class="card-metric">Cost: <tspan font-weight="700" fill="#b91c1c">$0.2682</tspan> / grounded answer</text>')
    svg.append(f'  <text x="{card_r4_x + 14}" y="{card_r4_y + 64}" class="card-metric">pass³: <tspan font-weight="700">2.00%</tspan> [0.68%, 5.71%] · pass@1: 14.89%</text>')
    svg.append(f'  <rect x="{card_r4_x + 14}" y="{card_r4_y + 74}" width="235" height="18" rx="9" fill="#fee2e2"/>')
    svg.append(f'  <text x="{card_r4_x + 24}" y="{card_r4_y + 87}" class="badge-text" fill="#991b1b">Fragile Frontier: 28% Step-Cap Exhaustion</text>')

    # --- R2 PLOT ---
    # R2 CI: [0.1670, 0.3000]
    r2_ci_lo = map_x(0.1670)
    r2_ci_hi = map_x(0.3000)
    svg.append(f'  <!-- R2 CI Whisker -->')
    svg.append(f'  <line x1="{r2_ci_lo}" y1="{r2_y}" x2="{r2_ci_hi}" y2="{r2_y}" stroke="#15803d" stroke-width="2" stroke-linecap="round"/>')
    svg.append(f'  <line x1="{r2_ci_lo}" y1="{r2_y - 6}" x2="{r2_ci_lo}" y2="{r2_y + 6}" stroke="#15803d" stroke-width="2" stroke-linecap="round"/>')
    svg.append(f'  <line x1="{r2_ci_hi}" y1="{r2_y - 6}" x2="{r2_ci_hi}" y2="{r2_y + 6}" stroke="#15803d" stroke-width="2" stroke-linecap="round"/>')

    # R2 Point
    svg.append(f'  <!-- R2 Point -->')
    svg.append(f'  <circle cx="{r2_x}" cy="{r2_y}" r="11" fill="#10b981" stroke="#065f46" stroke-width="2.5" filter="url(#shadow)"/>')

    # R2 Callout Card
    card_r2_x = r2_x - 300
    card_r2_y = r2_y - 110
    svg.append(f'  <!-- R2 Callout Card -->')
    svg.append(f'  <rect x="{card_r2_x}" y="{card_r2_y}" width="280" height="100" rx="6" fill="#ffffff" stroke="#34d399" stroke-width="1.5" filter="url(#shadow)"/>')
    svg.append(f'  <rect x="{card_r2_x}" y="{card_r2_y}" width="280" height="5" rx="2" fill="#10b981"/>')
    svg.append(f'  <text x="{card_r2_x + 14}" y="{card_r2_y + 24}" class="card-title" fill="#065f46">R2: Cheap Workhorse (glm-5.3-flash)</text>')
    svg.append(f'  <text x="{card_r2_x + 14}" y="{card_r2_y + 44}" class="card-metric">Cost: <tspan font-weight="700" fill="#047857">$0.0147</tspan> / grounded answer</text>')
    svg.append(f'  <text x="{card_r2_x + 14}" y="{card_r2_y + 64}" class="card-metric">pass³: <tspan font-weight="700" fill="#047857">22.67%</tspan> [16.7%, 30.0%] · pass@1: 63.11%</text>')
    svg.append(f'  <rect x="{card_r2_x + 14}" y="{card_r2_y + 74}" width="250" height="18" rx="9" fill="#d1fae5"/>')
    svg.append(f'  <text x="{card_r2_x + 24}" y="{card_r2_y + 87}" class="badge-text" fill="#065f46">★ 11.3× Higher Reliability · 18.3× Lower Cost</text>')

    # --- R6 Point ---
    r6_x = map_x(0.0)
    r6_y = map_y(0.0)
    svg.append(f'  <!-- R6 Boundary Point -->')
    svg.append(f'  <rect x="{r6_x - 6}" y="{r6_y - 6}" width="12" height="12" fill="#9ca3af" stroke="#4b5563" stroke-width="1.5" rx="2"/>')
    svg.append(f'  <text x="{r6_x + 15}" y="{r6_y - 10}" class="card-meta" fill="#4b5563">R6 (deepseek-v4-pro): 0.0% pass³ (Upstream Timeout Floor)</text>')

    # --- Bottom Legend ---
    leg_y = 640
    leg_w = 880
    leg_x = (width - leg_w) / 2
    svg.append(f'  <!-- Legend Container -->')
    svg.append(f'  <rect x="{leg_x}" y="{leg_y}" width="{leg_w}" height="42" rx="6" fill="#f9fafb" stroke="#e5e7eb" stroke-width="1"/>')
    svg.append(f'  <circle cx="{leg_x + 35}" cy="{leg_y + 21}" r="7" fill="#10b981" stroke="#065f46" stroke-width="1.5"/>')
    svg.append(f'  <text x="{leg_x + 52}" y="{leg_y + 26}" class="legend-text">Optimal Workhorse Tier (R2: glm-5.3-flash)</text>')
    svg.append(f'  <circle cx="{leg_x + 350}" cy="{leg_y + 21}" r="7" fill="#ef4444" stroke="#991b1b" stroke-width="1.5"/>')
    svg.append(f'  <text x="{leg_x + 367}" y="{leg_y + 26}" class="legend-text">High-Cost Frontier Tier (R4: gpt-5.6-luna)</text>')
    svg.append(f'  <line x1="{leg_x + 655}" y1="{leg_y + 21}" x2="{leg_x + 680}" y2="{leg_y + 21}" stroke="#111827" stroke-width="2"/>')
    svg.append(f'  <text x="{leg_x + 692}" y="{leg_y + 26}" class="legend-text">Wilson 95% Confidence Interval</text>')

    svg.append('</svg>')
    return '\n'.join(svg)

if __name__ == "__main__":
    content = build_cost_vs_passk_svg()
    
    # Target files
    output_dir = Path("projects/p06_passk")
    svg_paths = [
        output_dir / "figure_cost_vs_passk.svg",
        output_dir / "figure.svg",
    ]
    
    for p in svg_paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        print(f"Wrote {p}")
        
    # Render PNG
    try:
        tmp_svg = output_dir / "figure_cost_vs_passk.svg"
        subprocess.run(["qlmanage", "-t", "-s", "2400", "-o", "/tmp", str(tmp_svg)], check=True, capture_output=True)
        tmp_png = Path(f"/tmp/{tmp_svg.name}.png")
        if tmp_png.exists():
            shutil.copyfile(tmp_png, output_dir / "figure_cost_vs_passk.png")
            shutil.copyfile(tmp_png, output_dir / "figure.png")
            print(f"Rendered PNG to {output_dir / 'figure_cost_vs_passk.png'}")
    except Exception as e:
        print(f"PNG render warning: {e}")
