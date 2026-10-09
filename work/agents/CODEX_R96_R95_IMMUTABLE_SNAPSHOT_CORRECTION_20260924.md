# R96 immutable snapshot correction for provenance attestation

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only correction to R94/R95. No runner, fixture, sync, owner/H2
artifact, real C8 input, replay, GPU/Slurm job, receipt, or validation flag was
created or modified.

## Decision and boundary

Apply only R95's TOCTOU correction. A provenance attestation is valid only for
two immutable, content-addressed snapshots: one frozen locally before transfer
and one frozen remotely before the attestation receipt. This is evidence
hygiene; it does not authorize execution or make missing owner/H2 artifacts
available.

`NO_COMMAND_AVAILABLE` remains in force. Project flags remain
`new_method_validated=false` and `novelty_authorization=NONE`.

## Fixed snapshot identity

The local controller creates a fresh random `sync_nonce` and a fixed manifest
set of path/role/size/SHA entries. It copies the exact set into a new temporary
snapshot directory, using no-follow regular-file opens, and closes all writers.
It then computes:

```text
local_manifest_sha256 = SHA256(canonical_json_v2({
  set_version, sorted(path, fixed_role, size_bytes, sha256)
}))
frozen_snapshot_id = "local:" + sync_nonce + ":" + local_manifest_sha256
```

The expected digest is computed from the staged snapshot bytes, not from a
mutable source worktree. The staging directory is complete before it can be
renamed. Missing, extra, duplicate, symlink, hard-link, traversal, alias,
socket, or non-regular entries fail the local snapshot before transfer.

## Atomic remote snapshot

The remote verifier receives only the fresh nonce, fixed manifest set, and
expected local digest. It writes to a new temporary directory under the remote
snapshot root. Each file is opened with `O_NOFOLLOW|O_RDONLY` for verification;
its regular-file identity, size, and SHA are recorded. After every entry passes,
the verifier `fsync`s file data and the temporary directory, atomically renames
the directory to `snapshot/<sync_nonce>`, and makes the final tree read-only
and content-addressed. The mutable remote checkout is never the attested read
root.

The verifier then performs a post-rename pass: reopen every final file with
`O_NOFOLLOW`, recheck regular-file type/identity/size, recompute every SHA and
the complete manifest digest, and require equality to the expected local
digest. Only this post-freeze result may produce:

```text
remote_frozen_snapshot_id = "remote:" + sync_nonce + ":" + remote_manifest_sha256
status = SYNC_VERIFIED
```

The receipt contains the nonce, frozen snapshot path/ID, exact set version, and
the post-freeze digest. A remote-reported status is not trusted by itself; the
local controller compares the receipt to its fresh nonce, frozen local digest,
and full path/role/size/SHA set.

## Freeze-before-readiness rule

Immediately before any owner or H2 readiness check, the local controller:

1. reopens the local frozen snapshot and recomputes its complete digest;
2. revalidates the remote receipt nonce, frozen snapshot ID, exact set, and
   post-freeze digest;
3. accepts `SYNC_VERIFIED` only when both frozen digests and all entries match;
4. passes only the remote frozen snapshot root to the readiness consumer.

The consumer must not reopen the mutable remote checkout or the pre-freeze
temporary directory. Any changed inode/link, type, size, byte hash, path role,
set version, nonce, or snapshot digest yields
`REMOTE_PROVENANCE_UNVERIFIED`; a change detected after a previously valid
attestation yields `STALE`. Both statuses stop before owner/H2 readiness and
require a new local snapshot, nonce, transfer, and post-freeze pass.

## Gate separation and stop conditions

`SYNC_VERIFIED` only proves evidence-set synchronization. It does not replace
R89 `manifest_identity` owner hashing, R70 H2 packet checks, or R62 phase
ordering. If a frozen set is valid but runner, fixture, owner artifact, H2
source manifest, packet, or boundary artifact is absent, retain
`NO_COMMAND_AVAILABLE`; malformed owner/code inputs remain `OWNER_REVIEW_REQUIRED`
or `REJECT_FIXTURE`; H2 absence or mismatch remains `H2_UNIDENTIFIABLE` before
context/hash/arm operations.

No real C8/evaluation data, target sensor, checkpoint, network, GPU, Slurm,
receipt, or validation flag may be opened or changed by this guard.

**R96 status: IMMUTABLE SNAPSHOT CORRECTION / FUTURE-ONLY / NO EXECUTION.**
