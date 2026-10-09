# R129 final five-record consistency audit

**Date:** 2026-09-24 (Asia/Shanghai)  
**Scope:** read-only review of the current tops of the plan, handoff, Chinese memory, and method-direction records, together with the R126 canonical invariant and the R128 correction memo. No command discovery or execution, protected-data access, runner/fixture work, GPU/Slurm work, receipt or flag mutation, owner acceptance, or method reopening occurred.

## Verdict: REVISE ONCE (documentation-only)

All four anchored-final-root conditions are explicit and mutually consistent in the four current records and in the R126 canonical source memo. One current-top symmetry gap remains in `RESEARCH_MEMORY.md`: its R129 top states that the no-execution boundary is preserved, but it does not enumerate the full restriction set that is explicit in the English plan, handoff, method-direction record, and R126 stop rule. This is a documentation omission only. It does not authorize execution, reopen the method line, or change validation state.

## Anchored-final-root matrix

| Record | Fixed-manifest owner bytes | Retained descriptor anchored to verified root/device/inode/parent | No cached-root pathname after final digest | Fail closed stale/remote-unverified + new nonce | Result |
|---|---|---|---|---|---|
| `docs/RESEARCH_PLANS_EN.md` current R129 top | PASS, lines 3–6 | PASS, lines 5–6 | PASS, lines 6–7 | PASS, lines 7–10 | All four explicit. |
| `docs/RESEARCH_HANDOFF_CURRENT.md` current R129 top | PASS, lines 3–5 | PASS, lines 5–7 | PASS, lines 7–8 | PASS, lines 8–10 | All four explicit. |
| `RESEARCH_MEMORY.md` current R129 top | PASS, line 3 | PASS, line 3 | PASS, line 3 | PASS, line 3 | Chinese summary states all four together. |
| `docs/METHOD_DIRECTION_CURRENT.md` current R129 top | PASS, lines 3–6 | PASS, lines 5–7 | PASS, lines 7–8 | PASS, lines 8–10 | All four explicit. |
| R126 canonical acceptance condition | PASS, lines 80–82 | PASS, lines 82–85 | PASS, lines 85–86 | PASS, lines 86–93 | Canonical source is complete. |

The R126 source is the detailed contract: exact owner bytes are fixed-manifest members, all readiness reads use an anchored retained descriptor, cached-root pathname lookup is forbidden after the final digest, and any root/parent/owner/role change or unproved anchor fails closed with a new nonce (`work/agents/CODEX_R126_INVARIANT_REDTEAM_20260924.md:80-93`). R128 documented the prior top-level asymmetry and required the current-top correction (`work/agents/CODEX_R128_ANCHORED_ROOT_CONSISTENCY_RERUN_20260924.md:9-20,55-66`).

## Paused-state and no-execution matrix

- **Plan:** `docs/RESEARCH_PLANS_EN.md:12-18` explicitly preserves `NO_COMMAND_AVAILABLE`, `NO_REOPEN`, END-LINE, both validation flags, VMem SHA and no-data-smoke state, stale/unverified SSH state, and the complete no-exposure/no-execution/no-dispatch/no-scheduling/protected-data/GPU/Slurm/C8/evaluation/S103/S132/GRC/receipt/flag boundary.
- **Handoff:** `docs/RESEARCH_HANDOFF_CURRENT.md:12-18` states the same paused tokens, VMem/smoke state, SSH stale/unverified state, and full execution restrictions.
- **Method direction:** `docs/METHOD_DIRECTION_CURRENT.md:12-18` states the same tokens, VMem/smoke state, SSH stale/unverified state, and full execution restrictions.
- **R126 source stop rule:** `work/agents/CODEX_R126_INVARIANT_REDTEAM_20260924.md:99-107` independently states the absent packet, stale/unverified post-R111 remote state, unchanged flags, and full no-execution boundary.
- **Chinese memory:** `RESEARCH_MEMORY.md:3-5` preserves the paused tokens, flags, absent owner packet, VMem/smoke and remote-stale summary, and no command exposure/execution authorization. However, the current top does not enumerate dispatch/scheduling, protected-data, GPU/Slurm, C8/evaluation, S103/S132/GRC, receipt, and flag-mutation prohibitions with the same explicitness as the other records. The phrase “禁止执行边界” is a summary assertion rather than the full boundary text.

## Required correction

Update only the current R129 top of `RESEARCH_MEMORY.md` to spell out the same no-execution boundary already present in the other records: no command exposure, execution, dispatch, scheduling, protected-data access, GPU/Slurm work, C8/evaluation replay, S103/S132/GRC run, receipt mutation, or flag change. Preserve the existing anchored-final-root sentence, VMem `COMPLETE_SHA_VERIFIED`, historical smoke no-rerun rule, stale/unverified SSH state, `NO_COMMAND_AVAILABLE`, `NO_REOPEN`, END-LINE, and both validation flags. Then run one fresh read-only five-record check.

This correction must remain documentation-only. It cannot authorize a runner, fixture, command, C8/evaluation replay, GPU/Slurm work, S103/S132/GRC, method reopening, or validation-flag change.

## Current stop rule

The owner packet remains absent and the post-R111 remote synchronization remains stale/unverified. Keep `NO_COMMAND_AVAILABLE`, `NO_REOPEN`, END-LINE, `new_method_validated=false`, and `novelty_authorization=NONE`. Do not expose, execute, dispatch, or schedule commands; do not read protected data, submit GPU/Slurm jobs, rerun the historical smoke, mutate receipts, or change flags.

**R129 status: REVISE ONCE / Chinese-memory no-execution boundary not fully enumerated / NO EXECUTION.**
