"""Generate self-contained blind audit HTML page for P18 CEO review.

Writes to /Volumes/SamirDrive/scratch/faultline/p18_audit/audit.html.
Embeds Exgentic trace text in safe JSON data island, rendered via textContent.
Completely blind: NO judge labels, NO reasoning, NO rule outputs, NO success/status, NO stratum.
Zero external network requests (no CDNs, no remote fonts).
"""
from __future__ import annotations

import argparse
import html
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from projects.p18_trace_triage.adapter import load_run_spans, build_judge_view

DEFAULT_OUTPUT_PATH = Path(
    os.environ.get(
        "AUDIT_HTML_PATH",
        "/Volumes/SamirDrive/scratch/faultline/p18_audit/audit.html",
    )
)

T1_DEF = (
    "code rule: a tool/API call errors (`error.type`, error text in tool result) "
    "and the run never succeeds at that step afterwards."
)
T2_DEF = (
    "code rule: the same tool call (same name + same normalized arguments) "
    "issued >=3 times with no new information in between."
)
T3_DEF = (
    "Laya judgment: agent cycles through reformulations/actions without getting "
    "closer to the goal (generalisation of FAULTLINE's `OVERCONSTRAINED_SEARCH_LOOP`)."
)
T4_DEF = (
    "Laya judgment: agent's next step contradicts or ignores what a tool actually returned."
)


