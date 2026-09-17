"""Generate figure.svg and figure.png for Project P7.

Reads projects/p07_variance/results.json and renders a clean, flat-style SVG
and 2x PNG rendering.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess


def main() -> None:
    base_dir = Path("projects/p07_variance")
    results_file = base_dir / "results.json"
    svg_file = base_dir / "figure.svg"
    png_file = base_dir / "figure.png"

    with open(results_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Extract metrics from results.json
    endpoints = data["endpoints"]
    aicredits = endpoints["aicredits"]
    agy = endpoints["agy"]

    rate_ai = aicredits["pass_rate"]
    rate_agy = agy["pass_rate"]
    ci_ai = aicredits["wilson_ci"]
    ci_agy = agy["wilson_ci"]
    n_ai = aicredits["n"]
    n_agy = agy["n"]

    contingency = data["contingency"]
    both = contingency["both_pass"]
    ai_only = contingency["aicredits_only"]
    agy_only = contingency["agy_only"]
    neither = contingency["neither"]

    mcnemar = data["mcnemar"]
    b = mcnemar["b"]
    c = mcnemar["c"]
    exact_p = mcnemar["exact_p_value"]

    latency = data["latency"]
    p95_ratio = latency["ratio_agy_over_aicredits"]["p95"]

    spend = data["total_spend_usd"]

    # Colors and styles
    # Accent color: Slate blue
    accent = "#4f6d8a"
    accent_tint = "#e8eef4"
    bg = "#ffffff"
    text_dark = "#1e293b"
    text_muted = "#64748b"
    hairline = "#cbd5e1"
    border_light = "#e2e8f0"

    # Layout coordinates (900x420)
    # Left panel: x from 40 to 520 (width 480). Plot area x: 100 to 500
    # Y-axis 0.80 to 1.00. Plot area y: 90 to 310 (height 220, range 0.20 => 1100 px per unit)
    y_min, y_max = 0.80, 1.00
    plot_top = 90
    plot_bottom = 310
    plot_height = plot_bottom - plot_top

    def val_to_y(val: float) -> float:
        return plot_bottom - ((val - y_min) / (y_max - y_min)) * plot_height

    # Ticks
    ticks = [0.80, 0.85, 0.90, 0.95, 1.00]

    # Bars:
    # Bar 1: aicredits x=180, width=80
    # Bar 2: agy x=340, width=80
    bar_width = 80
    bar_ai_x = 180
    bar_agy_x = 340

    bar_ai_y = val_to_y(rate_ai)
    bar_ai_h = plot_bottom - bar_ai_y

    bar_agy_y = val_to_y(rate_agy)
    bar_agy_h = plot_bottom - bar_agy_y

    # Error bars
    ci_ai_top = val_to_y(ci_ai[1])
    ci_ai_bot = val_to_y(ci_ai[0])
    ci_agy_top = val_to_y(ci_agy[1])
    ci_agy_bot = val_to_y(ci_agy[0])

    cap_width = 20

    # Right panel: x 560 to 860. Grid center x ~710, y ~110 to 270
    grid_x = 610
    grid_y = 110
    cell_w = 110
    cell_h = 75

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 420" width="900" height="420">
  <rect width="900" height="420" fill="{bg}"/>

  <!-- Left Panel -->
  <text x="40" y="45" font-family="Helvetica, Inter, sans-serif" font-size="16" font-weight="600" fill="{text_dark}">Grounded pass rate, same model, two gateways</text>

  <!-- Left Panel Grid & Axes -->
  <g stroke="{border_light}" stroke-width="1">
"""
    for t in ticks:
        ty = val_to_y(t)
        svg += f'    <line x1="90" y1="{ty:.1f}" x2="480" y2="{ty:.1f}" />\n'

    svg += f"""  </g>
  <g font-family="Helvetica, Inter, sans-serif" font-size="11" fill="{text_muted}" text-anchor="end">
"""
    for t in ticks:
        ty = val_to_y(t)
        svg += f'    <text x="82" y="{ty + 4:.1f}">{t:.2f}</text>\n'

    svg += f"""  </g>

  <!-- Y-axis line -->
  <line x1="90" y1="{plot_top}" x2="90" y2="{plot_bottom}" stroke="{hairline}" stroke-width="1"/>

  <!-- Left Panel Bars -->
  <!-- aicredits -->
  <rect x="{bar_ai_x}" y="{bar_ai_y:.1f}" width="{bar_width}" height="{bar_ai_h:.1f}" fill="{accent}" fill-opacity="0.25" stroke="{accent}" stroke-width="1.5"/>
  <text x="{bar_ai_x + bar_width/2}" y="{bar_ai_y - 12:.1f}" font-family="Helvetica, Inter, sans-serif" font-size="12" font-weight="600" fill="{text_dark}" text-anchor="middle">{rate_ai:.4f}</text>
  <text x="{bar_ai_x + bar_width/2}" y="{plot_bottom + 18}" font-family="Helvetica, Inter, sans-serif" font-size="12" font-weight="500" fill="{text_dark}" text-anchor="middle">AI Credits</text>
  <text x="{bar_ai_x + bar_width/2}" y="{plot_bottom + 32}" font-family="Helvetica, Inter, sans-serif" font-size="11" fill="{text_muted}" text-anchor="middle">n={n_ai}</text>

  <!-- aicredits Wilson error bar -->
  <line x1="{bar_ai_x + bar_width/2}" y1="{ci_ai_bot:.1f}" x2="{bar_ai_x + bar_width/2}" y2="{ci_ai_top:.1f}" stroke="{text_dark}" stroke-width="1.2"/>
  <line x1="{bar_ai_x + bar_width/2 - cap_width/2}" y1="{ci_ai_top:.1f}" x2="{bar_ai_x + bar_width/2 + cap_width/2}" y2="{ci_ai_top:.1f}" stroke="{text_dark}" stroke-width="1.2"/>
  <line x1="{bar_ai_x + bar_width/2 - cap_width/2}" y1="{ci_ai_bot:.1f}" x2="{bar_ai_x + bar_width/2 + cap_width/2}" y2="{ci_ai_bot:.1f}" stroke="{text_dark}" stroke-width="1.2"/>

  <!-- agy -->
  <rect x="{bar_agy_x}" y="{bar_agy_y:.1f}" width="{bar_width}" height="{bar_agy_h:.1f}" fill="{accent}" fill-opacity="0.25" stroke="{accent}" stroke-width="1.5"/>
  <text x="{bar_agy_x + bar_width/2}" y="{bar_agy_y - 12:.1f}" font-family="Helvetica, Inter, sans-serif" font-size="12" font-weight="600" fill="{text_dark}" text-anchor="middle">{rate_agy:.4f}</text>
  <text x="{bar_agy_x + bar_width/2}" y="{plot_bottom + 18}" font-family="Helvetica, Inter, sans-serif" font-size="12" font-weight="500" fill="{text_dark}" text-anchor="middle">Antigravity (agy)</text>
  <text x="{bar_agy_x + bar_width/2}" y="{plot_bottom + 32}" font-family="Helvetica, Inter, sans-serif" font-size="11" fill="{text_muted}" text-anchor="middle">n={n_agy}</text>

  <!-- agy Wilson error bar -->
  <line x1="{bar_agy_x + bar_width/2}" y1="{ci_agy_bot:.1f}" x2="{bar_agy_x + bar_width/2}" y2="{ci_agy_top:.1f}" stroke="{text_dark}" stroke-width="1.2"/>
  <line x1="{bar_agy_x + bar_width/2 - cap_width/2}" y1="{ci_agy_top:.1f}" x2="{bar_agy_x + bar_width/2 + cap_width/2}" y2="{ci_agy_top:.1f}" stroke="{text_dark}" stroke-width="1.2"/>
  <line x1="{bar_agy_x + bar_width/2 - cap_width/2}" y1="{ci_agy_bot:.1f}" x2="{bar_agy_x + bar_width/2 + cap_width/2}" y2="{ci_agy_bot:.1f}" stroke="{text_dark}" stroke-width="1.2"/>

  <!-- Left Panel Caption -->
  <text x="40" y="{plot_bottom + 58}" font-family="Helvetica, Inter, sans-serif" font-size="11" fill="{text_muted}">Wilson 95% intervals overlap on [{ci_ai[0]:.4f}, {ci_agy[1]:.4f}] — disjoint-CI criterion not met</text>

  <!-- Divider Line between panels -->
  <line x1="535" y1="40" x2="535" y2="370" stroke="{border_light}" stroke-width="1"/>

  <!-- Right Panel -->
  <text x="560" y="45" font-family="Helvetica, Inter, sans-serif" font-size="16" font-weight="600" fill="{text_dark}">Paired discordance, McNemar</text>

  <!-- Column/Row Headers for 2x2 table -->
  <g font-family="Helvetica, Inter, sans-serif" font-size="11" fill="{text_muted}" text-anchor="middle">
    <text x="{grid_x + cell_w/2}" y="{grid_y - 12}">agy Pass</text>
    <text x="{grid_x + cell_w*1.5}" y="{grid_y - 12}">agy Fail</text>
  </g>
  <g font-family="Helvetica, Inter, sans-serif" font-size="11" fill="{text_muted}" text-anchor="end">
    <text x="{grid_x - 12}" y="{grid_y + cell_h/2 + 4}">AI Credits Pass</text>
    <text x="{grid_x - 12}" y="{grid_y + cell_h*1.5 + 4}">AI Credits Fail</text>
  </g>

  <!-- 2x2 Grid cells -->
  <!-- Top-left: both pass (130) -->
  <rect x="{grid_x}" y="{grid_y}" width="{cell_w}" height="{cell_h}" fill="#ffffff" stroke="{border_light}" stroke-width="1"/>
  <text x="{grid_x + cell_w/2}" y="{grid_y + 36}" font-family="Helvetica, Inter, sans-serif" font-size="20" font-weight="600" fill="{text_dark}" text-anchor="middle">{both}</text>
  <text x="{grid_x + cell_w/2}" y="{grid_y + 54}" font-family="Helvetica, Inter, sans-serif" font-size="10" fill="{text_muted}" text-anchor="middle">both pass</text>

  <!-- Top-right: aicredits only (14) - Discordant, shaded -->
  <rect x="{grid_x + cell_w}" y="{grid_y}" width="{cell_w}" height="{cell_h}" fill="{accent_tint}" stroke="{accent}" stroke-width="1.5"/>
  <text x="{grid_x + cell_w*1.5}" y="{grid_y + 36}" font-family="Helvetica, Inter, sans-serif" font-size="20" font-weight="600" fill="{text_dark}" text-anchor="middle">{ai_only}</text>
  <text x="{grid_x + cell_w*1.5}" y="{grid_y + 54}" font-family="Helvetica, Inter, sans-serif" font-size="10" font-weight="500" fill="{accent}" text-anchor="middle">aicredits only</text>

  <!-- Bottom-left: agy only (4) - Discordant, shaded -->
  <rect x="{grid_x}" y="{grid_y + cell_h}" width="{cell_w}" height="{cell_h}" fill="{accent_tint}" stroke="{accent}" stroke-width="1.5"/>
  <text x="{grid_x + cell_w/2}" y="{grid_y + cell_h + 36}" font-family="Helvetica, Inter, sans-serif" font-size="20" font-weight="600" fill="{text_dark}" text-anchor="middle">{agy_only}</text>
  <text x="{grid_x + cell_w/2}" y="{grid_y + cell_h + 54}" font-family="Helvetica, Inter, sans-serif" font-size="10" font-weight="500" fill="{accent}" text-anchor="middle">agy only</text>

  <!-- Bottom-right: neither (2) -->
  <rect x="{grid_x + cell_w}" y="{grid_y + cell_h}" width="{cell_w}" height="{cell_h}" fill="#ffffff" stroke="{border_light}" stroke-width="1"/>
  <text x="{grid_x + cell_w*1.5}" y="{grid_y + cell_h + 36}" font-family="Helvetica, Inter, sans-serif" font-size="20" font-weight="600" fill="{text_dark}" text-anchor="middle">{neither}</text>
  <text x="{grid_x + cell_w*1.5}" y="{grid_y + cell_h + 54}" font-family="Helvetica, Inter, sans-serif" font-size="10" fill="{text_muted}" text-anchor="middle">neither</text>

  <!-- Right Panel Captions -->
  <text x="560" y="{grid_y + cell_h*2 + 32}" font-family="Helvetica, Inter, sans-serif" font-size="11" fill="{text_muted}">b={b}, c={c}, exact p={exact_p:.4f} — significant at 0.05</text>
  <text x="560" y="{grid_y + cell_h*2 + 50}" font-family="Helvetica, Inter, sans-serif" font-size="11" fill="{text_muted}">Latency p95: agy {p95_ratio:.1f}x AI Credits</text>

  <!-- Footer -->
  <line x1="40" y1="390" x2="860" y2="390" stroke="{border_light}" stroke-width="1"/>
  <text x="40" y="407" font-family="Helvetica, Inter, sans-serif" font-size="10" fill="{text_muted}">FAULTLINE P7 · 150 matched scenarios · MEC v1.3 · spend ${spend:.2f}</text>
</svg>
"""

    svg_file.write_text(svg, encoding="utf-8")
    print(f"Generated {svg_file}")

    # Render PNG at 2x via Headless Chrome
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    try:
        svg_abs = svg_file.resolve().as_uri()
        cmd = [
            chrome_path,
            "--headless",
            "--disable-gpu",
            "--force-device-scale-factor=2",
            f"--screenshot={png_file.resolve()}",
            "--window-size=900,420",
            svg_abs,
        ]
        res = subprocess.run(cmd, capture_output=True, timeout=15)
        if res.returncode == 0:
            print(f"Rendered 2x PNG to {png_file}")
        else:
            print(f"Notice: headless Chrome exited with {res.returncode}; shipped SVG only.")
    except Exception as e:
        print(f"Notice: Could not render PNG via headless Chrome ({e}); shipped SVG only.")


if __name__ == "__main__":
    main()
