# R128 anchored-final-root consistency rerun

**Date:** 2026-09-24 (Asia/Shanghai)  
**Scope:** Read-only review of the current top record in the plan, handoff,
memory, method-direction file, plus the R126 invariant memo. No command
discovery or execution, protected-data access, GPU/Slurm work, receipt or flag
mutation, or owner acceptance was performed.

## Verdict: REVISE once (documentation-only)

The four anchored-final-root details are not explicit in every current top
record. The `docs/METHOD_DIRECTION_CURRENT.md` R128 top (lines 1--7) only says
that the R127 omission was corrected; it does not repeat any of the four
conditions. Its R127 historical block (lines 11--19) is complete, so this is a
record-top omission rather than a new contract or scientific result. The
handoff R128 top (lines 3--6) is a concise summary but omits the explicit
verified device/inode/parent-entry wording and the literal
`REMOTE_PROVENANCE_UNVERIFIED` status; its R127 block (lines 16--21) is
complete. For a five-record *current-top* consistency check, both tops should
spell out the same four conditions.

## Four-detail matrix

| Record (current top) | Fixed-manifest owner bytes | Retained-FD root/device/inode/parent anchor | No cached-root pathname after final digest | Fail closed stale/remote-unverified + new nonce | Evidence / result |
|---|---|---|---|---|---|
| `docs/RESEARCH_PLANS_EN.md` R128 | PASS | PASS (lines 5--7) | PASS (lines 6--7) | PASS (lines 7--8) | PASS; lines 3--8 state all four explicitly. |
| `docs/RESEARCH_HANDOFF_CURRENT.md` R128 | PASS (line 4) | PARTIAL (line 5 says retained-FD root/parent anchoring, but omits explicit verified device/inode/parent-entry wording) | PASS (lines 5--6) | PARTIAL (line 6 says stale/new nonce, but omits literal `REMOTE_PROVENANCE_UNVERIFIED`) | REVISE top; R127 lines 16--21 are complete. |
| `RESEARCH_MEMORY.md` R128 | PASS | PASS | PASS | PASS | PASS; line 3 states all four, including root device/inode/parent and both statuses. |
| `docs/METHOD_DIRECTION_CURRENT.md` R128 | MISSING | MISSING | MISSING | MISSING | REVISE top; lines 3--7 only point to the R127 paragraph. R127 lines 11--19 are complete. |
| `work/agents/CODEX_R126_INVARIANT_REDTEAM_20260924.md` acceptance condition | PASS (lines 80--82) | PASS (lines 82--85) | PASS (lines 85--86) | PASS (lines 86--88) | PASS; lines 80--88 are the canonical full condition. |

## State-consistency check

- `NO_COMMAND_AVAILABLE`, `NO_REOPEN`, and END-LINE remain asserted in the
  plan R128 top (lines 10--12), handoff R128 top (lines 8--10), memory R128
  top (line 5), and R126 stop rule (lines 101--104). The method-direction R128
  top does not repeat these tokens; its R127 block does (lines 20--22), so the
  top record should repeat them for a strict five-record check.
- VMem remains `COMPLETE_SHA_VERIFIED`, and the historical no-data smoke is
  valid and must not be rerun in the plan R128 top (lines 12--14), handoff R128
  top (lines 10--12), memory R128 top (line 5), and R126 stop rule (lines
  101--107). The method-direction R128 top omits both, which is an omission,
  not a contradictory state.
- SSH exit 255 / post-R111 synchronization stale-unverified is consistent in
  plan lines 14--15, handoff lines 11--12, memory line 5, method-direction
  lines 5--6, and R126 lines 101--102.
- No execution/dispatch/scheduling, protected-data access, GPU/Slurm,
  C8/evaluation replay, S103/S132/GRC, receipt mutation, or flag changes remain
  forbidden in plan lines 14--17, handoff R127 lines 23--29, memory R124 lines
  27--29, method-direction R127 lines 19--22, and R126 lines 104--107. The
  R128 method-direction top says only “no method, execution, or owner
  acceptance state changes” (lines 3--5); it should carry the same explicit
  boundary if it is intended as the current authoritative top.

## Required documentation-only correction

Rewrite the current top of `docs/METHOD_DIRECTION_CURRENT.md` (and, for exact
five-record symmetry, the handoff R128 top) to repeat the canonical four-detail
sentence from the plan R127 block (lines 31--37) / R126 memo (lines 80--88), and
repeat the full paused-state tokens and execution boundary. Do not change any
scientific gate, owner acceptance, validation flag, method decision, remote
state, VMem state, or smoke state. Do not expose or execute a command.

Until that wording correction is applied and a fresh read-only check passes,
retain `REVISE ONCE`; this finding does not authorize a runner, fixture, C8,
GPU/Slurm, S103/S132/GRC, or any method reopening.
