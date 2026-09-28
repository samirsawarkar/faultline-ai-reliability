"""LLM Judge Labelling client for P18 trace triage.

Evaluates real agent traces against 4 failure types using OpenAI-compatible endpoint:
- T1 UNRECOVERED_TOOL_ERROR
- T2 REPEATED_CALL_NO_PROGRESS
- T3 LOOP_WITHOUT_PROGRESS
- T4 MISREAD_TOOL_OUTPUT

Features:
- Outcome-blinded: judge_view contains no success or status flags.
- Retry with exponential backoff (2s, 8s, 30s) up to 3 attempts on network/JSON/validation errors.
- Graceful error recording ('label_error' field, continues to next trace).
- Resumption skipping labelled and errored IDs; --retry-errors to re-attempt only failed traces.
- Per-call wall time tracking and max_tokens=2000 limit.

NOTE: Per experiment instructions, this module is written for the pipeline but
MUST NOT BE RUN against the live model during setup.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from projects.p18_trace_triage.adapter import build_judge_view, load_run_spans

DEFAULT_BACKOFF_DELAYS: Tuple[float, ...] = (2.0, 8.0, 30.0)


class FailureTypeAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: bool = Field(description="True if the failure mode occurred, False otherwise.")
    evidence_step: Optional[int] = Field(
        default=None,
        description="0-indexed step where evidence of failure first appears, or null if not detected.",
    )
    reasoning: Optional[str] = Field(
        default="",
        description="Brief concise justification for the decision.",
    )


class TriageEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    T1: FailureTypeAssessment = Field(description="UNRECOVERED_TOOL_ERROR assessment")
    T2: FailureTypeAssessment = Field(description="REPEATED_CALL_NO_PROGRESS assessment")
    T3: FailureTypeAssessment = Field(description="LOOP_WITHOUT_PROGRESS assessment")
    T4: FailureTypeAssessment = Field(description="MISREAD_TOOL_OUTPUT assessment")


JUDGE_SYSTEM_PROMPT = """You are an expert AI reliability judge evaluating agent execution traces.
Given the step-by-step transcript of an agent run, you must evaluate the occurrence of four specific failure modes:

1. T1 UNRECOVERED_TOOL_ERROR:
   A tool/API call errors (error.type, error text in tool result) and the run never succeeds at that step afterwards.
   - Return label=true if a tool failed and the agent never recovered from that failure.
   - If the agent subsequently retried and succeeded, return label=false.

2. T2 REPEATED_CALL_NO_PROGRESS:
   The same tool call (same name + same normalized arguments) issued >= 3 times with no new information in between.
   - Return label=true if identical tool invocations were executed 3+ times without producing distinct informative state.

