"""Unit tests for P18 trace triage rule detectors (T1, T2) using hand-made span fixtures."""
import json
import pytest

from projects.p18_trace_triage.rules import (
    eval_unrecovered_tool_error,
    eval_repeated_call_no_progress,
)


def _make_span(
    step_idx: int,
    tool_name: str | None = None,
    tool_args: dict | None = None,
    tool_result: str | None = None,
    call_id: str | None = None,
    error_type: str | None = None,
    status_code: int = 1,
    incoming_responses: list[dict] | None = None,
    user_prompt: str | None = None,
) -> dict:
    """Helper to construct a realistic OpenTelemetry GenAI chat span."""
    input_messages = []
    if user_prompt:
        input_messages.append({
            "role": "user",
            "parts": [{"type": "text", "content": user_prompt}],
        })
    if incoming_responses:
        for resp in incoming_responses:
            input_messages.append({
                "role": "user",
                "parts": [{
                    "type": "tool_call_response",
                    "id": resp["id"],
                    "result": resp["result"],
                }],
            })

    output_messages = []
    if tool_name is not None:
        cid = call_id or f"call_{step_idx}"
        output_messages.append({
            "role": "assistant",
            "parts": [{
                "type": "tool_call",
                "id": cid,
                "name": tool_name,
                "arguments": tool_args or {},
            }],
        })

    return {
        "span_id": f"span_{step_idx}",
        "name": f"step_{step_idx}",
        "status": {"code": status_code, "message": ""},
        "attributes": {
            "error.type": error_type,
            "gen_ai.input.messages": json.dumps(input_messages) if input_messages else "",
            "gen_ai.output.messages": json.dumps(output_messages) if output_messages else "",
        },
    }


def test_unrecovered_tool_error_detected():
    """T1: Tool errors with structural error prefix and is never recovered."""
    spans = [
        _make_span(0, tool_name="fetch_records", tool_args={"table": "users"}, call_id="c1", user_prompt="Get users"),
        _make_span(1, incoming_responses=[{"id": "c1", "result": "Error: Database connection failed"}]),
    ]

    detected, step, reason = eval_unrecovered_tool_error(spans)
    assert detected is True
    assert step == 0
    assert "fetch_records" in reason
    assert "Database connection failed" in reason


def test_unrecovered_tool_error_recovered():
    """T1: Tool errors at step 0, but a retry at step 1 succeeds."""
    spans = [
        _make_span(0, tool_name="fetch_records", tool_args={"table": "users"}, call_id="c1", user_prompt="Get users"),
        _make_span(
            1,
            tool_name="fetch_records",
            tool_args={"table": "users_backup"},
            call_id="c2",
            incoming_responses=[{"id": "c1", "result": "Error: Table not found"}],
        ),
        _make_span(2, incoming_responses=[{"id": "c2", "result": json.dumps([{"id": 1, "name": "Alice"}])}]),
    ]

    detected, step, reason = eval_unrecovered_tool_error(spans)
    assert detected is False
    assert step is None


def test_tool_output_containing_error_substrings_not_error():
    """Requirement (a): bash output containing 'raise ValueError' and 'errorlist' is NOT an error."""
    bash_output = (
        "def validate_form(data):\n"
        "    if not data:\n"
        "        raise ValueError('Missing form data')\n"
        "    errorlist = []\n"
        "    return errorlist\n"
    )
    spans = [
        _make_span(0, tool_name="bash", tool_args={"cmd": "cat forms.py"}, call_id="c1", user_prompt="Inspect forms"),
        _make_span(1, incoming_responses=[{"id": "c1", "result": bash_output}]),
    ]

    detected, step, reason = eval_unrecovered_tool_error(spans)
    assert detected is False, f"Expected False but got True with reason: {reason}"
    assert step is None


