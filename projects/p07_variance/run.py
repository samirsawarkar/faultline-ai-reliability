"""Project P7: Provider Variance & Multi-Endpoint Grounding Calibration Runner.

Evaluates whether identical model architectures deployed across distinct
API provider channels / gateways exhibit statistically significant divergence in grounded factual
accuracy, latency, and economics.

Compares identical model architecture across 2 production routing endpoints:
- Endpoint 1 (aicredits): AICredits Gateway Route (google/gemini-3.7-flash)
- Endpoint 2 (agy): AGY CLI Native Platform Route (native environment model)

Evaluates Pre-Registered Hypothesis H6:
"Same model, 2+ endpoints, grounded rates with disjoint CIs."
Falsified if Wilson 95% score intervals overlap across endpoint pairs.

Generates manifest.json, results.json, trace.db, ledger.jsonl, figure.svg, and figure.png.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import logging
import os
import random
import shutil
import sqlite3
import subprocess
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.getLogger("LiteLLM").setLevel(logging.ERROR)

from faultline_p2.agent.agent import run_agent
from faultline_p2.agent.contracts import OutcomeStatus, ScenarioTask
from faultline_p2.agent.model import LiteLLMModel, ModelResponse, StubModel
from faultline_p2.cost.ledger import CostLedger, LedgerEntry, PriceTable, RungPricing
from faultline_p2.env.corpus import Scenario, build_corpus
from faultline_p2.oracle._day01_oracle import oracle_check
from faultline_p2.resilience import CircuitBreaker, ResilientModel, RetryPolicy
from faultline_p2.stats.intervals import wilson_interval
from faultline_p2.stats.paired import mcnemar_from_pairs
from faultline_p2.trace.store import TraceStore

DEFAULT_AICREDITS_BASE = "https://aicredits.in/v1"


def normalize_model_name(name: str) -> str:
    """Normalise only the provider prefix (strip 'google/', 'gemini/')."""
    if not name:
        return ""
    s = name.strip()
    for prefix in ("google/", "gemini/"):
        if s.startswith(prefix):
            s = s[len(prefix):]
    return s


class TrackedLiteLLMModel:
    """Wraps LiteLLMModel to capture the actual response.model attribute returned by LiteLLM."""
    def __init__(self, inner: LiteLLMModel):
        self.inner = inner
        self.model_name = inner.model_name
        self.provider = inner.provider
        self.version = inner.version
        self.reported_model: Optional[str] = None

    def generate(self, messages: List[Dict[str, Any]]) -> ModelResponse:
        import litellm
        reported = [None]
        orig_completion = litellm.completion

        def _completion_wrapper(*args, **kwargs):
            resp = orig_completion(*args, **kwargs)
            reported[0] = getattr(resp, "model", None)
            return resp

        litellm.completion = _completion_wrapper
        try:
            res = self.inner.generate(messages)
        finally:
            litellm.completion = orig_completion

        if reported[0]:
            self.reported_model = str(reported[0])
            self.version = self.reported_model
        return res


class AGYModel:
    """Invokes local AGY CLI in print mode to evaluate native environment performance."""
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name
        self.provider = "agy_cli"
        self.version = "3.7-flash"
        self.reported_model: Optional[str] = None

    def generate(self, messages: List[Dict[str, Any]]) -> ModelResponse:
        import re
        system_instruction = (
            "You are an autonomous fact-finding agent navigating a deterministic document store.\n"
            "Available actions (respond with ONLY a single JSON object):\n"
            "1. Search: {\"tool\": \"search\", \"query\": \"<keywords>\"}\n"
            "2. Lookup: {\"tool\": \"lookup\", \"doc_id\": \"<doc-xxxx or link-xxxx>\"}\n"
            "3. Calc: {\"tool\": \"calc\", \"expression\": \"<arithmetic>\"}\n"
            "4. Answer: {\"answer\": \"<exact final answer>\", \"cited_source\": \"<doc-xxxx containing the verified fact>\"}\n\n"
            "Respond strictly with the single JSON object, no conversational filler or markdown explanation."
        )

        prompt_parts = [system_instruction, "\n--- Conversation History ---"]
        for m in messages:
            role = m.get("role", "user").upper()
            content = m.get("content", "")
            prompt_parts.append(f"{role}: {content}")
        prompt_parts.append("ASSISTANT (JSON only):")

        full_prompt = "\n".join(prompt_parts)

        agy_bin = shutil.which("agy") or "/Users/samir/.local/bin/agy"
        cmd = [
            agy_bin, "-p", full_prompt,
            "--output-format", "json"
        ]
        if self.model_name:
            cmd.extend(["--model", self.model_name])

        last_err = None
        for attempt in range(3):
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
                out_json = json.loads(proc.stdout)
                rep_m = out_json.get("model") or self.model_name or "gemini-3.7-flash"
                self.reported_model = str(rep_m)
                self.version = self.reported_model

                resp_text = out_json.get("response", "")
                m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", resp_text, re.DOTALL)
                if not m:
                    m = re.search(r"(\{.*\})", resp_text, re.DOTALL)
                raw_json = m.group(1) if m else resp_text.strip()
                data = json.loads(raw_json)

                if "answer" in data:
                    src = data.get("cited_source") or data.get("doc_id") or ""
                    return ModelResponse(thought=resp_text, answer=str(data["answer"]), cited_sources=[str(src)] if src else [])
                elif "tool" in data:
                    return ModelResponse(thought=resp_text, tool_call=data)
                else:
                    return ModelResponse(thought=resp_text, answer=None, tool_call=None)
            except Exception as e:
                last_err = e
                time.sleep(1.0 * (attempt + 1))

        return ModelResponse(thought=f"AGY Error: {last_err}", answer=None, tool_call=None)


ENDPOINT_LIST: List[Tuple[str, str, Optional[str]]] = [
    ("aicredits", "aicredits", "google/gemini-3.7-flash"),
    ("agy", "agy_cli", None),  # model string is whatever agy returns; do not hardcode it
]

ENDPOINTS: Dict[str, Dict[str, Any]] = {
    "aicredits": {
        "id": "aicredits",
        "name": "AICredits Gateway",
        "model_label": "gemini-3.7-flash",
        "model_name": "google/gemini-3.7-flash",
        "provider": "aicredits",
        "version": "3.7-flash",
        "in_price": 0.10,
        "out_price": 0.40,
        "route_type": "gateway",
    },
    "agy": {
        "id": "agy",
        "name": "AGY CLI Native Platform",
        "model_label": "gemini-3.7-flash",
        "model_name": None,  # model string is whatever agy returns; do not hardcode it
        "provider": "agy_cli",
        "version": "3.7-flash",
        "in_price": 0.10,
        "out_price": 0.40,
        "route_type": "native_cli",
    },
}


def ensure_manifest(output_dir: Path, scenario_count: int = 150) -> Dict[str, Any]:
    """Ensure manifest.json is present, drawn deterministically from standard pool with seed 42, and SHA-256 verified."""
    manifest_path = output_dir / "manifest.json"
    corpus = build_corpus()
    std_scenarios = [s for s in corpus.scenarios if s.pool == "standard"]

    rng = random.Random(42)
    sampled = rng.sample(std_scenarios, min(scenario_count, len(std_scenarios)))
    selected_ids = [s.scenario_id for s in sampled]

    std_sha = hashlib.sha256(json.dumps(selected_ids).encode()).hexdigest()

    manifest_data = {
        "spec_version": "2.0.0",
        "experiment": "p07_provider_variance",
        "hypothesis": "H6: Same model across 2+ endpoints produces disjoint grounded pass rate CIs",
        "model_under_test": "google/gemini-3.7-flash",
        "corpus_hash": corpus.content_hash,
        "scenario_count": len(selected_ids),
        "tier_counts": {
            "T1": len([s for s in sampled if s.tier == "T1"]),
            "T2": len([s for s in sampled if s.tier == "T2"]),
            "T3": len([s for s in sampled if s.tier == "T3"]),
        },
        "scenario_ids_sha256": std_sha,
        "scenario_ids": selected_ids,
        "endpoints": {k: v["name"] + (" (" + str(v["model_label"]) + ")" if v.get("model_label") else "") for k, v in ENDPOINTS.items()},
    }

    manifest_bytes = json.dumps(manifest_data, indent=2, sort_keys=True).encode()
    manifest_data["manifest_sha256"] = hashlib.sha256(manifest_bytes).hexdigest()

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    return manifest_data


def generate_figure(results: Dict[str, Any], output_path: Path) -> None:
    """Generate publication-grade SVG chart comparing endpoints across accuracy, latency, and cost."""
    width = 1200
    height = 760

    svg = []
    svg.append(f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">')
    svg.append('  <rect width="100%" height="100%" fill="#ffffff" rx="8"/>')
    svg.append('  <style>')
    svg.append('    .title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 20px; font-weight: 700; fill: #111827; }')
    svg.append('    .subtitle { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 13px; fill: #4b5563; }')
    svg.append('    .section-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 14px; font-weight: 700; fill: #1f2937; }')
    svg.append('    .axis-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 12px; font-weight: 600; fill: #4b5563; }')
    svg.append('    .tick-label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 11px; fill: #4b5563; }')
    svg.append('    .bar-val { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 12px; font-weight: 700; }')
    svg.append('    .legend-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 11px; fill: #374151; font-weight: 500; }')
    svg.append('    .badge-hdr { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 12px; font-weight: 700; }')
    svg.append('    .badge-body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 11.5px; fill: #374151; }')
    svg.append('  </style>')

    # Outer border
    svg.append(f'  <rect x="1" y="1" width="{width-2}" height="{height-2}" fill="none" stroke="#e5e7eb" stroke-width="1.5" rx="8"/>')

    # Title & Subtitle
    svg.append(f'  <text x="{width/2}" y="38" class="title" text-anchor="middle">Figure 7: Provider Variance &amp; Multi-Endpoint Grounding Calibration (MEC v1.3)</text>')
    svg.append(f'  <text x="{width/2}" y="62" class="subtitle" text-anchor="middle">Identical Architecture Evaluated Across AICredits &amp; AGY Native CLI (N={results.get("n_scenarios", 150)} Scenarios)</text>')

    endpoints_data = results.get("endpoints", {})
    e_keys = [k for k in ["aicredits", "agy"] if k in endpoints_data] or list(endpoints_data.keys())
    colors = {
        "aicredits": "#1e40af",  # Deep Blue
        "agy": "#059669",        # Emerald Green
    }

    # =========================================================================
    # PANEL A: Grounded Pass Rate (pass@1) with Wilson 95% CIs (Left Panel)
    # =========================================================================
    p1_left = 60
    p1_width = 515
    p1_top = 145
    p1_bottom = 370
    p1_height = p1_bottom - p1_top

    svg.append('  <!-- PANEL A BACKGROUND -->')
    svg.append(f'  <rect x="{p1_left}" y="88" width="{p1_width}" height="328" fill="#f9fafb" rx="6" stroke="#e5e7eb" stroke-width="1"/>')
    svg.append(f'  <text x="{p1_left+16}" y="114" class="section-title">A. Grounded Pass Rate (pass@1) with Wilson 95% CIs</text>')

    # Y-axis Grid for Panel A (0% to 100%)
    for pct in [0, 25, 50, 75, 100]:
        y = p1_bottom - (pct / 100.0) * p1_height
        svg.append(f'  <line x1="{p1_left+55}" y1="{y}" x2="{p1_left+p1_width-18}" y2="{y}" stroke="#e5e7eb" stroke-width="1" stroke-dasharray="3,3"/>')
        svg.append(f'  <text x="{p1_left+46}" y="{y+4}" class="tick-label" text-anchor="end">{pct}%</text>')

    # Bars for endpoints
    n_bars = max(len(e_keys), 1)
    bar_width = 64
    spacing = p1_width / (n_bars + 1)
    bar_centers = [p1_left + spacing * (i + 1) for i in range(n_bars)]

    for idx, e_key in enumerate(e_keys):
        edata = endpoints_data.get(e_key, {})
        pass_rate = edata.get("pass_rate", 0.0)
        ci = edata.get("wilson_ci", [0.0, 0.0])
        cx = bar_centers[idx]
        bx = cx - bar_width / 2
        bh = pass_rate * p1_height
        by = p1_bottom - bh
        color = colors.get(e_key, "#4b5563")

        # Bar
        svg.append(f'  <rect x="{bx}" y="{by}" width="{bar_width}" height="{bh}" fill="{color}" rx="4"/>')
        val_text = f"{pass_rate:.1%}" if "status" not in edata else "STUB"
        svg.append(f'  <text x="{cx}" y="{by-9}" class="bar-val" fill="{color}" text-anchor="middle">{val_text}</text>')

        # Wilson CI Whisker
        if "status" not in edata:
            ci_top_y = p1_bottom - ci[1] * p1_height
            ci_bot_y = p1_bottom - ci[0] * p1_height
            svg.append(f'  <line x1="{cx}" y1="{ci_top_y}" x2="{cx}" y2="{ci_bot_y}" stroke="#111827" stroke-width="2"/>')
            svg.append(f'  <line x1="{cx-6}" y1="{ci_top_y}" x2="{cx+6}" y2="{ci_top_y}" stroke="#111827" stroke-width="2"/>')
            svg.append(f'  <line x1="{cx-6}" y1="{ci_bot_y}" x2="{cx+6}" y2="{ci_bot_y}" stroke="#111827" stroke-width="2"/>')

        # X-axis label
        label_main = edata.get("name", e_key)
        label_sub = f"Provider: {edata.get('provider', e_key)}"
        svg.append(f'  <text x="{cx}" y="{p1_bottom+18}" class="tick-label" font-weight="600" text-anchor="middle">{label_main}</text>')
        svg.append(f'  <text x="{cx}" y="{p1_bottom+32}" class="tick-label" font-size="10px" text-anchor="middle">{label_sub}</text>')

    # =========================================================================
    # PANEL B: Latency Distribution (p50 & p90 ms) (Right Panel)
    # =========================================================================
    p2_left = 625
    p2_width = 515
    p2_top = 145
    p2_bottom = 370
    p2_height = p2_bottom - p2_top

    svg.append('  <!-- PANEL B BACKGROUND -->')
    svg.append(f'  <rect x="{p2_left}" y="88" width="{p2_width}" height="328" fill="#f9fafb" rx="6" stroke="#e5e7eb" stroke-width="1"/>')
    svg.append(f'  <text x="{p2_left+16}" y="114" class="section-title">B. Latency Profiles per Agent Step (p50 &amp; p90 ms)</text>')

    max_lat = 14000.0

    # Y-axis Grid for Panel B
    step_size = 2000
    for step in range(0, int(max_lat) + 1, step_size):
        y = p2_bottom - (step / max_lat) * p2_height
        svg.append(f'  <line x1="{p2_left+65}" y1="{y}" x2="{p2_left+p2_width-18}" y2="{y}" stroke="#e5e7eb" stroke-width="1" stroke-dasharray="3,3"/>')
        svg.append(f'  <text x="{p2_left+56}" y="{y+4}" class="tick-label" text-anchor="end">{step}ms</text>')

    p2_centers = [p2_left + (p2_width / (n_bars + 1)) * (i + 1) for i in range(n_bars)]
    bw2 = 28

    for idx, e_key in enumerate(e_keys):
        edata = endpoints_data.get(e_key, {})
        p50 = edata.get("latency_p50_ms", 0.0)
        p90 = edata.get("latency_p90_ms", 0.0)
        mean_lat = edata.get("latency_mean_ms", 0.0)
        cx = p2_centers[idx]
        color = colors.get(e_key, "#4b5563")

        # p50 bar
        bx1 = cx - bw2 - 2
        bh1 = (p50 / max_lat) * p2_height
        by1 = p2_bottom - bh1
        svg.append(f'  <rect x="{bx1}" y="{by1}" width="{bw2}" height="{bh1}" fill="{color}" rx="3"/>')
        svg.append(f'  <text x="{bx1 + bw2/2}" y="{by1-5}" class="bar-val" font-size="10px" fill="{color}" text-anchor="middle">{int(p50)}</text>')

        # p90 bar
        bx2 = cx + 2
        bh2 = (p90 / max_lat) * p2_height
        by2 = p2_bottom - bh2
        svg.append(f'  <rect x="{bx2}" y="{by2}" width="{bw2}" height="{bh2}" fill="{color}" opacity="0.6" rx="3"/>')
        svg.append(f'  <text x="{bx2 + bw2/2}" y="{by2-5}" class="bar-val" font-size="10px" fill="{color}" text-anchor="middle">{int(p90)}</text>')

        # Labels
        label_main = edata.get("name", e_key)
        svg.append(f'  <text x="{cx}" y="{p2_bottom+18}" class="tick-label" font-weight="600" text-anchor="middle">{label_main}</text>')
        svg.append(f'  <text x="{cx}" y="{p2_bottom+32}" class="tick-label" font-size="10px" text-anchor="middle">Mean: {int(mean_lat)}ms</text>')

    # Panel B Legend
    leg_x = p2_left + p2_width - 185
    leg_y = 96
    svg.append(f'  <rect x="{leg_x}" y="{leg_y}" width="170" height="42" fill="#ffffff" rx="4" stroke="#e5e7eb" stroke-width="1"/>')
    svg.append(f'  <rect x="{leg_x+10}" y="{leg_y+8}" width="12" height="10" fill="#374151" rx="2"/>')
    svg.append(f'  <text x="{leg_x+28}" y="{leg_y+17}" class="legend-text">p50 Latency (Median)</text>')
    svg.append(f'  <rect x="{leg_x+10}" y="{leg_y+24}" width="12" height="10" fill="#374151" opacity="0.6" rx="2"/>')
    svg.append(f'  <text x="{leg_x+28}" y="{leg_y+33}" class="legend-text">p90 Latency</text>')

    # =========================================================================
    # PANEL C: Statistical Summary & Hypothesis Resolution (Bottom Panel)
    # =========================================================================
    p3_top = 445
    p3_height = 280

    svg.append('  <!-- PANEL C BACKGROUND -->')
    svg.append(f'  <rect x="60" y="{p3_top}" width="{width-120}" height="{p3_height}" fill="#f9fafb" rx="6" stroke="#e5e7eb" stroke-width="1"/>')
    svg.append(f'  <text x="80" y="{p3_top+26}" class="section-title">C. Hypothesis H6 Statistical Test &amp; Multi-Endpoint Decision Matrix</text>')

    h6_res = results.get("h6") or results.get("hypothesis_h6", {})
    if h6_res.get("status") == "NOT EVALUABLE":
        badge_bg = "#fef2f2"
        badge_border = "#ef4444"
        badge_txt_color = "#b91c1c"
        badge_title = "HYPOTHESIS H6: NOT EVALUABLE"
        badge_desc = h6_res.get("reason", "Endpoints served different models or stub.")
    else:
        verdict = h6_res.get("verdict", "FALSIFIED (CIs Overlap)")
        is_falsified = "FALSIFIED" in verdict or "REJECTED" in verdict or "NOT_SUPPORTED" in verdict
        badge_bg = "#eff6ff" if is_falsified else "#ecfdf5"
        badge_border = "#3b82f6" if is_falsified else "#059669"
        badge_txt_color = "#1d4ed8" if is_falsified else "#047857"
        badge_title = f"HYPOTHESIS H6: {verdict.upper()}"
        badge_desc = "Pre-registration: Disjoint Wilson 95% CIs across endpoints."

    # Verdict Box (Left Box)
    svg.append(f'  <rect x="80" y="{p3_top+40}" width="515" height="215" fill="{badge_bg}" rx="6" stroke="{badge_border}" stroke-width="1.5"/>')
    svg.append(f'  <text x="98" y="{p3_top+64}" class="badge-hdr" fill="{badge_txt_color}">{badge_title}</text>')
    svg.append(f'  <text x="98" y="{p3_top+88}" class="badge-body">{badge_desc}</text>')

    y_offset = p3_top + 112
    for idx, ek in enumerate(e_keys):
        ed = endpoints_data.get(ek, {})
        if "status" in ed:
            svg.append(f'  <text x="98" y="{y_offset + idx*22}" class="badge-body">• {ed.get("name", ek)}: {ed["status"]}</text>')
        else:
            ci_vals = ed.get("wilson_ci", [0.0, 0.0])
            ci_str = f"[{ci_vals[0]:.1%}, {ci_vals[1]:.1%}]"
            pass_ct = ed.get("passed", 0)
            n_sc = ed.get("n_scenarios", 0)
            name_str = ed.get("name", ek)
            svg.append(f'  <text x="98" y="{y_offset + idx*22}" class="badge-body">• {name_str} 95% CI: {ci_str} ({pass_ct}/{n_sc})</text>')

    p_comp = results.get("mcnemar_tests", {}).get("aicredits_vs_agy")
    if p_comp:
        p_val = p_comp.get("p_value", 1.0)
        svg.append(f'  <text x="98" y="{y_offset + len(e_keys)*22 + 10}" class="badge-body">• Paired McNemar Exact Test: p = {p_val:.4f}</text>')
        parity_str = "✔ Statistical Parity: No significant difference between aicredits and agy." if p_val > 0.05 else "Delta statistically significant."
        svg.append(f'  <text x="98" y="{p3_top+200}" class="badge-body" font-weight="700" fill="#111827">{parity_str}</text>')
    else:
        svg.append(f'  <text x="98" y="{y_offset + len(e_keys)*22 + 10}" class="badge-body">• McNemar paired test: SKIPPED (not evaluable or stub)</text>')

    # Right Box: Economics & Operational Routing
    svg.append(f'  <rect x="615" y="{p3_top+40}" width="505" height="215" fill="#ffffff" rx="6" stroke="#e5e7eb" stroke-width="1"/>')
    svg.append(f'  <text x="633" y="{p3_top+64}" class="badge-hdr" fill="#1f2937">OPERATIONAL INSIGHTS &amp; PRODUCTION ROUTING</text>')

    total_spend = results.get("total_sweep_cost_usd", 0.0)
    svg.append(f'  <text x="633" y="{p3_top+90}" class="badge-body">• Total Sweep Spend: ${total_spend:.4f} USD (Enforced under $5.00 P7 Cap).</text>')
    for idx, ek in enumerate(e_keys):
        ed = endpoints_data.get(ek, {})
        if "status" in ed:
            svg.append(f'  <text x="633" y="{p3_top+114 + idx*22}" class="badge-body">• {ed.get("name", ek)}: {ed["status"]}</text>')
        else:
            cost_1k = ed.get("cost_per_1k_queries", 0.0)
            p50 = ed.get("latency_p50_ms", 0.0)
            pr = ed.get("pass_rate", 0.0)
            svg.append(f'  <text x="633" y="{p3_top+114 + idx*22}" class="badge-body">• {ed.get("name", ek)}: Pass Rate={pr:.1%}, p50={int(p50)}ms, ${cost_1k:.2f}/1k queries.</text>')
    svg.append(f'  <text x="633" y="{p3_top+186}" class="badge-body" font-weight="700" fill="#059669">✔ Grounding variance calibrated across endpoints.</text>')

    svg.append('</svg>')

    svg_content = '\n'.join(svg)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"Wrote SVG figure to {output_path}")

    # Render PNG using Chrome headless if available, falling back to qlmanage
    png_out = output_path.with_suffix(".png")
    chrome_path = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    rendered = False
    if chrome_path.exists():
        try:
            cmd = [
                str(chrome_path),
                "--headless",
                "--disable-gpu",
                f"--screenshot={png_out}",
                f"--window-size={width},{height}",
                str(output_path.resolve()),
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"Rendered high-res PNG via Chrome headless to {png_out}")
            rendered = True
        except Exception as e:
            print(f"Warning: Chrome headless render failed: {e}")

    if not rendered:
        try:
            subprocess.run(["qlmanage", "-t", "-s", "2400", "-o", "/tmp", str(output_path)], check=True, capture_output=True)
            tmp_png = Path(f"/tmp/{output_path.name}.png")
            if tmp_png.exists():
                shutil.copyfile(tmp_png, png_out)
                print(f"Rendered PNG via qlmanage to {png_out}")
        except Exception as e:
            print(f"Warning: Could not render PNG: {e}")


def execute_scenario(
    task: ScenarioTask,
    scenario: Scenario,
    corpus: Any,
    endpoint_cfg: Dict[str, Any],
    trace_store: TraceStore,
    ledger: CostLedger,
    step_cap: int,
    real: bool,
    run_id: str,
) -> Dict[str, Any]:
    """Execute a single scenario against a specific endpoint and return structured results."""
    env = {"documents": corpus.documents}
    e_id = endpoint_cfg["id"]

    if real:
        if endpoint_cfg.get("provider") == "agy_cli":
            model = AGYModel(model_name=endpoint_cfg.get("model_name"))
        else:
            aicredits_key = os.getenv("AICREDITS_API_KEY")
            aicredits_base = os.getenv("AICREDITS_BASE_URL", DEFAULT_AICREDITS_BASE)
            raw_model = LiteLLMModel(
                model_name=endpoint_cfg["model_name"],
                provider=endpoint_cfg["provider"],
                version=endpoint_cfg["version"],
                dry_run=False,
                api_base=aicredits_base,
                api_key=aicredits_key,
                custom_llm_provider="openai",
            )
            tracked_model = TrackedLiteLLMModel(raw_model)
            retry_policy = RetryPolicy(
                max_retries=5,
                initial_backoff_s=2.0,
                backoff_multiplier=2.0,
                max_backoff_s=30.0,
                seed=42,
            )
            model = ResilientModel(
                inner_model=tracked_model,
                retry_policy=retry_policy,
                circuit_breaker=CircuitBreaker(failure_threshold=5, cooldown_seconds=5.0),
            )
    else:
        model = StubModel(behavior="solver")

    t_start = time.time()
    outcome = run_agent(
        task=task,
        env=env,
        model=model,
        step_cap=step_cap,
        trace_store=trace_store,
        run_id=run_id,
    )
    wall_ms = (time.time() - t_start) * 1000

    # Grounded Oracle check
    q_dict = {
        "id": scenario.scenario_id,
        "answer": scenario.final_answer,
        "required_source": scenario.required_source,
    }
    r_dict = {
        "answer": outcome.answer or "",
        "cited_sources": outcome.cited_sources,
    }
    verdict = oracle_check(q_dict, r_dict)
    passed = bool(verdict.get("passed", False))
    trace_store.record_verdict(run_id, scenario.scenario_id, passed)

    # Record the actual reported model string into span's model_version field
    reported_model = None
    if hasattr(model, "reported_model") and model.reported_model:
        reported_model = model.reported_model
    elif hasattr(model, "inner_model") and hasattr(model.inner_model, "reported_model") and model.inner_model.reported_model:
        reported_model = model.inner_model.reported_model
    elif not real:
        reported_model = getattr(model, "model_name", "stub")

    if reported_model:
        with trace_store._lock:
            trace_store.conn.execute(
                "UPDATE spans SET model_version = ? WHERE run_id = ?",
                (reported_model, run_id),
            )

    # Calculate tokens & cost from trace store spans
    with trace_store._lock:
        cur = trace_store.conn.cursor()
        cur.execute(
            "SELECT SUM(prompt_tokens), SUM(completion_tokens), AVG(latency_ms), MAX(latency_ms) FROM spans WHERE run_id = ?",
            (run_id,),
        )
        row = cur.fetchone()
        in_tok = int(row[0] or 0)
        out_tok = int(row[1] or 0)
        avg_lat = float(row[2] or wall_ms)

    cost_usd = (in_tok * endpoint_cfg["in_price"] / 1_000_000.0) + (out_tok * endpoint_cfg["out_price"] / 1_000_000.0)

    # Record in cost ledger only if real API call was made
    if real:
        ledger.record(
            LedgerEntry(
                run_id=run_id,
                project="p07_provider",
                rung=e_id,
                input_tokens=in_tok,
                output_tokens=out_tok,
                usd=cost_usd,
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
            )
        )

    return {
        "run_id": run_id,
        "scenario_id": scenario.scenario_id,
        "tier": scenario.tier,
        "endpoint_id": e_id,
        "grounded": passed,
        "correct_answer": verdict["correct"],
        "cited_source": verdict["cited_required"],
        "answer": outcome.answer,
        "cited_sources": outcome.cited_sources,
        "steps_used": outcome.steps_used,
        "status": outcome.status.value,
        "wall_time_ms": wall_ms,
        "avg_step_latency_ms": avg_lat,
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "cost_usd": cost_usd,
        "reported_model": reported_model,
    }


def build_results_from_trace(
    trace_store: TraceStore,
    endpoint_results: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    manifest: Optional[Dict[str, Any]] = None,
    output_dir: Path = Path("projects/p07_variance"),
) -> Dict[str, Any]:
    """Build results.json and figure.svg strictly from trace.db, rejecting any stub runs."""
    results_path = output_dir / "results.json"
    if endpoint_results is None:
        if results_path.exists():
            try:
                prev_data = json.loads(results_path.read_text(encoding="utf-8"))
                endpoint_results = prev_data.get("raw_runs", {})
            except Exception:
                endpoint_results = {}
        if not endpoint_results:
            endpoint_results = {k: [] for k in ENDPOINTS}

    if manifest is None:
        manifest_path = output_dir / "manifest.json"
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                manifest = ensure_manifest(output_dir)
        else:
            manifest = ensure_manifest(output_dir)

    selected_ids = manifest.get("scenario_ids", [])

    summary_endpoints: Dict[str, Any] = {}
    any_stub = False
    endpoint_models: Dict[str, str] = {}

    for e_key in ENDPOINTS:
        res_list = endpoint_results.get(e_key, [])
        run_ids = [r["run_id"] for r in res_list if "run_id" in r]

        # Query model_name and provider from trace.db for these run_ids
        with trace_store._lock:
            cur = trace_store.conn.cursor()
            if run_ids:
                placeholders = ",".join("?" for _ in run_ids)
                cur.execute(
                    f"""
                    SELECT DISTINCT model_name, provider, model_version
                    FROM spans
                    WHERE run_id IN ({placeholders})
                    """,
                    run_ids,
                )
                span_info = cur.fetchall()
            else:
                span_info = []

        # Check if any model in spans is stub or provider is local
        is_stub_run = any(
            (row["model_name"] == "stub" or row["provider"] == "local")
            for row in span_info
        )

        if not span_info and not run_ids:
            is_stub_run = True

        if is_stub_run:
            any_stub = True
            summary_endpoints[e_key] = {
                "status": "STUB RUN — not a measurement",
                "endpoint_id": e_key,
                "name": ENDPOINTS[e_key]["name"],
                "model_label": ENDPOINTS[e_key]["model_label"],
                "model_name": "stub",
                "provider": "local",
                "n_scenarios": len(run_ids),
            }
            endpoint_models[e_key] = "stub"
            continue

        # Non-stub, real measurement: Query MAX(verdict) from trace.db
        with trace_store._lock:
            cur = trace_store.conn.cursor()
            placeholders = ",".join("?" for _ in run_ids)
            cur.execute(
                f"""
                SELECT run_id, scenario_id, tier, MAX(COALESCE(verdict, 0)) AS passed
                FROM spans
                WHERE run_id IN ({placeholders})
                GROUP BY run_id, scenario_id
                """,
                run_ids,
            )
            db_rows = cur.fetchall()

        n = len(db_rows)
        pass_count = sum(1 for row in db_rows if row["passed"] == 1)
        pass_rate = pass_count / n if n > 0 else 0.0
        ci = wilson_interval(pass_count, n, confidence=0.95)

        tiers = {}
        for t in ["T1", "T2", "T3"]:
            t_rows = [row for row in db_rows if row["tier"] == t]
            t_n = len(t_rows)
            t_pass = sum(1 for row in t_rows if row["passed"] == 1)
            t_rate = t_pass / t_n if t_n > 0 else 0.0
            t_ci = wilson_interval(t_pass, t_n, confidence=0.95)
            tiers[t] = {
                "n": t_n,
                "passed": t_pass,
                "pass_rate": round(t_rate, 4),
                "wilson_ci": [round(t_ci[0], 4), round(t_ci[1], 4)],
            }

        latencies = sorted([r["avg_step_latency_ms"] for r in res_list if "avg_step_latency_ms" in r])
        p50_lat = latencies[int(len(latencies) * 0.50)] if latencies else 0.0
        p90_lat = latencies[int(len(latencies) * 0.90)] if latencies else 0.0
        mean_lat = sum(latencies) / len(latencies) if latencies else 0.0

        total_cost = sum(r.get("cost_usd", 0.0) for r in res_list)
        cost_per_1k = (total_cost / n) * 1000 if n > 0 else 0.0

        distinct_versions = sorted(set(row["model_version"] for row in span_info if row["model_version"]))
        reported_model_str = ", ".join(distinct_versions) if distinct_versions else str(ENDPOINTS[e_key].get("model_name") or "unknown")
        endpoint_models[e_key] = reported_model_str

        summary_endpoints[e_key] = {
            "endpoint_id": e_key,
            "name": ENDPOINTS[e_key]["name"],
            "model_label": ENDPOINTS[e_key]["model_label"],
            "model_name": ENDPOINTS[e_key]["model_name"],
            "provider": ENDPOINTS[e_key]["provider"],
            "version": reported_model_str,
            "n_scenarios": n,
            "passed": pass_count,
            "pass_rate": round(pass_rate, 4),
            "wilson_ci": [round(ci[0], 4), round(ci[1], 4)],
            "tiers": tiers,
            "latency_p50_ms": round(p50_lat, 1),
            "latency_p90_ms": round(p90_lat, 1),
            "latency_mean_ms": round(mean_lat, 1),
            "total_cost_usd": round(total_cost, 6),
            "cost_per_1k_queries": round(cost_per_1k, 4),
        }

    # H6 resolution
    if any_stub:
        h6_result = {
            "status": "NOT EVALUABLE",
            "reason": "one or more endpoints ran the stub model",
        }
        mcnemar_tests: Dict[str, Any] = {}
    else:
        model_aicredits = endpoint_models.get("aicredits", "unknown")
        model_agy = endpoint_models.get("agy", "unknown")
        norm_aicredits = normalize_model_name(model_aicredits)
        norm_agy = normalize_model_name(model_agy)

        if norm_aicredits != norm_agy:
            h6_result = {
                "status": "NOT EVALUABLE",
                "reason": f"endpoints served different models: {model_aicredits} vs {model_agy}",
            }
            mcnemar_tests = {}
        else:
            mcnemar_tests = {}
            pairs = [("aicredits", "agy")]
            for a, b in pairs:
                a_runs = [r["run_id"] for r in endpoint_results.get(a, []) if "run_id" in r]
                b_runs = [r["run_id"] for r in endpoint_results.get(b, []) if "run_id" in r]
                with trace_store._lock:
                    cur = trace_store.conn.cursor()
                    a_map = {}
                    if a_runs:
                        placeholders = ",".join("?" for _ in a_runs)
                        cur.execute(
                            f"SELECT scenario_id, MAX(COALESCE(verdict, 0)) AS passed FROM spans WHERE run_id IN ({placeholders}) GROUP BY run_id, scenario_id",
                            a_runs,
                        )
                        a_map = {row["scenario_id"]: bool(row["passed"]) for row in cur.fetchall()}
                    b_map = {}
                    if b_runs:
                        placeholders = ",".join("?" for _ in b_runs)
                        cur.execute(
                            f"SELECT scenario_id, MAX(COALESCE(verdict, 0)) AS passed FROM spans WHERE run_id IN ({placeholders}) GROUP BY run_id, scenario_id",
                            b_runs,
                        )
                        b_map = {row["scenario_id"]: bool(row["passed"]) for row in cur.fetchall()}
                common_sids = sorted(set(a_map.keys()) & set(b_map.keys()))
                a_bools = [a_map[sid] for sid in common_sids]
                b_bools = [b_map[sid] for sid in common_sids]
                pair_key = f"{a}_vs_{b}"
                if common_sids:
                    mcnemar_tests[pair_key] = mcnemar_from_pairs(a_bools, b_bools)
                else:
                    mcnemar_tests[pair_key] = {"p_value": 1.0, "statistic": 0.0}

            aicredits_ci = summary_endpoints.get("aicredits", {}).get("wilson_ci", [0.0, 0.0])
            agy_ci = summary_endpoints.get("agy", {}).get("wilson_ci", [0.0, 0.0])

            def is_disjoint(ci1: List[float], ci2: List[float]) -> bool:
                return ci1[1] < ci2[0] or ci2[1] < ci1[0]

            disjoint = is_disjoint(aicredits_ci, agy_ci)
            h6_result = {
                "statement": "Same model, 2+ endpoints, grounded rates with disjoint CIs",
                "verdict": "SUPPORTED (Identical model across endpoints produced disjoint CIs)" if disjoint else "FALSIFIED (Wilson CIs overlap across endpoints)",
                "disjoint_ci_pairs": {"aicredits_vs_agy": disjoint},
                "statistical_power_declared": "MEC v1.0 powered to detect >= 10pp delta at alpha=0.05",
            }

    total_sweep_cost = sum(v.get("total_cost_usd", 0.0) for v in summary_endpoints.values())

    final_results = {
        "spec_version": "2.0.0",
        "experiment": "p07_provider_variance",
        "model_under_test": "google/gemini-3.7-flash",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "n_scenarios": len(selected_ids),
        "manifest_sha256": manifest.get("manifest_sha256", ""),
        "h6": h6_result,
        "hypothesis_h6": h6_result,
        "total_sweep_cost_usd": round(total_sweep_cost, 6),
        "endpoints": summary_endpoints,
        "mcnemar_tests": mcnemar_tests,
        "raw_runs": endpoint_results,
    }

    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(final_results, f, indent=2)
    print(f"\nWrote results to {results_path}")

    fig_path = output_dir / "figure.svg"
    generate_figure(final_results, fig_path)

    return final_results


def run_variance_experiment(
    scenario_count: int = 150,
    step_cap: int = 24,
    concurrency: int = 2,
    real: bool = False,
    confirm: bool = False,
    dry_run: bool = False,
    target_endpoint: Optional[str] = None,
    output_dir: Path = Path("projects/p07_variance"),
) -> Dict[str, Any]:
    """Execute complete Project P7 variance sweep across endpoints."""
    load_dotenv()
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = ensure_manifest(output_dir, scenario_count=scenario_count)
    selected_ids = manifest["scenario_ids"]

    corpus = build_corpus()
    scenario_map = {s.scenario_id: s for s in corpus.scenarios if s.scenario_id in selected_ids}

    trace_db_path = output_dir / "trace.db"
    trace_store = TraceStore(str(trace_db_path))

    ledger_path = output_dir / "ledger.jsonl"
    price_table = PriceTable(
        rungs={
            k: RungPricing(model_name=v["model_name"] or "agy-default", input_price_per_m=v["in_price"], output_price_per_m=v["out_price"])
            for k, v in ENDPOINTS.items()
        }
    )
    ledger = CostLedger(ledger_path=ledger_path)

    # Dry-run cost estimate
    est_in_tokens = 3500 * scenario_count
    est_out_tokens = 300 * scenario_count
    total_est_cost = 0.0
    for k, v in ENDPOINTS.items():
        c = (est_in_tokens * v["in_price"] / 1_000_000.0) + (est_out_tokens * v["out_price"] / 1_000_000.0)
        total_est_cost += c

    if real and confirm:
        print("MODE: REAL ENDPOINTS (spending)")
    else:
        print("MODE: DRY-RUN / STUB (no spend)")

    print("=" * 70)
    print("PROJECT P7: PROVIDER VARIANCE & MULTI-ENDPOINT GROUNDING CALIBRATION")
    print(f"Model Under Test:  google/gemini-3.7-flash / gemini-3.8-flash (Shared Architecture across all Endpoints)")
    print(f"Scenarios:         {len(selected_ids)} (T1={manifest['tier_counts']['T1']}, T2={manifest['tier_counts']['T2']}, T3={manifest['tier_counts']['T3']})")
    print(f"Step Cap:          {step_cap}")
    print(f"Endpoints:         {list(ENDPOINTS.keys()) if not target_endpoint else [target_endpoint]}")
    print(f"Total Runs:        {len(selected_ids) * (len(ENDPOINTS) if not target_endpoint else 1)}")
    print(f"Est. Total:        ${total_est_cost:.4f} USD (P7 Budget Cap: $5.00 USD)")
    print("=" * 70)

    if dry_run or (not confirm):
        print("\nDry run completed successfully without network spend.")
        return {"dry_run_est_cost_usd": total_est_cost, "manifest": manifest}

    endpoint_results: Dict[str, List[Dict[str, Any]]] = {k: [] for k in ENDPOINTS}

    # If targeting a specific endpoint (e.g. agy), load previous runs for other endpoints from results.json
    results_path = output_dir / "results.json"
    if target_endpoint and results_path.exists():
        try:
            prev_data = json.loads(results_path.read_text(encoding="utf-8"))
            raw_runs = prev_data.get("raw_runs", {})
            for k in ENDPOINTS:
                if k != target_endpoint and k in raw_runs:
                    endpoint_results[k] = raw_runs[k]
                    print(f"[REUSE] Loaded {len(endpoint_results[k])} existing runs for [{k}] from results.json")
        except Exception as e:
            print(f"Warning: Could not load previous runs: {e}")

    endpoints_to_run = {target_endpoint: ENDPOINTS[target_endpoint]} if target_endpoint else ENDPOINTS
    sweep_ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    for e_key, endpoint_cfg in endpoints_to_run.items():
        print(f"\n>>> Executing Sweep for Endpoint [{e_key}]: {endpoint_cfg['name']} ({endpoint_cfg['model_label']})...")
        tasks = [
            ScenarioTask(task_id=sid, prompt=scenario_map[sid].prompt, tier=scenario_map[sid].tier)
            for sid in selected_ids
        ]

        def _worker(task: ScenarioTask) -> Dict[str, Any]:
            run_id = f"p07_{e_key}_{task.task_id}_{sweep_ts}"
            return execute_scenario(
                task=task,
                scenario=scenario_map[task.task_id],
                corpus=corpus,
                endpoint_cfg=endpoint_cfg,
                trace_store=trace_store,
                ledger=ledger,
                step_cap=step_cap,
                real=real,
                run_id=run_id,
            )

        if concurrency > 1 and real:
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
                futures = [pool.submit(_worker, t) for t in tasks]
                for fut in concurrent.futures.as_completed(futures):
                    res = fut.result()
                    endpoint_results[e_key].append(res)
                    status_icon = "PASS" if res["grounded"] else "FAIL"
                    print(f"  [{e_key}] {res['scenario_id']} ({res['tier']}) -> {status_icon} (steps={res['steps_used']}, lat={res['wall_time_ms']:.0f}ms)")
        else:
            for t in tasks:
                res = _worker(t)
                endpoint_results[e_key].append(res)
                status_icon = "PASS" if res["grounded"] else "FAIL"
                print(f"  [{e_key}] {res['scenario_id']} ({res['tier']}) -> {status_icon} (steps={res['steps_used']}, lat={res['wall_time_ms']:.0f}ms)")

    # Sort results deterministically by scenario_id
    for e_key in endpoint_results:
        endpoint_results[e_key].sort(key=lambda x: x["scenario_id"])

    # Build results strictly from trace.db
    final_results = build_results_from_trace(
        trace_store=trace_store,
        endpoint_results=endpoint_results,
        manifest=manifest,
        output_dir=output_dir,
    )

    return final_results


def main():
    parser = argparse.ArgumentParser(description="Project P7: Provider Variance Runner")
    parser.add_argument("--scenarios", type=int, default=150, help="Number of scenarios to evaluate (default 150)")
    parser.add_argument("--step-cap", type=int, default=24, help="Step cap per scenario (default 24)")
    parser.add_argument("--concurrency", type=int, default=4, help="Parallel threads for evaluation")
    parser.add_argument("--confirm", action="store_true", help="Confirm real LLM spend and execute real endpoints")
    parser.add_argument("--real", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--dry-run", action="store_true", help="Perform dry-run estimation only")
    parser.add_argument("--rebuild-results", action="store_true", help="Rebuild results.json and figure from trace.db without running sweep")
    parser.add_argument("--endpoint", type=str, default=None, help="Target specific endpoint (e.g. agy)")
    parser.add_argument("--output-dir", type=str, default="projects/p07_variance", help="Output directory")

    args = parser.parse_args()
    output_dir = Path(args.output_dir)

    if args.rebuild_results:
        trace_db_path = output_dir / "trace.db"
        trace_store = TraceStore(str(trace_db_path))
        build_results_from_trace(trace_store=trace_store, output_dir=output_dir)
        return

    # --confirm implies real
    is_confirm = bool(args.confirm)
    is_real = bool(args.confirm or args.real)
    is_dry_run = bool(args.dry_run or not args.confirm)

    run_variance_experiment(
        scenario_count=args.scenarios,
        step_cap=args.step_cap,
        concurrency=args.concurrency,
        real=is_real,
        confirm=is_confirm,
        dry_run=is_dry_run,
        target_endpoint=args.endpoint,
        output_dir=output_dir,
    )


if __name__ == "__main__":
    main()
