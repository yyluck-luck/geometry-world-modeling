# R126 conjunctive-invariant adversarial audit

**Date:** 2026-09-24 (Asia/Shanghai)  
**Scope:** read-only adversarial audit of the R125 owner-packet acceptance
matrix and the R108--R125 provenance/owner-gate records. No runner or fixture
execution, command discovery, protected C8/evaluation read, GPU/Slurm work,
receipt mutation, or validation-flag change occurred.

## Verdict: REVISE once

One concrete directory-replacement race remains possible under the current
wording of the R125 invariant. The individual hash, owner-subject, and
`O_NOFOLLOW` checks are sound when they all read one immutable root, but the
contract does not explicitly anchor the **post-check readiness reads** to the
same open root directory/inode, nor does it explicitly require the owner review
artifact bytes themselves to be members of the final manifest set. A path-name
swap can therefore preserve the cached snapshot identity and all R85
code/H2/boundary hashes while substituting a self-consistent owner artifact.

This is a contract gap, not an observed execution result. The packet remains
absent and `NO_COMMAND_AVAILABLE` remains in force.

## Concrete race / substitution counterexample

Let `R = local_snapshot/<nonce>-D` be the R98 final root and let the parent
snapshot directory remain renameable by another process (for example, an owner
refresh or a concurrent staging process). Assume the R85 code, H2-source, and
boundary files in `R` are unchanged.

1. The verifier performs R98's second full digest pass through the pathname
   `R`, obtains `snapshot_final_digest = D`, and caches
   `frozen_snapshot_id = local:<nonce>:D`. This is the check described by
   R98:43--64 and R125:29--53.
2. Before the owner/H2 readiness reads, a concurrent process atomically renames
   the directory entry `R` to `R.old` and installs a prepared directory `R'`
   under the same name `R`. `R'` contains byte-identical R85 code/H2/boundary
   files but a different, canonical `review_artifact.json` whose single
   `review_artifact_sha256` correctly hashes its own canonical subject.
3. The verifier reopens `R/owner_gate/review_artifact.json` by pathname. The
   child is a regular file and `O_NOFOLLOW` therefore succeeds; the owner
   subject recomputation also succeeds. The unchanged R85 role-bound files
   still match the cached R85 hashes. Unless the implementation performs a
   fresh digest *after this replacement* or reads through an anchored root
   file descriptor, the cached `D` and `local:<nonce>:D` still satisfy the
   R125 conjunctive invariant.
4. The substituted owner review can now carry a different reviewer, scope, or
   accepted chain while appearing bound to the old snapshot identity. This is
   a replay/substitution acceptance even though no JSON alias or second owner
   hash is present.

The race also applies to a review artifact read from a mutable worktree or a
remote path: R125's listed R85 hashes do not, by themselves, commit the exact
owner-review bytes to `snapshot_final_digest`. R98:54--57 says the frozen root
is the readiness input, but R125 should make the root anchoring and owner-file
membership explicit rather than relying on path discipline.

## Why the existing checks do not close this branch

* R98:43--47 protects files against writes and checks `O_NOFOLLOW`, but
  `O_NOFOLLOW` on a later pathname lookup does not prove that the containing
  directory entry is the same inode that was hashed earlier.
* R98:59--64 requires another full digest pass immediately before readiness,
  but it leaves a non-atomic interval between that pass and the subsequent
  owner/H2 opens. A directory-entry replacement in that interval is not
  observed by the cached digest.
* R125's invariant (R125:29--53) binds `frozen_snapshot_id`, final digest, and
  R85 role-bound hashes, yet it does not state that `review_artifact.json` is a
  fixed-manifest member or that all readiness reads use the same opened root.
* R112's single-hash rule (R112:26--43) correctly rejects aliases and makes the
  swapped artifact self-consistent; it therefore does not detect this
  directory-level substitution.
* R114's status order (R114:50--67) would reject a detected stale root, but the
  race is precisely that the verifier's stale-root evidence is no longer
  consulted after the final path swap.

## Sharpened acceptance condition

Add one mandatory condition to R125/R98/R114 before owner or H2 access:

> **Anchored-final-root condition.** The complete fixed manifest set MUST
> include the exact owner review artifact bytes (with its canonical
> `review_artifact_sha256` subject check), and readiness MUST read every role
> from a retained file descriptor for the post-rename final root, anchored to
> the verified root device/inode and parent directory entry (`O_NOFOLLOW` plus
> an equivalent beneath/no-reparse constraint). No pathname lookup by the
> cached root name is allowed after the last full digest pass. If the root
> inode, parent entry, owner-artifact bytes/hash, or any role file changes,
> return `STALE`/`REMOTE_PROVENANCE_UNVERIFIED` and restart with a new nonce.

If the implementation cannot retain an anchored root descriptor, it must
perform a final digest and owner/H2 opens under an equivalent atomic exclusion
mechanism and prove the parent entry is immutable; otherwise the condition
fails closed as `STALE`.

This correction is compatible with the existing R85/R89/R98/R110--R114 gate
order. It only closes the remaining TOCTOU path; it does not authorize command
discovery, synthetic execution, method reopening, or GPU work.

## Current state and stop rule

The local owner/H2/fixture/runner packet remains absent; the remote state after
R111 is stale/unverified while SSH synchronization is unavailable. Keep
`NO_COMMAND_AVAILABLE`, `NO_REOPEN`, END-LINE,
`new_method_validated=false`, and `novelty_authorization=NONE`. Do not expose,
execute, dispatch, or schedule a command; do not read protected C8/evaluation
data, submit GPU/Slurm jobs, rerun the historical smoke, mutate receipts, or
change validation flags.

**R126 status: REVISE ONCE / directory-replacement TOCTOU identified / NO
EXECUTION.**
