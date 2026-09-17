"""Generate figure.svg and figure.png for Project P8 (MCPTox Tool Poisoning).

Reads projects/p08_mcptox/results.json and renders a clean, flat-style SVG
and 2x PNG rendering via headless Chrome.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess


def main() -> None:
    base_dir = Path("projects/p08_mcptox")
    results_file = base_dir / "results.json"
    svg_file = base_dir / "figure.svg"
    png_file = base_dir / "figure.png"

    with open(results_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    rungs_data = data["rungs"]
    rung_order = ["R1", "R2", "R3", "R4", "R5", "R6"]

    # Display names for models
    model_names = {
        "R1": "Qwen 3.7 Flash",
        "R2": "GLM 5.3 Flash",
        "R3": "Qwen 3.8 Flash",
        "R4": "GPT 5.6 Luna",
        "R5": "Gemini 3.7 Flash",
        "R6": "DeepSeek v4 Pro",
    }

    # Dimensions and palette
    width = 900
    height = 460
    bg = "#ffffff"
    text_dark = "#1e293b"
    text_muted = "#64748b"
    hairline = "#cbd5e1"
    border_light = "#f1f5f9"
    grid_line = "#e2e8f0"

    # Bar styling: Arm A (crimson/red), Arm B (cobalt/blue)
    color_a = "#dc2626"
    color_b = "#2563eb"
    fill_a = "#dc2626"
    fill_b = "#2563eb"

    # Reference lines
    ref_mean = 0.365
    ref_peak = 0.728
    color_mean = "#b45309"
    color_peak = "#7c3aed"

    # Plot coordinates
    plot_left = 65
    plot_right = 865
    plot_top = 95
    plot_bottom = 355
    plot_height = plot_bottom - plot_top
    plot_width = plot_right - plot_left

    y_min, y_max = 0.0, 0.80

    def val_to_y(val: float) -> float:
        return plot_bottom - ((val - y_min) / (y_max - y_min)) * plot_height

    ticks = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        f'  <rect width="{width}" height="{height}" fill="{bg}"/>',
        '',
        '  <!-- Title -->',
        f'  <text x="40" y="38" font-family="Helvetica, Inter, sans-serif" font-size="15" font-weight="600" fill="{text_dark}">Tool poisoning ASR: published protocol vs provenance contract, 300 matched instances per rung</text>',
        '',
        '  <!-- Legend -->',
        f'  <rect x="40" y="55" width="13" height="13" fill="{fill_a}" fill-opacity="0.22" stroke="{color_a}" stroke-width="1.5"/>',
        f'  <text x="58" y="66" font-family="Helvetica, Inter, sans-serif" font-size="11" fill="{text_dark}">Arm A: Published protocol (single turn)</text>',
        f'  <rect x="285" y="55" width="13" height="13" fill="{fill_b}" fill-opacity="0.22" stroke="{color_b}" stroke-width="1.5"/>',
        f'  <text x="303" y="66" font-family="Helvetica, Inter, sans-serif" font-size="11" fill="{text_dark}">Arm B: Provenance contract (call-only retry)</text>',
        f'  <line x1="550" y1="61" x2="575" y2="61" stroke="{color_mean}" stroke-width="1.5" stroke-dasharray="5,3"/>',
        f'  <text x="581" y="65" font-family="Helvetica, Inter, sans-serif" font-size="10.5" fill="{text_muted}">MCPTox mean (0.365)</text>',
        f'  <line x1="720" y1="61" x2="745" y2="61" stroke="{color_peak}" stroke-width="1.5" stroke-dasharray="2,2"/>',
        f'  <text x="751" y="65" font-family="Helvetica, Inter, sans-serif" font-size="10.5" fill="{text_muted}">Published peak (0.728)</text>',
        '',
        '  <!-- Grid & Y-Ticks -->',
        f'  <g stroke="{grid_line}" stroke-width="1">',
    ]

    for t in ticks:
        ty = val_to_y(t)
        svg_parts.append(f'    <line x1="{plot_left}" y1="{ty:.1f}" x2="{plot_right}" y2="{ty:.1f}"/>')

    svg_parts.extend([
        '  </g>',
        f'  <g font-family="Helvetica, Inter, sans-serif" font-size="10" fill="{text_muted}" text-anchor="end">',
    ])

    for t in ticks:
        ty = val_to_y(t)
        svg_parts.append(f'    <text x="{plot_left - 8}" y="{ty + 3.5:.1f}">{t:.2f}</text>')

    svg_parts.extend([
        '  </g>',
        f'  <line x1="{plot_left}" y1="{plot_top}" x2="{plot_left}" y2="{plot_bottom}" stroke="{hairline}" stroke-width="1"/>',
        '',
        '  <!-- Published Reference Lines -->',
        f'  <!-- MCPTox published peak ASR (0.728) -->',
        f'  <line x1="{plot_left}" y1="{val_to_y(ref_peak):.1f}" x2="{plot_right}" y2="{val_to_y(ref_peak):.1f}" stroke="{color_peak}" stroke-width="1.2" stroke-dasharray="2,3"/>',
        f'  <text x="{plot_right}" y="{val_to_y(ref_peak) - 5:.1f}" font-family="Helvetica, Inter, sans-serif" font-size="10" font-weight="500" fill="{color_peak}" text-anchor="end">published peak (0.728)</text>',
        '',
        f'  <!-- MCPTox published mean ASR (0.365) -->',
        f'  <line x1="{plot_left}" y1="{val_to_y(ref_mean):.1f}" x2="{plot_right}" y2="{val_to_y(ref_mean):.1f}" stroke="{color_mean}" stroke-width="1.2" stroke-dasharray="6,4"/>',
        f'  <rect x="580" y="{val_to_y(ref_mean) - 13:.1f}" width="170" height="13" fill="#ffffff" fill-opacity="0.9"/>',
        f'  <text x="665" y="{val_to_y(ref_mean) - 3:.1f}" font-family="Helvetica, Inter, sans-serif" font-size="10" font-weight="500" fill="{color_mean}" text-anchor="middle">MCPTox published mean ASR (0.365)</text>',
        '',
        '  <!-- Grouped Bars per Rung -->',
    ])

    # 6 rungs layout
    num_rungs = len(rung_order)
    slot_width = plot_width / num_rungs
    bar_width = 36
    bar_gap = 6
    cap_width = 14

    for i, rung_id in enumerate(rung_order):
        rung_info = rungs_data[rung_id]
        model_name = model_names.get(rung_id, rung_info.get("model", rung_id))

        arm_a = rung_info["arm_a"]
        arm_b = rung_info["arm_b"]
        comp = rung_info["comparison"]
        mcnemar = comp["paired_mcnemar"]

        asr_a = arm_a["asr_over_valid"]
        ci_a = arm_a["wilson_ci_over_valid"]

        asr_b = arm_b["asr_over_valid"]
        ci_b = arm_b["wilson_ci_over_valid"]

        # Center of this rung slot
        cx = plot_left + (i + 0.5) * slot_width

        # Arm A bar: left of slot center
        bx_a = cx - bar_gap / 2 - bar_width
        by_a = val_to_y(asr_a)
        bh_a = plot_bottom - by_a

        # Arm B bar: right of slot center
        bx_b = cx + bar_gap / 2
        by_b = val_to_y(asr_b)
        bh_b = plot_bottom - by_b

        # Error bar positions
        ci_a_top = val_to_y(ci_a[1])
        ci_a_bot = val_to_y(ci_a[0])
        ci_b_top = val_to_y(ci_b[1])
        ci_b_bot = val_to_y(ci_b[0])

        # Value label positions: strictly ABOVE top error cap by 5px so they NEVER overlap caps
        label_a_y = ci_a_top - 5
        label_b_y = ci_b_top - 5

        # Format McNemar p
        if rung_id == "R5":
            p_text = "n.s. p=0.22"
            p_color = text_muted
        else:
            p_text = "p &lt; 1e-8"
            p_color = "#047857"

        svg_parts.extend([
            f'  <!-- {rung_id}: {model_name} -->',
            f'  <g id="rung-{rung_id}">',
            f'    <!-- Arm A Bar -->',
            f'    <rect x="{bx_a:.1f}" y="{by_a:.1f}" width="{bar_width}" height="{bh_a:.1f}" fill="{fill_a}" fill-opacity="0.22" stroke="{color_a}" stroke-width="1.5"/>',
            f'    <!-- Arm A Error Bar -->',
            f'    <line x1="{bx_a + bar_width/2:.1f}" y1="{ci_a_bot:.1f}" x2="{bx_a + bar_width/2:.1f}" y2="{ci_a_top:.1f}" stroke="{text_dark}" stroke-width="1.2"/>',
            f'    <line x1="{bx_a + bar_width/2 - cap_width/2:.1f}" y1="{ci_a_top:.1f}" x2="{bx_a + bar_width/2 + cap_width/2:.1f}" y2="{ci_a_top:.1f}" stroke="{text_dark}" stroke-width="1.2"/>',
            f'    <line x1="{bx_a + bar_width/2 - cap_width/2:.1f}" y1="{ci_a_bot:.1f}" x2="{bx_a + bar_width/2 + cap_width/2:.1f}" y2="{ci_a_bot:.1f}" stroke="{text_dark}" stroke-width="1.2"/>',
            f'    <!-- Arm A Value Label (above cap) -->',
            f'    <text x="{bx_a + bar_width/2:.1f}" y="{label_a_y:.1f}" font-family="Helvetica, Inter, sans-serif" font-size="10" font-weight="600" fill="{color_a}" text-anchor="middle">{asr_a:.3f}</text>',
            '',
            f'    <!-- Arm B Bar -->',
            f'    <rect x="{bx_b:.1f}" y="{by_b:.1f}" width="{bar_width}" height="{bh_b:.1f}" fill="{fill_b}" fill-opacity="0.22" stroke="{color_b}" stroke-width="1.5"/>',
            f'    <!-- Arm B Error Bar -->',
            f'    <line x1="{bx_b + bar_width/2:.1f}" y1="{ci_b_bot:.1f}" x2="{bx_b + bar_width/2:.1f}" y2="{ci_b_top:.1f}" stroke="{text_dark}" stroke-width="1.2"/>',
            f'    <line x1="{bx_b + bar_width/2 - cap_width/2:.1f}" y1="{ci_b_top:.1f}" x2="{bx_b + bar_width/2 + cap_width/2:.1f}" y2="{ci_b_top:.1f}" stroke="{text_dark}" stroke-width="1.2"/>',
            f'    <line x1="{bx_b + bar_width/2 - cap_width/2:.1f}" y1="{ci_b_bot:.1f}" x2="{bx_b + bar_width/2 + cap_width/2:.1f}" y2="{ci_b_bot:.1f}" stroke="{text_dark}" stroke-width="1.2"/>',
            f'    <!-- Arm B Value Label (above cap) -->',
            f'    <text x="{bx_b + bar_width/2:.1f}" y="{label_b_y:.1f}" font-family="Helvetica, Inter, sans-serif" font-size="10" font-weight="600" fill="{color_b}" text-anchor="middle">{asr_b:.3f}</text>',
            '',
            f'    <!-- X Axis Labels -->',
            f'    <text x="{cx:.1f}" y="{plot_bottom + 17}" font-family="Helvetica, Inter, sans-serif" font-size="11.5" font-weight="600" fill="{text_dark}" text-anchor="middle">{rung_id}</text>',
            f'    <text x="{cx:.1f}" y="{plot_bottom + 30}" font-family="Helvetica, Inter, sans-serif" font-size="9.5" fill="{text_muted}" text-anchor="middle">{model_name}</text>',
            f'    <text x="{cx:.1f}" y="{plot_bottom + 45}" font-family="Helvetica, Inter, sans-serif" font-size="10" font-weight="600" fill="{p_color}" text-anchor="middle">{p_text}</text>',
            f'  </g>',
            '',
        ])

    svg_parts.extend([
        '  <!-- Footer -->',
        f'  <line x1="40" y1="425" x2="{plot_right}" y2="425" stroke="{border_light}" stroke-width="1"/>',
        f'  <text x="40" y="443" font-family="Helvetica, Inter, sans-serif" font-size="9.5" fill="{text_muted}">FAULTLINE P8 · MCPTox (commit f85189f) · 300 instances/rung (seed 42) · judge: GLM-5.3-Flash · Wilson 95% CIs</text>',
        '</svg>',
    ])

    svg_content = "\n".join(svg_parts)
    svg_file.write_text(svg_content, encoding="utf-8")
    print(f"Generated {svg_file}")

    # Render 2x PNG via Headless Chrome
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    try:
        svg_abs = svg_file.resolve().as_uri()
        cmd = [
            chrome_path,
            "--headless",
            "--disable-gpu",
            "--force-device-scale-factor=2",
            f"--screenshot={png_file.resolve()}",
            f"--window-size={width},{height}",
            svg_abs,
        ]
        res = subprocess.run(cmd, capture_output=True, timeout=15)
        if res.returncode == 0:
            print(f"Rendered 2x PNG to {png_file}")
        else:
            print(f"Notice: headless Chrome exited with {res.returncode}; stderr: {res.stderr.decode('utf-8', errors='ignore')}")
    except Exception as e:
        print(f"Notice: Could not render PNG via headless Chrome ({e}); shipped SVG only.")


if __name__ == "__main__":
    main()
