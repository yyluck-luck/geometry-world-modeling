# R82 final hostile audit of the R81 source-manifest correction

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only audit. No runner, fixture, source manifest, H2 artifact, receipt, real C8 input, GPU/Slurm job, or validation flag was created or accessed.

## Decision

**REVISE ONCE BEFORE IMPLEMENTATION.**

R81 removes the code-manifest self-hash cycle and keeps the four-root and
phase-0-before-materialization ordering. One concrete H2/owner binding error
remains: it assigns R70 H2 source_manifest_sha256 to the runner's code manifest.
R52/R70 use that H2 field for the independently reviewed producer/boundary source
manifest, which is a different identity domain.

## Checks that pass

* files[] covers every other regular code-root file exactly once; the manifest
  itself is structural only and no longer recursively hashed.
* Fixed manifest_path/schema/code_root_role fields, relative paths, byte lengths,
  lowercase hashes, and missing/extra/link/alias rejection are explicit.
* code-root verification is placed before fixture-role reads and before phase 0;
  the R62 order and H2-before-hash/score gate remain preserved.
* The four roots remain compatible: read-only stdlib/code, role-limited input,
  and new atomic output. NO_COMMAND_AVAILABLE and all execution blocks remain.

## Remaining concrete flaw: H2 source-manifest identity is conflated with code identity

R81 lines 61-67 state that
R70 h2_provenance.source_manifest_sha256 equals the non-recursive runner
source_code_manifest subject. R52 defines source_manifest_sha256 as the SHA-256 of
the exact producer and boundary files (CODEX_R52_CGLR_PROTOCOL_REVISION_20260924.md
lines 21-44), while R70 keeps that field alongside the separate
boundary_artifact_sha256 and producer-frame evidence (lines 22-59). The runner's
code-root manifest cannot replace this H2 provenance artifact without changing the
meaning of the H2 gate. A fixture could therefore pass a code identity check while
the producer pointmap convention remains unbound.

## One minimal correction

Split the two identities without changing the R70 H2 schema:

1. Keep source_code_manifest.json and its recomputed subject for the runner
   code-root identity. Bind it through a clearly named runner field such as
   fixture.runner_binding.runner_code_manifest_sha256 (or an equivalently
   explicit non-H2 field). Do not write this value into
   h2_provenance.source_manifest_sha256.
2. Add one role-bound input artifact, h2_source_manifest.json, containing the
   independently reviewed producer/boundary source file list and lowercase hashes.
   Its canonical subject is the value required by R52/R70
   h2_provenance.source_manifest_sha256. The artifact is read only in phase 2
   together with h2_packet.json and boundary_artifact.json.
3. Require h2_packet.source_manifest_sha256 to equal the recomputed
   h2_source_manifest subject and h2_packet.boundary_artifact_sha256 to equal the
   recomputed boundary artifact. Missing/mismatched H2 source identity returns
   H2_UNIDENTIFIABLE before fixture_context extraction or any arm hash.
4. Add h2_source_manifest to the input role allowlist and role log, while keeping
   code-root manifest verification before phase-0 fixture reads. The two manifests
   must be recorded as different identities in the launch receipt and may not be
   substituted for one another.

This preserves the non-recursive code manifest, the four-root policy, and the
R62 phase order while restoring the original H2 provenance meaning.

## Terminal

Until this identity split is incorporated and independently reviewed, the runner
remains unimplemented and the command remains NO_COMMAND_AVAILABLE. No fixture,
real C8, replay, GPU/Slurm, receipt edit, or validation-flag change is authorized.

**R82 status: REVISE ONCE / FINAL SOURCE-MANIFEST AUDIT COMPLETE / DESIGN-ONLY.**
Project flags remain new_method_validated=false and novelty_authorization=NONE.
