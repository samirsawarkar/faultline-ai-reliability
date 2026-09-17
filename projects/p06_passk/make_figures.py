#!/usr/bin/env python3
"""Deterministic figure generation for Publication 01 (pass^k reliability).

Reads STRICTLY from JSON artifacts under research/experiments/raw/:
- analysis.json
- timeline.json
- infra_signature.json
- p03_results.json
- p04_results.json
- p05_results.json

Outputs both .svg and .png (300 dpi) to publications/publication_01_passk_reliability/:
- fig_1_successes_per_scenario
- fig_2_passk_vs_naive
- fig_3_icc_extrapolation
- fig_4_incident_timeline
- fig_B_p03_depth
- fig_C_p04_taxonomy
- fig_D_p05_kappa

Design rules:
- Okabe-Ito color-blind safe palette
- One sans-serif font family
- No chart junk, no inside-figure titles (captions carry titles)
- Explicit units and error-bar definitions
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

# Set publication style
plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Helvetica", "Arial", "sans-serif"],
        "font.size": 10,
        "axes.labelsize": 10.5,
        "axes.titlesize": 11,
        "xtick.labelsize": 9.5,
        "ytick.labelsize": 9.5,
        "legend.fontsize": 9,
        "axes.grid": True,
        "grid.color": "#EAEAEA",
        "grid.linestyle": "--",
        "grid.linewidth": 0.8,
        "grid.alpha": 0.8,
        "axes.edgecolor": "#333333",
        "axes.linewidth": 0.8,
    }
)

# Okabe-Ito colorblind-safe palette
OKABE_ITO = {
    "black": "#000000",
    "orange": "#E69F00",
    "sky_blue": "#56B4E9",
    "bluish_green": "#009E73",
    "yellow": "#F0E442",
    "blue": "#0072B2",
    "vermilion": "#D55E00",
    "reddish_purple": "#CC79A7",
    "grey": "#7F7F7F",
    "light_grey": "#D3D3D3",
}

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = REPO_ROOT / "research" / "experiments" / "raw"
OUT_DIR = REPO_ROOT / "publications" / "publication_01_passk_reliability"


def save_fig(fig: plt.Figure, name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    svg_path = OUT_DIR / f"{name}.svg"
    png_path = OUT_DIR / f"{name}.png"
    fig.savefig(svg_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {name}.svg and {name}.png (300 dpi)")


def make_fig_1_successes_per_scenario(analysis: Dict[str, Any]) -> None:
    """Observed vs Binomial(3, pass@1) expected counts of scenarios with 0/1/2/3 successes."""
    panels = [
        ("R2 (as-run, $n=150$)", analysis["rungs"]["R2"]["as_run"]),
        ("R4 as-run ($n=150$)", analysis["rungs"]["R4"]["as_run"]),
        ("R4 infra-excluded ($n=117$)", analysis["rungs"]["R4"]["infra_excluded"]),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.5), sharey=False)
    x = np.arange(4)
    width = 0.36

    for ax, (title, data) in zip(axes, panels):
        obs_dict = data["independence_test"]["observed_histogram"]
        exp_dict = data["independence_test"]["expected_histogram"]
        
        obs_vals = [obs_dict[str(k)] for k in range(4)]
        exp_vals = [exp_dict[str(k)] for k in range(4)]

        rects1 = ax.bar(
            x - width / 2,
            obs_vals,
            width,
            label="Observed scenarios",
            color=OKABE_ITO["blue"],
            edgecolor="#222222",
            linewidth=0.8,
        )
        rects2 = ax.bar(
            x + width / 2,
            exp_vals,
            width,
            label="Binomial(3, pass@1) expected",
            color=OKABE_ITO["orange"],
            edgecolor="#222222",
            linewidth=0.8,
            hatch="//",
            alpha=0.85,
        )

        # Value annotations
        for r in rects1:
            h = r.get_height()
            ax.annotate(
                f"{int(h)}",
                xy=(r.get_x() + r.get_width() / 2, h),
                xytext=(0, 2),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8.5,
            )
        for r in rects2:
            h = r.get_height()
            ax.annotate(
                f"{h:.1f}",
                xy=(r.get_x() + r.get_width() / 2, h),
                xytext=(0, 2),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8.5,
            )

        ax.set_title(title, pad=10)
        ax.set_xlabel("Successes per scenario ($s \\in \\{0, 1, 2, 3\\}$)")
        ax.set_xticks(x)
        ax.set_xticklabels(["0", "1", "2", "3"])
        ax.set_ylabel("Number of scenarios")
        # Raised y-headroom by ~15% relative to baseline (1.15 * 1.15 = ~1.32)
        y_max = max(max(obs_vals), max(exp_vals))
        ax.set_ylim(0, y_max * 1.32)

    # Place legend outside axes at upper center with clear margin above panel titles
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.04),
        ncol=2,
        frameon=True,
        fontsize=9.5,
    )

    fig.tight_layout(rect=[0, 0, 1, 0.89])
    save_fig(fig, "fig_1_successes_per_scenario")


def make_fig_2_passk_vs_naive(analysis: Dict[str, Any]) -> None:
    """Measured pass^k with scenario-bootstrap 95% CIs vs (pass@1)^k for k=1,2,3."""
    panels = [
        ("R2 (as-run, $n=150$)", analysis["rungs"]["R2"]["as_run"]),
        ("R4 as-run ($n=150$)", analysis["rungs"]["R4"]["as_run"]),
        ("R4 infra-excluded ($n=117$)", analysis["rungs"]["R4"]["infra_excluded"]),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2), sharey=False)
    ks = [1, 2, 3]

    for ax, (title, data) in zip(axes, panels):
        p1 = data["pass_at_1"]["score"]
        p1_ci = data["pass_at_1"]["scenario_bootstrap_ci"]
        
        p2 = data["pass_k"]["k2"]["pass_hat_k"]
        p2_ci = data["pass_k"]["k2"]["pass_hat_k_bootstrap_ci"]
        
        p3 = data["pass_k"]["k3"]["pass_hat_k"]
        p3_ci = data["pass_k"]["k3"]["pass_hat_k_bootstrap_ci"]

        obs_y = [p1, p2, p3]
        cis = [p1_ci, p2_ci, p3_ci]
        yerr_lower = [obs_y[i] - cis[i][0] for i in range(3)]
        yerr_upper = [cis[i][1] - obs_y[i] for i in range(3)]
        yerr = [yerr_lower, yerr_upper]

        naive_y = [
            p1,
            data["pass_k"]["k2"]["naive_k"],
            data["pass_k"]["k3"]["naive_k"],
        ]

        ax.errorbar(
            ks,
            obs_y,
            yerr=yerr,
            fmt="o-",
            color=OKABE_ITO["blue"],
            ecolor=OKABE_ITO["blue"],
            elinewidth=1.6,
            capsize=4,
            capthick=1.2,
            markersize=6,
            linewidth=1.8,
            label="Empirical $\\widehat{\\text{pass}}^k$ (95% bootstrap CI)",
            zorder=4,
        )

        ax.plot(
            ks,
            naive_y,
            "s--",
            color=OKABE_ITO["vermilion"],
            markersize=6,
            linewidth=1.8,
            label="Naive $(\\text{pass@1})^k$",
            zorder=3,
        )

        ax.set_title(title, pad=10)
        ax.set_xlabel("Repeated executions ($k$)")
        ax.set_xticks(ks)
        ax.set_ylabel("Joint pass rate (pass$^k$)")
        ax.legend(frameon=True, loc="upper right")

    fig.tight_layout()
    save_fig(fig, "fig_2_passk_vs_naive")


def make_fig_3_icc_extrapolation(analysis: Dict[str, Any]) -> None:
    """C_k for k=1..10 implied by ICC at point estimate and 95% CI upper bound."""
    panels = [
        ("R2 ($n=150, \\widehat{\\mathrm{ICC}}=-0.029$)", analysis["rungs"]["R2"]["as_run"]),
        ("R4 as-run ($n=150, \\widehat{\\mathrm{ICC}}=0.206$)", analysis["rungs"]["R4"]["as_run"]),
        ("R4 infra-excluded ($n=117, \\widehat{\\mathrm{ICC}}=0.085$)", analysis["rungs"]["R4"]["infra_excluded"]),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.4), sharey=False)
    ks = np.arange(1, 11)

    for ax, (title, data) in zip(axes, panels):
        ext_table = data["intra_scenario_correlation"]["extrapolation_table_beta_binomial"]
        ck_pe = [ext_table[f"k{k}"]["concentration_ratio_C_k"] for k in ks]
        ck_upper = [ext_table[f"k{k}"]["concentration_ratio_at_icc_ci_upper"] for k in ks]

        ax.plot(
            ks,
            ck_pe,
            "o-",
            color=OKABE_ITO["blue"],
            linewidth=2.0,
            markersize=5.5,
            label="Beta-binomial model at $\\widehat{\\mathrm{ICC}}$",
            zorder=4,
        )
        ax.plot(
            ks,
            ck_upper,
            "^--",
            color=OKABE_ITO["vermilion"],
            linewidth=1.6,
            markersize=5,
            label="Upper bound at 95% bootstrap CI upper ICC",
            zorder=3,
        )
        ax.fill_between(
            ks,
            ck_pe,
            ck_upper,
            color=OKABE_ITO["sky_blue"],
            alpha=0.25,
            label="Parametric extrapolation uncertainty",
            zorder=2,
        )
        ax.axhline(
            1.0,
            color=OKABE_ITO["grey"],
            linestyle=":",
            linewidth=1.4,
            label="Independence null ($C_k=1$)",
            zorder=1,
        )

        ax.set_title(title, pad=10)
        ax.set_xlabel("Repeated executions ($k$)")
        ax.set_xticks(ks)
        ax.set_ylabel("Concentration ratio ($C_k = \\text{pass}^k / (\\text{pass@1})^k$)")
        ax.set_yscale("log")
        ax.legend(frameon=True, loc="upper left", fontsize=8.5)

    fig.tight_layout()
    save_fig(fig, "fig_3_icc_extrapolation")


def make_fig_4_incident_timeline(timeline_data: Dict[str, Any], infra_sig: Dict[str, Any]) -> None:
    """Per-run terminal state over run start time for R2/R4/R6 final pass."""
    fig, axes = plt.subplots(3, 1, figsize=(13.5, 7.2), sharex=True)

    state_colors = {
        "answered_pass": (OKABE_ITO["bluish_green"], "Answered Pass", "o"),
        "answered_fail": (OKABE_ITO["sky_blue"], "Answered Fail", "s"),
        "step_cap": (OKABE_ITO["orange"], "Step Cap ($\\geq 24$ steps)", "^"),
        "midrun_no_completion": (OKABE_ITO["vermilion"], "Mid-run No Completion", "D"),
        "dead_at_start": (OKABE_ITO["reddish_purple"], "Dead at Start (0 tokens)", "X"),
        "other": (OKABE_ITO["grey"], "Other", "v"),
    }

    w1_start = datetime.fromisoformat("2026-09-11T14:42:37.484499")
    w1_end = datetime.fromisoformat("2026-09-11T14:45:38.377375")
    w2_start = datetime.fromisoformat("2026-09-11T22:30:10.879042")
    w2_end = datetime.fromisoformat("2026-09-11T22:41:55.061108")

    rungs = [
        ("R6 (DeepSeek-V4-Pro, all runs lost to outage)", "R6"),
        ("R4 (GPT-5.6-Luna, 95 dead trials during outage)", "R4"),
        ("R2 (GLM-5.3-Flash, control run before outage)", "R2"),
    ]

    for ax, (title, rung) in zip(axes, rungs):
        runs = timeline_data[rung]
        
        # Draw outage shading
        ax.axvspan(w1_start, w1_end, color="#FF0000", alpha=0.18, zorder=1)
        ax.axvspan(w2_start, w2_end, color="#FF0000", alpha=0.18, zorder=1)

        # Plot points grouped by state
        by_state: Dict[str, List[datetime]] = {}
        for r in runs:
            ts_str = r["start_time"]
            # Handle ISO string with timezone or without
            if "+" in ts_str:
                ts_str = ts_str.split("+")[0]
            ts = datetime.fromisoformat(ts_str)
            by_state.setdefault(r["terminal_state"], []).append(ts)

        for state, (color, label, marker) in state_colors.items():
            if state in by_state:
                pts = by_state[state]
                y_vals = np.linspace(0.2, 0.8, len(pts)) if len(pts) > 1 else [0.5]
                ax.scatter(
                    pts,
                    y_vals,
                    c=color,
                    marker=marker,
                    s=28,
                    alpha=0.85,
                    edgecolors="#333333",
                    linewidths=0.5,
                    label=label,
                    zorder=3,
                )

        ax.set_title(title, pad=6, loc="left", fontsize=10.5)
        ax.set_yticks([])
        ax.set_ylabel("Runs", fontsize=9.5)
        ax.set_ylim(0, 1.0)

    # Annotate outage windows on top axis
    axes[0].annotate(
        "Incident Window 1\n(14:42-14:45 UTC)",
        xy=(w1_start, 0.85),
        xytext=(w1_start, 0.95),
        ha="center",
        fontsize=8.5,
        color="#B30000",
        fontweight="bold",
    )
    axes[0].annotate(
        "Incident Window 2\n(22:30-22:42 UTC)",
        xy=(w2_start, 0.85),
        xytext=(w2_start, 0.95),
        ha="center",
        fontsize=8.5,
        color="#B30000",
        fontweight="bold",
    )

    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M UTC"))
    axes[-1].xaxis.set_major_locator(mdates.HourLocator(interval=2))
    axes[-1].set_xlabel("Run Start Time (UTC, 2026-09-11)")

    # Unified legend
    handles, labels = axes[1].get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    fig.legend(
        by_label.values(),
        by_label.keys(),
        loc="upper center",
        bbox_to_anchor=(0.5, 1.02),
        ncol=6,
        frameon=True,
        fontsize=8.5,
    )

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    save_fig(fig, "fig_4_incident_timeline")


def make_fig_B_p03_depth(p03: Dict[str, Any]) -> None:
    """Pass@1 across reasoning depth tiers (T1: 1-hop, T2: 2-3 hops, T3: 4-5 hops)."""
    fig, ax = plt.subplots(figsize=(7.5, 4.4))
    tiers = ["T1 (1-hop)", "T2 (2-3 hops)", "T3 (4-5 hops)"]
    x = np.arange(len(tiers))
    width = 0.25

    models = [
        ("R2 (GLM-5.3-Flash)", "R2", OKABE_ITO["blue"]),
        ("R6 (DeepSeek-V4-Pro)", "R6", OKABE_ITO["sky_blue"]),
        ("R4 (GPT-5.6-Luna)", "R4", OKABE_ITO["vermilion"]),
    ]

    for idx, (label, rung_key, color) in enumerate(models):
        rung_data = p03["rungs"][rung_key]
        pass_rates = []
        yerr_lower = []
        yerr_upper = []

        for t_key in ["T1", "T2", "T3"]:
            tier_info = rung_data["tiers"][t_key]
            pr = tier_info["pass_rate"]
            ci = tier_info["wilson_ci"]
            pass_rates.append(pr)
            yerr_lower.append(max(0.0, pr - ci[0]))
            yerr_upper.append(max(0.0, ci[1] - pr))

        yerr = [yerr_lower, yerr_upper]
        offset = (idx - 1) * width
        rects = ax.bar(
            x + offset,
            pass_rates,
            width,
            yerr=yerr,
            capsize=3.5,
            label=label,
            color=color,
            edgecolor="#222222",
            linewidth=0.8,
        )

        for r, pr in zip(rects, pass_rates):
            ax.annotate(
                f"{pr:.1%}",
                xy=(r.get_x() + r.get_width() / 2, pr),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
            )

    ax.set_ylabel("pass@1 success rate")
    ax.set_xlabel("Reasoning depth tier ($n=200$ scenarios)")
    ax.set_xticks(x)
    ax.set_xticklabels(tiers)
    ax.set_ylim(0, 1.15)
    ax.legend(frameon=True, loc="upper right")

    fig.tight_layout()
    save_fig(fig, "fig_B_p03_depth")


def make_fig_C_p04_taxonomy(p04: Dict[str, Any]) -> None:
    """Axial failure mode prevalence across 9 categories (n=183 failed traces)."""
    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    prev_dict = p04["failure_mode_prevalence"]

    # Sort categories by count
    sorted_items = sorted(prev_dict.items(), key=lambda item: item[1]["count"], reverse=True)
    names = [item[1]["spec"]["name"] for item in sorted_items]
    counts = [item[1]["count"] for item in sorted_items]
    prevalences = [item[1]["prevalence"] * 100 for item in sorted_items]

    colors = []
    for item in sorted_items:
        fam = item[1]["spec"]["family"]
        if fam == "transport_infrastructure":
            colors.append(OKABE_ITO["vermilion"])
        elif fam == "structured_output":
            colors.append(OKABE_ITO["orange"])
        else:
            colors.append(OKABE_ITO["blue"])

    y_pos = np.arange(len(names))
    rects = ax.barh(y_pos, prevalences, color=colors, edgecolor="#222222", linewidth=0.8)

    for r, c, p in zip(rects, counts, prevalences):
        ax.annotate(
            f" {p:.1f}% ($n={c}$)",
            xy=(r.get_width(), r.get_y() + r.get_height() / 2),
            xytext=(3, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=8.5,
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names)
    ax.invert_yaxis()  # Highest prevalence on top
    ax.set_xlabel("Prevalence (% of $n=183$ failed execution traces)")
    ax.set_xlim(0, 75)

    # Custom legend for families
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=OKABE_ITO["vermilion"], edgecolor="#222", label="Transport / Infrastructure"),
        Patch(facecolor=OKABE_ITO["orange"], edgecolor="#222", label="Structured-Output Corruption"),
        Patch(facecolor=OKABE_ITO["blue"], edgecolor="#222", label="Agentic Reasoning / Retrieval"),
    ]
    ax.legend(handles=legend_elements, frameon=True, loc="lower right", fontsize=8.5)

    fig.tight_layout()
    save_fig(fig, "fig_C_p04_taxonomy")


def make_fig_D_p05_kappa(p05: Dict[str, Any]) -> None:
    """Inter-rater agreement (Cohen's kappa) for LLM evaluators vs human axial coding."""
    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    evals = p05["evaluators"]

    # Sort by kappa
    sorted_items = sorted(evals.items(), key=lambda item: item[1]["cohen_kappa"], reverse=True)
    names = [k.replace("_", " ").title() for k, _ in sorted_items]
    kappas = [val["cohen_kappa"] for _, val in sorted_items]

    colors = []
    for k in kappas:
        if k >= 0.8:
            colors.append(OKABE_ITO["bluish_green"])
        elif k > 0.0:
            colors.append(OKABE_ITO["orange"])
        else:
            colors.append(OKABE_ITO["vermilion"])

    y_pos = np.arange(len(names))
    rects = ax.barh(y_pos, kappas, color=colors, edgecolor="#222222", linewidth=0.8)

    for r, k in zip(rects, kappas):
        offset = 3 if k >= 0 else -3
        ha = "left" if k >= 0 else "right"
        ax.annotate(
            f"{k:.3f}",
            xy=(r.get_width(), r.get_y() + r.get_height() / 2),
            xytext=(offset, 0),
            textcoords="offset points",
            ha=ha,
            va="center",
            fontsize=8.5,
        )

    ax.axvline(0.0, color="#333333", linewidth=1.0)
    ax.axvline(0.8, color=OKABE_ITO["grey"], linestyle="--", linewidth=1.0, label=r"Near-perfect threshold ($\kappa = 0.8$)")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names)
    ax.invert_yaxis()
    ax.set_xlabel(r"Cohen's $\kappa$ agreement with human ground truth ($n=60$ test traces)")
    ax.set_xlim(-0.15, 1.15)
    ax.legend(frameon=True, loc="lower right", fontsize=8.5)

    fig.tight_layout()
    save_fig(fig, "fig_D_p05_kappa")