def test_tool_output_json_error_key_is_error():
    """Requirement (b): {\"error\": \"Document 1 not found\"} IS an error."""
    json_error_output = json.dumps({"error": "Document 1 not found"})
    spans = [
        _make_span(0, tool_name="get_document", tool_args={"id": 1}, call_id="c1", user_prompt="Get doc 1"),
        _make_span(1, incoming_responses=[{"id": "c1", "result": json_error_output}]),
    ]

    detected, step, reason = eval_unrecovered_tool_error(spans)
    assert detected is True, "Expected True for top-level JSON error key"
    assert step == 0
    assert "get_document" in reason
    assert "Document 1 not found" in reason


def test_tool_output_tool_use_error_tag_is_error():
    """Requirement (c): <tool_use_error>..</tool_use_error> IS an error."""
    tagged_error_output = "<tool_use_error>Network timeout connecting to server</tool_use_error>"
    spans = [
        _make_span(0, tool_name="fetch_url", tool_args={"url": "http://api.internal"}, call_id="c1", user_prompt="Fetch"),
        _make_span(1, incoming_responses=[{"id": "c1", "result": tagged_error_output}]),
    ]

    detected, step, reason = eval_unrecovered_tool_error(spans)
    assert detected is True, "Expected True for <tool_use_error> tag"
    assert step == 0
    assert "fetch_url" in reason
    assert "<tool_use_error>" in reason


def test_three_identical_calls_different_responses_not_t2():
    """Requirement (d): three identical calls with three different responses is NOT T2."""
    spans = [
        _make_span(0, tool_name="bash", tool_args={"cmd": "git status"}, call_id="c1", user_prompt="Check git"),
        _make_span(
            1,
            tool_name="bash",
            tool_args={"cmd": "git status"},
            call_id="c2",
            incoming_responses=[{"id": "c1", "result": "On branch main\nnothing to commit"}],
        ),
        _make_span(
            2,
            tool_name="bash",
            tool_args={"cmd": "git status"},
            call_id="c3",
            incoming_responses=[{"id": "c2", "result": "On branch main\nChanges not staged:\n  modified: app.py"}],
        ),
        _make_span(3, incoming_responses=[{"id": "c3", "result": "On branch main\nChanges to commit:\n  modified: app.py"}]),
    ]

    detected, step, reason = eval_repeated_call_no_progress(spans)
    assert detected is False, f"Expected False for different responses, got {detected} ({reason})"
    assert step is None


def test_three_identical_calls_identical_responses_is_t2():
    """Requirement (e): three identical calls with identical responses IS T2."""
    identical_resp = "On branch main\nnothing to commit, working tree clean"
    spans = [
        _make_span(0, tool_name="bash", tool_args={"cmd": "git status"}, call_id="c1", user_prompt="Check git"),
        _make_span(
            1,
            tool_name="bash",
            tool_args={"cmd": "git status"},
            call_id="c2",
            incoming_responses=[{"id": "c1", "result": identical_resp}],
        ),
        _make_span(
            2,
            tool_name="bash",
            tool_args={"cmd": "git status"},
            call_id="c3",
            incoming_responses=[{"id": "c2", "result": "  On branch main\n nothing to commit, working tree clean  "}],
        ),
        _make_span(3, incoming_responses=[{"id": "c3", "result": identical_resp}]),
    ]

    detected, step, reason = eval_repeated_call_no_progress(spans)
    assert detected is True, "Expected True for 3 identical calls with identical responses"
    assert step == 2
    assert "bash" in reason
    assert "git status" in reason


def test_outcome_blinding_in_adapter_views():
    """FIX 1: Assert neither laya_state nor judge_view contains 'Success:' or 'Status:' for a fixture run with success=False."""
    from projects.p18_trace_triage.adapter import build_laya_state, build_judge_view

    spans = [
        _make_span(0, tool_name="bash", tool_args={"cmd": "false"}, call_id="c1", user_prompt="Run job", status_code=2),
        _make_span(1, incoming_responses=[{"id": "c1", "result": "exit 1"}], status_code=2),
    ]

    laya_state, _ = build_laya_state(spans, session_id="run_fail_1")
    judge_view, _ = build_judge_view(spans, benchmark="swebench", session_id="run_fail_1")

    # Assert neither output leaks outcome
    assert "Success:" not in laya_state, "laya_state leaked Success:"
    assert "Status:" not in laya_state, "laya_state leaked Status:"
    assert "Success:" not in judge_view, "judge_view leaked Success:"
    assert "Status:" not in judge_view, "judge_view leaked Status:"

    # Benchmark belongs in judge_view only
    assert "Benchmark: swebench" in judge_view
    assert "Benchmark:" not in laya_state


