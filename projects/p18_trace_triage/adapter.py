"""Adapter for Exgentic agent traces to Laya state and LLM judge view.

Converts raw OpenTelemetry GenAI chat spans from Exgentic/agent-llm-traces-v2 into:
1. laya_state: Compact text <= 512 Laya tokens (tools called in order with short args,
   repeated-call counts, errors, final status, step count).
2. judge_view: Fuller transcript capped at 30,000 tokens (~120,000 chars) for the labelling
   model, preserving initial and final turns when cutting middle turns.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_TOKENIZER = None


def get_laya_tokenizer():
    """Load the ModernBERT-large tokenizer for Laya from local cache."""
    global _TOKENIZER
    if _TOKENIZER is not None:
        return _TOKENIZER

    from transformers import AutoTokenizer

    hf_cache = os.environ.get("HF_HOME", "/Volumes/SamirDrive/cache/huggingface")
    pattern = f"{hf_cache}/hub/models--convaiinnovations--laya/snapshots/*/tokenizer"
    matches = sorted(glob.glob(pattern))
    if matches:
        _TOKENIZER = AutoTokenizer.from_pretrained(matches[0], local_files_only=True)
        return _TOKENIZER

    # Fallback to model id with cache_dir
    _TOKENIZER = AutoTokenizer.from_pretrained(
        "convaiinnovations/laya",
        subfolder="tokenizer",
        cache_dir=hf_cache,
    )
    return _TOKENIZER


_PARQUET_FILE_CACHE: Dict[str, Tuple[Any, List[Tuple[int, int, int]]]] = {}


def load_run_spans(run_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Load spans for a given run from its parquet shard and row_idx in O(1) time."""
    import pyarrow.parquet as pq

    shard_path = run_meta["shard_path"]
    row_idx = run_meta["row_idx"]

    if shard_path not in _PARQUET_FILE_CACHE:
        pf = pq.ParquetFile(shard_path)
        offsets = []
        curr = 0
        for rg in range(pf.num_row_groups):
            nrows = pf.metadata.row_group(rg).num_rows
            offsets.append((curr, curr + nrows, rg))
            curr += nrows
        _PARQUET_FILE_CACHE[shard_path] = (pf, offsets)

    pf, offsets = _PARQUET_FILE_CACHE[shard_path]
    for s, e, rg in offsets:
        if s <= row_idx < e:
            table = pf.read_row_group(rg, columns=["session_id", "spans"])
            return table["spans"][row_idx - s].as_py()
    raise IndexError(f"Row index {row_idx} not found in {shard_path}")


def clean_tool_response_text(raw: Any) -> str:
    """Extract human-readable text from tool call response payload."""
    if raw is None:
        return ""
    if isinstance(raw, str):
        # Often JSON string: '[{"type": "text", "text": "..."}]'
        s = raw.strip()
        if (s.startswith("[") and s.endswith("]")) or (s.startswith("{") and s.endswith("}")):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    texts = []
                    for item in parsed:
                        if isinstance(item, dict) and "text" in item:
                            texts.append(str(item["text"]))
                        else:
                            texts.append(str(item))
                    return " ".join(texts)
                elif isinstance(parsed, dict) and "text" in parsed:
                    return str(parsed["text"])
            except Exception:
                pass
        return s
    return str(raw)