def generate_audit_html_content(
    audit_manifest: Dict[str, Any],
    spans_loader: Any = load_run_spans,
) -> str:
    """Generate the complete self-contained HTML page as a string."""
    runs = audit_manifest.get("runs", [])

    # Assemble sanitized items: position, benchmark, session_id, judge_view text
    # Strictly exclude judge labels, reasoning, rules, success/status, stratum
    items: List[Dict[str, Any]] = []
    for idx, r in enumerate(runs, start=1):
        sid = r["session_id"]
        bench = r["benchmark"]
        try:
            spans = spans_loader(r)
            judge_view_text, _ = build_judge_view(
                spans=spans,
                benchmark=bench,
                session_id=sid,
                max_tokens=30000,
            )
        except Exception as e:
            judge_view_text = f"Error loading trace for {sid}: {e}"

        # Ensure run metadata does not leak outcome
        if "=== RUN METADATA ===" in judge_view_text:
            meta_block = judge_view_text.split("=== INITIAL TASK PROMPT ===")[0]
            assert "Success:" not in meta_block, f"Outcome leakage 'Success:' in metadata of {sid}"
            assert "Status:" not in meta_block, f"Outcome leakage 'Status:' in metadata of {sid}"

        items.append({
            "position": idx,
            "total": len(runs),
            "session_id": sid,
            "benchmark": bench,
            "trace_text": judge_view_text,
        })

    # Encode items safely into JSON for script tag (escaping </script>)
    raw_json = json.dumps(items, ensure_ascii=False)
    safe_json = raw_json.replace("</", "<\\/")

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>P18 Trace Triage — Blind CEO Audit (100 Runs)</title>
  <style>
    :root {{
      --bg-body: #f8f9fa;
      --bg-card: #ffffff;
      --bg-panel: #f1f3f5;
      --bg-code: #1e1e1e;
      --text-code: #d4d4d4;
      --border: #ced4da;
      --border-subtle: #e9ecef;
      --text-main: #212529;
      --text-muted: #6c757d;
      --primary: #0d6efd;
      --primary-hover: #0b5ed7;
      --primary-focus: rgba(13, 110, 253, 0.25);
      --card-focus: #0d6efd;
      --badge-bg: #e7f1ff;
      --badge-text: #0d6efd;
      --btn-yes-bg: #d1e7dd;
      --btn-yes-text: #0f5132;
      --btn-no-bg: #f8d7da;
      --btn-no-text: #842029;
      --btn-unsure-bg: #fff3cd;
      --btn-unsure-text: #664d03;
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        --bg-body: #121212;
        --bg-card: #1e1e1e;
        --bg-panel: #252525;
        --bg-code: #0d0d0d;
        --text-code: #c9d1d9;
        --border: #333333;
        --border-subtle: #2a2a2a;
        --text-main: #e0e0e0;
        --text-muted: #888888;
        --primary: #3b82f6;
        --primary-hover: #2563eb;
        --primary-focus: rgba(59, 130, 246, 0.35);
        --card-focus: #3b82f6;
        --badge-bg: #1e3a5f;
        --badge-text: #60a5fa;
        --btn-yes-bg: #133926;
        --btn-yes-text: #75b798;
        --btn-no-bg: #44171a;
        --btn-no-text: #ea868f;
        --btn-unsure-bg: #3f3108;
        --btn-unsure-text: #ffda6a;
      }}
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg-body);
      color: var(--text-main);
      height: 100vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }}
    header {{
      background: var(--bg-card);
      border-bottom: 1px solid var(--border);
      padding: 10px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-shrink: 0;
      gap: 12px;
    }}
    .header-left {{
      display: flex;
      align-items: center;
      gap: 14px;
    }}
    .header-title {{
      font-size: 16px;
      font-weight: 700;
    }}
    .progress-pill {{
      background: var(--badge-bg);
      color: var(--badge-text);
      padding: 4px 12px;
      border-radius: 999px;
      font-size: 13px;
      font-weight: 600;
    }}
    .header-right {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .btn {{
      padding: 6px 14px;
      border-radius: 6px;
      border: 1px solid var(--border);
      background: var(--bg-panel);
      color: var(--text-main);
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}
    .btn:hover {{
      background: var(--border-subtle);
    }}
    .btn-primary {{
      background: var(--primary);
      color: #ffffff;
      border-color: var(--primary);
    }}
    .btn-primary:hover {{
      background: var(--primary-hover);
    }}
    .shortcut-banner {{
      background: var(--bg-panel);
      border-bottom: 1px solid var(--border);
      padding: 6px 20px;
      font-size: 12px;
      color: var(--text-muted);
      display: flex;
      gap: 16px;
      flex-wrap: wrap;
      align-items: center;
    }}
    .kbd {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 1px 6px;
      font-family: monospace;
      font-size: 11px;
      color: var(--text-main);
      box-shadow: 0 1px 1px rgba(0,0,0,0.1);
    }}
    .main-container {{
      flex: 1;
      display: flex;
      overflow: hidden;
    }}
    .trace-pane {{
      flex: 3;
      border-right: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      background: var(--bg-card);
    }}
    .pane-header {{
      padding: 10px 16px;
      border-bottom: 1px solid var(--border-subtle);
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--bg-card);
    }}
    .trace-meta {{
      font-size: 13px;
      display: flex;
      gap: 16px;
      color: var(--text-muted);
    }}
    .trace-meta strong {{
      color: var(--text-main);
    }}
    .trace-scroll {{
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      background: var(--bg-code);
      color: var(--text-code);
    }}
    .trace-pre {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
      font-size: 12.5px;
      line-height: 1.5;
      white-space: pre-wrap;
      word-break: break-word;
    }}
    .eval-pane {{
      flex: 2;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 16px;
      background: var(--bg-body);
    }}
    .type-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      transition: border-color 0.15s, box-shadow 0.15s;
    }}
    .type-card.focused {{
      border-color: var(--card-focus);
      box-shadow: 0 0 0 3px var(--primary-focus);
    }}
    .card-title-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .card-title {{
      font-size: 14px;
      font-weight: 700;
    }}
    .focused-badge {{
      font-size: 11px;
      font-weight: 600;
      color: var(--primary);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .card-def {{
      font-size: 12px;
      color: var(--text-muted);
      line-height: 1.45;
    }}
    .card-def code {{
      background: var(--bg-panel);
      padding: 1px 4px;
      border-radius: 3px;
      font-family: monospace;
    }}
    .radio-group {{
      display: flex;
      gap: 8px;
    }}
    .choice-btn {{
      flex: 1;
      padding: 8px 4px;
      border-radius: 6px;
      border: 1px solid var(--border);
      background: var(--bg-panel);
      color: var(--text-main);
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      text-align: center;
      transition: all 0.15s;
    }}
    .choice-btn:hover {{
      border-color: var(--text-muted);
    }}
    .choice-btn.selected-yes {{
      background: var(--btn-yes-bg);
      color: var(--btn-yes-text);
      border-color: var(--btn-yes-text);
    }}
    .choice-btn.selected-no {{
      background: var(--btn-no-bg);
      color: var(--btn-no-text);
      border-color: var(--btn-no-text);
    }}
    .choice-btn.selected-unsure {{
      background: var(--btn-unsure-bg);
      color: var(--btn-unsure-text);
      border-color: var(--btn-unsure-text);
    }}
    .notes-box {{
      width: 100%;
      height: 80px;
      border-radius: 6px;
      border: 1px solid var(--border);
      background: var(--bg-card);
      color: var(--text-main);
      padding: 10px;
      font-size: 13px;
      font-family: inherit;
      resize: vertical;
    }}
    .notes-box:focus {{
      outline: none;
      border-color: var(--primary);
      box-shadow: 0 0 0 2px var(--primary-focus);
    }}
    .nav-buttons {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      margin-top: 4px;
    }}
    .nav-btn {{
      flex: 1;
      padding: 10px;
      font-size: 14px;
    }}
    .file-input-hidden {{
      display: none;
    }}
  </style>
</head>
<body>
  <header>
    <div class="header-left">
      <div class="header-title">P18 Trace Triage — CEO Blind Audit</div>
      <div class="progress-pill" id="progress-indicator">0 of {len(runs)} fully answered</div>
    </div>
    <div class="header-right">
      <button class="btn" id="export-btn" title="Download audit_labels.json">Export Labels</button>
      <button class="btn" id="import-btn" title="Restore from audit_labels.json">Import Labels</button>
      <input type="file" id="import-file-input" class="file-input-hidden" accept=".json">
    </div>
  </header>

  <div class="shortcut-banner">
    <span><strong>Shortcuts:</strong></span>
    <span><span class="kbd">j</span> Next trace</span>
    <span><span class="kbd">k</span> Prev trace</span>
    <span><span class="kbd">t</span> Cycle type focus (T1-T4)</span>
    <span><span class="kbd">1</span> Yes</span>
    <span><span class="kbd">2</span> No</span>
    <span><span class="kbd">3</span> Can't tell</span>
    <span style="margin-left: auto;">(Shortcuts disabled while typing in notes)</span>
  </div>

  <div class="main-container">
    <div class="trace-pane">
      <div class="pane-header">
        <div class="trace-meta">
          <span>Position: <strong id="meta-pos">1 of {len(runs)}</strong></span>
          <span>Benchmark: <strong id="meta-bench">-</strong></span>
          <span>Session: <strong id="meta-sid">-</strong></span>
        </div>
      </div>
      <div class="trace-scroll">
        <pre class="trace-pre" id="trace-text-elem"></pre>
      </div>
    </div>

    <div class="eval-pane">
      <!-- T1 Card -->
      <div class="type-card" id="card-T1" data-type="T1">
        <div class="card-title-row">
          <div class="card-title">T1 UNRECOVERED_TOOL_ERROR</div>
          <div class="focused-badge" id="focus-badge-T1"></div>
        </div>
        <div class="card-def">{html.escape(T1_DEF)}</div>
        <div class="radio-group">
          <button type="button" class="choice-btn" data-type="T1" data-val="yes">1. Yes</button>
          <button type="button" class="choice-btn" data-type="T1" data-val="no">2. No</button>
          <button type="button" class="choice-btn" data-type="T1" data-val="unsure">3. Can't tell</button>
        </div>
      </div>

      <!-- T2 Card -->
      <div class="type-card" id="card-T2" data-type="T2">
        <div class="card-title-row">
          <div class="card-title">T2 REPEATED_CALL_NO_PROGRESS</div>
          <div class="focused-badge" id="focus-badge-T2"></div>
        </div>
        <div class="card-def">{html.escape(T2_DEF)}</div>
        <div class="radio-group">
          <button type="button" class="choice-btn" data-type="T2" data-val="yes">1. Yes</button>
          <button type="button" class="choice-btn" data-type="T2" data-val="no">2. No</button>
          <button type="button" class="choice-btn" data-type="T2" data-val="unsure">3. Can't tell</button>
        </div>
      </div>

      <!-- T3 Card -->
      <div class="type-card" id="card-T3" data-type="T3">
        <div class="card-title-row">
          <div class="card-title">T3 LOOP_WITHOUT_PROGRESS</div>
          <div class="focused-badge" id="focus-badge-T3"></div>
        </div>
        <div class="card-def">{html.escape(T3_DEF)}</div>
        <div class="radio-group">
          <button type="button" class="choice-btn" data-type="T3" data-val="yes">1. Yes</button>
          <button type="button" class="choice-btn" data-type="T3" data-val="no">2. No</button>
          <button type="button" class="choice-btn" data-type="T3" data-val="unsure">3. Can't tell</button>
        </div>
      </div>

      <!-- T4 Card -->
      <div class="type-card" id="card-T4" data-type="T4">
        <div class="card-title-row">
          <div class="card-title">T4 MISREAD_TOOL_OUTPUT</div>
          <div class="focused-badge" id="focus-badge-T4"></div>
        </div>
        <div class="card-def">{html.escape(T4_DEF)}</div>
        <div class="radio-group">
          <button type="button" class="choice-btn" data-type="T4" data-val="yes">1. Yes</button>
          <button type="button" class="choice-btn" data-type="T4" data-val="no">2. No</button>
          <button type="button" class="choice-btn" data-type="T4" data-val="unsure">3. Can't tell</button>
        </div>
      </div>

      <!-- Free-text notes -->
      <div style="display: flex; flex-direction: column; gap: 6px;">
        <label for="trace-notes" style="font-size: 13px; font-weight: 600;">Run Notes:</label>
        <textarea id="trace-notes" class="notes-box" placeholder="Observations, ambiguous steps, or reasoning..."></textarea>
      </div>

      <!-- Navigation -->
      <div class="nav-buttons">
        <button class="btn nav-btn" id="prev-btn">Previous (k)</button>
        <button class="btn nav-btn btn-primary" id="next-btn">Next (j)</button>
      </div>
    </div>
  </div>

  <!-- Raw trace data embedded safely -->
  <script type="application/json" id="audit-manifest-data">
{safe_json}
  </script>

  <script>
    (function() {{
      const STORAGE_KEY = "p18_audit_labels";
      const INDEX_KEY = "p18_audit_current_index";
      const TYPES = ["T1", "T2", "T3", "T4"];

      let auditData = [];
      try {{
        auditData = JSON.parse(document.getElementById("audit-manifest-data").textContent);
      }} catch (e) {{
        console.error("Failed to load audit data:", e);
      }}

      let currentIndex = 0;
      let focusedTypeIndex = 0; // 0=T1, 1=T2, 2=T3, 3=T4

      // State: session_id -> {{ T1, T2, T3, T4, notes, answered_at }}
      let answers = {{}};
      try {{
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {{
          answers = JSON.parse(stored);
        }}
      }} catch (e) {{
        console.warn("Storage access failed, using in-memory state:", e);
      }}

      try {{
        const storedIdx = localStorage.getItem(INDEX_KEY);
        if (storedIdx !== null) {{
          const parsed = parseInt(storedIdx, 10);
          if (parsed >= 0 && parsed < auditData.length) {{
            currentIndex = parsed;
          }}
        }}
      }} catch (e) {{}}

      function saveState() {{
        try {{
          localStorage.setItem(STORAGE_KEY, JSON.stringify(answers));
          localStorage.setItem(INDEX_KEY, currentIndex.toString());
        }} catch (e) {{}}
        updateProgress();
      }}

      function updateProgress() {{
        let fullyAnswered = 0;
        for (let i = 0; i < auditData.length; i++) {{
          const sid = auditData[i].session_id;
          const a = answers[sid];
          if (a && a.T1 && a.T2 && a.T3 && a.T4) {{
            fullyAnswered++;
          }}
        }}
        document.getElementById("progress-indicator").textContent =
          fullyAnswered + " of " + auditData.length + " fully answered";
      }}

      function renderCurrentRun() {{
        if (!auditData.length) return;
        const run = auditData[currentIndex];

        document.getElementById("meta-pos").textContent = run.position + " of " + run.total;
        document.getElementById("meta-bench").textContent = run.benchmark;
        document.getElementById("meta-sid").textContent = run.session_id;

        // Render trace strictly via textContent (never innerHTML)
        document.getElementById("trace-text-elem").textContent = run.trace_text;

        const curAns = answers[run.session_id] || {{}};

        TYPES.forEach(t => {{
          const val = curAns[t] || null;
          const card = document.getElementById("card-" + t);
          const btns = card.querySelectorAll(".choice-btn");
          btns.forEach(btn => {{
            const bVal = btn.getAttribute("data-val");
            btn.className = "choice-btn";
            if (val === bVal) {{
              btn.classList.add("selected-" + val);
            }}
          }});
        }});

        document.getElementById("trace-notes").value = curAns.notes || "";
        updateFocusHighlight();
        updateProgress();
      }}

      function updateFocusHighlight() {{
        TYPES.forEach((t, i) => {{
          const card = document.getElementById("card-" + t);
          const badge = document.getElementById("focus-badge-" + t);
          if (i === focusedTypeIndex) {{
            card.classList.add("focused");
            badge.textContent = "Focused (1/2/3)";
          }} else {{
            card.classList.remove("focused");
            badge.textContent = "";
          }}
        }});
      }}

      function setChoice(type, val) {{
        const run = auditData[currentIndex];
        if (!run) return;
        if (!answers[run.session_id]) {{
          answers[run.session_id] = {{}};
        }}
        answers[run.session_id][type] = val;
        answers[run.session_id].answered_at = new Date().toISOString();
        saveState();
        renderCurrentRun();
      }}

      // Button listeners
      document.querySelectorAll(".choice-btn").forEach(btn => {{
        btn.addEventListener("click", function() {{
          const t = this.getAttribute("data-type");
          const val = this.getAttribute("data-val");
          focusedTypeIndex = TYPES.indexOf(t);
          setChoice(t, val);
        }});
      }});

      // Card focus on click
      TYPES.forEach((t, i) => {{
        const card = document.getElementById("card-" + t);
        card.addEventListener("click", function(e) {{
          if (e.target.tagName !== "BUTTON") {{
            focusedTypeIndex = i;
            updateFocusHighlight();
          }}
        }});
      }});

      // Notes change
      document.getElementById("trace-notes").addEventListener("input", function() {{
        const run = auditData[currentIndex];
        if (!run) return;
        if (!answers[run.session_id]) {{
          answers[run.session_id] = {{}};
        }}
        answers[run.session_id].notes = this.value;
        answers[run.session_id].answered_at = new Date().toISOString();
        saveState();
      }});

      // Prev / Next
      function goPrev() {{
        if (currentIndex > 0) {{
          currentIndex--;
          saveState();
          renderCurrentRun();
        }}
      }}
      function goNext() {{
        if (currentIndex < auditData.length - 1) {{
          currentIndex++;
          saveState();
          renderCurrentRun();
        }}
      }}

      document.getElementById("prev-btn").addEventListener("click", goPrev);
      document.getElementById("next-btn").addEventListener("click", goNext);

      // Keyboard shortcuts
      window.addEventListener("keydown", function(e) {{
        // Disable shortcuts if typing in notes or input
        const activeTag = document.activeElement ? document.activeElement.tagName.toLowerCase() : "";
        if (activeTag === "textarea" || activeTag === "input") {{
          return;
        }}

        if (e.key === "j" || e.key === "J") {{
          e.preventDefault();
          goNext();
        }} else if (e.key === "k" || e.key === "K") {{
          e.preventDefault();
          goPrev();
        }} else if (e.key === "t" || e.key === "T") {{
          e.preventDefault();
          focusedTypeIndex = (focusedTypeIndex + 1) % TYPES.length;
          updateFocusHighlight();
        }} else if (e.key === "1") {{
          e.preventDefault();
          setChoice(TYPES[focusedTypeIndex], "yes");
        }} else if (e.key === "2") {{
          e.preventDefault();
          setChoice(TYPES[focusedTypeIndex], "no");
        }} else if (e.key === "3") {{
          e.preventDefault();
          setChoice(TYPES[focusedTypeIndex], "unsure");
        }}
      }});

      // Export labels
      document.getElementById("export-btn").addEventListener("click", function() {{
        const blob = new Blob([JSON.stringify(answers, null, 2)], {{ type: "application/json" }});
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "audit_labels.json";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }});

      // Import labels
      const importInput = document.getElementById("import-file-input");
      document.getElementById("import-btn").addEventListener("click", function() {{
        importInput.value = "";
        importInput.click();
      }});

      importInput.addEventListener("change", function(e) {{
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = function(evt) {{
          try {{
            const loaded = JSON.parse(evt.target.result);
            if (typeof loaded === "object" && loaded !== null) {{
              answers = loaded;
              saveState();
              renderCurrentRun();
              alert("Successfully imported " + Object.keys(loaded).length + " audit records.");
            }}
          }} catch (err) {{
            alert("Error parsing JSON: " + err.message);
          }}
        }};
        reader.readAsText(file);
      }});

      // Initialize
      renderCurrentRun();
    }})();
  </script>
</body>
</html>
"""
    return html_template


def main():
    parser = argparse.ArgumentParser(description="Build P18 CEO Audit Page")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("projects/p18_trace_triage/audit_manifest.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
    )
    args = parser.parse_args()

    with open(args.manifest, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    html_content = generate_audit_html_content(manifest)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html_content)

    size_kb = args.output.stat().st_size / 1024
    print(f"Generated {args.output} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
