# R117 command-wording consistency audit

Date: 2026-09-24 (Asia/Shanghai)  
Scope: read-only audit of owner-facing plan and handoff language. No
implementation, fixture execution, GPU/Slurm job, protected C8/evaluation
read, receipt update, or flag change.

## Verdict: REVISE once

The canonical review-only sentence now appears in the current reopening plan
(R106 line 79), owner checklist (R114 line 86), handoff correction (R115 lines
24–27), and closure memo (R116 lines 23–27). However, the earlier unqualified
phrases remain in the same owner-facing documents:

* R106 still lists “supported command” as a packet item at lines 49–52.
* R114 still says “source-pinned CPU-only runner, supported command” at lines
  43–46 and “provide the supported CPU command for review” at lines 72–74.
* The prior acceptance checklist says “Expose the supported command only after
  all gates pass” and that completing the checklist “would authorize only a
  later synthetic CPU contract conformance attempt”
  (`work/agents/CODEX_R92_OWNER_H2_ACCEPTANCE_CHECKLIST_20260924.md:114-133`).

The addenda make the intended boundary clear, but append-only wording leaves a
reader able to treat one of these older phrases as execution authorization.

## One required consistency edit

Replace every owner-facing occurrence above with this exact sentence:

> Provide the supported CPU command **text and discovery evidence for review
> only**. Until the complete packet and every gate are independently accepted,
> do not execute, dispatch, schedule, or expose the command as runnable.

In R92, also replace “would authorize only a later synthetic CPU contract
conformance attempt” with “would support a later owner decision; it does not
authorize execution.” This is a wording replacement only; it adds no schema,
gate, runner, or permission.

## What is already consistent

R74 labels its conditional command shape intentionally non-runnable and says
`NO_COMMAND_AVAILABLE`; R75/R77 require independent owner/H2 acceptance before
any separate CPU conformance run and prohibit real C8, GPU/Slurm, replay, and
flag changes. Those plans do not create a new authorization path. After the
replacement above, the plan and handoff will have one unambiguous command
boundary.

Keep `NO_COMMAND_AVAILABLE`, `NO_REOPEN`, END-LINE,
`new_method_validated=false`, and `novelty_authorization=NONE` until the full
packet and all gates are accepted. No command may be executed or scheduled by
this wording audit.

**R117 status: REVISE ONCE / replace residual unqualified command language /
NO EXECUTION.**
