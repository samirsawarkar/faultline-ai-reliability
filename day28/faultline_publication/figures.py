"""Generate five publication figures directly from Q1-Q5 result JSON."""
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from .evidence import DAY, FIGURES, ROOT, load_json, sha256_file, source_inventory

W, H = 960, 560
INK = "#17212B"
MUTED = "#5E6B77"
GRID = "#DCE3E8"
PAPER = "#FBFCFD"
BLUE = "#146C94"
TEAL = "#138A72"
ORANGE = "#D97706"
RED = "#C2413A"
PURPLE = "#7554A3"
PALE_BLUE = "#DCEEF6"
PALE_TEAL = "#DDF3ED"
PALE_ORANGE = "#FAE8C8"


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _base(title: str, description: str, metadata: Dict[str, Any]) -> List[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">',
        f"<title id=\"title\">{esc(title)}</title>",
        f"<desc id=\"desc\">{esc(description)}</desc>",
        f"<metadata>{esc(json.dumps(metadata, sort_keys=True))}</metadata>",
        "<style>",
        "text{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"
        "'Segoe UI',sans-serif;fill:#17212B} .title{font-size:25px;font-weight:700}"
        ".subtitle{font-size:14px;fill:#5E6B77}.axis{font-size:12px;fill:#5E6B77}"
        ".label{font-size:13px}.small{font-size:11px;fill:#5E6B77}"
        ".value{font-size:12px;font-weight:700}.note{font-size:12px;font-weight:600}"
        ".grid{stroke:#DCE3E8;stroke-width:1}.axisline{stroke:#8B98A3;stroke-width:1.2}",
        "</style>",
        f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
        f'<text x="64" y="48" class="title">{esc(title)}</text>',
        f'<text x="64" y="73" class="subtitle">{esc(description)}</text>',
    ]


def _finish(lines: List[str], source_label: str) -> str:
    lines.extend([
        f'<text x="64" y="550" class="small">Source: {esc(source_label)}</text>',
        "</svg>",
        "",
    ])
    return "\n".join(lines)


def _line_path(points: Sequence[Tuple[float, float]]) -> str:
    return " ".join(
        ("M" if index == 0 else "L") + f" {x:.1f} {y:.1f}"
        for index, (x, y) in enumerate(points)
    )


