# R111 owner-gate final provenance audit

Date: 2026-09-24 (Asia/Shanghai)  
Scope: read-only design audit. No runner or fixture execution, GPU/Slurm job,
protected C8/evaluation read, implementation, receipt update, or flag change.

## Verdict: REVISE once

R110 closes the concrete role/path and snapshot replay attacks once its checks
are applied, but its pseudo-field `owner_subject_sha256` leaves one residual
schema ambiguity. R89 defines exactly one supplied owner hash,
`/owner_gate/review_artifact_sha256`, and exactly one hash subject: the
canonical review artifact with only that field removed. If
`owner_subject_sha256` is materialized as a second JSON field, or is excluded
from a second hash subject, an implementation could accept an alias or
alternate self-hash and replay a review under a changed artifact. This is the
remaining substitution branch.

Evidence: R110 identifies the field at lines 51–69 and uses it in the phase-0
binding (`work/agents/CODEX_R110_OWNER_GATE_SUBSTITUTION_AUDIT_20260924.md:51-69`);
R89 forbids a second subject and fixes the single deletion at lines 31–41 and
79–97 (`work/agents/CODEX_R89_R88_CANONICAL_JSON_V2_CORRECTION_20260924.md:31-41,79-97`).

## Required correction

Treat `owner_subject_sha256` as an internal recomputed variable only. It must
never be a JSON field, alias, pointer, or supplied artifact value:

```text
supplied_owner_hash = review_artifact["owner_gate"]["review_artifact_sha256"]
owner_subject_bytes = canonical_json_v2(
    review_artifact with exactly
    /owner_gate/review_artifact_sha256 removed)
owner_subject_sha256 = SHA256(owner_subject_bytes)  # internal value only
require supplied_owner_hash == owner_subject_sha256
```

There is no second owner hash, no projected/filtered subject, and no alternate
field that may be removed before canonicalization. Strict duplicate-key,
unknown-field, marker, type, and canonical-json-v2 checks remain phase-0
rejections. The owner subject therefore still includes the accepted protocol
chain, the exact R85 `manifest_identity` object, H2/boundary hashes, the frozen
snapshot identity, scope, decision time, and reviewer role as ordinary fields
of the one review artifact.

R85 remains unchanged: `manifest_identity` has exactly seven fields, fixed
schemas/roles/paths, three independently recomputed hashes, and
`runner_code_manifest_sha256 != h2_source_manifest_sha256`
(`work/agents/CODEX_R85_R84_MANIFEST_IDENTITY_TUPLE_CORRECTION_20260924.md:19-69,71-118`).
No manifest-chain name or snapshot label can substitute for one of those
identity fields.

## Snapshot and status precedence

R98's final frozen root remains the freshness boundary. The verifier uses the
post-rename read-only root, reopens it with `O_NOFOLLOW`, and recomputes the
full digest immediately before owner/H2 readiness. Its identity is
`local:<fresh_sync_nonce>:<final_manifest_sha256>`
(`work/agents/CODEX_R98_R97_LOCAL_SNAPSHOT_FREEZE_CORRECTION_20260924.md:41-64`).

To avoid a status alias, apply the following order:

1. If the final root, nonce, inode/link, role/path, file hash, or digest
   changes, return R98's `STALE` or `REMOTE_PROVENANCE_UNVERIFIED` and abandon
   the snapshot. Do not evaluate the owner artifact against a mutable root.
2. Only after the final snapshot pass succeeds, run the phase-0 owner gate. A
   missing, replayed, alias-bound, or mismatched owner hash/tuple/chain returns
   `OWNER_REVIEW_REQUIRED` before materialization or H2 access.
3. After owner acceptance, retain R85/R89 phase-2 behavior: an independently
   failing H2 source, packet, or boundary returns `H2_UNIDENTIFIABLE` before
   fixture-context extraction or arm scoring.

This ordering preserves R98's provenance statuses and R110's canonical owner
status; it does not introduce a second owner rejection path.

## Readiness result and stop condition

The exact local paths checked by R110 (`review_artifact.json`,
`source_code_manifest.json`, `h2_source_manifest.json`, `h2_packet.json`,
`boundary_artifact.json`, and `fixture.json`) remain absent, and no supported
runner command is available. The state is therefore still
`NO_COMMAND_AVAILABLE`. No owner/H2 artifact is present to verify, so this
audit cannot reopen END-LINE or authorize a synthetic run. Preserve
`new_method_validated=false` and `novelty_authorization=NONE`; do not read
protected C8/evaluation data or change validation flags.

**R111 status: REVISE ONCE (remove the materialized `owner_subject_sha256`
alias; preserve internal recomputation only) / NO EXECUTION.**
