#!/usr/bin/env python3
"""Produce 10 hand-checkable oracle cases and print a verdict table.

Each row states: the crafted response, what a human expects the oracle to say,
and what the oracle actually said. The script FAILS (exit 1) if any oracle
verdict disagrees with the human-obvious expectation -- so "hand-check" is both
readable by a person and enforced by the process.

Usage:
    python scripts/handcheck.py           # human-readable table
    python scripts/handcheck.py --json    # machine-readable, for evidence/
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from faultline import build_env, oracle_check  # noqa: E402

SEED = 7


def build_cases():
    env = build_env(SEED)
    q = env["questions"]
    q0, q1, q2 = q[0], q[1], q[2]
    right_ans0 = q0["answer"]
    right_src0 = q0["required_source"]
    # a real distractor doc id (never the required source of an entity question)
    distractor = env["documents"][-1]["id"]

    # (name, question, response, human_expected_pass, rationale)
    cases = [
        ("exact answer + right source", q0,
         {"answer": right_ans0, "cited_sources": [right_src0]}, True,
         "correct token, cited the doc that holds it"),
        ("answer in a sentence + right source", q0,
         {"answer": f"It is {right_ans0}.", "cited_sources": [right_src0]}, True,
         "token contained in a natural sentence"),
        ("right answer, NO citation", q0,
         {"answer": right_ans0, "cited_sources": []}, False,
         "correct but ungrounded -> oracle refuses"),
        ("right answer, cited a distractor", q0,
         {"answer": right_ans0, "cited_sources": [distractor]}, False,
         "correct token but did not retrieve the real source"),
        ("right answer, cited another entity's doc", q0,
         {"answer": right_ans0, "cited_sources": [q1["required_source"]
          if q1["required_source"] != right_src0 else distractor]}, False,
         "wrong source -> not grounded"),
        ("wrong answer, right source", q0,
         {"answer": q2["answer"], "cited_sources": [right_src0]}, False,
         "grounded but the token is wrong"),
        ("empty answer, right source", q0,
         {"answer": "", "cited_sources": [right_src0]}, False,
         "no answer cannot be correct"),
        ("case/space-insensitive match", q0,
         {"answer": f"  {right_ans0.upper()}  ", "cited_sources": [right_src0]}, True,
         "normalization handles case and whitespace"),
        ("right source among several citations", q0,
         {"answer": right_ans0,
          "cited_sources": [distractor, right_src0]}, True,
         "extra citations are fine as long as the required one is present"),
        ("second question, exact + right source", q1,
         {"answer": q1["answer"], "cited_sources": [q1["required_source"]]}, True,
         "independent question, same rules"),
    ]
    return cases


def run():
    rows = []
    ok = True
    for name, q, resp, expected, why in build_cases():
        verdict = oracle_check(q, resp)
        agree = verdict["passed"] == expected
        ok = ok and agree
        rows.append({
            "case": name,
            "question_id": q["id"],
            "response": resp,
            "human_expected_pass": expected,
            "oracle_passed": verdict["passed"],
            "oracle_correct": verdict["correct"],
            "oracle_cited_required": verdict["cited_required"],
            "agree": agree,
            "rationale": why,
        })
    return rows, ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows, ok = run()
    if args.json:
        print(json.dumps({"seed": SEED, "all_agree": ok, "cases": rows}, indent=2))
    else:
        print(f"Hand-check of oracle on seed {SEED}\n")
        for i, r in enumerate(rows, 1):
            mark = "OK " if r["agree"] else "XX "
            print(f"{mark}{i:2}. {r['case']}")
            print(f"      expected pass={r['human_expected_pass']}  "
                  f"oracle pass={r['oracle_passed']}  "
                  f"(correct={r['oracle_correct']}, "
                  f"cited_required={r['oracle_cited_required']})")
            print(f"      why: {r['rationale']}")
        print(f"\nall_agree = {ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