def figure_q1(spec: Dict[str, Any]) -> str:
    artifact = "day07/evidence/q1_results.json"
    data = load_json(ROOT / artifact)
    curve = data["curve"]
    x0, x1, y0, y1 = 88, 900, 105, 470
    sx = lambda hop: x0 + (hop - 1) * (x1 - x0) / 7
    sy = lambda value: y1 - value * (y1 - y0)
    meta = {"figure": spec["id"], "sources": [artifact]}
    lines = _base(
        spec["title"],
        "End-to-end success by required tool depth; bars are measured 95% Wilson intervals.",
        meta,
    )
    for tick in (0, .2, .4, .6, .8, 1):
        y = sy(tick)
        lines += [
            f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" class="grid"/>',
            f'<text x="{x0-12}" y="{y+4:.1f}" text-anchor="end" class="axis">{tick:.1f}</text>',
        ]
    for hop in range(1, 9):
        x = sx(hop)
        lines.append(
            f'<text x="{x:.1f}" y="{y1+24}" text-anchor="middle" class="axis">{hop}</text>'
        )
    lines += [
        f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" class="axisline"/>',
        f'<text x="{(x0+x1)/2}" y="{y1+48}" text-anchor="middle" class="label">Required hops</text>',
        f'<text x="23" y="{(y0+y1)/2}" transform="rotate(-90 23 {(y0+y1)/2})" '
        'text-anchor="middle" class="label">End-to-end success</text>',
    ]
    measured = [(sx(row["hops"]), sy(row["measured"])) for row in curve]
    naive = [(sx(row["hops"]), sy(row["naive"])) for row in curve]
    corrected = [(sx(row["hops"]), sy(row["corrected"])) for row in curve]
    for row in curve:
        x = sx(row["hops"])
        low, high = row["measured_ci95"]
        lines += [
            f'<line x1="{x:.1f}" y1="{sy(low):.1f}" x2="{x:.1f}" y2="{sy(high):.1f}" '
            f'stroke="{BLUE}" stroke-width="2"/>',
            f'<line x1="{x-5:.1f}" y1="{sy(low):.1f}" x2="{x+5:.1f}" y2="{sy(low):.1f}" '
            f'stroke="{BLUE}" stroke-width="2"/>',
            f'<line x1="{x-5:.1f}" y1="{sy(high):.1f}" x2="{x+5:.1f}" y2="{sy(high):.1f}" '
            f'stroke="{BLUE}" stroke-width="2"/>',
        ]
    lines += [
        f'<path d="{_line_path(naive)}" fill="none" stroke="{ORANGE}" stroke-width="3" '
        'stroke-dasharray="8 7"/>',
        f'<path d="{_line_path(corrected)}" fill="none" stroke="{MUTED}" stroke-width="2.5" '
        'stroke-dasharray="3 6"/>',
        f'<path d="{_line_path(measured)}" fill="none" stroke="{BLUE}" stroke-width="3.5"/>',
    ]
    for x, y in measured:
        lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{BLUE}"/>')
    sep_x = sx(data["first_divergence_hop"])
    lines += [
        f'<line x1="{sep_x:.1f}" y1="{y0}" x2="{sep_x:.1f}" y2="{y1}" '
        f'stroke="{RED}" stroke-width="1.5" stroke-dasharray="4 5"/>',
        f'<rect x="{sep_x+9:.1f}" y="111" width="183" height="45" rx="5" fill="#F9E2E0"/>',
        f'<text x="{sep_x+20:.1f}" y="130" class="note">First interval separation</text>',
        f'<text x="{sep_x+20:.1f}" y="147" class="small">hop 3: 0.818 vs 0.91833</text>',
        f'<line x1="652" y1="91" x2="685" y2="91" stroke="{BLUE}" stroke-width="3.5"/>',
        '<text x="693" y="95" class="axis">measured</text>',
        f'<line x1="772" y1="91" x2="805" y2="91" stroke="{ORANGE}" stroke-width="3" '
        'stroke-dasharray="8 7"/>',
        '<text x="813" y="95" class="axis">naive p₁ⁿ</text>',
        f'<line x1="652" y1="111" x2="685" y2="111" stroke="{MUTED}" stroke-width="2.5" '
        'stroke-dasharray="3 6"/>',
        '<text x="693" y="115" class="axis">product of measured hop rates</text>',
        f'<text x="{sx(8)-5:.1f}" y="{sy(curve[-1]["measured"])+24:.1f}" '
        f'text-anchor="end" class="value">0.288</text>',
        f'<text x="{sx(8)-5:.1f}" y="{sy(curve[-1]["naive"])-10:.1f}" '
        f'text-anchor="end" class="value">0.796765</text>',
    ]
    return _finish(lines, artifact)


def figure_q2(spec: Dict[str, Any]) -> str:
    artifact = "day15/evidence/q2_results.json"
    data = load_json(ROOT / artifact)["full_labelled_set"]
    rows = data["per_class_confusion"]
    deterministic = {"F2", "F4", "F6"}
    x0, x1 = 262, 870
    sx = lambda value: x0 + value * (x1 - x0)
    lines = _base(
        spec["title"],
        "Recall by fault family on the full labelled set; intervals are 95% Wilson.",
        {"figure": spec["id"], "sources": [artifact]},
    )
    for tick in (0, .25, .5, .75, 1):
        x = sx(tick)
        lines += [
            f'<line x1="{x:.1f}" y1="112" x2="{x:.1f}" y2="438" class="grid"/>',
            f'<text x="{x:.1f}" y="462" text-anchor="middle" class="axis">{tick:.2f}</text>',
        ]
    labels = {
        "F1": "structured output",
        "F2": "latency",
        "F3": "schema/value drift",
        "F4": "provider error",
        "F5": "context corruption",
        "F6": "loop exhaustion",
    }
    for index, fault in enumerate(("F1", "F2", "F3", "F4", "F5", "F6")):
        row = rows[fault]
        y = 135 + index * 52
        color = BLUE if fault in deterministic else PURPLE
        lo, hi = row["recall_ci95"]
        lines += [
            f'<text x="70" y="{y+4}" class="label">{fault} · {labels[fault]}</text>',
            f'<line x1="{sx(lo):.1f}" y1="{y}" x2="{sx(hi):.1f}" y2="{y}" '
            f'stroke="{color}" stroke-width="5" stroke-linecap="round"/>',
            f'<circle cx="{sx(row["recall"]):.1f}" cy="{y}" r="7" fill="{color}"/>',
            f'<text x="{min(sx(row["recall"])+13, 887):.1f}" y="{y+4}" class="value">'
            f'{row["recall"]:.2f}</text>',
        ]
    taxonomy = data["no_hiding"]["fn_taxonomy"]
    lines += [
        '<text x="566" y="490" class="small">Group: </text>',
        f'<circle cx="615" cy="486" r="5" fill="{BLUE}"/><text x="627" y="490" class="small">deterministic</text>',
        f'<circle cx="725" cy="486" r="5" fill="{PURPLE}"/><text x="737" y="490" class="small">semantic</text>',
        f'<rect x="67" y="476" width="425" height="36" rx="5" fill="{PALE_ORANGE}"/>',
        f'<text x="80" y="499" class="note">10 misses: {taxonomy["threshold_reducible"]} threshold-reducible · '
        f'{taxonomy["irreducible_semantic_escape"]} semantic escapes</text>',
    ]
    return _finish(lines, artifact)


