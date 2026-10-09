# R99 final symmetric audit of the R98/R96 provenance snapshots

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design/read-only audit. No sync, runner, fixture, owner/H2 artifact,
real C8 input, replay, GPU/Slurm job, receipt, or validation flag was created,
opened, or modified.

## Decision

**PASS.** R98 now supplies the local half that was missing in R96. The local
and remote protocols are symmetric at the security boundary, and the remaining
nonce/path naming difference is covered by the post-freeze digest in each
snapshot ID and the local receipt comparison. No concrete provenance or
substitution gap remains in this design.

## Side-by-side protocol audit

| Property | Local R98 | Remote R96 | Audit result |
|---|---|---|---|
| Fixed manifest set | No-follow copy of exact path/role/size/SHA set; missing/extra/duplicate/link/path entries fail | Same exact set received and rechecked | PASS: no partial or wildcard set |
| Fresh challenge | `sync_nonce` names the local temporary/final snapshot and handshake | Same nonce is required in remote receipt and frozen ID | PASS: old receipt replay fails |
| Content identity | Provisional digest becomes final after post-rename full rehash; final ID is `local:nonce:digest` | Post-freeze full rehash produces `remote:nonce:digest`; path is nonce-scoped but receipt ID is digest-bound | PASS: both accepted identities bind nonce plus final content digest |
| Durability/atomicity | `fsync` each file and temporary parent, then atomic rename to final root | `fsync` file data and temporary directory, then atomic rename to final root | PASS |
| Frozen root | Final tree read-only, no write handle, transfer/readiness use final root only | Final tree read-only/content-addressed, mutable checkout never used | PASS |
| Link/path safety | `O_NOFOLLOW` reopen; regular-file identity/size/link checks | `O_NOFOLLOW` reopen; same final checks | PASS |
| Post-freeze verification | Reopen every final file and recompute complete digest; repeat before attestation/readiness | Reopen every final file after rename and recompute complete digest | PASS |
| Mutation/replay | Any local root/hash/nonce/role mutation becomes `REMOTE_PROVENANCE_UNVERIFIED` or `STALE` | Any remote receipt/root/hash/nonce mutation has the same result | PASS |
| Gate separation | Synchronization only; R89/R70/R62 remain authoritative | Same | PASS |

The remote directory name `snapshot/<sync_nonce>` is not, by itself, treated as
content identity. R96's `remote_frozen_snapshot_id` includes the post-freeze
manifest digest, and local acceptance compares that ID/digest and every entry
to its frozen local set. Thus a same-nonce replacement is detected at the
readiness recheck rather than silently accepted.

## Actual artifact check

Exact-name checks were repeated for both roots:

* local: `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling`;
* remote: `/home/yliutz/geometry-world-modeling` on `superpod.ust.hk`.

At both roots, `review_artifact.json`, `source_code_manifest.json`,
`h2_source_manifest.json`, `h2_packet.json`, `boundary_artifact.json`, and
`fixture.json` remain **ABSENT**. The only checked S131 paths present at both
roots are `work/S131_CGLR_contract/episode_schema.json` and
`DESIGN_AND_PREREGISTRATION.md`; they are contract/design records with
`CONTRACT_ONLY`, not executable artifacts. This agrees with
`work/agents/CODEX_R93_OWNER_H2_CHECKLIST_VERIFICATION_20260924.md:24-34`
and the post-R93 sync record in `RESEARCH_LOG.md:15618-15626`.

## Terminal condition

The symmetric provenance design is owner-reviewable but has not been
implemented, and the required runner/H2 artifacts remain absent. Keep
`NO_COMMAND_AVAILABLE`; do not run or create a runner/fixture, read/replay
real C8, submit GPU/Slurm, mutate receipts, or change validation flags.
Project flags remain `new_method_validated=false` and
`novelty_authorization=NONE`.

**R99 status: PASS / FINAL SYMMETRIC PROVENANCE AUDIT / DESIGN-ONLY.**