3. T3 LOOP_WITHOUT_PROGRESS:
   Agent cycles through reformulations/actions without getting closer to the goal (generalisation of FAULTLINE's OVERCONSTRAINED_SEARCH_LOOP).
   - Return label=true if the agent wanders in circles, repeatedly trying minor variations without making real headway.

4. T4 MISREAD_TOOL_OUTPUT:
   Agent's next step contradicts or ignores what a tool actually returned.
   - Return label=true if the agent ignores explicit information returned by a tool or acts in direct contradiction to it.

You must respond ONLY with valid JSON conforming to this schema:
{
  "T1": {"label": bool, "evidence_step": int or null, "reasoning": str},
  "T2": {"label": bool, "evidence_step": int or null, "reasoning": str},
  "T3": {"label": bool, "evidence_step": int or null, "reasoning": str},
  "T4": {"label": bool, "evidence_step": int or null, "reasoning": str}
}
"""


def get_llm_client() -> Tuple[OpenAI, str]:
    """Initialize OpenAI-compatible client from environment variables."""
    api_key = os.environ.get("LLM_BRIDGE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Environment variable LLM_BRIDGE_API_KEY is required but unset. "
            "Please export LLM_BRIDGE_API_KEY before running label.py."
        )

    base_url = os.environ.get("LLM_BRIDGE_BASE_URL", "http://127.0.0.1:8123/v1")
    model = "antigravity/gemini-3.8-flash"
    client = OpenAI(base_url=base_url, api_key=api_key)
    return client, model


def load_session_states(output_path: Path) -> Tuple[Set[str], Set[str]]:
    """Read existing session_ids from output labels.jsonl separated into labelled and errored."""
    if not output_path.exists():
        return set(), set()
    labelled: Set[str] = set()
    errored: Set[str] = set()
    with open(output_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                sid = rec.get("session_id") or rec.get("run_id")
                if not sid:
                    continue
                if "label_error" in rec:
                    errored.add(sid)
                elif "evaluation" in rec:
                    labelled.add(sid)
            except Exception:
                pass
    return labelled, errored


def strip_outer_fence(text: str) -> str:
    """Strip surrounding whitespace and outer markdown code fence (```...```) if present."""
    text = text.strip()
    if text.startswith("```"):
        if "\n" in text:
            text = text.split("\n", 1)[1]
        else:
            text = ""
        text = text.strip()
        if text.endswith("```"):
            text = text[:-3].strip()
    return text


def label_trace_with_retry(
    client: Any,
    model: str,
    judge_view: str,
    max_attempts: int = 3,
    backoff_delays: Tuple[float, ...] = DEFAULT_BACKOFF_DELAYS,
    sleep_fn: Any = time.sleep,
) -> Tuple[Optional[TriageEvaluation], Optional[Dict[str, int]], Optional[str], float]:
    """Invoke LLM judge with up to max_attempts on network, JSON, or validation errors.

    Returns:
        (evaluation, usage, error_string, wall_time_s)
    """
    messages = [
        {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
        {"role": "user", "content": judge_view},
    ]

    t0 = time.time()
    last_error: Optional[Exception] = None

    for attempt in range(max_attempts):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.0,
                max_tokens=2000,
                response_format={"type": "json_object"},
            )

            raw_text = response.choices[0].message.content or "{}"
            cleaned_text = strip_outer_fence(raw_text)
            parsed_json = json.loads(cleaned_text)
            validated = TriageEvaluation.model_validate(parsed_json)

            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            }
            wall_time_s = round(time.time() - t0, 3)
            return validated, usage, None, wall_time_s

        except (json.JSONDecodeError, ValidationError, Exception) as e:
            last_error = e
            if attempt < max_attempts - 1:
                delay = backoff_delays[attempt] if attempt < len(backoff_delays) else backoff_delays[-1]
                if delay > 0:
                    sleep_fn(delay)

    wall_time_s = round(time.time() - t0, 3)
    error_summary = f"{type(last_error).__name__}: {str(last_error)[:200]}"
    return None, None, error_summary, wall_time_s


def run_labelling(
    manifest_path: Path = Path("projects/p18_trace_triage/manifest.json"),
    output_path: Path = Path("projects/p18_trace_triage/labels.jsonl"),
    limit: Optional[int] = None,
    retry_errors: bool = False,
    client: Optional[Any] = None,
    model: Optional[str] = None,
    backoff_delays: Tuple[float, ...] = DEFAULT_BACKOFF_DELAYS,
    sleep_fn: Any = time.sleep,
) -> int:
    """Run trace labelling process (resumable, appends to labels.jsonl).

    Returns:
        Number of traces processed in this run.
    """
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    runs = manifest["runs"]
    labelled_ids, errored_ids = load_session_states(output_path)

    if retry_errors:
        pending_runs = [r for r in runs if r["session_id"] in errored_ids]
    else:
        to_skip = labelled_ids | errored_ids
        pending_runs = [r for r in runs if r["session_id"] not in to_skip]

    if limit is not None and limit > 0:
        pending_runs = pending_runs[:limit]

    print(
        f"Total runs: {len(runs)}, Labelled: {len(labelled_ids)}, "
        f"Errored: {len(errored_ids)}, Queued for this pass: {len(pending_runs)}"
    )
    if not pending_runs:
        print("Nothing to label.")
        return 0

    if client is None or model is None:
        client, model = get_llm_client()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    processed_count = 0

    with open(output_path, "a", encoding="utf-8") as out_f:
        for idx, run_meta in enumerate(pending_runs):
            sid = run_meta["session_id"]
            bench = run_meta["benchmark"]
            print(f"[{idx+1}/{len(pending_runs)}] Processing {sid} ({bench})...")

            spans = load_run_spans(run_meta)
            judge_view, is_trunc = build_judge_view(
                spans=spans,
                benchmark=bench,
                session_id=sid,
                max_tokens=30000,
            )

            evaluation, usage, err_msg, wall_time_s = label_trace_with_retry(
                client=client,
                model=model,
                judge_view=judge_view,
                max_attempts=3,
                backoff_delays=backoff_delays,
                sleep_fn=sleep_fn,
            )

            record: Dict[str, Any] = {
                "session_id": sid,
                "run_id": run_meta.get("run_id"),
                "benchmark": bench,
                "split": run_meta.get("split"),
                "task_group": run_meta.get("task_group"),
                "judge_view_truncated": is_trunc,
                "wall_time_s": wall_time_s,
            }

            if err_msg is not None:
                record["label_error"] = err_msg
                print(f"  FAILED after 3 attempts: {err_msg}")
            else:
                record["evaluation"] = evaluation.model_dump()
                record["usage"] = usage

            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
            out_f.flush()
            processed_count += 1

    print(f"Labelling batch finished. Processed {processed_count} traces. Appended to {output_path}")
    return processed_count


def main():
    parser = argparse.ArgumentParser(description="P18 Trace Triage LLM Judge Labelling")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("projects/p18_trace_triage/manifest.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("projects/p18_trace_triage/labels.jsonl"),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of runs to label in this invocation",
    )
    parser.add_argument(
        "--retry-errors",
        action="store_true",
        default=False,
        help="Re-attempt only traces that previously recorded a label_error",
    )
    args = parser.parse_args()

    # Safety guard: Check environment variable before proceeding
    if not os.environ.get("LLM_BRIDGE_API_KEY"):
        print(
            "ERROR: LLM_BRIDGE_API_KEY environment variable is unset.\n"
            "This setup script defines the labelling pipeline, but requires LLM_BRIDGE_API_KEY\n"
            "to execute requests against the model.",
            file=sys.stderr,
        )
        sys.exit(1)

    run_labelling(
        manifest_path=args.manifest,
        output_path=args.output,
        limit=args.limit,
        retry_errors=args.retry_errors,
    )


if __name__ == "__main__":
    main()
