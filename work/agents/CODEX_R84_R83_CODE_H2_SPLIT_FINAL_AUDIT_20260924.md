# R84 final hostile audit of the R83 code/H2 manifest split

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only audit. No runner, fixture, manifest, review artifact, H2 packet, receipt, real C8 input, GPU/Slurm job, or validation flag was created or accessed.

## Decision

**REVISE ONCE BEFORE IMPLEMENTATION.**

R83 correctly separates runner code identity from H2 producer/boundary identity,
places H2 verification before fixture-context and arm hashes, and preserves the
four-root role log and path restrictions. One concrete substitution gap remains:
the plan does not require a machine-readable reviewed identity tuple or reject
content-level equality between the two manifests.

## Checks that pass

* runner_code_manifest_sha256 is a code-root identity and
  h2_source_manifest.json is an input-root H2 identity; neither field is used as
  the other.
* Phase 2 opens h2_source_manifest, h2_packet, and boundary_artifact only after
  phase 1, and H2_UNIDENTIFIABLE precedes fixture_context extraction, all
  H2-dependent hashes, and arm score.
* Four-root role logging records h2_source_manifest separately; code and H2
  artifacts remain read-only and output remains new/atomic.
* Symlink, traversal, alias, hard-link, socket, process, GPU, dynamic-import,
  and unlisted-path escapes remain denied.

## Remaining concrete flaw

R83 says the two identities “may not substitute for one another” and calls the
H2 source manifest independently reviewed, but it does not define a reviewed
identity tuple that binds all three artifacts. A fixture could provide a
syntactically valid h2_source_manifest whose canonical subject equals the runner
code-manifest subject, or could replace the reviewed H2 source/boundary pair while
keeping packet and recomputed hashes internally consistent. Disjoint path roots
prevent a filesystem alias, but they do not by themselves prevent content
substitution or prove that the H2 identity was the one independently reviewed.

## One minimal correction

Add one canonical identity tuple to review_artifact.json and require it at the
existing gates:

    manifest_identity:
      runner_code_manifest_sha256: lowercase 64-hex
      h2_source_manifest_sha256: lowercase 64-hex
      h2_boundary_artifact_sha256: lowercase 64-hex
      runner_code_schema: "gwm-cglr-source-code-manifest-v1"
      h2_source_schema: "gwm-cglr-h2-source-manifest-v1"
      runner_code_role: "cglr_runner_code"
      h2_source_role: "h2_source_manifest"

The tuple must be included in the owner-bound review artifact and satisfy:

1. runner_code_manifest_sha256, h2_source_manifest_sha256, and
   h2_boundary_artifact_sha256 are independently recomputed values;
2. runner_code_manifest_sha256 differs from h2_source_manifest_sha256;
3. schemas, role names, canonical roots, and manifest paths are distinct and
   cannot be cross-labeled;
4. phase 0 checks tuple presence/types and binds the review artifact without
   opening H2 files;
5. phase 2 recomputes h2_source_manifest and boundary hashes, compares them with
   both the tuple and H2 packet, and returns H2_UNIDENTIFIABLE on any mismatch
   before fixture_context/hash/arm operations.

The runner code identity remains an OWNER_REVIEW_REQUIRED or REJECT_FIXTURE
failure if stale before phase 0. The tuple does not authorize opening producer
source paths; h2_source_manifest remains a hash/identity artifact only.

## Terminal

Until this reviewed-identity tuple and inequality check are incorporated and
independently reviewed, the runner remains unimplemented and the command remains
NO_COMMAND_AVAILABLE. No fixture, real C8, replay, GPU/Slurm, receipt edit, or
validation-flag change is authorized.

**R84 status: REVISE ONCE / FINAL CODE-H2 SPLIT AUDIT / DESIGN-ONLY.**
Project flags remain new_method_validated=false and novelty_authorization=NONE.