def is_structural_tool_error(
    part: Optional[Dict[str, Any]],
    raw_result: Any,
    text: str,
) -> Tuple[bool, str]:
    """Evaluate structural error signals on a tool response.

    Rules (CTO specification):
    1. tool_call_response part carries an explicit error flag/status field.
    2. Response parses as JSON whose top-level object has an 'error' key,
       or a top-level non-zero exit/return code field.
    3. Response text is wrapped in <tool_use_error>...</tool_use_error>.
    4. Response STARTS WITH (after whitespace) 'Error:', 'ERROR:',
       'Traceback (most recent call last)', or 'An error occurred while parsing tool arguments'.
    Does NOT match error words inside the body of otherwise normal output.
    """
    # 1. Explicit error flag/status on the part dictionary
    if part and isinstance(part, dict):
        if part.get("is_error") is True:
            return True, "tool_call_response part has is_error=True"
        if part.get("error"):
            return True, f"tool_call_response part error: {part.get('error')}"
        if str(part.get("status", "")).lower() in ("error", "failed"):
            return True, f"tool_call_response part status: {part.get('status')}"

    # 2. JSON top-level object with 'error' key or non-zero exit/return code
    candidate_objs: List[Dict[str, Any]] = []

    def check_candidate_json(val: Any) -> None:
        if isinstance(val, dict):
            candidate_objs.append(val)
        elif isinstance(val, str):
            s = val.strip()
            if s.startswith("{") and s.endswith("}"):
                try:
                    p = json.loads(s)
                    if isinstance(p, dict):
                        candidate_objs.append(p)
                except Exception:
                    pass
            elif s.startswith("[") and s.endswith("]"):
                try:
                    p = json.loads(s)
                    if isinstance(p, list):
                        for item in p:
                            if isinstance(item, dict) and "text" in item and isinstance(item["text"], str):
                                t_s = item["text"].strip()
                                if t_s.startswith("{") and t_s.endswith("}"):
                                    try:
                                        sub = json.loads(t_s)
                                        if isinstance(sub, dict):
                                            candidate_objs.append(sub)
                                    except Exception:
                                        pass
                except Exception:
                    pass

    check_candidate_json(raw_result)
    if isinstance(text, str) and text:
        check_candidate_json(text)

    for obj in candidate_objs:
        if "error" in obj and obj["error"]:
            return True, f"JSON top-level error: {str(obj['error'])[:80]}"
        for code_key in ("exit_code", "return_code", "exitcode", "returncode", "exit_status"):
            if code_key in obj:
                try:
                    if int(obj[code_key]) != 0:
                        return True, f"Non-zero {code_key}: {obj[code_key]}"
                except (ValueError, TypeError):
                    pass

    # 3. <tool_use_error>...</tool_use_error>
    t_clean = (text or "").strip()
    if "<tool_use_error>" in t_clean and "</tool_use_error>" in t_clean:
        return True, "<tool_use_error> tag present"

    # 4. STARTS WITH (after whitespace)
    error_prefixes = (
        "Error:",
        "ERROR:",
        "Traceback (most recent call last)",
        "An error occurred while parsing tool arguments",
    )
    for pfx in error_prefixes:
        if t_clean.startswith(pfx):
            return True, f"Response starts with '{pfx}'"

    return False, ""