def figure_q3(spec: Dict[str, Any]) -> str:
    artifact = "day19/evidence/retry_sweep.json"
    crossover_artifact = "day19/evidence/crossover.json"
    data = load_json(ROOT / artifact)
    independent, correlated = data["independent"], data["correlated"]
    x0, x1 = 100, 900
    sx = lambda k: x0 + (k - 1) * (x1 - x0) / 5
    top0, top1 = 114, 309
    sy_success = lambda value: top1 - value * (top1 - top0)
    bottom0, bottom1 = 350, 486
    sy_amp = lambda value: bottom1 - (value / 4.5) * (bottom1 - bottom0)
    lines = _base(
        spec["title"],
        "Success gains flatten while attempts amplify; the safe retry cap depends on fault correlation.",
        {"figure": spec["id"], "sources": [artifact, crossover_artifact]},
    )
    for tick in (0, .25, .5, .75, 1):
        y = sy_success(tick)
        lines += [
            f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" class="grid"/>',
            f'<text x="{x0-12}" y="{y+4:.1f}" text-anchor="end" class="axis">{tick:.2f}</text>',
        ]
    for tick in (0, 1, 2, 3, 4):
        y = sy_amp(tick)
        lines += [
            f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" class="grid"/>',
            f'<text x="{x0-12}" y="{y+4:.1f}" text-anchor="end" class="axis">{tick}×</text>',
        ]
    for k in range(1, 7):
        x = sx(k)
        lines.append(f'<text x="{x:.1f}" y="507" text-anchor="middle" class="axis">{k}</text>')
    lines += [
        '<text x="24" y="215" transform="rotate(-90 24 215)" text-anchor="middle" class="label">Success rate</text>',
        '<text x="24" y="418" transform="rotate(-90 24 418)" text-anchor="middle" class="label">Attempt amplification</text>',
        '<text x="500" y="529" text-anchor="middle" class="label">Maximum attempts K</text>',
    ]
    for rows, color, dash, label in (
        (independent, TEAL, "", "independent faults"),
        (correlated, RED, "8 6", "correlated faults"),
    ):
        success_points = [(sx(row["K"]), sy_success(row["success_rate"])) for row in rows]
        amp_points = [(sx(row["K"]), sy_amp(row["amplification"])) for row in rows]
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        lines += [
            f'<path d="{_line_path(success_points)}" fill="none" stroke="{color}" '
            f'stroke-width="3.5"{dash_attr}/>',
            f'<path d="{_line_path(amp_points)}" fill="none" stroke="{color}" '
            f'stroke-width="3.5"{dash_attr}/>',
        ]
        for x, y in success_points + amp_points:
            lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{color}"/>')
    ceiling_y = sy_amp(data["ceilings"]["cost_ceiling_amplification"])
    lines += [
        f'<line x1="{x0}" y1="{ceiling_y:.1f}" x2="{x1}" y2="{ceiling_y:.1f}" '
        f'stroke="{ORANGE}" stroke-width="2" stroke-dasharray="3 5"/>',
        f'<text x="{x1-3}" y="{ceiling_y-7:.1f}" text-anchor="end" class="note">'
        '2.0× attempt ceiling</text>',
        f'<rect x="{sx(3)-20:.1f}" y="{sy_success(.76)-35:.1f}" width="42" height="25" rx="12" fill="{PALE_TEAL}"/>',
        f'<text x="{sx(3)+1:.1f}" y="{sy_success(.76)-18:.1f}" text-anchor="middle" class="value">K=3</text>',
        f'<rect x="{sx(2)-20:.1f}" y="{sy_success(.365)-35:.1f}" width="42" height="25" rx="12" fill="#F9E2E0"/>',
        f'<text x="{sx(2)+1:.1f}" y="{sy_success(.365)-18:.1f}" text-anchor="middle" class="value">K=2</text>',
        f'<line x1="625" y1="92" x2="658" y2="92" stroke="{TEAL}" stroke-width="3.5"/>',
        '<text x="667" y="96" class="axis">independent</text>',
        f'<line x1="772" y1="92" x2="805" y2="92" stroke="{RED}" stroke-width="3.5" stroke-dasharray="8 6"/>',
        '<text x="814" y="96" class="axis">correlated</text>',
    ]
    return _finish(lines, f"{artifact}; {crossover_artifact}")