def test_label_retry_and_error_handling_with_fake_client(tmp_path):
    """FIX 2: Fake client returning invalid JSON 3 times triggers backoff, writes error record, and loop continues."""
    from projects.p18_trace_triage.label import run_labelling

    class FakeMessage:
        def __init__(self, content):
            self.content = content

    class FakeChoice:
        def __init__(self, content):
            self.message = FakeMessage(content)

    class FakeCompletions:
        def __init__(self, responses):
            self.responses = list(responses)
            self.call_count = 0

        def create(self, **kwargs):
            self.call_count += 1
            if self.responses:
                text = self.responses.pop(0)
            else:
                text = "fallback invalid"
            return type(
                "Resp",
                (),
                {
                    "choices": [FakeChoice(text)],
                    "usage": type("Usage", (), {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15})(),
                },
            )()

    class FakeClient:
        def __init__(self, responses):
            self.chat = type("Chat", (), {"completions": FakeCompletions(responses)})()

    # Create dummy manifest with 2 runs
    test_runs = [
        {
            "session_id": "test_sid_001",
            "run_id": "test_run_001",
            "benchmark": "swebench",
            "split": "train",
            "task_group": "swebench:g1",
            "shard_path": "fake_shard.parquet",
            "row_idx": 0,
        },
        {
            "session_id": "test_sid_002",
            "run_id": "test_run_002",
            "benchmark": "swebench",
            "split": "train",
            "task_group": "swebench:g2",
            "shard_path": "fake_shard.parquet",
            "row_idx": 1,
        },
    ]

    manifest_file = tmp_path / "manifest.json"
    labels_file = tmp_path / "labels.jsonl"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump({"runs": test_runs}, f)

    # Mock load_run_spans to avoid needing real parquet files
    import projects.p18_trace_triage.label as label_mod

    orig_load_spans = label_mod.load_run_spans
    label_mod.load_run_spans = lambda r: [_make_span(0, user_prompt=f"Task for {r['session_id']}")]

    try:
        valid_eval_json = json.dumps({
            "T1": {"label": False, "evidence_step": None, "reasoning": "none"},
            "T2": {"label": False, "evidence_step": None, "reasoning": "none"},
            "T3": {"label": False, "evidence_step": None, "reasoning": "none"},
            "T4": {"label": False, "evidence_step": None, "reasoning": "none"},
        })

        # Run 1 fails 3 times on invalid JSON; Run 2 succeeds on valid JSON
        responses = [
            "malformed 1",
            "malformed 2",
            "malformed 3",
            valid_eval_json,
        ]
        fake_client = FakeClient(responses)

        processed = run_labelling(
            manifest_path=manifest_file,
            output_path=labels_file,
            client=fake_client,
            model="fake-model",
            backoff_delays=(0.0, 0.0, 0.0),
            sleep_fn=lambda _: None,
        )

        assert processed == 2
        assert fake_client.chat.completions.call_count == 4

        with open(labels_file, "r", encoding="utf-8") as f:
            records = [json.loads(line) for line in f]

        assert len(records) == 2

        # Record 0 must contain label_error and NO evaluation
        r0 = records[0]
        assert r0["session_id"] == "test_sid_001"
        assert "label_error" in r0
        assert "JSONDecodeError" in r0["label_error"]
        assert "evaluation" not in r0
        assert "wall_time_s" in r0

        # Record 1 must contain evaluation and NO label_error
        r1 = records[1]
        assert r1["session_id"] == "test_sid_002"
        assert "evaluation" in r1
        assert "label_error" not in r1
        assert r1["evaluation"]["T1"]["label"] is False
        assert "wall_time_s" in r1

        # Test resumption: running again should skip both labelled and errored IDs
        fake_client_empty = FakeClient([])
        re_processed = run_labelling(
            manifest_path=manifest_file,
            output_path=labels_file,
            client=fake_client_empty,
            model="fake-model",
        )
        assert re_processed == 0

        # Test --retry-errors: re-attempts only errored ID
        retry_client = FakeClient([valid_eval_json])
        retry_processed = run_labelling(
            manifest_path=manifest_file,
            output_path=labels_file,
            retry_errors=True,
            client=retry_client,
            model="fake-model",
            backoff_delays=(0.0, 0.0, 0.0),
            sleep_fn=lambda _: None,
        )
        assert retry_processed == 1

    finally:
        label_mod.load_run_spans = orig_load_spans


