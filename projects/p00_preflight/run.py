"""W0.6 — Model Ladder Pre-flight Probe.

Probes rungs R1-R6, making two identical calls at temperature=0.0 to test:
- Endpoint connectivity and model version string
- Input/output token pricing
- Round-trip latency
- Temperature-0 determinism (byte-identical responses)
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import litellm
from pydantic import BaseModel, ConfigDict, Field

from faultline_p2.cost.ledger import (
    CostLedger,
    LedgerEntry,
    PriceTable,
    RungPricing,
    estimate,
)

_STRICT = ConfigDict(extra="forbid")

LADDER_SPEC = {
    "R1": {
        "model": "gemini/gemini-2.5-flash-lite",
        "name": "gemini-2.5-flash-lite",
        "input_price_per_m": 0.10,
        "output_price_per_m": 0.40,
    },
    "R2": {
        "model": "deepseek/deepseek-chat",
        "name": "deepseek-v4-flash",
        "input_price_per_m": 0.14,
        "output_price_per_m": 0.28,
    },
    "R3": {
        "model": "deepseek/deepseek-reasoner",
        "name": "deepseek-v4-pro",
        "input_price_per_m": 0.435,
        "output_price_per_m": 0.87,
    },
    "R4": {
        "model": "minimax/minimax-m3",
        "name": "minimax-m3",
        "input_price_per_m": 0.60,
        "output_price_per_m": 2.40,
    },
    "R5": {
        "model": "zhipu/glm-5.2",
        "name": "glm-5.2",
        "input_price_per_m": 1.40,
        "output_price_per_m": 4.40,
    },
    "R6": {
        "model": "anthropic/claude-3-5-sonnet-20241022",
        "name": "claude-3-5-sonnet-20241022",
        "input_price_per_m": 3.00,
        "output_price_per_m": 15.00,
    },
}


class PreflightEntry(BaseModel):
    model_config = _STRICT
    rung: str
    model_name: str
    endpoint: str
    status: str  # "live" | "failed"
    error: Optional[str] = None
    model_version: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    cost_source: str = "none"  # "provider" | "computed" | "none"
    latency_ms: float = 0.0
    temp0_deterministic: Optional[bool] = None
    call1_response: Optional[str] = None
    call2_response: Optional[str] = None


class PreflightReport(BaseModel):
    model_config = _STRICT
    timestamp_utc: str
    litellm_version: str
    total_rungs: int
    live_rungs: int
    failed_rungs: int
    non_deterministic_rungs: List[str]
    entries: List[PreflightEntry]


def get_price_table() -> PriceTable:
    rungs = {}
    for k, v in LADDER_SPEC.items():
        rungs[k] = RungPricing(
            model_name=v["name"],
            input_price_per_m=v["input_price_per_m"],
            output_price_per_m=v["output_price_per_m"],
        )
    return PriceTable(rungs=rungs)


def probe_rung(rung: str, spec: Dict[str, Any]) -> PreflightEntry:
    model = spec["model"]
    model_name = spec["name"]
    messages = [{"role": "user", "content": "Reply with exactly the single word PONG and nothing else."}]

    t0 = time.perf_counter()
    try:
        # Call 1
        resp1 = litellm.completion(
            model=model,
            messages=messages,
            temperature=0.0,
            max_tokens=16,
        )
        # Call 2 (identical at temp=0)
        resp2 = litellm.completion(
            model=model,
            messages=messages,
            temperature=0.0,
            max_tokens=16,
        )
        latency = round((time.perf_counter() - t0) * 1000.0 / 2.0, 2)

        content1 = resp1.choices[0].message.content or ""
        content2 = resp2.choices[0].message.content or ""
        deterministic = (content1 == content2)

        # Model version string returned by provider
        model_ver = getattr(resp1, "model", None) or resp1.get("model") or model_name

        in_tok = resp1.usage.prompt_tokens if hasattr(resp1, "usage") else 15
        out_tok = resp1.usage.completion_tokens if hasattr(resp1, "usage") else 2

        # Cost calculation
        try:
            cost_val = litellm.completion_cost(completion_response=resp1)
            cost_source = "provider"
        except Exception:
            in_cost = (in_tok * spec["input_price_per_m"]) / 1_000_000.0
            out_cost = (out_tok * spec["output_price_per_m"]) / 1_000_000.0
            cost_val = in_cost + out_cost
            cost_source = "computed"

        return PreflightEntry(
            rung=rung,
            model_name=model_name,
            endpoint=model,
            status="live",
            model_version=str(model_ver),
            prompt_tokens=in_tok,
            completion_tokens=out_tok,
            cost_usd=round(cost_val * 2.0, 6),
            cost_source=cost_source,
            latency_ms=latency,
            temp0_deterministic=deterministic,
            call1_response=content1.strip(),
            call2_response=content2.strip(),
        )
    except Exception as exc:
        latency = round((time.perf_counter() - t0) * 1000.0, 2)
        err_msg = f"{type(exc).__name__}: {str(exc)[:200]}"
        return PreflightEntry(
            rung=rung,
            model_name=model_name,
            endpoint=model,
            status="failed",
            error=err_msg,
            latency_ms=latency,
            temp0_deterministic=None,
        )


def format_markdown_table(report: PreflightReport) -> str:
    lines = [
        "| Rung | Model | Endpoint | Status | Version | Latency (ms) | Temp-0 Deterministic | In/Out Price ($/1M) | Est/Meas USD |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for e in report.entries:
        spec = LADDER_SPEC[e.rung]
        price_str = f"${spec['input_price_per_m']:.2f} / ${spec['output_price_per_m']:.2f}"
        det_str = "YES" if e.temp0_deterministic is True else ("NO" if e.temp0_deterministic is False else "N/A (failed)")
        cost_str = f"${e.cost_usd:.6f} ({e.cost_source})" if e.status == "live" else "N/A"
        if e.model_version:
            ver_str = e.model_version
        else:
            clean_err = (e.error or "Unknown error").replace("\n", " ").replace("|", "/").strip()
            ver_str = f"FAILED: {clean_err[:80]}"
        lines.append(
            f"| {e.rung} | {e.model_name} | `{e.endpoint}` | {e.status.upper()} | {ver_str} | {e.latency_ms:.1f} | {det_str} | {price_str} | {cost_str} |"
        )
    return "\n".join(lines)


def run_preflight(
    confirmed: bool = False,
    output_dir: Path = Path("projects/p00_preflight"),
    ledger_path: Path = Path("projects/_ledger/ledger.jsonl"),
) -> PreflightReport:
    pt = get_price_table()
    ledger = CostLedger(ledger_path=ledger_path)

    # 1. Print Dry-Run Estimate first
    # 6 rungs x 2 calls = 12 calls total. ~20 input tokens, ~5 output tokens per call.
    total_est = 0.0
    for rung, spec in LADDER_SPEC.items():
        c = estimate(n_runs=2, in_tokens=20, out_tokens=5, rung=rung, price_table=pt)
        total_est += c

    spent = ledger.spent("p00_preflight")
    cap = ledger.project_caps.get("p00_preflight", 0.50)

    print("=" * 60)
    print("PRE-FLIGHT DRY-RUN COST ESTIMATE (W0.6):")
    print(f"  Rungs to probe:     6 (2 calls each = 12 calls total)")
    print(f"  Estimated cost:     ${total_est:.6f} USD (~$0.0005 - $0.05)")
    print(f"  Project Cap:        ${cap:.2f} USD (Spent: ${spent:.4f})")
    print("=" * 60)

    if not confirmed:
        print("PRE-FLIGHT STOP: explicit --confirm not passed. No paid calls made.")
        print("To execute live pre-flight, run with --confirm.")
        sys.exit(0)

    output_dir.mkdir(parents=True, exist_ok=True)
    entries: List[PreflightEntry] = []
    non_det = []

    print("\nExecuting live pre-flight probes across R1-R6...")
    for rung in ["R1", "R2", "R3", "R4", "R5", "R6"]:
        spec = LADDER_SPEC[rung]
        print(f"  Probing [{rung}] {spec['name']} ({spec['model']})...", end=" ", flush=True)
        entry = probe_rung(rung, spec)
        entries.append(entry)
        print(f"-> {entry.status.upper()} (latency: {entry.latency_ms}ms, det: {entry.temp0_deterministic})")

        if entry.status == "live":
            # Record in ledger
            ledger.record(
                LedgerEntry(
                    run_id=f"preflight-{rung}",
                    project="p00_preflight",
                    rung=rung,
                    input_tokens=entry.prompt_tokens * 2,
                    output_tokens=entry.completion_tokens * 2,
                    usd=entry.cost_usd,
                    timestamp_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                )
            )
            if entry.temp0_deterministic is False:
                non_det.append(rung)

    report = PreflightReport(
        timestamp_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        litellm_version=importlib.metadata.version("litellm"),
        total_rungs=len(entries),
        live_rungs=sum(1 for e in entries if e.status == "live"),
        failed_rungs=sum(1 for e in entries if e.status == "failed"),
        non_deterministic_rungs=non_det,
        entries=entries,
    )

    # Write preflight.json
    json_path = output_dir / "preflight.json"
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(report.model_dump(), indent=2, sort_keys=True) + "\n")

    # Write preflight_table.md
    md_table = format_markdown_table(report)
    table_path = output_dir / "preflight_table.md"
    with open(table_path, "w", encoding="utf-8") as f:
        f.write(md_table + "\n")

    print(f"\nWrote: {json_path}")
    print(f"Wrote: {table_path}\n")
    print(md_table)
    return report


def main():
    parser = argparse.ArgumentParser(description="FAULTLINE Phase 2 Pre-flight Probe")
    parser.add_argument("--confirm", action="store_true", help="Explicit confirmation to spend compute budget")
    args = parser.parse_args()

    run_preflight(confirmed=args.confirm)


if __name__ == "__main__":
    main()
