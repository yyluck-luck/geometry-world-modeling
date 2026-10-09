# R116 command-wording closure audit

Date: 2026-09-24 (Asia/Shanghai)  
Scope: read-only wording consistency audit. No implementation, fixture
execution, GPU/Slurm job, protected C8/evaluation read, receipt update, or
flag change.

## Verdict: REVISE once

R115 contains the required wording, but it has not yet been applied to the
owner checklist or the reopening plan. R114 still says “source-pinned CPU-only
runner, supported command” and “provide the supported CPU command for review”
without the explicit review-only prohibition
(`work/agents/CODEX_R114_OWNER_ACTION_CHECKLIST_20260924.md:39-46,70-79`).
R106 likewise lists a “supported command” as packet evidence without stating
that only command text/discovery evidence may be supplied
(`work/agents/CODEX_R106_ENDLINE_REOPEN_CRITERIA_20260924.md:44-55`). R115's
proposed correction itself is precise, but remains only in the audit memo
(`work/agents/CODEX_R115_AUTHORIZATION_BOUNDARY_AUDIT_20260924.md:20-37`).

## One canonical sentence to apply everywhere

Replace each owner-facing unqualified “supported command” requirement with:

> Provide the supported CPU command **text and discovery evidence for review
> only**. Until the complete packet and every gate are independently accepted,
> do not execute, dispatch, schedule, or expose the command as runnable.

Apply this sentence to R114 item 7 and its owner-decision paragraph, and to the
R106 packet item. Future handoff or plan text should use the same sentence
verbatim. This is a wording correction only: it adds no schema field, gate,
runner, or authorization.

## Boundary after correction

The source and handoff must continue to state `NO_COMMAND_AVAILABLE`,
`NO_REOPEN`, END-LINE, `new_method_validated=false`, and
`novelty_authorization=NONE` until the complete packet is present and all gates
pass. R112 already states that artifact supply and review do not authorize
execution (`work/agents/CODEX_R112_CANONICAL_OWNER_HASH_CLOSURE_20260924.md:45-65`).
The correction extends that same boundary to CPU command discovery and removes
the only remaining wording that could be read as executable authorization.

**R116 status: REVISE ONCE / apply the canonical review-only command sentence to
R114 and R106 / NO EXECUTION.**
