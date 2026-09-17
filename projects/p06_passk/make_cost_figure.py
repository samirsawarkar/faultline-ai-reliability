"""Generate publication-grade SVG and PNG chart for Figure 6: Cost vs Empirical Joint Reliability."""
import os
import shutil
import subprocess
from pathlib import Path

def generate_cost_figure():
    width = 980
    height = 620

    chart_left = 120
    chart_right = width - 80
    chart_width = chart_right - chart_left  # 780

    chart_top = 100
    chart_bottom = 470
    chart_height = chart_bottom - chart_top  # 370

    x_max = 0.30
    y_max = 0.30

    def get_x(val):
        return chart_left + (val / x_max) * chart_width

    def get_y(val):
        return chart_bottom - (val / y_max) * chart_height

    svg = []
    svg.append(f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">')
    svg.append('  <rect width="100%" height="100%" fill="#ffffff" rx="8"/>')
    svg.append('  <style>')
    svg.append('    .title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 19px; font-weight: 700; fill: #111827; }')
    svg.append('    .subtitle { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 13px; fill: #4b5563; }')
    svg.append('    .axis-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 13px; font-weight: 600; fill: #374151; }')
    svg.append('    .axis { stroke: #9ca3af; stroke-width: 1.5; }')
    svg.append('    .grid { stroke: #f3f4f6; stroke-dasharray: 4,4; stroke-width: 1; }')
    svg.append('    .tick-label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 12px; fill: #4b5563; font-weight: 500; }')
    svg.append('    .card-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 13px; font-weight: 700; }')
    svg.append('    .card-metric { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 12px; fill: #1f2937; }')
    svg.append('    .card-meta { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 11px; fill: #6b7280; }')
    svg.append('    .badge-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 10px; font-weight: 700; }')
    svg.append('    .arrow-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 12px; font-weight: 600; fill: #059669; }')
    svg.append('    .legend-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 12px; fill: #374151; font-weight: 500; }')
    svg.append('  </style>')

    # Outer Card Border
    svg.append(f'  <rect x="1" y="1" width="{width-2}" height="{height-2}" fill="none" stroke="#e5e7eb" stroke-width="1.5" rx="8"/>')

    # Titles
    svg.append(f'  <text x="{width/2}" y="38" class="title" text-anchor="middle">Figure 6: Cost per Grounded Answer vs. Empirical Joint Reliability (pass\u00b3)</text>')
    svg.append(f'  <text x="{width/2}" y="60" class="subtitle" text-anchor="middle">The Economic Workhorse Inversion: Workhorse (R2) Achieves 11.3\u00d7 Higher Reliability at 18.3\u00d7 Lower Cost</text>')

    # Background Quadrant Highlights
    # Sweet spot: bottom-right
    sweet_x = get_x(0.15)
    sweet_y = get_y(0.15)
    svg.append('  <!-- Sweet spot quadrant -->')
    svg.append(f'  <rect x="{sweet_x}" y="{sweet_y}" width="{chart_right - sweet_x}" height="{chart_bottom - sweet_y}" fill="#f0fdf4" opacity="0.6" rx="4"/>')
    svg.append(f'  <text x="{chart_right - 15}" y="{chart_bottom - 15}" class="badge-text" fill="#16a34a" text-anchor="end">PARETO OPTIMAL: High Reliability / Low Cost</text>')

    # Fragile quadrant: top-left
    fragile_w = sweet_x - chart_left
    fragile_h = sweet_y - chart_top
    svg.append('  <!-- Fragile quadrant -->')
    svg.append(f'  <rect x="{chart_left}" y="{chart_top}" width="{fragile_w}" height="{fragile_h}" fill="#fef2f2" opacity="0.6" rx="4"/>')
    svg.append(f'  <text x="{chart_left + 15}" y="{chart_top + 20}" class="badge-text" fill="#dc2626" text-anchor="start">HIGH FRAGILITY: Low Reliability / High Cost</text>')

    # Y-Axis Grid & Ticks ($0.00 to $0.30 in steps of $0.05)
    for i in range(0, 7):
        cost_val = i * 0.05
        y = get_y(cost_val)
        svg.append(f'  <line x1="{chart_left}" y1="{y}" x2="{chart_right}" y2="{y}" class="grid"/>')
        svg.append(f'  <text x="{chart_left - 14}" y="{y + 4}" class="tick-label" text-anchor="end">${cost_val:.2f}</text>')

    # X-Axis Grid & Ticks (0% to 30% in steps of 5%)
    for i in range(0, 7):
        pct_val = i * 0.05
        x = get_x(pct_val)
        svg.append(f'  <line x1="{x}" y1="{chart_top}" x2="{x}" y2="{chart_bottom}" class="grid"/>')
        svg.append(f'  <text x="{x}" y="{chart_bottom + 20}" class="tick-label" text-anchor="middle">{pct_val:.0%}</text>')

    # Axes lines
    svg.append(f'  <line x1="{chart_left}" y1="{chart_bottom}" x2="{chart_right}" y2="{chart_bottom}" class="axis"/>')
    svg.append(f'  <line x1="{chart_left}" y1="{chart_top}" x2="{chart_left}" y2="{chart_bottom}" class="axis"/>')

    # Axis Titles
    svg.append(f'  <text x="{chart_left + chart_width/2}" y="{chart_bottom + 42}" class="axis-title" text-anchor="middle">Empirical Joint Reliability (pass\u00b3, k=3 on 150 Hard T3 Scenarios)</text>')
    svg.append(f'  <text x="32" y="{chart_top + chart_height/2}" class="axis-title" text-anchor="middle" transform="rotate(-90 32 {chart_top + chart_height/2})">Cost per Grounded Answer (USD)</text>')

    # Points coordinates
    r4_x = get_x(0.02)
    r4_y = get_y(0.2682)
    r2_x = get_x(0.2267)
    r2_y = get_y(0.0147)

    # Defs for marker arrows and drop shadows
    svg.append('  <defs>')
    svg.append('    <marker id="arrow-emerald" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">')
    svg.append('      <path d="M 0 1 L 10 5 L 0 9 z" fill="#059669"/>')
    svg.append('    </marker>')
    svg.append('    <filter id="shadow" x="-10%" y="-10%" width="130%" height="130%">')
    svg.append('      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.1"/>')
    svg.append('    </filter>')
    svg.append('  </defs>')

    # Draw curved transition arrow
    svg.append('  <!-- Inversion Trajectory Arrow -->')
    svg.append(f'  <path d="M {r4_x + 18} {r4_y + 12} Q {chart_left + chart_width*0.42} {chart_top + chart_height*0.48} {r2_x - 18} {r2_y - 12}" fill="none" stroke="#059669" stroke-width="2.5" stroke-dasharray="6,4" marker-end="url(#arrow-emerald)"/>')
    svg.append(f'  <rect x="{chart_left + chart_width*0.28}" y="{chart_top + chart_height*0.40}" width="220" height="28" rx="14" fill="#ecfdf5" stroke="#a7f3d0" stroke-width="1" filter="url(#shadow)"/>')
    svg.append(f'  <text x="{chart_left + chart_width*0.28 + 110}" y="{chart_top + chart_height*0.40 + 18}" class="arrow-text" text-anchor="middle">18.3\u00d7 Cost Reduction \u2192</text>')

    # 1. Plot R4 Point & Whisker & Card
    r4_ci_lo = get_x(0.0068)
    r4_ci_hi = get_x(0.0571)
    svg.append('  <!-- R4 CI Whisker -->')
    svg.append(f'  <line x1="{r4_ci_lo}" y1="{r4_y}" x2="{r4_ci_hi}" y2="{r4_y}" stroke="#b91c1c" stroke-width="2" stroke-linecap="round"/>')
    svg.append(f'  <line x1="{r4_ci_lo}" y1="{r4_y - 6}" x2="{r4_ci_lo}" y2="{r4_y + 6}" stroke="#b91c1c" stroke-width="2" stroke-linecap="round"/>')
    svg.append(f'  <line x1="{r4_ci_hi}" y1="{r4_y - 6}" x2="{r4_ci_hi}" y2="{r4_y + 6}" stroke="#b91c1c" stroke-width="2" stroke-linecap="round"/>')

    # R4 Scatter Node
    svg.append('  <!-- R4 Point -->')
    svg.append(f'  <circle cx="{r4_x}" cy="{r4_y}" r="10" fill="#ef4444" stroke="#991b1b" stroke-width="2.5" filter="url(#shadow)"/>')

    # R4 Callout Box (Positioned to the right of R4)
    r4_box_x = r4_x + 28
    r4_box_y = r4_y - 45
    svg.append('  <!-- R4 Callout Card -->')
    svg.append(f'  <rect x="{r4_box_x}" y="{r4_box_y}" width="255" height="95" rx="6" fill="#ffffff" stroke="#f87171" stroke-width="1.5" filter="url(#shadow)"/>')
    svg.append(f'  <rect x="{r4_box_x}" y="{r4_box_y}" width="255" height="6" rx="3" fill="#ef4444"/>')
    svg.append(f'  <text x="{r4_box_x + 12}" y="{r4_box_y + 24}" class="card-title" fill="#991b1b">R4: OpenAI Frontier (gpt-5.6-luna)</text>')
    svg.append(f'  <text x="{r4_box_x + 12}" y="{r4_box_y + 42}" class="card-metric">Cost: <tspan font-weight="700" fill="#b91c1c">$0.2682</tspan> / grounded answer</text>')
    svg.append(f'  <text x="{r4_box_x + 12}" y="{r4_box_y + 60}" class="card-metric">pass\u00b3: <tspan font-weight="700">2.00%</tspan> [0.68%, 5.71%] \u00b7 pass@1: 14.89%</text>')
    svg.append(f'  <rect x="{r4_box_x + 12}" y="{r4_box_y + 70}" width="225" height="16" rx="8" fill="#fee2e2"/>')
    svg.append(f'  <text x="{r4_box_x + 20}" y="{r4_box_y + 82}" class="badge-text" fill="#991b1b">Fragile Frontier: 28% Step-Cap Exhaustion</text>')

    # 2. Plot R2 Point & Whisker & Card
    r2_ci_lo = get_x(0.1670)
    r2_ci_hi = get_x(0.3000)
    svg.append('  <!-- R2 CI Whisker -->')
    svg.append(f'  <line x1="{r2_ci_lo}" y1="{r2_y}" x2="{r2_ci_hi}" y2="{r2_y}" stroke="#15803d" stroke-width="2" stroke-linecap="round"/>')
    svg.append(f'  <line x1="{r2_ci_lo}" y1="{r2_y - 6}" x2="{r2_ci_lo}" y2="{r2_y + 6}" stroke="#15803d" stroke-width="2" stroke-linecap="round"/>')
    svg.append(f'  <line x1="{r2_ci_hi}" y1="{r2_y - 6}" x2="{r2_ci_hi}" y2="{r2_y + 6}" stroke="#15803d" stroke-width="2" stroke-linecap="round"/>')

    # R2 Scatter Node
    svg.append('  <!-- R2 Point -->')
    svg.append(f'  <circle cx="{r2_x}" cy="{r2_y}" r="11" fill="#10b981" stroke="#065f46" stroke-width="2.5" filter="url(#shadow)"/>')

    # R2 Callout Box (Positioned above-left of R2)
    r2_box_x = r2_x - 280
    r2_box_y = r2_y - 110
    svg.append('  <!-- R2 Callout Card -->')
    svg.append(f'  <rect x="{r2_box_x}" y="{r2_box_y}" width="265" height="95" rx="6" fill="#ffffff" stroke="#34d399" stroke-width="1.5" filter="url(#shadow)"/>')
    svg.append(f'  <rect x="{r2_box_x}" y="{r2_box_y}" width="265" height="6" rx="3" fill="#10b981"/>')
    svg.append(f'  <text x="{r2_box_x + 12}" y="{r2_box_y + 24}" class="card-title" fill="#065f46">R2: Cheap Workhorse (glm-5.3-flash)</text>')
    svg.append(f'  <text x="{r2_box_x + 12}" y="{r2_box_y + 42}" class="card-metric">Cost: <tspan font-weight="700" fill="#047857">$0.0147</tspan> / grounded answer</text>')
    svg.append(f'  <text x="{r2_box_x + 12}" y="{r2_box_y + 60}" class="card-metric">pass\u00b3: <tspan font-weight="700" fill="#047857">22.67%</tspan> [16.7%, 30.0%] \u00b7 pass@1: 63.11%</text>')
    svg.append(f'  <rect x="{r2_box_x + 12}" y="{r2_box_y + 70}" width="235" height="16" rx="8" fill="#d1fae5"/>')
    svg.append(f'  <text x="{r2_box_x + 20}" y="{r2_box_y + 82}" class="badge-text" fill="#065f46">\u2605 11.3\u00d7 Higher Reliability \u00b7 18.3\u00d7 Lower Cost</text>')

    # 3. Plot R6 Boundary Marker (Timeout floor)
    r6_x = get_x(0.0)
    r6_y = get_y(0.0)
    svg.append('  <!-- R6 Boundary Point -->')
    svg.append(f'  <rect x="{r6_x - 6}" y="{r6_y - 6}" width="12" height="12" fill="#9ca3af" stroke="#4b5563" stroke-width="1.5" rx="2"/>')
    svg.append(f'  <text x="{r6_x + 16}" y="{r6_y - 8}" class="card-meta" fill="#4b5563">R6 (deepseek-v4-pro): 0.0% pass\u00b3 (Upstream Timeout Floor)</text>')

    # Bottom Legend Container
    legend_y = 560
    svg.append('  <!-- Legend Container -->')
    svg.append(f'  <rect x="{chart_left}" y="{legend_y}" width="{chart_width}" height="42" rx="6" fill="#f9fafb" stroke="#e5e7eb" stroke-width="1"/>')
    svg.append(f'  <circle cx="{chart_left + 30}" cy="{legend_y + 21}" r="7" fill="#10b981" stroke="#065f46" stroke-width="1.5"/>')
    svg.append(f'  <text x="{chart_left + 46}" y="{legend_y + 26}" class="legend-text">Optimal Workhorse Tier (R2)</text>')

    svg.append(f'  <circle cx="{chart_left + 280}" cy="{legend_y + 21}" r="7" fill="#ef4444" stroke="#991b1b" stroke-width="1.5"/>')
    svg.append(f'  <text x="{chart_left + 296}" y="{legend_y + 26}" class="legend-text">High-Cost Frontier Tier (R4)</text>')

    svg.append(f'  <line x1="{chart_left + 540}" y1="{legend_y + 21}" x2="{chart_left + 565}" y2="{legend_y + 21}" stroke="#111827" stroke-width="2"/>')
    svg.append(f'  <text x="{chart_left + 575}" y="{legend_y + 26}" class="legend-text">Wilson 95% Confidence Interval</text>')

    svg.append('</svg>')

    svg_content = '\n'.join(svg)

    svg_paths = [
        'projects/p06_passk/figure_cost_vs_passk.svg',
        'publications/publication_01_passk_reliability/figure_cost_vs_passk.svg',
    ]

    for p in svg_paths:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        print(f'Wrote SVG to {p}')

    # Render PNGs with QuickLook
    subprocess.run(['qlmanage', '-t', '-s', '2200', '-o', '/tmp', 'projects/p06_passk/figure_cost_vs_passk.svg'], check=True)
    tmp_png = '/tmp/figure_cost_vs_passk.svg.png'

    png_paths = [
        'projects/p06_passk/figure_cost_vs_passk.png',
        'publications/publication_01_passk_reliability/figure_cost_vs_passk.png',
    ]

    for p in png_paths:
        shutil.copyfile(tmp_png, p)
        print(f'Copied high-res PNG to {p}')

if __name__ == '__main__':
    generate_cost_figure()
