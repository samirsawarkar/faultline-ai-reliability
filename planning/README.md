# FAULTLINE Phase 2 — planning

Every planning document lives here. Nothing in this folder is code, and nothing
here is generated. `day01/` … `day30/` are frozen and are never touched by any
work described in this folder.

```
planning/
  cto/                 written by the owner — decisions, contracts, why
    PHASE2-PLAN.md     the research contract: what is measured and why
    PHASE2-BUILD.md    the build order, build decisions D1-D6, project briefs
  agent/               written for the implementing agent — what to do, exactly
    AGENT-RULES.md     standing rules · read at the start of EVERY session
    WEEK0.md           the Week 0 work order · the first thing that gets built
    WEEK0-FIX.md       corrective order after the Week 0 review
```

## Which file, when

| You are about to… | Read |
|---|---|
| Start any session, no exceptions | `agent/AGENT-RULES.md` |
| Build the foundation (first work of Phase 2) | `agent/WEEK0.md` |
| Fix what the Week 0 review rejected | `agent/WEEK0-FIX.md` |
| Ask "what is this project for, what is its gate" | `cto/PHASE2-BUILD.md` §4 |
| Ask "why is it built this way" | `cto/PHASE2-BUILD.md` §1 (D1-D6) |
| Ask "why measure this at all", or touch statistics | `cto/PHASE2-PLAN.md` §2, §3, §5 |
| Ask "can I spend money on this" | `cto/PHASE2-PLAN.md` §4 + `MEC.md` caps |

## Reading order, first time

1. `agent/AGENT-RULES.md` — short, and it is binding
2. `cto/PHASE2-BUILD.md` §0 (scope boundary) and §1 (decisions)
3. `agent/WEEK0.md` — the work order
4. `cto/PHASE2-PLAN.md` — read once, end to end, before writing anything that
   produces a number

## Authority

`cto/` outranks `agent/`. If a work order tells you to do something the build
plan forbids, the build plan wins — stop and say so.

`MEC.md` and `HYPOTHESES.md` (repo root, created at the end of Week 0) outrank
everything in this folder. They are contracts. Once committed they change only
through `AMENDMENTS.md`, and only by the owner.