def test_strip_outer_fence():
    """Verify strip_outer_fence helper behavior across various outer fence formats and edges."""
    from projects.p18_trace_triage.label import strip_outer_fence

    # Standard ```json ... ```
    assert strip_outer_fence("```json\n{\"k\": \"v\"}\n```") == "{\"k\": \"v\"}"

    # Fence without language tag ``` ... ```
    assert strip_outer_fence("```\n{\"k\": \"v\"}\n```") == "{\"k\": \"v\"}"

    # Surrounding whitespace around fences
    assert strip_outer_fence("  \n```json\n{\"k\": \"v\"}\n```\n  ") == "{\"k\": \"v\"}"

    # Plain JSON without fences (must be untouched)
    assert strip_outer_fence("{\"k\": \"v\"}") == "{\"k\": \"v\"}"

    # JSON with backticks inside content (inner backticks preserved)
    inner_code = "{\"msg\": \"ran `cat file`\"}"
    assert strip_outer_fence(f"```json\n{inner_code}\n```") == inner_code

    # Non-fence prefix: only outer fence is stripped, do not search elsewhere
    non_fence = "Here is the response:\n```json\n{\"k\": \"v\"}\n```"
    assert strip_outer_fence(non_fence) == non_fence.strip()


def test_label_parses_json_wrapped_in_markdown_fence():
    """Verify label_trace_with_retry parses and validates JSON returned inside markdown fences."""
    from projects.p18_trace_triage.label import label_trace_with_retry, TriageEvaluation

    valid_json = json.dumps({
        "T1": {"label": False, "evidence_step": None, "reasoning": "No tool error detected"},
        "T2": {"label": True, "evidence_step": 2, "reasoning": "Same bash command issued 3 times"},
        "T3": {"label": False, "evidence_step": None, "reasoning": "No loop"},
        "T4": {"label": False, "evidence_step": None, "reasoning": "Output read accurately"},
    })

    fenced_content = f"```json\n{valid_json}\n```"

    class FakeChoice:
        def __init__(self, content):
            self.message = type("Msg", (), {"content": content})()

    class FakeCompletions:
        def __init__(self, content):
            self.content = content

        def create(self, **kwargs):
            return type(
                "Resp",
                (),
                {
                    "choices": [FakeChoice(self.content)],
                    "usage": type(
                        "Usage",
                        (),
                        {"prompt_tokens": 120, "completion_tokens": 60, "total_tokens": 180},
                    )(),
                },
            )()

    class FakeClient:
        def __init__(self, content):
            self.chat = type("Chat", (), {"completions": FakeCompletions(content)})()

    client = FakeClient(fenced_content)
    evaluation, usage, err, wall_time = label_trace_with_retry(
        client=client,
        model="fake-model",
        judge_view="[Fake transcript]",
        max_attempts=1,
    )

    assert err is None, f"Expected no error, got: {err}"
    assert isinstance(evaluation, TriageEvaluation)
    assert evaluation.T1.label is False
    assert evaluation.T2.label is True
    assert evaluation.T2.evidence_step == 2
    assert evaluation.T2.reasoning == "Same bash command issued 3 times"
    assert evaluation.T3.label is False
    assert evaluation.T4.label is False
    assert usage["total_tokens"] == 180
    assert wall_time >= 0.0

