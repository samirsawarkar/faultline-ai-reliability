"""Run the agent on a batch of tasks over a seed and emit structured outcomes.

Produces evidence/sample_run_seed7.json: a full, JSON-serialized AgentOutcome
(including the reason->tool->observe trace) for a solvable task, proving the
outcome is structured end to end.
"""
import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401
from _bootstrap import entity_names

from faultline_agent import Agent, ArchiveSumTask, load_env, verdict

EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "evidence"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--k", type=int, default=3, help="entities in the sample task")
    ap.add_argument("--step-cap", type=int, default=12)
    args = ap.parse_args()

    env = load_env(args.seed)
    names = entity_names(env)
    task_in = {"task_id": f"sample-seed{args.seed}-k{args.k}", "entities": names[: args.k]}
    task = ArchiveSumTask.model_validate(task_in)
    out = Agent(env, step_cap=args.step_cap).run(task_in)
    v = verdict(env, task, out)

    payload = {"task": task.model_dump(), "outcome": out.model_dump(mode="json"),
               "verdict": v}
    path = EVIDENCE_DIR / f"sample_run_seed{args.seed}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    print(f"seed={args.seed}  status={out.status.value}  answer={out.answer}  "
          f"steps={out.steps_used}/{out.step_cap}  passed={v['passed']}")
    print("trace:")
    for s in out.trace:
        obs = s.observation
        summary = getattr(obs, "value", None)
        if summary is None and getattr(obs, "candidates", None):
            summary = obs.candidates[0].doc_id
        if summary is None:
            summary = obs.doc_id
        print(f"  {s.index:>2}. {s.tool_call.tool:<7} -> {summary}   ({s.thought})")
    print(f"\nwrote {path.relative_to(path.parents[2])}")


if __name__ == "__main__":
    main()