def extract_trace_events(spans: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Parse spans into a chronological sequence of steps with tool calls and responses.

    Tool calls are in gen_ai.output.messages; tool responses are in gen_ai.input.messages.
    """
    # 1. Map tool responses by tool call ID
    responses_by_id: Dict[str, Dict[str, Any]] = {}
    initial_prompt = ""

    for s in spans:
        attrs = s.get("attributes") or {}
        raw_inp = attrs.get("gen_ai.input.messages")
        if not raw_inp:
            continue
        try:
            msgs = json.loads(raw_inp) if isinstance(raw_inp, str) else raw_inp
            for m in msgs:
                role = m.get("role")
                parts = m.get("parts", [])
                if role == "user" and not initial_prompt:
                    for p in parts:
                        if p.get("type") == "text":
                            initial_prompt = str(p.get("content", ""))
                            break
                for p in parts:
                    if p.get("type") == "tool_call_response":
                        cid = p.get("id")
                        if cid:
                            raw_res = p.get("result")
                            clean_txt = clean_tool_response_text(raw_res)
                            responses_by_id[cid] = {
                                "text": clean_txt,
                                "raw_result": raw_res,
                                "part": p,
                            }
        except Exception:
            pass

    # 2. Extract chronological steps
    steps: List[Dict[str, Any]] = []
    all_errors: List[str] = []

    for idx, s in enumerate(spans):
        attrs = s.get("attributes") or {}
        span_status = s.get("status") or {}
        span_err_type = attrs.get("error.type")
        span_status_code = span_status.get("code")
        span_status_msg = span_status.get("message")

        step_has_error = False
        step_err_desc = ""

        if span_err_type:
            step_has_error = True
            step_err_desc = f"Span error: {span_err_type}"
            all_errors.append(step_err_desc)
        elif span_status_code == 2:
            step_has_error = True
            step_err_desc = f"Span status error: {span_status_msg or 'Code 2'}"
            all_errors.append(step_err_desc)

        # Output message and tool calls
        raw_out = attrs.get("gen_ai.output.messages")
        assistant_text = ""
        tool_calls: List[Dict[str, Any]] = []

        if raw_out:
            try:
                msgs = json.loads(raw_out) if isinstance(raw_out, str) else raw_out
                for m in msgs:
                    for p in m.get("parts", []):
                        ptype = p.get("type")
                        if ptype == "text":
                            assistant_text += str(p.get("content", ""))
                        elif ptype == "tool_call":
                            cid = p.get("id")
                            name = p.get("name", "unknown_tool")
                            args = p.get("arguments", {})
                            resp_info = responses_by_id.get(cid, {"text": "", "raw_result": None, "part": None})
                            resp = resp_info["text"]

                            # Check tool response for STRUCTURAL error indications
                            resp_err, err_reason = is_structural_tool_error(
                                resp_info["part"],
                                resp_info["raw_result"],
                                resp,
                            )
                            if resp_err:
                                step_has_error = True
                                step_err_desc = f"Tool {name} error: {err_reason}"
                                all_errors.append(step_err_desc)

                            tool_calls.append({
                                "id": cid,
                                "name": name,
                                "arguments": args,
                                "response": resp,
                                "is_error": resp_err,
                                "error_desc": err_reason if resp_err else "",
                            })
            except Exception:
                pass

        steps.append({
            "step_index": idx,
            "assistant_text": assistant_text.strip(),
            "tool_calls": tool_calls,
            "has_error": step_has_error,
            "error_desc": step_err_desc,
        })

    return {
        "initial_prompt": initial_prompt.strip(),
        "steps": steps,
        "total_steps": len(steps),
        "errors": all_errors,
    }


def format_short_args(args: Any, max_len: int = 40) -> str:
    """Format tool call arguments compactly."""
    if not args:
        return ""
    if isinstance(args, dict):
        parts = []
        for k, v in args.items():
            s = str(v)
            if len(s) > 15:
                s = s[:12] + "..."
            parts.append(f"{k}={s}")
        res = ", ".join(parts)
    else:
        res = str(args)
    if len(res) > max_len:
        res = res[: max_len - 3] + "..."
    return res


def build_laya_state(
    spans: List[Dict[str, Any]],
    session_id: str = "",
    max_tokens: int = 512,
    tokenizer: Any = None,
) -> Tuple[str, bool]:
    """Build compact text representation <= 512 Laya tokens.

    Outcome-blinded: excludes success/status and benchmark.
    Returns:
        (laya_state_string, is_truncated)
    """
    if tokenizer is None:
        try:
            tokenizer = get_laya_tokenizer()
        except Exception:
            tokenizer = None

    events = extract_trace_events(spans)
    prompt_snippet = events["initial_prompt"][:140].replace("\n", " ")
    if len(events["initial_prompt"]) > 140:
        prompt_snippet += "..."

    header = (
        f"Run: {session_id}\n"
        f"Prompt: {prompt_snippet}\n"
        f"Steps: {events['total_steps']}\n"
    )

    # Build sequence of tool calls, compressing consecutive identical calls
    call_entries: List[str] = []
    curr_key = None
    curr_count = 0
    curr_err = False

    for st in events["steps"]:
        for tc in st["tool_calls"]:
            short_args = format_short_args(tc["arguments"])
            key = f"{tc['name']}({short_args})"
            is_err = tc["is_error"]
            if key == curr_key and is_err == curr_err:
                curr_count += 1
            else:
                if curr_key is not None:
                    suffix = f" [x{curr_count}]" if curr_count > 1 else ""
                    if curr_err:
                        suffix += " -> ERR"
                    call_entries.append(f"{curr_key}{suffix}")
                curr_key = key
                curr_count = 1
                curr_err = is_err

    if curr_key is not None:
        suffix = f" [x{curr_count}]" if curr_count > 1 else ""
        if curr_err:
            suffix += " -> ERR"
        call_entries.append(f"{curr_key}{suffix}")

    errors_text = ""
    if events["errors"]:
        unique_errs = list(dict.fromkeys(events["errors"]))[:3]
        errors_text = "Errors: " + "; ".join(unique_errs) + "\n"

    # Assemble full untruncated state
    def assemble(entries: List[str]) -> str:
        body = "\n".join(f"{i+1}. {c}" for i, c in enumerate(entries))
        return f"{header}Tools:\n{body}\n{errors_text}".strip()

    full_state = assemble(call_entries)

    def count_tokens(text: str) -> int:
        if tokenizer is not None:
            return len(tokenizer.encode(text, add_special_tokens=False))
        return len(text) // 4  # heuristic fallback

    initial_tokens = count_tokens(full_state)
    if initial_tokens <= max_tokens:
        return full_state, False

    # Truncate intermediate entries keeping head and tail
    is_truncated = True
    head_size = 4
    tail_size = 4

    while head_size + tail_size >= len(call_entries):
        if head_size > 1:
            head_size -= 1
        elif tail_size > 1:
            tail_size -= 1
        else:
            break

    while head_size + tail_size < len(call_entries):
        omitted = len(call_entries) - (head_size + tail_size)
        trimmed = (
            call_entries[:head_size]
            + [f"[... {omitted} intermediate calls omitted ...]"]
            + call_entries[-tail_size:]
        )
        cand = assemble(trimmed)
        if count_tokens(cand) <= max_tokens:
            return cand, True
        # Reduce head or tail
        if head_size > 1 and head_size >= tail_size:
            head_size -= 1
        elif tail_size > 1:
            tail_size -= 1
        else:
            # Further truncate header/prompt if still over budget
            break

    # Hard truncate if still over budget
    lines = cand.split("\n")
    while count_tokens("\n".join(lines)) > max_tokens and len(lines) > 2:
        lines.pop(-2)

    return "\n".join(lines), True


def build_judge_view(
    spans: List[Dict[str, Any]],
    benchmark: str = "",
    session_id: str = "",
    max_tokens: int = 30000,
) -> Tuple[str, bool]:
    """Build full conversation transcript capped at 30,000 tokens (~120,000 chars).

    Outcome-blinded: excludes success and status (preserves benchmark in metadata).
    Preserves initial task instructions and final turns when cutting middle turns.
    Returns:
        (judge_view_string, is_truncated)
    """
    max_chars = max_tokens * 4  # approx 120,000 chars

    events = extract_trace_events(spans)

    header = (
        f"=== RUN METADATA ===\n"
        f"Run ID: {session_id}\n"
        f"Benchmark: {benchmark}\n"
        f"Total Steps: {events['total_steps']}\n\n"
        f"=== INITIAL TASK PROMPT ===\n"
        f"{events['initial_prompt']}\n\n"
        f"=== STEP-BY-STEP EXECUTION ===\n"
    )

    rendered_steps: List[str] = []
    for st in events["steps"]:
        s_lines = [f"[Step {st['step_index']}]"]
        if st["assistant_text"]:
            s_lines.append(f"Assistant: {st['assistant_text']}")
        for tc in st["tool_calls"]:
            args_str = json.dumps(tc["arguments"], ensure_ascii=False) if isinstance(tc["arguments"], dict) else str(tc["arguments"])
            s_lines.append(f"Tool Call: {tc['name']}({args_str})")
            if tc["response"]:
                s_lines.append(f"Tool Result: {tc['response']}")
        if st["has_error"]:
            s_lines.append(f"Error: {st['error_desc']}")
        rendered_steps.append("\n".join(s_lines))

    full_body = "\n\n".join(rendered_steps)
    full_text = header + full_body

    if len(full_text) <= max_chars:
        return full_text, False

    # Needs truncation: preserve first turns and last turns
    is_truncated = True
    head_k = len(rendered_steps) // 2
    tail_m = len(rendered_steps) - head_k

    # Binary search or decrement middle cut to fit inside max_chars
    low_cut_start = 5
    high_cut_end = len(rendered_steps) - 5
    if high_cut_end <= low_cut_start:
        low_cut_start = 1
        high_cut_end = max(2, len(rendered_steps) - 1)

    while low_cut_start < high_cut_end:
        cut_count = high_cut_end - low_cut_start
        cut_marker = f"\n\n[... Truncated {cut_count} intermediate steps (Step {low_cut_start} to {high_cut_end - 1}) to fit 30,000 token limit ...]\n\n"
        cand = (
            header
            + "\n\n".join(rendered_steps[:low_cut_start])
            + cut_marker
            + "\n\n".join(rendered_steps[high_cut_end:])
        )
        if len(cand) <= max_chars:
            return cand, True
        # Widen cut
        if low_cut_start > 2:
            low_cut_start -= 1
        if high_cut_end < len(rendered_steps) - 2:
            high_cut_end += 1
        else:
            break

    # Fallback character hard-cut on the candidate
    cut_marker = "\n\n[... Truncated intermediate turns to fit 30,000 token limit ...]\n\n"
    budget_each = (max_chars - len(header) - len(cut_marker)) // 2
    head_text = full_body[:budget_each]
    tail_text = full_body[-budget_each:]
    return f"{header}{head_text}{cut_marker}{tail_text}", True


def evaluate_sample_truncation(
    manifest_path: Path = Path("projects/p18_trace_triage/manifest.json"),
) -> Dict[str, Any]:
    """Measure truncation rate of laya_state and judge_view on the sampled manifest runs."""
    import pyarrow.parquet as pq

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Group runs by shard_path
    by_shard: Dict[str, List[Dict[str, Any]]] = {}
    for r in manifest["runs"]:
        by_shard.setdefault(r["shard_path"], []).append(r)

    total_runs = len(manifest["runs"])
    laya_truncated_count = 0
    judge_truncated_count = 0

    tokenizer = get_laya_tokenizer()

    for shard_path, shard_runs in by_shard.items():
        pf = pq.ParquetFile(shard_path)
        # Build row group offset index
        rg_offsets = []
        curr = 0
        for rg in range(pf.num_row_groups):
            nrows = pf.metadata.row_group(rg).num_rows
            rg_offsets.append((curr, curr + nrows, rg))
            curr += nrows

        # Group runs by row group
        rg_to_runs: Dict[int, List[Tuple[int, Dict[str, Any]]]] = {}
        for r in shard_runs:
            ridx = r["row_idx"]
            for s, e, rg in rg_offsets:
                if s <= ridx < e:
                    rg_to_runs.setdefault(rg, []).append((ridx - s, r))
                    break

        for rg, local_runs in rg_to_runs.items():
            table = pf.read_row_group(rg, columns=["session_id", "benchmark", "spans"])
            for local_idx, run_meta in local_runs:
                spans = table["spans"][local_idx].as_py()
                bench = run_meta["benchmark"]
                sid = run_meta["session_id"]

                _, laya_trunc = build_laya_state(
                    spans=spans,
                    session_id=sid,
                    max_tokens=512,
                    tokenizer=tokenizer,
                )
                _, judge_trunc = build_judge_view(
                    spans=spans,
                    benchmark=bench,
                    session_id=sid,
                    max_tokens=30000,
                )

                if laya_trunc:
                    laya_truncated_count += 1
                if judge_trunc:
                    judge_truncated_count += 1

    laya_rate = (laya_truncated_count / total_runs) if total_runs > 0 else 0.0
    judge_rate = (judge_truncated_count / total_runs) if total_runs > 0 else 0.0

    return {
        "total_runs": total_runs,
        "laya_truncated": laya_truncated_count,
        "laya_truncation_rate": laya_rate,
        "judge_truncated": judge_truncated_count,
        "judge_truncation_rate": judge_rate,
    }


def main():
    parser = argparse.ArgumentParser(description="P18 Trace Triage Adapter")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("projects/p18_trace_triage/manifest.json"),
    )
    args = parser.parse_args()

    results = evaluate_sample_truncation(args.manifest)
    print("=== P18 Adapter Truncation Evaluation on 400 Sampled Runs ===")
    print(f"Total runs evaluated: {results['total_runs']}")
    print(f"Laya state (<= 512 tokens): {results['laya_truncated']}/{results['total_runs']} truncated ({results['laya_truncation_rate']:.2%})")
    print(f"Judge view (<= 30k tokens): {results['judge_truncated']}/{results['total_runs']} truncated ({results['judge_truncation_rate']:.2%})")


if __name__ == "__main__":
    main()
