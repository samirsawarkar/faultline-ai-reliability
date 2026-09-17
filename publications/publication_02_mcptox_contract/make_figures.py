"""Generate publication figures for Publication #2 (MCPTox Tool Poisoning & Provenance Contract).

Produces:
  - fig_1_asr_by_rung.svg / .png (copied from projects/p08_mcptox/figure.svg / .png)
  - fig_2_blocked_vs_false.svg / .png (attacks removed vs benign blocked per rung)
  - fig_3_paradigm.svg / .png (pooled ASR and counterfactual replay block-rate by paradigm)
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import struct
import subprocess
import xml.sax.saxutils as saxutils


def esc(text: str | int | float) -> str:
    """Escape text for safe XML embedding."""
    return saxutils.escape(str(text))


def get_png_dimensions(path: Path) -> tuple[int, int]:
    """Read PNG dimensions from IHDR chunk using standard library."""
    with open(path, "rb") as f:
        data = f.read(24)
        if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError(f"{path} is not a valid PNG file")
        w, h = struct.unpack(">II", data[16:24])
        return w, h


def render_svg_to_png(svg_file: Path, png_file: Path, width: int, height: int) -> None:
    """Render 2x PNG via headless Google Chrome."""
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    svg_uri = svg_file.resolve().as_uri()
    cmd = [
        chrome_path,
        "--headless",
        "--disable-gpu",
        "--force-device-scale-factor=2",
        f"--screenshot={png_file.resolve()}",
        f"--window-size={width},{height}",
        svg_uri,
    ]
    res = subprocess.run(cmd, capture_output=True, timeout=15)
    if res.returncode != 0:
        raise RuntimeError(
            f"Headless Chrome rendering failed with code {res.returncode}: {res.stderr.decode('utf-8', errors='ignore')}"
        )


def make_fig_2(analysis_data: dict, out_dir: Path) -> None:
    """Generate fig_2_blocked_vs_false.svg and .png."""
    svg_file = out_dir / "fig_2_blocked_vs_false.svg"
    png_file = out_dir / "fig_2_blocked_vs_false.png"

    rung_order = ["R1", "R2", "R3", "R4", "R5", "R6"]
    model_names = {
        "R1": "Qwen 3.7 Flash",
        "R2": "GLM 5.3 Flash",
        "R3": "Qwen 3.8 Flash",
        "R4": "GPT 5.6 Luna",
        "R5": "Gemini 3.7 Flash",
        "R6": "DeepSeek v4 Pro",
    }

    width = 900
    height = 460
    bg = "#ffffff"
    text_dark = "#1e293b"
    text_muted = "#64748b"
    hairline = "#cbd5e1"
    border_light = "#f1f5f9"
    grid_line = "#e2e8f0"

    color_rem = "#2563eb"
    fill_rem = "#2563eb"
    color_fbp = "#d97706"
    fill_fbp = "#d97706"

    plot_left = 65
    plot_right = 865
    plot_top = 95
    plot_bottom = 355
    plot_height = plot_bottom - plot_top
    plot_width = plot_right - plot_left

    y_min, y_max = 0, 120
    ticks = [0, 20, 40, 60, 80, 100, 120]

    def val_to_y(val: float) -> float:
        return plot_bottom - ((val - y_min) / (y_max - y_min)) * plot_height

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        f'  <rect width="{width}" height="{height}" fill="{bg}"/>',
        '',
        '  <!-- Title -->',
        f'  <text x="40" y="38" font-family="Helvetica, Inter, sans-serif" font-size="15" font-weight="600" fill="{text_dark}">{esc("Contract defense vs benign impact: attacks removed vs false blocks (N=300 per rung)")}</text>',
        '',
        '  <!-- Legend -->',
        f'  <rect x="40" y="55" width="13" height="13" fill="{fill_rem}" fill-opacity="0.22" stroke="{color_rem}" stroke-width="1.5"/>',
        f'  <text x="58" y="66" font-family="Helvetica, Inter, sans-serif" font-size="11" fill="{text_dark}">{esc("Attacks removed (Arm A Success not Arm B Success)")}</text>',
        f'  <rect x="440" y="55" width="13" height="13" fill="{fill_fbp}" fill-opacity="0.22" stroke="{color_fbp}" stroke-width="1.5"/>',
        f'  <text x="458" y="66" font-family="Helvetica, Inter, sans-serif" font-size="11" fill="{text_dark}">{esc("Benign blocked (false_block_proxy)")}</text>',
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
        svg_parts.append(f'    <text x="{plot_left - 8}" y="{ty + 3.5:.1f}">{esc(t)}</text>')

    svg_parts.extend([
        '  </g>',
        f'  <line x1="{plot_left}" y1="{plot_top}" x2="{plot_left}" y2="{plot_bottom}" stroke="{hairline}" stroke-width="1"/>',
        '',
        '  <!-- Grouped Bars per Rung -->',
    ])

    num_rungs = len(rung_order)
    slot_width = plot_width / num_rungs
    bar_width = 32
    bar_gap = 6

    for i, rung_id in enumerate(rung_order):
        rung_data = analysis_data["rungs"][rung_id]
        model_name = model_names.get(rung_id, rung_data.get("model", rung_id))
        ar = rung_data["comparison"]["attacks_removed"]
        fbp = rung_data["arm_b"]["false_block_proxy"]

        cx = plot_left + (i + 0.5) * slot_width

        bx_1 = cx - bar_gap / 2 - bar_width
        by_1 = val_to_y(ar)
        bh_1 = plot_bottom - by_1

        bx_2 = cx + bar_gap / 2
        by_2 = val_to_y(fbp)
        bh_2 = plot_bottom - by_2

        svg_parts.extend([
            f'  <!-- {esc(rung_id)}: {esc(model_name)} -->',
            f'  <g id="rung-{esc(rung_id)}">',
            f'    <!-- Attacks Removed Bar -->',
            f'    <rect x="{bx_1:.1f}" y="{by_1:.1f}" width="{bar_width}" height="{bh_1:.1f}" fill="{fill_rem}" fill-opacity="0.22" stroke="{color_rem}" stroke-width="1.5"/>',
            f'    <text x="{bx_1 + bar_width/2:.1f}" y="{by_1 - 5:.1f}" font-family="Helvetica, Inter, sans-serif" font-size="10" font-weight="600" fill="{color_rem}" text-anchor="middle">{esc(ar)}</text>',
            '',
            f'    <!-- Benign Blocked Bar -->',
            f'    <rect x="{bx_2:.1f}" y="{by_2:.1f}" width="{bar_width}" height="{bh_2:.1f}" fill="{fill_fbp}" fill-opacity="0.22" stroke="{color_fbp}" stroke-width="1.5"/>',
            f'    <text x="{bx_2 + bar_width/2:.1f}" y="{by_2 - 5:.1f}" font-family="Helvetica, Inter, sans-serif" font-size="10" font-weight="600" fill="{color_fbp}" text-anchor="middle">{esc(fbp)}</text>',
            '',
            f'    <!-- X Labels -->',
            f'    <text x="{cx:.1f}" y="{plot_bottom + 17}" font-family="Helvetica, Inter, sans-serif" font-size="11.5" font-weight="600" fill="{text_dark}" text-anchor="middle">{esc(rung_id)}</text>',
            f'    <text x="{cx:.1f}" y="{plot_bottom + 30}" font-family="Helvetica, Inter, sans-serif" font-size="9.5" fill="{text_muted}" text-anchor="middle">{esc(model_name)}</text>',
            f'  </g>',
            '',
        ])

    svg_parts.extend([
        '  <!-- Footer -->',
        f'  <line x1="40" y1="425" x2="{plot_right}" y2="425" stroke="{border_light}" stroke-width="1"/>',
        f'  <text x="40" y="443" font-family="Helvetica, Inter, sans-serif" font-size="9.5" fill="{text_muted}">{esc("FAULTLINE P8 · MCPTox (commit f85189f) · 300 instances/rung · attacks removed = Arm A Success & not Arm B Success · false_block_proxy = benign calls blocked")}</text>',
        '</svg>',
    ])

    svg_file.write_text("\n".join(svg_parts), encoding="utf-8")
    render_svg_to_png(svg_file, png_file, width, height)


def make_fig_3(analysis_data: dict, replay_data: dict, out_dir: Path) -> None:
    """Generate fig_3_paradigm.svg and .png."""
    svg_file = out_dir / "fig_3_paradigm.svg"
    png_file = out_dir / "fig_3_paradigm.png"

    paradigms = ["Template-1", "Template-2", "Template-3"]
    paradigm_labels = {
        "Template-1": ("Template-1", "explicit trigger"),
        "Template-2": ("Template-2", "implicit trigger via function hijack"),
        "Template-3": ("Template-3", "parameter tampering"),
    }

    width = 900
    height = 460
    bg = "#ffffff"
    text_dark = "#1e293b"
    text_muted = "#64748b"
    hairline = "#cbd5e1"
    border_light = "#f1f5f9"
    grid_line = "#e2e8f0"

    color_a = "#dc2626"
    fill_a = "#dc2626"
    color_b = "#2563eb"
    fill_b = "#2563eb"
    color_rep = "#059669"

    plot_left = 65
    plot_right = 865
    plot_top = 95
    plot_bottom = 355
    plot_height = plot_bottom - plot_top
    plot_width = plot_right - plot_left

    y_min, y_max = 0.0, 1.05
    ticks = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

    def val_to_y(val: float) -> float:
        return plot_bottom - ((val - y_min) / (y_max - y_min)) * plot_height

    diamond_label = esc("Replay block-rate on the MCPTox authors' recorded Success responses (replay_results.json)")

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        f'  <rect width="{width}" height="{height}" fill="{bg}"/>',
        '',
        '  <!-- Title -->',
        f'  <text x="40" y="38" font-family="Helvetica, Inter, sans-serif" font-size="15" font-weight="600" fill="{text_dark}">{esc("Attack success and replay block-rate across poisoning paradigms (pooled N=1800)")}</text>',
        '',
        '  <!-- Legend -->',
        f'  <rect x="40" y="55" width="13" height="13" fill="{fill_a}" fill-opacity="0.22" stroke="{color_a}" stroke-width="1.5"/>',
        f'  <text x="58" y="66" font-family="Helvetica, Inter, sans-serif" font-size="10.5" fill="{text_dark}">{esc("Arm A: Baseline ASR")}</text>',
        f'  <rect x="175" y="55" width="13" height="13" fill="{fill_b}" fill-opacity="0.22" stroke="{color_b}" stroke-width="1.5"/>',
        f'  <text x="193" y="66" font-family="Helvetica, Inter, sans-serif" font-size="10.5" fill="{text_dark}">{esc("Arm B: Runtime contract ASR")}</text>',
        f'  <polygon points="365,61.5 371,55.5 377,61.5 371,67.5" fill="{color_rep}" stroke="{color_rep}" stroke-width="1.5"/>',
        f'  <text x="383" y="66" font-family="Helvetica, Inter, sans-serif" font-size="10" fill="{text_dark}">{diamond_label}</text>',
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
        svg_parts.append(f'    <text x="{plot_left - 8}" y="{ty + 3.5:.1f}">{esc(f"{t:.1f}")}</text>')

    svg_parts.extend([
        '  </g>',
        f'  <line x1="{plot_left}" y1="{plot_top}" x2="{plot_left}" y2="{plot_bottom}" stroke="{hairline}" stroke-width="1"/>',
        '',
        '  <!-- Grouped Elements per Paradigm -->',
    ])

    slot_width = plot_width / len(paradigms)
    bar_width = 34
    cap_width = 12

    for i, p in enumerate(paradigms):
        p_data = analysis_data["pooled"]["by_paradigm"][p]
        rep_p = replay_data["pooled"]["by_paradigm"][p]
        title_p, desc_p = paradigm_labels[p]

        cx = plot_left + (i + 0.5) * slot_width

        # Arm A
        asr_a = p_data["arm_a"]["asr_over_valid"]
        ci_a = p_data["arm_a"]["wilson_ci_over_valid"]
        bx_a = cx - 55 - bar_width / 2
        by_a = val_to_y(asr_a)
        bh_a = plot_bottom - by_a
        ci_a_top = val_to_y(ci_a[1])
        ci_a_bot = val_to_y(ci_a[0])

        # Arm B
        asr_b = p_data["arm_b"]["asr_over_valid"]
        ci_b = p_data["arm_b"]["wilson_ci_over_valid"]
        bx_b = cx - bar_width / 2
        by_b = val_to_y(asr_b)
        bh_b = plot_bottom - by_b
        ci_b_top = val_to_y(ci_b[1])
        ci_b_bot = val_to_y(ci_b[0])

        # Replay Block Rate (marker)
        br = rep_p["block_rate_on_success"]
        ci_br = rep_p["block_rate_ci"]
        xm = cx + 55
        ym = val_to_y(br)
        ci_br_top = val_to_y(ci_br[1])
        ci_br_bot = val_to_y(ci_br[0])

        svg_parts.extend([
            f'  <!-- {esc(p)} -->',
            f'  <g id="paradigm-{esc(p)}">',
            f'    <!-- Arm A Bar & Error Bar -->',
            f'    <rect x="{bx_a:.1f}" y="{by_a:.1f}" width="{bar_width}" height="{bh_a:.1f}" fill="{fill_a}" fill-opacity="0.22" stroke="{color_a}" stroke-width="1.5"/>',
            f'    <line x1="{bx_a + bar_width/2:.1f}" y1="{ci_a_bot:.1f}" x2="{bx_a + bar_width/2:.1f}" y2="{ci_a_top:.1f}" stroke="{text_dark}" stroke-width="1.2"/>',
            f'    <line x1="{bx_a + bar_width/2 - cap_width/2:.1f}" y1="{ci_a_top:.1f}" x2="{bx_a + bar_width/2 + cap_width/2:.1f}" y2="{ci_a_top:.1f}" stroke="{text_dark}" stroke-width="1.2"/>',
            f'    <line x1="{bx_a + bar_width/2 - cap_width/2:.1f}" y1="{ci_a_bot:.1f}" x2="{bx_a + bar_width/2 + cap_width/2:.1f}" y2="{ci_a_bot:.1f}" stroke="{text_dark}" stroke-width="1.2"/>',
            f'    <text x="{bx_a + bar_width/2:.1f}" y="{ci_a_top - 5:.1f}" font-family="Helvetica, Inter, sans-serif" font-size="10" font-weight="600" fill="{color_a}" text-anchor="middle">{esc(f"{asr_a:.3f}")}</text>',
            '',
            f'    <!-- Arm B Bar & Error Bar -->',
            f'    <rect x="{bx_b:.1f}" y="{by_b:.1f}" width="{bar_width}" height="{bh_b:.1f}" fill="{fill_b}" fill-opacity="0.22" stroke="{color_b}" stroke-width="1.5"/>',
            f'    <line x1="{bx_b + bar_width/2:.1f}" y1="{ci_b_bot:.1f}" x2="{bx_b + bar_width/2:.1f}" y2="{ci_b_top:.1f}" stroke="{text_dark}" stroke-width="1.2"/>',
            f'    <line x1="{bx_b + bar_width/2 - cap_width/2:.1f}" y1="{ci_b_top:.1f}" x2="{bx_b + bar_width/2 + cap_width/2:.1f}" y2="{ci_b_top:.1f}" stroke="{text_dark}" stroke-width="1.2"/>',
            f'    <line x1="{bx_b + bar_width/2 - cap_width/2:.1f}" y1="{ci_b_bot:.1f}" x2="{bx_b + bar_width/2 + cap_width/2:.1f}" y2="{ci_b_bot:.1f}" stroke="{text_dark}" stroke-width="1.2"/>',
            f'    <text x="{bx_b + bar_width/2:.1f}" y="{ci_b_top - 5:.1f}" font-family="Helvetica, Inter, sans-serif" font-size="10" font-weight="600" fill="{color_b}" text-anchor="middle">{esc(f"{asr_b:.3f}")}</text>',
            '',
            f'    <!-- Replay Block Rate Marker & Error Bar -->',
            f'    <line x1="{xm:.1f}" y1="{ci_br_bot:.1f}" x2="{xm:.1f}" y2="{ci_br_top:.1f}" stroke="{color_rep}" stroke-width="1.2"/>',
            f'    <line x1="{xm - cap_width/2:.1f}" y1="{ci_br_top:.1f}" x2="{xm + cap_width/2:.1f}" y2="{ci_br_top:.1f}" stroke="{color_rep}" stroke-width="1.2"/>',
            f'    <line x1="{xm - cap_width/2:.1f}" y1="{ci_br_bot:.1f}" x2="{xm + cap_width/2:.1f}" y2="{ci_br_bot:.1f}" stroke="{color_rep}" stroke-width="1.2"/>',
            f'    <polygon points="{xm:.1f},{ym-6:.1f} {xm+6:.1f},{ym:.1f} {xm:.1f},{ym+6:.1f} {xm-6:.1f},{ym:.1f}" fill="{color_rep}" stroke="{color_rep}" stroke-width="1.5"/>',
            f'    <text x="{xm:.1f}" y="{ci_br_top - 5:.1f}" font-family="Helvetica, Inter, sans-serif" font-size="10" font-weight="600" fill="{color_rep}" text-anchor="middle">{esc(f"{br:.3f}")}</text>',
            '',
            f'    <!-- X Labels -->',
            f'    <text x="{cx:.1f}" y="{plot_bottom + 17}" font-family="Helvetica, Inter, sans-serif" font-size="11.5" font-weight="600" fill="{text_dark}" text-anchor="middle">{esc(title_p)}</text>',
            f'    <text x="{cx:.1f}" y="{plot_bottom + 30}" font-family="Helvetica, Inter, sans-serif" font-size="9.5" fill="{text_muted}" text-anchor="middle">{esc(desc_p)}</text>',
            f'  </g>',
            '',
        ])

    svg_parts.extend([
        '  <!-- Footer -->',
        f'  <line x1="40" y1="425" x2="{plot_right}" y2="425" stroke="{border_light}" stroke-width="1"/>',
        f'  <text x="40" y="443" font-family="Helvetica, Inter, sans-serif" font-size="9.5" fill="{text_muted}">{esc("FAULTLINE P8 · MCPTox (commit f85189f) · 1800 instances pooled · Wilson 95% CIs · diamonds = counterfactual replay block-rate")}</text>',
        '</svg>',
    ])

    svg_file.write_text("\n".join(svg_parts), encoding="utf-8")
    render_svg_to_png(svg_file, png_file, width, height)


def main() -> None:
    src_dir = Path("projects/p08_mcptox")
    out_dir = Path("publications/publication_02_mcptox_contract")
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Copy fig_1_asr_by_rung.svg and .png from projects/p08_mcptox
    shutil.copyfile(src_dir / "figure.svg", out_dir / "fig_1_asr_by_rung.svg")
    shutil.copyfile(src_dir / "figure.png", out_dir / "fig_1_asr_by_rung.png")

    # Load data
    with open(src_dir / "analysis.json", "r", encoding="utf-8") as f:
        analysis_data = json.load(f)
    with open(src_dir / "replay_results.json", "r", encoding="utf-8") as f:
        replay_data = json.load(f)

    # 2. Make fig_2
    make_fig_2(analysis_data, out_dir)

    # 3. Make fig_3
    make_fig_3(analysis_data, replay_data, out_dir)

    # 4. Inspect rendered PNG dimensions
    pngs = ["fig_1_asr_by_rung.png", "fig_2_blocked_vs_false.png", "fig_3_paradigm.png"]
    for name in pngs:
        png_path = out_dir / name
        w, h = get_png_dimensions(png_path)
        print(f"{name}: {w}x{h}")


if __name__ == "__main__":
    main()
