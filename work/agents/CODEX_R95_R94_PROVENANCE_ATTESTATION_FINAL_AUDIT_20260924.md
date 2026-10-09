# R95 final hostile audit of the R94 provenance attestation

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design/read-only audit. No sync, runner, fixture, owner/H2 artifact,
real C8 input, replay, GPU/Slurm job, receipt, or validation flag was created
or modified.

## Decision

**REVISE ONCE.** R94 correctly binds a fresh nonce to a fixed exact path/role
set, checks every size/SHA, rejects links and aliases, detects ledger appends,
and leaves R89 owner hashing/R70 H2 gates authoritative. One TOCTOU gap remains:
R94 says the remote verifier stages a disposable snapshot and hashes it, but it
does not require that the local source snapshot or remote snapshot be frozen and
revalidated immediately before a readiness decision. A file can change after
the hash pass and before an owner/H2 consumer opens it.

## Checks that pass

* **Fresh challenge:** a local fresh nonce is compared by the local controller;
  an old remote receipt cannot satisfy a new challenge.
* **Complete set:** fixed `set_version` and exact path/role cardinality reject
  missing, extra, duplicate, or wildcard-copied records.
* **Identity:** every entry carries fixed role, regular-file status, size, and
  SHA; the whole-set digest is recomputed locally and remotely.
* **Path safety:** symlink, hard-link, traversal, alias, socket, and non-regular
  paths are rejected before bytes are accepted.
* **Ledger replay:** appending to a listed ledger changes its hash and requires
  a new set/nonce; a stale attestation is not readiness.
* **Separation:** the guard only establishes evidence synchronization. It cannot
  satisfy R89 `manifest_identity`, R70 H2 provenance, owner acceptance, or the
  phase-2 `H2_UNIDENTIFIABLE` precedence.

These properties address the observed stale checkout in
`work/agents/CODEX_R93_OWNER_H2_CHECKLIST_VERIFICATION_20260924.md:47-51` and
the subsequent ten-file hash match recorded in `RESEARCH_LOG.md:15618-15626`.

## Remaining TOCTOU gap

R94's `stages the exact set under a new disposable snapshot root` and
`remote_manifest_sha256` describe a hash-time state, not a lifetime guarantee.
The source worktree can change between local digest creation and transfer; the
remote staged files can change after hashing; and a readiness consumer could
later reopen the mutable checkout rather than the bytes that were attested.
Nonce equality and per-file SHA cannot detect a post-attestation mutation unless
the snapshot is revalidated at use time.

## One minimal correction: freeze and final revalidation

Add a `frozen_snapshot_id` rule to R94's same handshake:

1. The local controller copies the fixed set into a temporary snapshot, closes
   all writers, rehashes the snapshot, and computes
   `expected_local_manifest_sha256` from that frozen snapshot. It does not hash
   a live worktree and then continue editing it.
2. The remote verifier copies into a temporary directory using no-follow,
   regular-file opens, writes atomically, `fsync`s file and directory data, then
   atomically renames it to `snapshot/<sync_nonce>`. It makes the final tree
   read-only/content-addressed and records a `frozen_snapshot_id` equal to the
   nonce plus the final manifest digest.
3. After the rename, the verifier reopens every final file with `O_NOFOLLOW`,
   rechecks regular-file identity/size, and recomputes the complete digest. The
   receipt is emitted only from this post-freeze pass.
4. The local controller revalidates its frozen source digest and the remote
   receipt's nonce/digest immediately before any owner/H2 readiness check. The
   consumer then reads only the frozen snapshot path, never the mutable checkout.

Any reopen, size, inode/link, role/path, or digest mismatch returns
`REMOTE_PROVENANCE_UNVERIFIED`/`STALE` and forbids owner/H2 readiness. This is a
TOCTOU correction only; it does not alter R89 canonical owner hashing or R70
H2 status codes.

## Terminal condition

Until the owner reviews this freeze/revalidation correction and all R92 artifacts
exist, remote evidence remains non-authoritative for execution. Keep
`NO_COMMAND_AVAILABLE`; do not create or run a runner/fixture, read/replay real
C8, submit GPU/Slurm, mutate receipts, or change validation flags. Project flags
remain `new_method_validated=false` and `novelty_authorization=NONE`.

**R95 status: REVISE ONCE / FINAL PROVENANCE ATTESTATION AUDIT / DESIGN-ONLY.**
