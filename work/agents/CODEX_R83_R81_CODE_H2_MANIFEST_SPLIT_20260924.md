# R83 code/H2 source-manifest split for the future CGLR runner

Date: 2026-09-24 (Asia/Shanghai)  
Scope: future-only design addendum to R81. No runner, manifest, fixture, H2 packet, boundary artifact, receipt, real C8 input, GPU/Slurm job, or validation flag was created or accessed.

## Decision and boundary

This addendum applies the single R82 identity correction. The four-root policy,
non-recursive code manifest, R62 phase order, R70/R72 H2 schema, and all
NO_COMMAND_AVAILABLE blocks remain unchanged. Every path below is proposed and
absent.

The runner now has two independent manifest identities:

1. runner_code_manifest_sha256 for the source-pinned runner code root;
2. h2_source_manifest.json for the independently reviewed producer/boundary
   provenance required by the R70 H2 packet.

Neither identity may substitute for the other.

## Runner code identity

The read-only code_root contains source_code_manifest.json and the runner modules.
Its non-recursive files[] rules remain exactly those in R81. The bootstrap verifies
the recomputed code-manifest subject before reading any input role.

fixture.json records the code identity only in a separate runner binding object:

    runner_binding:
      runner_code_manifest_sha256: lowercase 64-hex hash

The runner binding is not R70 h2_provenance.source_manifest_sha256. A missing,
stale, malformed, path-set, link, or byte/hash mismatch returns
OWNER_REVIEW_REQUIRED or REJECT_FIXTURE before phase 0, as defined by the R81
source-manifest gate.

## H2 producer/boundary identity

The read-only input_root contains one additional role-bound JSON file:

    h2_source_manifest.json

This file is a provenance manifest for the producer/boundary convention, not for
the runner code. It contains a fixed schema/version, an ordered producer_files[]
list with relative identity labels and lowercase hashes, the producer frame
declaration identity, and the boundary artifact identity. The manifest subject
excludes only its own supplied manifest_sha256 field and contains no RGB/depth
array, target sensor, checkpoint, or learned weight.

The producer_files[] entries are identity records only. The synthetic runner never
opens the listed producer source paths; it opens only h2_source_manifest.json,
h2_packet.json, and boundary_artifact.json under the input role allowlist.

R70 h2_provenance.source_manifest_sha256 must equal the recomputed
h2_source_manifest.json subject. R70 h2_provenance.boundary_artifact_sha256 must
equal the recomputed boundary_artifact.json bytes. The H2 packet's
source_manifest_sha256 therefore binds the producer/boundary evidence, while
runner_binding.runner_code_manifest_sha256 binds the executable code.

## Role logging and phase ordering

The role allowlist adds h2_source_manifest with read-only access. Its successful
open is logged with role, canonical path, phase, mode, process ID, and byte hash.
The launch receipt records runner_code_manifest_sha256 and
h2_source_manifest_sha256 as different fields.

The exact order is:

    bootstrap_code_manifest
      -> phase_0_static_preflight
      -> phase_1_materialize
      -> phase_2_H2_gate
      -> phase_3_hash_verification
      -> phase_4_arm_score

1. bootstrap_code_manifest verifies only code_root and the immutable runner
   binding. It does not open h2_source_manifest or any scientific role.
2. phase 0 reads fixture/review/protocol role bytes, checks the canonical fixture,
   S131 fields, owner gate, runner binding, arm table, and marker/path rules.
   It does not open h2_source_manifest, h2_packet, or boundary contents.
3. phase 1 materializes computed synthetic geometry without H2-dependent hashes.
4. phase 2 opens h2_source_manifest.json, h2_packet.json, and
   boundary_artifact.json. It recomputes both identities, checks the exact R70/R72
   T_c2w packet and bidirectional error, and verifies the producer-frame
   declaration.
5. Only after phase-2 PASS may the runner extract fixture_context_paths, calculate
   fixture_context_sha256, calculate base/rule/arm hashes, or score an arm.

## H2 failure precedence

Return H2_UNIDENTIFIABLE before fixture-context extraction or any H2-dependent hash
for any of these cases:

* h2_source_manifest.json, h2_packet.json, or boundary_artifact.json is missing,
  malformed, marker-valued, stale, or not a role-allowed regular file;
* h2_packet.source_manifest_sha256 differs from the recomputed
  h2_source_manifest subject;
* h2_packet.boundary_artifact_sha256 differs from the recomputed boundary bytes;
* producer_files[] is incomplete, duplicated, non-hex, or inconsistent with the
  independently reviewed boundary/frame declaration;
* any R70/R72 frame label, T_c2w direction, formula, numeric error, threshold, or
  status check fails.

A code-root identity failure remains OWNER_REVIEW_REQUIRED or REJECT_FIXTURE before
phase 0. It cannot be downgraded to H2_UNIDENTIFIABLE, and an H2 failure cannot
authorize a code-manifest substitution.

## Four-root and no-data compatibility

* stdlib_root and code_root remain read-only and contain no scientific inputs.
* input_root now permits h2_source_manifest.json only as a hash/identity JSON role;
  listed producer paths are never opened.
* output_root remains new, atomic, and receipt-only.
* sockets, processes, dynamic imports, GPU/device APIs, symlinks, traversal,
  aliases, hard links, and unlisted paths remain denied.

No real producer source, RGB/depth, C8 scene, target answer, checkpoint, model,
replay, GPU/Slurm job, or existing receipt is opened by this synthetic protocol.

## Owner-review acceptance checklist

Before implementation can be accepted, the reviewer must confirm:

1. The code-root manifest and H2 source manifest have distinct schema/subjects,
   fields, hashes, and role-log entries.
2. R70 h2_provenance.source_manifest_sha256 binds only h2_source_manifest.json,
   never the runner code manifest.
3. fixture.runner_binding.runner_code_manifest_sha256 binds only source_code_manifest.
4. Phase 2 reads and verifies all three H2 artifacts before any
   fixture_context/hash/arm score operation.
5. Any H2 identity mismatch returns H2_UNIDENTIFIABLE first; code identity
   failures remain pre-phase-0 owner/schema failures.

**R83 status: CODE/H2 MANIFEST SPLIT COMPLETE / FUTURE-ONLY / NO EXECUTION.**
NO_COMMAND_AVAILABLE remains in force. Project flags remain
new_method_validated=false and novelty_authorization=NONE.