def figure_q4(spec: Dict[str, Any]) -> str:
    artifact = "day21/evidence/availability_quality_comparison.json"
    detector_artifact = "day21/evidence/degradation_detector.json"
    comparison = load_json(ROOT / artifact)["comparison"]
    detector = load_json(ROOT / detector_artifact)
    primary = comparison["primary_only"]
    fallback = comparison["fallback_enabled"]
    x_positions = (260, 455, 650)
    metrics = (
        ("Availability", primary["availability"], fallback["availability"]),
        (
            "Strict quality | answered",
            primary["strict_quality_given_answered"],
            fallback["strict_quality_given_answered"],
        ),
        (
            "Strict service pass",
            primary["strict_quality_service_rate"],
            fallback["strict_quality_service_rate"],
        ),
    )
    y0, y1 = 120, 392
    sy = lambda value: y1 - value * (y1 - y0)
    lines = _base(
        spec["title"],
        "Fallback fills every outage, but availability and answer quality move in opposite directions.",
        {"figure": spec["id"], "sources": [artifact, detector_artifact]},
    )
    for tick in (0, .25, .5, .75, 1):
        y = sy(tick)
        lines += [
            f'<line x1="150" y1="{y:.1f}" x2="760" y2="{y:.1f}" class="grid"/>',
            f'<text x="138" y="{y+4:.1f}" text-anchor="end" class="axis">{tick:.2f}</text>',
        ]
    for x, (label, before, after) in zip(x_positions, metrics):
        for delta, row, color in ((-27, before, MUTED), (27, after, BLUE)):
            value = row["rate"]
            bar_y = sy(value)
            lines += [
                f'<rect x="{x+delta-18}" y="{bar_y:.1f}" width="36" height="{y1-bar_y:.1f}" '
                f'rx="3" fill="{color}"/>',
                f'<text x="{x+delta}" y="{bar_y-8:.1f}" text-anchor="middle" class="value">'
                f'{value:.2f}</text>',
            ]
        lines.append(f'<text x="{x}" y="419" text-anchor="middle" class="axis">{esc(label)}</text>')
    lines += [
        f'<rect x="790" y="130" width="120" height="251" rx="7" fill="{PALE_ORANGE}"/>',
        '<text x="850" y="157" text-anchor="middle" class="note">40 fallback answers</text>',
        f'<rect x="817" y="181" width="66" height="126" fill="{RED}" opacity=".88"/>',
        f'<rect x="817" y="307" width="66" height="42" fill="{TEAL}" opacity=".9"/>',
        '<text x="850" y="232" text-anchor="middle" fill="#FFFFFF" style="font:700 20px system-ui">30</text>',
        '<text x="850" y="252" text-anchor="middle" fill="#FFFFFF" style="font:12px system-ui">silently degraded</text>',
        '<text x="850" y="331" text-anchor="middle" fill="#FFFFFF" style="font:700 17px system-ui">10 acceptable</text>',
        f'<text x="850" y="370" text-anchor="middle" class="small">detector recall {detector["recall"]["rate"]:.4f}</text>',
        f'<circle cx="482" cy="92" r="5" fill="{MUTED}"/><text x="494" y="96" class="axis">primary only</text>',
        f'<circle cx="590" cy="92" r="5" fill="{BLUE}"/><text x="602" y="96" class="axis">fallback enabled</text>',
    ]
    return _finish(lines, f"{artifact}; {detector_artifact}")


