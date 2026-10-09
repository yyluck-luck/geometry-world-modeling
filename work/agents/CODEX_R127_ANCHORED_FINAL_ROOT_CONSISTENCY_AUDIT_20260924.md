# R127 anchored-final-root consistency audit

**Date:** 2026-09-24 (Asia/Shanghai)  
**Scope:** read-only consistency audit of the R126 anchored-final-root correction across the current plan, handoff, memory, method-direction record, and R126 memo. No command discovery or execution, protected-data access, runner/fixture work, GPU/Slurm work, receipt mutation, or validation-flag change occurred.

## Verdict: REVISE ONCE (documentation-only)

The correction is stated explicitly and consistently in the current plan, handoff,
and Chinese memory. The method-direction record names the correction and preserves
all state/authorization invariants, but its R127 paragraph does not spell out the
four required acceptance details. Add those details (or an exact reference to the
R126 condition) to the method-direction top section, then rerun this consistency
check. This is a wording repair only; it cannot reopen the method line or authorize
execution.

## Required anchored-final-root details

The R126 correction must retain all of these details together:

1. The exact owner review artifact bytes are members of the fixed manifest.
2. Every post-check readiness read uses a retained file descriptor anchored to
   the verified final-root device/inode and parent entry, with `O_NOFOLLOW` plus
   an equivalent beneath/no-reparse constraint (or an explicitly proven atomic
   equivalent).
3. No pathname lookup by the cached root name occurs after the last full digest
   pass.
4. Root, parent-entry, owner bytes/hash, or role-file changes fail closed as
   `STALE`/`REMOTE_PROVENANCE_UNVERIFIED` and require a new nonce; inability to
   prove descriptor anchoring also fails closed.

## Evidence by record

- **R126 source memo — complete.**
  `work/agents/CODEX_R126_INVARIANT_REDTEAM_20260924.md:80-93` states all four
  details, including the fixed-manifest owner bytes, retained descriptor,
  no-pathname rule, fail-closed statuses, and the atomic-equivalent fallback.
  Lines `95-107` state that this is provenance hygiene only, leaves
  `NO_COMMAND_AVAILABLE`/`NO_REOPEN`/END-LINE and both validation flags unchanged,
  and forbids command, protected-data, GPU/Slurm, smoke rerun, receipt, and flag
  changes.

- **Current English plan — complete.**
  `docs/RESEARCH_PLANS_EN.md:9-17` explicitly repeats all four conditions and
  the no-readiness rule. Lines `19-28` preserve `NO_COMMAND_AVAILABLE`,
  `NO_REOPEN`, END-LINE, `new_method_validated=false`,
  `novelty_authorization=NONE`, the valid historical VMem/smoke state, and the
  no-execution/no-GPU/no-C8/evaluation/no-receipt/no-flag restrictions.

- **Current handoff — complete.**
  `docs/RESEARCH_HANDOFF_CURRENT.md:3-8` explicitly repeats fixed-manifest owner
  bytes, retained-FD anchoring, no pathname lookup after digest, and fail-closed
  statuses/new nonce. Lines `10-18` classify it as a documentation-level
  provenance correction, preserve stale/unverified remote semantics and all
  unchanged gates/flags, and prohibit execution and protected/GPU/evaluation work.

- **Current Chinese memory — complete.**
  `RESEARCH_MEMORY.md:1-5` states the owner bytes in the fixed manifest, retained
  FD anchored to device/inode/parent with `O_NOFOLLOW`/beneath-no-reparse,
  no cached-root pathname lookup after digest, fail-closed statuses/new nonce,
  and explicitly says this is not method authorization while preserving all flags
  and the no-rerun rule.

- **Current method direction — incomplete detail.**
  `docs/METHOD_DIRECTION_CURRENT.md:3-7` says only that R126 found a provenance
  TOCTOU gap and that the owner-packet contract is sharpened with an
  “anchored-final-root condition”; it records stale/unverified remote state and
  unchanged `new_method_validated=false`/`novelty_authorization=NONE`, but does
  not state the four concrete conditions above. A reader relying only on this
  record cannot verify the fixed-manifest membership, retained-FD/no-pathname
  rule, or fail-closed status requirement.

## Required bounded correction

Update only the R127 top paragraph of `docs/METHOD_DIRECTION_CURRENT.md` to
include the four concrete anchored-final-root conditions (or cite the exact R126
memo section containing them), while preserving the existing statements that this
is provenance documentation, not a method result or authorization. Do not alter
Gate 0, END-LINE/NO_REOPEN, VMem/smoke status, remote stale/unverified status, or
validation flags. After that wording-only edit, rerun the same five-record check;
expected verdict is PASS if all four details and the unchanged authorization
boundary are visible in each current top record.

## State and stop rule

Current state remains `NO_COMMAND_AVAILABLE`, `NO_REOPEN`, END-LINE,
`new_method_validated=false`, and `novelty_authorization=NONE`. VMem is
`COMPLETE_SHA_VERIFIED`; the historical no-data smoke remains valid and must not
be rerun. The owner/H2/fixture/runner packet is absent; post-R111 remote sync is
stale/unverified because SSH closes before verification. Do not expose, execute,
dispatch, schedule, or make runnable any command; do not read protected C8/evaluation
data, submit GPU/Slurm jobs, run S103/S132/GRC, mutate receipts, or change flags.

**R127 status: REVISE ONCE / method-direction detail omission / NO EXECUTION.**
