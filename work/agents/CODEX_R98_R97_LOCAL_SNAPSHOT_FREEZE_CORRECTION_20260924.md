# R98 local snapshot freeze correction

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only correction to R97. No runner, fixture, sync, owner/H2
artifact, real C8 input, replay, GPU/Slurm job, receipt, or validation flag was
created or modified.

## Decision and boundary

Apply only R97's local-side TOCTOU correction. The local controller now has a
fully frozen, content-addressed snapshot before any transfer or readiness
attestation. The remote R96 post-freeze protocol, R89 owner hash, and R70 H2
gates remain unchanged.

`NO_COMMAND_AVAILABLE` remains in force. Project flags remain
`new_method_validated=false` and `novelty_authorization=NONE`.

## Local staging and atomic final root

1. Create a new temporary directory named with the fresh `sync_nonce` under a
   dedicated local snapshot root. Copy only the fixed manifest-set entries using
   no-follow regular-file opens; reject missing, extra, duplicate, symlink,
   hard-link, traversal, alias, socket, and non-regular paths.
2. Hash each staged file and record its path, fixed role, size, and SHA. Compute
   a provisional manifest digest from the exact sorted set with
   `canonical_json_v2`.
3. `fsync` every staged file, then `fsync` the temporary parent directory. If
   any write, size, type, link, or hash check fails, delete the temporary tree
   and return `REMOTE_PROVENANCE_UNVERIFIED` without transfer.
4. Atomically rename the complete temporary tree to a final root whose name
   contains both nonce and provisional digest:

   ```text
   local_snapshot/<sync_nonce>-<provisional_manifest_sha256>
   ```

   The rename is the only transition that makes the snapshot eligible as an
   attestation source; the mutable worktree and pre-rename directory are never
   read afterward.

## Final read-only and post-rename verification

After the atomic rename, set the final tree read-only (directories searchable,
files non-writable) and retain no write handle. Reopen every final file with
`O_NOFOLLOW`, recheck regular-file identity/size and link status, and recompute
every file SHA plus the complete manifest digest. The final digest must equal
the provisional digest encoded in the root name. The resulting identity is:

```text
local_frozen_snapshot_id =
  "local:" + sync_nonce + ":" + final_manifest_sha256
```

Only this post-rename `final_manifest_sha256` becomes the expected digest sent
to the remote R96 verifier. The transfer source and later readiness input are
the final frozen root only. A pre-freeze hash, mutable worktree path, or
provisional receipt is never sufficient.

Immediately before sending the attestation and again before owner/H2 readiness,
reopen the final local root with `O_NOFOLLOW` and repeat the full digest pass.
Any changed inode/link, path role, size, byte hash, nonce, root name, or digest
returns `REMOTE_PROVENANCE_UNVERIFIED` or `STALE`; delete/abandon the root and
require a new nonce and new local snapshot. R96's remote atomic rename,
read-only root, post-freeze pass, and local/remote comparison remain required.

## Gate separation and terminal condition

This local freeze only establishes a trustworthy synchronization input. It does
not create the absent runner, fixture, owner tuple, H2 source manifest, packet,
or boundary artifact. `SYNC_VERIFIED` cannot replace R89 owner hashing, R70 H2
validation, or R62 phase ordering. Missing artifacts remain
`NO_COMMAND_AVAILABLE`; owner failures remain `OWNER_REVIEW_REQUIRED` or
`REJECT_FIXTURE`; H2 failures remain `H2_UNIDENTIFIABLE` before context/hash/arm
operations.

No real C8/evaluation data, target sensor, checkpoint, network, GPU, Slurm,
receipt, or validation flag may be opened or changed by this design.

**R98 status: LOCAL SNAPSHOT FREEZE CORRECTION / FUTURE-ONLY / NO EXECUTION.**
