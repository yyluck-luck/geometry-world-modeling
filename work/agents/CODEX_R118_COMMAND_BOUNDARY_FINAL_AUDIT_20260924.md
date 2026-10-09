# R118 command-boundary final audit

Date: 2026-09-24 (Asia/Shanghai)  
Scope: read-only final wording audit. No implementation, fixture execution,
GPU/Slurm job, protected C8/evaluation read, receipt update, or flag change.

## Verdict: REVISE once

R106, R92, R115, and R116 now carry the canonical review-only boundary. R106's
packet item says to provide command text and discovery evidence only and forbids
execution, dispatch, scheduling, or runnable exposure
(`work/agents/CODEX_R106_ENDLINE_REOPEN_CRITERIA_20260924.md:49-51`). R92's
command section is explicitly review-only and its non-authorization paragraph
now says a later owner decision is not execution authorization
(`work/agents/CODEX_R92_OWNER_H2_ACCEPTANCE_CHECKLIST_20260924.md:114-132`).
The R115 handoff sentence is also exact.

One residual owner-facing phrase remains in R114 lines 71–74:

> provide the supported CPU command for review. It is not permission to run GPU
> work ...

That wording forbids GPU work but does not forbid CPU execution, dispatch,
scheduling, or exposing a runnable command. R114's later addendum is correct,
but appending it leaves the older sentence available for misreading
(`work/agents/CODEX_R114_OWNER_ACTION_CHECKLIST_20260924.md:69-85`).

## Required final edit

Replace R114 lines 71–74 with the canonical sentence already used in R106,
R115, and R116:

> The owner action is to assemble and independently review the packet, then
> provide the supported CPU command **text and discovery evidence for review
> only**. Until the complete packet and every gate are independently accepted,
> do not execute, dispatch, schedule, or expose the command as runnable. This
> action is not permission to run CPU, GPU, Slurm, C8, or evaluation work.

Keep R114's following `NO_REOPEN`, `NO_COMMAND_AVAILABLE`, END-LINE, and flag
sentence unchanged. Remove the redundant addendum after replacing the source
paragraph, or retain it only as a cross-reference; do not leave two conflicting
owner-action sentences.

## Final boundary

The current plans (R75/R77) already require owner/H2 acceptance before any
separate CPU conformance run and block real C8, replay, GPU/Slurm, receipt, and
flag changes. After the R114 replacement, every current plan and handoff will
have one command boundary: text/discovery evidence for review only, with
`NO_COMMAND_AVAILABLE` and `NO_REOPEN` until all gates are accepted.

**R118 status: REVISE ONCE / replace residual R114 sentence / NO EXECUTION.**
