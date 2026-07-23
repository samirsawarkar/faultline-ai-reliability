"""Attack: force an over-budget task and prove clean, incomplete termination.

Runs the same agent on three tasks over seed 7 with step_cap=12:
  * under budget  (4 entities ->  9 steps)  -> SOLVED
  * at  boundary  (5 entities -> 11 steps)  -> SOLVED
  * over budget   (6 entities -> 13 steps)  -> INCOMPLETE (answer=None)

Writes evidence/budget_termination.json and prints a human-readable table.
The point: the over-budget task neither hangs nor raises nor fabricates an
answer — it stops exactly at the cap with an honest INCOMPLETE.
"""
import json
from pathlib import Path

import _bootstrap  # noqa: F401  (sets sys.path)
from _bootstrap import entity_names

from faultline_agent import Agent, ArchiveSumTask, load_env, verdict

SEED = 7
STEP_CAP = 12
EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "budget_termination.json"


def main() -> None:
    env = load_env(SEED)
    names = entity_names(env)
    cases = [
        ("under_budget", names[:4]),
        ("at_boundary", names[:5]),
        ("over_budget", names[:6]),
    ]

    records = []
    for label, ents in cases:
        task_in = {"task_id": f"{label}", "entities": ents}
        task = ArchiveSumTask.model_validate(task_in)
        out = Agent(env, step_cap=STEP_CAP).run(task_in)
        v = verdict(env, task, out)
        records.append({
            "label": label,
            "n_entities": len(ents),
            "steps_demanded": 2 * len(ents) + 1,
            "step_cap": STEP_CAP,
            "status": out.status.value,
            "steps_used": out.steps_used,
            "answer": out.answer,
            "reason": out.reason,
            "verdict_passed": v["passed"],
        })

    report = {"seed": SEED, "step_cap": STEP_CAP, "cases": records}
    EVIDENCE.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    print(f"seed={SEED}  step_cap={STEP_CAP}\n")
    hdr = f"{'case':<14}{'ents':>5}{'demand':>8}{'status':>12}{'steps':>7}{'answer':>9}"
    print(hdr)
    print("-" * len(hdr))
    for r in records:
        print(f"{r['label']:<14}{r['n_entities']:>5}{r['steps_demanded']:>8}"
              f"{r['status']:>12}{r['steps_used']:>7}{str(r['answer']):>9}")
    print(f"\nwrote {EVIDENCE.relative_to(EVIDENCE.parents[2])}")

    # Fail loudly if the invariant we advertise ever breaks.
    over = next(r for r in records if r["label"] == "over_budget")
    assert over["status"] == "incomplete", "over-budget task did not terminate incomplete"
    assert over["answer"] is None, "over-budget task fabricated an answer"
    assert over["steps_used"] == STEP_CAP, "over-budget task did not spend exactly the cap"


if __name__ == "__main__":
    main()