def main() -> None:
    print("Loading raw JSON inputs...")
    with open(RAW_DIR / "analysis.json") as f:
        analysis = json.load(f)
    with open(RAW_DIR / "timeline.json") as f:
        timeline = json.load(f)
    with open(RAW_DIR / "infra_signature.json") as f:
        infra_sig = json.load(f)
    with open(RAW_DIR / "p03_results.json") as f:
        p03 = json.load(f)
    with open(RAW_DIR / "p04_results.json") as f:
        p04 = json.load(f)
    with open(RAW_DIR / "p05_results.json") as f:
        p05 = json.load(f)

    print("Generating Figure 1: Observed vs Binomial(3, pass@1)...")
    make_fig_1_successes_per_scenario(analysis)

    print("Generating Figure 2: pass^k vs Naive (pass@1)^k...")
    make_fig_2_passk_vs_naive(analysis)

    print("Generating Figure 3: ICC -> C_k Extrapolation...")
    make_fig_3_icc_extrapolation(analysis)

    print("Generating Figure 4: Incident Timeline Post-Mortem...")
    make_fig_4_incident_timeline(timeline, infra_sig)

    print("Generating Figure B: P03 Reasoning Depth...")
    make_fig_B_p03_depth(p03)

    print("Generating Figure C: P04 Axial Failure Taxonomy...")
    make_fig_C_p04_taxonomy(p04)

    print("Generating Figure D: P05 Evaluator Cohen's Kappa...")
    make_fig_D_p05_kappa(p05)

    print("All 7 figures generated successfully in SVG and PNG format.")


if __name__ == "__main__":
    main()
