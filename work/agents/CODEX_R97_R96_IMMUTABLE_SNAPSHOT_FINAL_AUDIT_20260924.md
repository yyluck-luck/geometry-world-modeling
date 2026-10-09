# R97 final hostile audit of the R96 immutable snapshot correction

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design/read-only audit. No sync, runner, fixture, owner/H2 artifact,
real C8 input, replay, GPU/Slurm job, receipt, or validation flag was created
or modified.

## Decision

**REVISE ONCE.** R96 closes the remote-side TOCTOU path and correctly keeps
the nonce, content digest, link/path checks, final remote pass, readiness-time
recheck, and R89/R70 separation. One local-side freeze step is still implicit:
the local staging directory is hashed before transfer, but R96 does not require
local `fsync`, atomic rename to a final snapshot root, read-only/content-addressed
permissions, or a post-rename reopen/digest pass before that root is used as the
transfer source.

## Checks that pass

* Fresh `sync_nonce` and local/remote content-derived IDs bind one handshake;
  the receipt cannot be accepted with an old nonce or digest.
* Fixed path/role/size/SHA entries, no-follow regular-file opens, and rejection
  of missing, extra, duplicate, symlink, hard-link, traversal, alias, socket,
  or non-regular paths cover set and role substitution.
* Remote staging uses `fsync`, atomic rename, read-only final root, and an
  `O_NOFOLLOW` post-rename full digest pass.
* Immediately before owner/H2 readiness, local and remote digests, IDs, roles,
  and nonce are rechecked; mutation maps to
  `REMOTE_PROVENANCE_UNVERIFIED` or `STALE`.
* `SYNC_VERIFIED` remains evidence synchronization only and cannot replace R89
  owner hashing, R70 H2 checks, or R62 phase ordering.

The design addresses the stale checkout observed in
`work/agents/CODEX_R93_OWNER_H2_CHECKLIST_VERIFICATION_20260924.md:47-51` and
the later synchronization record in `RESEARCH_LOG.md:15618-15626`.

## Remaining local TOCTOU gap

R96 says the local staged directory “can be renamed” and that the local digest
is computed from staged bytes, but it does not define the local commit/freeze
operation. A local writer can change a staged file after the digest calculation
and before transfer, or the transfer can accidentally read the mutable staging
directory. The remote digest would then disagree (correctly) only after data
movement, and a caller that trusts the local ID or begins another check early
could still consume the wrong bytes.

## One minimal correction

Make the local side mirror the remote freeze protocol:

1. After all staged entries pass no-follow/type/link checks, `fsync` every file
   and the temporary directory, then atomically rename it to
   `local_snapshot/<sync_nonce>`.
2. Make that final local tree read-only/content-addressed. The transfer source
   is only this final root; the mutable worktree and pre-rename directory are
   forbidden.
3. Reopen every final local file with `O_NOFOLLOW`, recheck regular-file
   identity/size, and recompute the complete manifest digest. Only this
   post-rename digest becomes `local_manifest_sha256` and the expected value
   sent to the remote verifier.
4. If any local file, inode/link, role/path, size, nonce, or digest changes,
   return `REMOTE_PROVENANCE_UNVERIFIED`/`STALE` and require a new local
   snapshot and nonce before transfer. Keep R96's existing remote post-freeze
   pass and readiness-time recheck unchanged.

This is one local freeze clarification; it does not alter owner/H2 semantics or
authorize execution.

## Terminal condition

Until this local-freeze correction is owner-reviewed, a remote attestation is
not sufficient for readiness. Keep `NO_COMMAND_AVAILABLE`; do not create or run
a runner/fixture, read/replay real C8, submit GPU/Slurm, mutate receipts, or
change validation flags. Project flags remain `new_method_validated=false` and
`novelty_authorization=NONE`.

**R97 status: REVISE ONCE / FINAL IMMUTABLE-SNAPSHOT AUDIT / DESIGN-ONLY.**
