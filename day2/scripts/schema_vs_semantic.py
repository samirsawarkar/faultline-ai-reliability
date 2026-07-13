"""Demonstrate, as a durable artifact, that schema validity != correctness.

Constructs three AgentOutcomes that ALL pass Pydantic validation (they are
well-formed), then shows the verdict separating the one that is actually correct
from the two that merely look correct. Writes evidence/schema_vs_semantic.json.
"""
import json
from pathlib import Path

import _bootstrap  # noqa: F401
from _bootstrap import entity_names

from faultline_agent import Agent, ArchiveSumTask, ground_truth, load_env, verdict
from faultline_agent.contracts import AgentOutcome, OutcomeStatus

SEED = 7
EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "schema_vs_semantic.json"


def main() -> None:
    env = load_env(SEED)
    names = entity_names(env)[:3]
    task = ArchiveSumTask.model_validate({"task_id": "svc", "entities": names})
    truth, required = ground_truth(env, task)

    # The agent's real answer (correct + grounded).
    real = Agent(env).run(task.model_dump())

    # Two hand-built outcomes that are schema-valid but semantically wrong.
    wrong_number = AgentOutcome(
        task_id="svc", status=OutcomeStatus.SOLVED, answer=str(truth + 1),
        cited_sources=sorted(required), steps_used=0, step_cap=12,
    )
    ungrounded = AgentOutcome(
        task_id="svc", status=OutcomeStatus.SOLVED, answer=str(truth),
        cited_sources=[], steps_used=0, step_cap=12,
    )

    rows = []
    for label, out in [("agent_real", real),
                       ("wrong_number", wrong_number),
                       ("ungrounded", ungrounded)]:
        v = verdict(env, task, out)
        rows.append({
            "label": label,
            "schema_valid": True,  # each object exists => it validated
            "answer": out.answer,
            "correct": v["correct"],
            "grounded": v["grounded"],
            "semantically_passes": v["passed"],
        })

    report = {"seed": SEED, "expected_answer": str(truth),
              "required_sources": sorted(required), "outcomes": rows}
    EVIDENCE.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    print(f"expected answer = {truth}   required sources = {sorted(required)}\n")
    hdr = f"{'outcome':<14}{'schema':>8}{'correct':>9}{'grounded':>10}{'passes':>8}"
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        print(f"{r['label']:<14}{'valid':>8}{str(r['correct']):>9}"
              f"{str(r['grounded']):>10}{str(r['semantically_passes']):>8}")
    print(f"\nwrote {EVIDENCE.relative_to(EVIDENCE.parents[2])}")


if __name__ == "__main__":
    main()
