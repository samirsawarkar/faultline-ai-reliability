# Day 27 friction log

Every reader question or unrecorded choice is treated as a documentation defect,
not as a reader failure.

| defect | ambiguity found | documentation repair | final verification |
|---|---|---|---|
| F27-001 | revision unspecified | pin `v0.27.0-rc1`; forbid falling forward to `main` | exact branch audited and cloned |
| F27-002 | host Python varied | make Docker the sole cold path | executable block has no Python bootstrap |
| F27-003 | Docker client mistaken for daemon | add `docker version` and inner daemon preflight | transcript records preflight pass |
| F27-004 | “green” output hid the numbers | print and match all six headline strings | six expected lines observed |
| F27-005 | resource and platform envelope absent | state CPU, memory, disk, network, OS and architecture boundaries | requirement-token audit passes |
| F27-006 | mirrors required secret URL edits | document `FAULTLINE_REPOSITORY_URL` with a public default | local transport uses the same block |
| F27-007 | partial checkout repair was subjective | require a fresh empty directory for every attempt | harness confirms a new clone |
| F27-008 | troubleshooting encouraged dependency substitution | give stop/retry actions and prohibit changing pins/evidence | failure-action audit passes |
| F27-009 | volatile Git advice and image layer IDs obscured results | suppress success-path builder detail and detached-HEAD advice | final transcript contains stable checkpoints only |
| F27-010 | an outer snapshot test assumed Git existed inside the image | keep clone integration outside; unit-test its parsing boundary inside | clean image needs no hidden Git install |
| F27-011 | generator Make targets expected a host `.venv` inside the image | bind internal targets to the pinned image interpreter | all five generator families run from the copied command |
| F27-012 | shallow cloning an annotated tag emitted a misleading tag-object warning | use a direct commit tag for the reproduction identity | exact-tag clone is warning-free |

Final reader questions: **0**.

Final operator improvisations: **0**.