def figure_q5(spec: Dict[str, Any]) -> str:
    artifact = "day24/evidence/policy_comparison.json"
    attack_artifact = "day24/evidence/winner_attack.json"
    data = load_json(ROOT / artifact)
    attack = load_json(ROOT / attack_artifact)
    metrics = data["policy_metrics"]
    eligible = set(data["selection"]["eligible_candidates"])
    x0, x1, y0, y1 = 120, 845, 112, 430
    sx = lambda cost: x0 + (cost - .9) / 1.0 * (x1 - x0)
    sy = lambda success: y1 - (success - .5) / .5 * (y1 - y0)
    lines = _base(
        spec["title"],
        "Correct success versus mean cost; labels show p95 latency, and only uncertainty-qualified policies are eligible.",
        {"figure": spec["id"], "sources": [artifact, attack_artifact]},
    )
    for tick in (1.0, 1.25, 1.5, 1.75):
        x = sx(tick)
        lines += [
            f'<line x1="{x:.1f}" y1="{y0}" x2="{x:.1f}" y2="{y1}" class="grid"/>',
            f'<text x="{x:.1f}" y="{y1+24}" text-anchor="middle" class="axis">{tick:.2f}</text>',
        ]
    for tick in (.5, .6, .7, .8, .9, 1):
        y = sy(tick)
        lines += [
            f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" class="grid"/>',
            f'<text x="{x0-12}" y="{y+4:.1f}" text-anchor="end" class="axis">{tick:.1f}</text>',
        ]
    lines += [
        f'<text x="{(x0+x1)/2}" y="486" text-anchor="middle" class="label">Mean cost per request</text>',
        f'<text x="30" y="{(y0+y1)/2}" transform="rotate(-90 30 {(y0+y1)/2})" '
        'text-anchor="middle" class="label">User-visible correct success</text>',
    ]
    short = {
        "P0_no_recovery": "P0",
        "P1_bounded_retry": "P1",
        "P2_unchecked_fallback": "P2",
        "P3_full_cascade": "P3",
        "P4_selective_guarded": "P4",
    }
    winner = metrics[data["selection"]["winner"]]
    lines += [
        f'<rect x="643" y="195" width="259" height="68" rx="7" fill="{PALE_TEAL}"/>',
        '<text x="658" y="219" class="note">Base winner: P4 selective guarded</text>',
        f'<text x="658" y="240" class="small">success {winner["user_visible_correct_success"]["rate"]:.4f} · '
        f'cost {winner["mean_cost"]["value"]:.4f} · p95 {winner["p95_latency"]["value"]:.0f}</text>',
        '<text x="658" y="257" class="small">reference upper bound; both stress attacks fail</text>',
    ]
    offsets = {"P0": (11, -12), "P1": (-74, -13), "P2": (15, 34), "P3": (12, -11), "P4": (-61, -13)}
    for policy, row in metrics.items():
        label = short[policy]
        cost = row["mean_cost"]["value"]
        success = row["user_visible_correct_success"]["rate"]
        p95 = row["p95_latency"]["value"]
        x, y = sx(cost), sy(success)
        is_eligible = policy in eligible
        fill = TEAL if policy == data["selection"]["winner"] else (BLUE if is_eligible else MUTED)
        radius = 11 if policy == data["selection"]["winner"] else 8
        dx, dy = offsets[label]
        lines += [
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius}" fill="{fill}" '
            f'stroke="{PAPER}" stroke-width="3"/>',
            f'<text x="{x+dx:.1f}" y="{y+dy:.1f}" class="value">{label} · p95 {p95:.0f}</text>',
        ]
        if not is_eligible:
            lines.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius+5}" fill="none" '
                f'stroke="{RED}" stroke-width="1.5" stroke-dasharray="3 4"/>'
            )
    worse = attack["attacks"]["worse_severity"]["metrics"]
    tight = attack["attacks"]["tight_budgets"]["metrics"]
    for row, label, dy in ((worse, "P4 · worse severity", -9), (tight, "P4 · tight budgets", 20)):
        x = sx(row["mean_cost"]["value"])
        y = sy(row["user_visible_correct_success"]["rate"])
        lines += [
            f'<path d="M {x-7:.1f} {y-7:.1f} L {x+7:.1f} {y+7:.1f} M {x+7:.1f} {y-7:.1f} '
            f'L {x-7:.1f} {y+7:.1f}" stroke="{RED}" stroke-width="3"/>',
            f'<text x="{x+12:.1f}" y="{y+dy:.1f}" class="note">{esc(label)}</text>',
        ]
    return _finish(lines, f"{artifact}; {attack_artifact}")


BUILDERS = {
    "figure-1": figure_q1,
    "figure-2": figure_q2,
    "figure-3": figure_q3,
    "figure-4": figure_q4,
    "figure-5": figure_q5,
}


def build_figures() -> Dict[str, Any]:
    specs = load_json(DAY / "figures.json")["figures"]
    FIGURES.mkdir(parents=True, exist_ok=True)
    records: List[Dict[str, Any]] = []
    all_sources: List[str] = []
    for spec in specs:
        content = BUILDERS[spec["id"]](spec)
        path = FIGURES / spec["filename"]
        path.write_text(content, encoding="utf-8")
        sources = [source["artifact"] for source in spec["sources"]]
        all_sources.extend(sources)
        records.append({
            "id": spec["id"],
            "filename": path.relative_to(ROOT).as_posix(),
            "sha256": sha256_file(path),
            "sources": sources,
        })
    return {
        "figure_count": len(records),
        "figures": records,
        "source_inventory": source_inventory(all_sources),
    }
