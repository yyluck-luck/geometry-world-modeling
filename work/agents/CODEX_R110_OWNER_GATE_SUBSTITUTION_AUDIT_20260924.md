# R110 owner-gate substitution and replay audit

Date: 2026-09-24 (Asia/Shanghai)  
Scope: read-only local readiness audit. No runner/fixture execution, no GPU/
Slurm, no protected C8/evaluation reads, and no contract or flag changes.

## Verdict: REVISE once

R109 adds the right owner-gate labels, but the fields are still vulnerable to
three substitutions: (i) the review hash has no stated canonical subject,
(ii) the manifest-chain strings are not bound to the code/H2/boundary bytes,
and (iii) `decision_time_utc` is not a freshness proof. A previously valid
review artifact could therefore be replayed with a different fixture root or
role-labelled H2 files. R89, R85, and R98 already specify the missing checks.

## Local artifact check

At the local project root
`/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling`, the exact paths
`review_artifact.json`, `source_code_manifest.json`, `h2_source_manifest.json`,
`h2_packet.json`, `boundary_artifact.json`, and `fixture.json` are all absent.
A bounded filename search under `work/S131_CGLR_contract` and `work/agents`
found design/audit memos only, not executable owner/H2/fixture artifacts. The
state is therefore still `NO_COMMAND_AVAILABLE`; no artifact contents were
opened.

## Attack findings

1. **Owner-hash substitution.** R109 requires a 64-hex review hash but does
   not require recomputing it from the exact owner subject. R89 requires
   strict `canonical_json_v2(review_artifact with only
   /owner_gate/review_artifact_sha256 removed)`, duplicate-key rejection, and
   no alternate encodings
   (`work/agents/CODEX_R89_R88_CANONICAL_JSON_V2_CORRECTION_20260924.md:19-41,79-97`).
   Without that subject rule, a valid hash can be copied to a semantically
   different artifact.
2. **Role/path or manifest-chain substitution.** R109's chain is a list of
   names, not an identity tuple. R85 requires distinct, recomputed code,
   H2-source, and boundary hashes, fixed schemas/roles/paths, and
   `runner_code_manifest_sha256 != h2_source_manifest_sha256`
   (`work/agents/CODEX_R85_R84_MANIFEST_IDENTITY_TUPLE_CORRECTION_20260924.md:19-69,94-120`).
   A textually correct R70 chain must not authorize a code manifest placed at
   the H2 path or a boundary file copied into a different role.
3. **Replay/staleness.** R109 has a timestamp but no binding to the final
   immutable snapshot. R98 requires a post-rename read-only root, fresh nonce,
   final manifest digest, reopen/full-digest pass immediately before readiness,
   and mutation → `STALE`/`REMOTE_PROVENANCE_UNVERIFIED`
   (`work/agents/CODEX_R98_R97_LOCAL_SNAPSHOT_FREEZE_CORRECTION_20260924.md:41-64`).
   An old `OWNER_ACCEPTED` hash must not pass against a later root.

## Exact owner-gate binding required before materialization

Retain R109's existing fields and add these machine checks to phase 0:

```text
owner_subject_sha256 = SHA256(canonical_json_v2(review_artifact with only
  /owner_gate/review_artifact_sha256 removed))
manifest_identity = exactly R85's seven fields and fixed roles/schemas
runner_code_manifest_sha256 != h2_source_manifest_sha256
frozen_snapshot_id = local:<fresh_sync_nonce>:<final_manifest_sha256>
snapshot_final_digest = recomputed immediately before readiness
```

The owner subject must include the exact accepted protocol/manifest chain,
manifest identity tuple, H2/boundary hashes, frozen snapshot ID, decision scope,
timestamp, and reviewer role. Recompute every hash from the final frozen root;
do not trust supplied fields or timestamps. The chain must equal either the
exact latest R70 ID or the complete ordered R52→R62→R64→R68→R70 chain. No
extra/alias role or path is accepted.

## Single owner rejection status and order

Use **`OWNER_REVIEW_REQUIRED`** as the one canonical rejection status for a
missing, stale, replayed, substituted, or mismatched owner review hash,
manifest identity, chain, snapshot ID, nonce, or final digest. Emit it in
phase 0 before materialization, H2 opening, fixture-context extraction, or any
scientific hash. Do not downgrade such a failure to `H2_UNIDENTIFIABLE`.

After `OWNER_REVIEW_REQUIRED` is cleared, the existing phases remain:
owner gate → materialize → H2 gate → hash verification → score. H2 field or
boundary failures then return `H2_UNIDENTIFIABLE`; other computed/schema
failures remain `REJECT_FIXTURE`.

## Remaining blocker

The six owner/H2/fixture files and supported runner are absent locally, so this
correction cannot be executed or used to reopen END-LINE. Preserve
`NO_COMMAND_AVAILABLE`, `new_method_validated=false`, and
`novelty_authorization=NONE`; do not execute, access protected data, or change
flags.

