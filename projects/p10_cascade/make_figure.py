"""Generate publication-standard figure for Project P10: Calibrated Cascade."""
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
        res = json.load(f)

    # Dynamic numbers read directly from results.json
    all_test = res.get("all_test_metrics", {})
    test_m = res.get("test_metrics", {})
    frontier_pts = res.get("frontier_points", [])
    p6_rep = res.get("p6_replicate", {})
    p6_side = p6_rep.get("infra_excluded", {}).get("side_by_side", {})

    r2_test = test_m.get("r2_only", {})
    r4_test = test_m.get("r4_only", {})
    cascade_test = test_m.get("escalate_if_not_answered_or_steps_ge_23", test_m.get("escalate_if_not_answered", {}))

    width = 1600
    height = 700

    # Okabe-Ito / scientific palette
    c_blue = "#2563eb"     # Frontier / R2
    c_green = "#009E73"    # Cascade non-dominated
    c_red = "#dc2626"      # Dominated / R4
    c_text = "#1e293b"     # Slate 800
    c_muted = "#64748b"    # Slate 500
    c_grid = "#f1f5f9"     # Slate 100
    c_axis = "#94a3b8"     # Slate 400

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">')
    svg.append(f'  <rect width="{width}" height="{height}" fill="#ffffff"/>')

    # Main title
    svg.append('  <!-- Title -->')
    svg.append(f'  <text x="50" y="45" font-family="Helvetica, Arial, sans-serif" font-size="18" font-weight="600" fill="{c_text}">Calibrated model cascade and empirical Pareto frontier across model rungs</text>')

    # -------------------------------------------------------------
    # PANEL (a): Held-out test split (n=30)
    # -------------------------------------------------------------
    svg.append('  <!-- Panel (a) -->')
    svg.append(f'  <text x="50" y="85" font-family="Helvetica, Arial, sans-serif" font-size="14" font-weight="600" fill="{c_text}">(a) Cost–reliability frontier, held-out test split (n=30)</text>')

    # Legend for Panel (a)
    leg_y = 115
    svg.append(f'  <line x1="50" y1="{leg_y + 6}" x2="70" y2="{leg_y + 6}" stroke="{c_blue}" stroke-width="2"/>')
    svg.append(f'  <text x="76" y="{leg_y + 10}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_text}">Pareto frontier</text>')

    svg.append(f'  <circle cx="180" cy="{leg_y + 6}" r="4.5" fill="{c_blue}"/>')
    svg.append(f'  <text x="190" y="{leg_y + 10}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_text}">R2 baseline</text>')

    svg.append(f'  <circle cx="280" cy="{leg_y + 6}" r="4.5" fill="{c_green}"/>')
    svg.append(f'  <text x="290" y="{leg_y + 10}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_text}">Chosen cascade</text>')

    svg.append(f'  <circle cx="400" cy="{leg_y + 6}" r="4.5" fill="{c_red}"/>')
    svg.append(f'  <text x="410" y="{leg_y + 10}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_text}">R4 anchor (dominated)</text>')

    svg.append(f'  <circle cx="560" cy="{leg_y + 6}" r="3" fill="#94a3b8" fill-opacity="0.6"/>')
    svg.append(f'  <text x="568" y="{leg_y + 10}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_text}">Candidate policies</text>')

    svg.append(f'  <line x1="685" y1="{leg_y + 6}" x2="705" y2="{leg_y + 6}" stroke="{c_red}" stroke-width="1.5" stroke-dasharray="4,3"/>')
    svg.append(f'  <text x="712" y="{leg_y + 10}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_red}">Ceiling</text>')

    # Plot coordinates for Panel (a)
    p1_left = 110.0
    p1_right = 750.0
    p1_w = p1_right - p1_left
    p1_top = 150.0
    p1_bot = 540.0
    p1_h = p1_bot - p1_top

    def px_a(cost: float) -> float:
        return p1_left + (cost / 0.070) * p1_w

    def py_a(pass_rate: float) -> float:
        return p1_bot - pass_rate * p1_h

    # Grid and axes for Panel (a)
    for tick_y in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        y_pos = py_a(tick_y)
        svg.append(f'  <line x1="{p1_left}" y1="{y_pos:.1f}" x2="{p1_right}" y2="{y_pos:.1f}" stroke="{c_grid}" stroke-width="1"/>')
        svg.append(f'  <text x="{p1_left - 10}" y="{y_pos + 4:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_muted}" text-anchor="end">{int(tick_y * 100)}%</text>')

    for tick_x in [0.00, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07]:
        x_pos = px_a(tick_x)
        svg.append(f'  <line x1="{x_pos:.1f}" y1="{p1_top}" x2="{x_pos:.1f}" y2="{p1_bot}" stroke="{c_grid}" stroke-width="1"/>')
        svg.append(f'  <text x="{x_pos:.1f}" y="{p1_bot + 18}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_muted}" text-anchor="middle">${tick_x:.2f}</text>')

    svg.append(f'  <line x1="{p1_left}" y1="{p1_bot}" x2="{p1_right}" y2="{p1_bot}" stroke="{c_axis}" stroke-width="1"/>')
    svg.append(f'  <line x1="{p1_left}" y1="{p1_top}" x2="{p1_left}" y2="{p1_bot}" stroke="{c_axis}" stroke-width="1"/>')
    svg.append(f'  <text x="{p1_left + p1_w / 2:.1f}" y="{p1_bot + 45}" font-family="Helvetica, Arial, sans-serif" font-size="12" fill="{c_muted}" text-anchor="middle">Mean cost per scenario (USD)</text>')
    svg.append(f'  <text x="35" y="{p1_top + p1_h / 2:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="12" fill="{c_muted}" text-anchor="middle" transform="rotate(-90 35 {p1_top + p1_h / 2:.1f})">Pass rate (oracle grounded)</text>')

    # 1. Oracle-router ceiling line at 25/30 = 83.3%
    ceil_val = 25.0 / 30.0
    ceil_y = py_a(ceil_val)
    svg.append(f'  <line x1="{p1_left}" y1="{ceil_y:.1f}" x2="{p1_right}" y2="{ceil_y:.1f}" stroke="{c_red}" stroke-width="1.5" stroke-dasharray="5,4"/>')
    svg.append(f'  <text x="{p1_right - 6}" y="{ceil_y - 8:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="600" fill="{c_red}" text-anchor="end">oracle-router ceiling (test split): 25/30 ({ceil_val * 100:.1f}%)</text>')

    # 2. All candidate policies as small grey points
    for pol_k, pol_v in all_test.items():
        cx = px_a(pol_v["mean_cost"])
        cy = py_a(pol_v["pass_rate"])
        svg.append(f'  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="3" fill="#94a3b8" fill-opacity="0.5"/>')

    # 3. Stepped Pareto frontier line through unique non-dominated points
    # Distinct points on frontier:
    # (r2_only: 0.00777, 0.7667), (cascade: 0.01586, 0.8000), (steps_21: 0.01931, 0.8333)
    p_step1_x, p_step1_y = px_a(0.007772), py_a(0.766667)
    p_step2_x, p_step2_y = px_a(0.015860), py_a(0.800000)
    p_step3_x, p_step3_y = px_a(0.019315), py_a(0.833333)
    p_end_x = px_a(0.070)

    frontier_path = f"M {p_step1_x:.1f},{p_step1_y:.1f} H {p_step2_x:.1f} V {p_step2_y:.1f} H {p_step3_x:.1f} V {p_step3_y:.1f} H {p_end_x:.1f}"
    svg.append(f'  <path d="{frontier_path}" fill="none" stroke="{c_blue}" stroke-width="2"/>')

    # 4. Highlighted points with Wilson whiskers and leader lines
    # A. r2_only
    r2_cost = r2_test["mean_cost"]
    r2_pass = r2_test["pass_rate"]
    r2_ci = r2_test["wilson_ci"]
    r2_x = px_a(r2_cost)
    r2_y = py_a(r2_pass)
    r2_ci_low = py_a(r2_ci[0])
    r2_ci_high = py_a(r2_ci[1])

    svg.append(f'  <line x1="{r2_x:.1f}" y1="{r2_ci_low:.1f}" x2="{r2_x:.1f}" y2="{r2_ci_high:.1f}" stroke="{c_text}" stroke-width="1.5"/>')
    svg.append(f'  <line x1="{r2_x - 5:.1f}" y1="{r2_ci_low:.1f}" x2="{r2_x + 5:.1f}" y2="{r2_ci_low:.1f}" stroke="{c_text}" stroke-width="1.5"/>')
    svg.append(f'  <line x1="{r2_x - 5:.1f}" y1="{r2_ci_high:.1f}" x2="{r2_x + 5:.1f}" y2="{r2_ci_high:.1f}" stroke="{c_text}" stroke-width="1.5"/>')
    svg.append(f'  <circle cx="{r2_x:.1f}" cy="{r2_y:.1f}" r="5.5" fill="{c_blue}" stroke="{c_text}" stroke-width="1.5"/>')

    # Leader line for r2_only (left-up)
    svg.append(f'  <polyline points="{r2_x:.1f},{r2_y - 6:.1f} {r2_x - 25:.1f},{r2_y - 50:.1f} {r2_x - 55:.1f},{r2_y - 50:.1f}" fill="none" stroke="{c_axis}" stroke-width="1"/>')
    svg.append(f'  <text x="{r2_x - 60:.1f}" y="{r2_y - 54:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="600" fill="{c_blue}" text-anchor="end">r2_only: {r2_pass * 100:.1f}%</text>')
    svg.append(f'  <text x="{r2_x - 60:.1f}" y="{r2_y - 40:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="10.5" fill="{c_muted}" text-anchor="end">${r2_cost:.4f} / run</text>')

    # B. chosen cascade (escalate if not answered / steps >= 23)
    cas_cost = cascade_test["mean_cost"]
    cas_pass = cascade_test["pass_rate"]
    cas_ci = cascade_test["wilson_ci"]
    cas_esc = cascade_test.get("escalation_rate", 0.166667)
    cas_x = px_a(cas_cost)
    cas_y = py_a(cas_pass)
    cas_ci_low = py_a(cas_ci[0])
    cas_ci_high = py_a(cas_ci[1])

    svg.append(f'  <line x1="{cas_x:.1f}" y1="{cas_ci_low:.1f}" x2="{cas_x:.1f}" y2="{cas_ci_high:.1f}" stroke="{c_text}" stroke-width="1.5"/>')
    svg.append(f'  <line x1="{cas_x - 5:.1f}" y1="{cas_ci_low:.1f}" x2="{cas_x + 5:.1f}" y2="{cas_ci_low:.1f}" stroke="{c_text}" stroke-width="1.5"/>')
    svg.append(f'  <line x1="{cas_x - 5:.1f}" y1="{cas_ci_high:.1f}" x2="{cas_x + 5:.1f}" y2="{cas_ci_high:.1f}" stroke="{c_text}" stroke-width="1.5"/>')
    svg.append(f'  <circle cx="{cas_x:.1f}" cy="{cas_y:.1f}" r="5.5" fill="{c_green}" stroke="{c_text}" stroke-width="1.5"/>')

    # Leader line for cascade (right-up)
    svg.append(f'  <polyline points="{cas_x:.1f},{cas_y - 6:.1f} {cas_x + 35:.1f},{cas_y - 55:.1f} {cas_x + 65:.1f},{cas_y - 55:.1f}" fill="none" stroke="{c_axis}" stroke-width="1"/>')
    svg.append(f'  <text x="{cas_x + 70:.1f}" y="{cas_y - 59:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="600" fill="{c_green}" text-anchor="start">Cascade (unanswered / steps ≥ 23): {cas_pass * 100:.1f}%</text>')
    svg.append(f'  <text x="{cas_x + 70:.1f}" y="{cas_y - 45:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="10.5" fill="{c_muted}" text-anchor="start">${cas_cost:.4f} / run ({cas_esc * 100:.1f}% esc)</text>')

    # C. r4_only
    r4_cost = r4_test["mean_cost"]
    r4_pass = r4_test["pass_rate"]
    r4_ci = r4_test["wilson_ci"]
    r4_x = px_a(r4_cost)
    r4_y = py_a(r4_pass)
    r4_ci_low = py_a(r4_ci[0])
    r4_ci_high = py_a(r4_ci[1])

    svg.append(f'  <line x1="{r4_x:.1f}" y1="{r4_ci_low:.1f}" x2="{r4_x:.1f}" y2="{r4_ci_high:.1f}" stroke="{c_text}" stroke-width="1.5"/>')
    svg.append(f'  <line x1="{r4_x - 5:.1f}" y1="{r4_ci_low:.1f}" x2="{r4_x + 5:.1f}" y2="{r4_ci_low:.1f}" stroke="{c_text}" stroke-width="1.5"/>')
    svg.append(f'  <line x1="{r4_x - 5:.1f}" y1="{r4_ci_high:.1f}" x2="{r4_x + 5:.1f}" y2="{r4_ci_high:.1f}" stroke="{c_text}" stroke-width="1.5"/>')
    svg.append(f'  <circle cx="{r4_x:.1f}" cy="{r4_y:.1f}" r="5.5" fill="{c_red}" stroke="{c_text}" stroke-width="1.5"/>')

    # Leader line for r4_only (left-up)
    svg.append(f'  <polyline points="{r4_x:.1f},{r4_y - 6:.1f} {r4_x - 30:.1f},{r4_y - 40:.1f} {r4_x - 60:.1f},{r4_y - 40:.1f}" fill="none" stroke="{c_axis}" stroke-width="1"/>')
    svg.append(f'  <text x="{r4_x - 65:.1f}" y="{r4_y - 44:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="600" fill="{c_red}" text-anchor="end">r4_only: {r4_pass * 100:.1f}% (dominated)</text>')
    svg.append(f'  <text x="{r4_x - 65:.1f}" y="{r4_y - 30:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="10.5" fill="{c_muted}" text-anchor="end">${r4_cost:.4f} / run</text>')

    # -------------------------------------------------------------
    # PANEL (b): P6 replicate, infra-excluded test split (n=107)
    # -------------------------------------------------------------
    svg.append('  <!-- Panel (b) -->')
    svg.append(f'  <text x="890" y="85" font-family="Helvetica, Arial, sans-serif" font-size="14" font-weight="600" fill="{c_text}">(b) P6 replicate, infra-excluded test split (n=107)</text>')

    # Legend for Panel (b)
    svg.append(f'  <line x1="890" y1="{leg_y + 6}" x2="910" y2="{leg_y + 6}" stroke="{c_blue}" stroke-width="2"/>')
    svg.append(f'  <text x="916" y="{leg_y + 10}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_text}">Pareto frontier</text>')

    svg.append(f'  <circle cx="1020" cy="{leg_y + 6}" r="4.5" fill="{c_blue}"/>')
    svg.append(f'  <text x="1030" y="{leg_y + 10}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_text}">R2 baseline</text>')

    svg.append(f'  <circle cx="1130" cy="{leg_y + 6}" r="4.5" fill="{c_green}"/>')
    svg.append(f'  <text x="1140" y="{leg_y + 10}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_text}">Cascade policies</text>')

    svg.append(f'  <circle cx="1270" cy="{leg_y + 6}" r="4.5" fill="{c_red}"/>')
    svg.append(f'  <text x="1280" y="{leg_y + 10}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_text}">R4 anchor (dominated)</text>')

    p2_left = 930.0
    p2_right = 1550.0
    p2_w = p2_right - p2_left

    def px_b(cost: float) -> float:
        return p2_left + (cost / 0.070) * p2_w

    def py_b(pass_rate: float) -> float:
        return p1_bot - pass_rate * p1_h

    # Grid and axes for Panel (b)
    for tick_y in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        y_pos = py_b(tick_y)
        svg.append(f'  <line x1="{p2_left}" y1="{y_pos:.1f}" x2="{p2_right}" y2="{y_pos:.1f}" stroke="{c_grid}" stroke-width="1"/>')
        svg.append(f'  <text x="{p2_left - 10}" y="{y_pos + 4:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_muted}" text-anchor="end">{int(tick_y * 100)}%</text>')

    for tick_x in [0.00, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07]:
        x_pos = px_b(tick_x)
        svg.append(f'  <line x1="{x_pos:.1f}" y1="{p1_top}" x2="{x_pos:.1f}" y2="{p1_bot}" stroke="{c_grid}" stroke-width="1"/>')
        svg.append(f'  <text x="{x_pos:.1f}" y="{p1_bot + 18}" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="{c_muted}" text-anchor="middle">${tick_x:.2f}</text>')

    svg.append(f'  <line x1="{p2_left}" y1="{p1_bot}" x2="{p2_right}" y2="{p1_bot}" stroke="{c_axis}" stroke-width="1"/>')
    svg.append(f'  <line x1="{p2_left}" y1="{p1_top}" x2="{p2_left}" y2="{p1_bot}" stroke="{c_axis}" stroke-width="1"/>')
    svg.append(f'  <text x="{p2_left + p2_w / 2:.1f}" y="{p1_bot + 45}" font-family="Helvetica, Arial, sans-serif" font-size="12" fill="{c_muted}" text-anchor="middle">Mean cost per scenario (USD)</text>')

    # P6 Replicate side-by-side points
    p6_r2 = p6_side.get("r2_only", {}).get("test", {})
    p6_s24 = p6_side.get("escalate_if_steps_ge_24", {}).get("test", {})
    p6_unans = p6_side.get("escalate_if_not_answered", {}).get("test", {})
    p6_r4 = p6_side.get("r4_only", {}).get("test", {})

    # Stepped Pareto frontier for P6 replicate:
    # r2_only -> steps_ge_24 -> escalate_if_not_answered
    p6_step1_x, p6_step1_y = px_b(p6_r2["mean_cost"]), py_b(p6_r2["pass_rate"])
    p6_step2_x, p6_step2_y = px_b(p6_s24["mean_cost"]), py_b(p6_s24["pass_rate"])
    p6_step3_x, p6_step3_y = px_b(p6_unans["mean_cost"]), py_b(p6_unans["pass_rate"])
    p6_end_x = px_b(0.070)

    p6_frontier_path = f"M {p6_step1_x:.1f},{p6_step1_y:.1f} H {p6_step2_x:.1f} V {p6_step2_y:.1f} H {p6_step3_x:.1f} V {p6_step3_y:.1f} H {p6_end_x:.1f}"
    svg.append(f'  <path d="{p6_frontier_path}" fill="none" stroke="{c_blue}" stroke-width="2"/>')

    # Points with Wilson whiskers in Panel (b)
    # 1. P6 r2_only
    c_x = px_b(p6_r2["mean_cost"])
    c_y = py_b(p6_r2["pass_rate"])
    ci_l = py_b(p6_r2["wilson_ci"][0])
    ci_h = py_b(p6_r2["wilson_ci"][1])
    svg.append(f'  <line x1="{c_x:.1f}" y1="{ci_l:.1f}" x2="{c_x:.1f}" y2="{ci_h:.1f}" stroke="{c_text}" stroke-width="1.5"/>')
    svg.append(f'  <line x1="{c_x - 5:.1f}" y1="{ci_l:.1f}" x2="{c_x + 5:.1f}" y2="{ci_l:.1f}" stroke="{c_text}" stroke-width="1.5"/>')
    svg.append(f'  <line x1="{c_x - 5:.1f}" y1="{ci_h:.1f}" x2="{c_x + 5:.1f}" y2="{ci_h:.1f}" stroke="{c_text}" stroke-width="1.5"/>')
    svg.append(f'  <circle cx="{c_x:.1f}" cy="{c_y:.1f}" r="5.5" fill="{c_blue}" stroke="{c_text}" stroke-width="1.5"/>')

    # Leader line for P6 r2_only (left-up)
    svg.append(f'  <polyline points="{c_x:.1f},{c_y - 6:.1f} {c_x - 25:.1f},{c_y - 45:.1f} {c_x - 45:.1f},{c_y - 45:.1f}" fill="none" stroke="{c_axis}" stroke-width="1"/>')
    svg.append(f'  <text x="{c_x - 50:.1f}" y="{c_y - 49:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="600" fill="{c_blue}" text-anchor="end">r2_only: {p6_r2["pass_rate"] * 100:.1f}%</text>')
    svg.append(f'  <text x="{c_x - 50:.1f}" y="{c_y - 35:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="10.5" fill="{c_muted}" text-anchor="end">${p6_r2["mean_cost"]:.4f} / run</text>')

    # 2. P6 steps_ge_24
    c_x = px_b(p6_s24["mean_cost"])
    c_y = py_b(p6_s24["pass_rate"])
    ci_l = py_b(p6_s24["wilson_ci"][0])
    ci_h = py_b(p6_s24["wilson_ci"][1])
    svg.append(f'  <line x1="{c_x:.1f}" y1="{ci_l:.1f}" x2="{c_x:.1f}" y2="{ci_h:.1f}" stroke="{c_text}" stroke-width="1.5"/>')
    svg.append(f'  <line x1="{c_x - 5:.1f}" y1="{ci_l:.1f}" x2="{c_x + 5:.1f}" y2="{ci_l:.1f}" stroke="{c_text}" stroke-width="1.5"/>')
    svg.append(f'  <line x1="{c_x - 5:.1f}" y1="{ci_h:.1f}" x2="{c_x + 5:.1f}" y2="{ci_h:.1f}" stroke="{c_text}" stroke-width="1.5"/>')
    svg.append(f'  <circle cx="{c_x:.1f}" cy="{c_y:.1f}" r="5.5" fill="{c_green}" stroke="{c_text}" stroke-width="1.5"/>')

    # Leader line for P6 steps_ge_24 (right-up high)
    svg.append(f'  <polyline points="{c_x:.1f},{c_y - 6:.1f} {c_x + 30:.1f},{c_y - 75:.1f} {c_x + 55:.1f},{c_y - 75:.1f}" fill="none" stroke="{c_axis}" stroke-width="1"/>')
    svg.append(f'  <text x="{c_x + 60:.1f}" y="{c_y - 79:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="600" fill="{c_green}" text-anchor="start">Cascade (steps ≥ 24): {p6_s24["pass_rate"] * 100:.1f}%</text>')
    svg.append(f'  <text x="{c_x + 60:.1f}" y="{c_y - 65:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="10.5" fill="{c_muted}" text-anchor="start">${p6_s24["mean_cost"]:.4f} / run</text>')

    # 3. P6 escalate_if_not_answered
    c_x = px_b(p6_unans["mean_cost"])
    c_y = py_b(p6_unans["pass_rate"])
    ci_l = py_b(p6_unans["wilson_ci"][0])
    ci_h = py_b(p6_unans["wilson_ci"][1])
    svg.append(f'  <line x1="{c_x:.1f}" y1="{ci_l:.1f}" x2="{c_x:.1f}" y2="{ci_h:.1f}" stroke="{c_text}" stroke-width="1.5"/>')
    svg.append(f'  <line x1="{c_x - 5:.1f}" y1="{ci_l:.1f}" x2="{c_x + 5:.1f}" y2="{ci_l:.1f}" stroke="{c_text}" stroke-width="1.5"/>')
    svg.append(f'  <line x1="{c_x - 5:.1f}" y1="{ci_h:.1f}" x2="{c_x + 5:.1f}" y2="{ci_h:.1f}" stroke="{c_text}" stroke-width="1.5"/>')
    svg.append(f'  <circle cx="{c_x:.1f}" cy="{c_y:.1f}" r="5.5" fill="{c_green}" stroke="{c_text}" stroke-width="1.5"/>')

    # Leader line for P6 unanswered (right-up)
    svg.append(f'  <polyline points="{c_x:.1f},{c_y - 6:.1f} {c_x + 25:.1f},{c_y - 45:.1f} {c_x + 50:.1f},{c_y - 45:.1f}" fill="none" stroke="{c_axis}" stroke-width="1"/>')
    svg.append(f'  <text x="{c_x + 55:.1f}" y="{c_y - 49:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="600" fill="{c_green}" text-anchor="start">Cascade (unanswered): {p6_unans["pass_rate"] * 100:.1f}%</text>')
    svg.append(f'  <text x="{c_x + 55:.1f}" y="{c_y - 35:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="10.5" fill="{c_muted}" text-anchor="start">${p6_unans["mean_cost"]:.4f} / run</text>')

    # 4. P6 r4_only
    c_x = px_b(p6_r4["mean_cost"])
    c_y = py_b(p6_r4["pass_rate"])
    ci_l = py_b(p6_r4["wilson_ci"][0])
    ci_h = py_b(p6_r4["wilson_ci"][1])
    svg.append(f'  <line x1="{c_x:.1f}" y1="{ci_l:.1f}" x2="{c_x:.1f}" y2="{ci_h:.1f}" stroke="{c_text}" stroke-width="1.5"/>')
    svg.append(f'  <line x1="{c_x - 5:.1f}" y1="{ci_l:.1f}" x2="{c_x + 5:.1f}" y2="{ci_l:.1f}" stroke="{c_text}" stroke-width="1.5"/>')
    svg.append(f'  <line x1="{c_x - 5:.1f}" y1="{ci_h:.1f}" x2="{c_x + 5:.1f}" y2="{ci_h:.1f}" stroke="{c_text}" stroke-width="1.5"/>')
    svg.append(f'  <circle cx="{c_x:.1f}" cy="{c_y:.1f}" r="5.5" fill="{c_red}" stroke="{c_text}" stroke-width="1.5"/>')

    # Leader line for P6 r4_only (left-up)
    svg.append(f'  <polyline points="{c_x:.1f},{c_y - 6:.1f} {c_x - 30:.1f},{c_y - 40:.1f} {c_x - 55:.1f},{c_y - 40:.1f}" fill="none" stroke="{c_axis}" stroke-width="1"/>')
    svg.append(f'  <text x="{c_x - 60:.1f}" y="{c_y - 44:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="600" fill="{c_red}" text-anchor="end">r4_only: {p6_r4["pass_rate"] * 100:.1f}% (dominated)</text>')
    svg.append(f'  <text x="{c_x - 60:.1f}" y="{c_y - 30:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="10.5" fill="{c_muted}" text-anchor="end">${p6_r4["mean_cost"]:.4f} / run</text>')

    # Footer
    svg.append('  <!-- Footer -->')
    svg.append(f'  <line x1="50" y1="655" x2="{width - 50}" y2="655" stroke="#e2e8f0" stroke-width="1"/>')
    svg.append(f'  <text x="50" y="675" font-family="Helvetica, Arial, sans-serif" font-size="11.5" fill="{c_muted}">FAULTLINE P10 · 100 paired R2/R4 runs · sha256 70/30 split, thresholds fit on train · Wilson 95% CIs</text>')

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
    base = Path("projects/p10_cascade")
    results_path = base / "results.json"
    output_svg = base / "figure.svg"
    output_png = base / "figure.png"
    output_pdf = base / "figure.pdf"

    generate_figure(results_path, output_svg, output_png, output_pdf)


if __name__ == "__main__":
    main()
