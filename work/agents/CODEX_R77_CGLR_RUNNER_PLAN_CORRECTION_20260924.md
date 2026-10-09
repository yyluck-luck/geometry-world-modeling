# R77 corrected CGLR synthetic CPU runner plan

Date: 2026-09-24 (Asia/Shanghai)  
Scope: future-only design correction. No runner, fixture, owner artifact, H2 packet, source manifest, protocol manifest, receipt, real C8 input, GPU/Slurm job, or validation flag was created or accessed.

## Status and boundary

R76 returned REVISE on R75. This addendum applies all seven R76 corrections while
preserving the R62 five-phase order, R70 canonical H2 packet, and R72 typed-H2 rules.
Every path and module named below is a **proposed future path** and is currently absent.
The result remains NO_COMMAND_AVAILABLE until the owner supplies real review artifacts
and a separately reviewed implementation.

## Canonical future package (all paths currently absent)

The proposed package remains standard-library-only:

    work/S131_CGLR_contract/runner/cglr_cpu_runner.py
    work/S131_CGLR_contract/runner/schema.py
    work/S131_CGLR_contract/runner/materialize.py
    work/S131_CGLR_contract/runner/h2_gate.py
    work/S131_CGLR_contract/runner/hash_domains.py
    work/S131_CGLR_contract/runner/arm_rules.py
    work/S131_CGLR_contract/runner/receipt.py
    work/S131_CGLR_contract/runner/source_code_manifest.json
    work/S131_CGLR_contract/runner/README.md

The first implementation may not import torch, numpy, a model, a scene loader,
CUDA bindings, a network client, or a subprocess module. Adding any third-party
dependency requires a new source review and a new manifest chain; it is outside
this plan.

## One canonical fixture envelope and owner binding

The future input root contains these required role-bound files, plus only the
numeric JSON/text mask files explicitly referenced by fixture.json:

    input_root/
      fixture.json
      review_artifact.json
      h2_packet.json
      boundary_artifact.json
      protocol_manifest.json

Only fixture.json is the fixture. It must contain:

* schema cglr-episode-v1 and the complete S131 episode fields;
* owner_gate with status OWNER_ACCEPTED, accepted protocol, latest R70 manifest ID
  or the complete R52-to-R70 chain, decision_scope synthetic_cpu_conformance_only,
  review_artifact_sha256, source_code_manifest_sha256, and protocol_manifest_sha256;
* explicit references and lowercase SHA-256 values for h2_packet.json and
  boundary_artifact.json;
* the context, pre-reveal, reveal, future-query, state, event, and ten arm objects;
* the expected-field declarations and supplied hashes required by the R62 contract.

The owner gate must bind the exact fixture subject without a hash cycle. The
canonical fixture subject is the byte-stable fixture JSON with only these
self-referential fields removed from the subject: owner_gate.review_artifact_sha256
and any fixture-subject hash. Expected declarations, supplied hash values, roles,
arms, and protocol references remain in the owner-bound subject so the reviewer
cannot silently change them. review_artifact.json records the resulting
accepted_fixture_subject_sha256 and is itself bound by owner_gate.review_artifact_sha256.
The runner recomputes this subject before reading any scientific role and rejects a
mismatch as OWNER_REVIEW_REQUIRED.

The H2 packet remains a separate phase-2 file. Its reference and hash are supplied
inside fixture.json, but phase 0 excludes only the h2_provenance subtree from generic
marker checks; phase 2 owns all H2 presence, type, marker, direction, identity, and
threshold decisions.

## Complete S131 role and cardinality checks

Phase 0 must require all fields in work/S131_CGLR_contract/episode_schema.json:

* independent_split is true;
* exactly four context_frame_ids;
* exactly one pre_reveal_query_frame_id and one reveal_frame_id;
* at least two future_query_frame_ids, all distinct from reveal and pre-reveal roles;
* frame_sha256 and camera_pose_sha256 objects cover every declared frame;
* intrinsics_sha256 is a lowercase 64-hex hash;
* reveal_mask_path and untouched_mask_path resolve only to numeric JSON/text fixtures
  under input_root and have declared dimensions;
* target_rgb_depth_sealed is true and slot0_rs_canonicalized is true.

Camera IDs, patch IDs, cell IDs, event IDs, arm IDs, and role membership must be
unique and type-checked. Future-query camera IDs and pose/intrinsics metadata are
allowed. Future-query RGB/depth answers, target RGB/depth, scene archives,
checkpoints, learned weights, and any real C8 path are denied by role and suffix,
even if a filename is synthetic-looking. Sealed target fields are booleans or
hash references and are never opened.

## Distinct source and protocol manifest domains

The runner package's source_code_manifest.json is the ordered list of runner/module
paths and their lowercase SHA-256 values. It is shipped beside the future runner,
not copied into input_root. Its canonical hash subject excludes its own supplied
manifest hash field. It is the meaning of R70 h2_provenance.source_manifest_sha256.
fixture.owner_gate.source_code_manifest_sha256 and the H2 source_manifest_sha256
must equal this package manifest subject; a missing or modified package manifest
stops phase 0.

protocol_manifest.json is a separate ordered list of the schema and design IDs
R52, R62, R64, R68, R70, R72, S131, and their pinned SHA-256 values. Its own
supplied hash is excluded from its canonical subject. The two manifests may not
share a path or field name, and a stale or incomplete chain stops phase 0 before
fixture-role reads.

The runner records both manifest identities. H2 source_manifest_sha256 must match
the recomputed package source_code_manifest subject; protocol_manifest_sha256 is
verified against fixture.owner_gate and the contract_manifest hash domain.

## Atomic output and partial receipt semantics

The caller supplies a new output path. Before any input-role read, the runner checks
that the path is absent, regular-parent accessible, and outside input_root. It then
creates it atomically with a launch sentinel and immutable run ID. A race, existing
path, symlink, or parent escape is a boundary failure; the runner never picks a
different path automatically.

The launch record contains runner/source/protocol hashes and the CLI arguments.
Phase-0 owner/schema failures may write only a terminal partial receipt in this
newly-created output directory; they may not write an input or project receipt.
Later phase failures append the corresponding phase record and terminal status.
No output directory is reused or overwritten, and existing project flags and
receipts are never touched.

## Exact phase order and gates

    phase_0_static_preflight
      -> phase_1_materialize
      -> phase_2_H2_gate
      -> phase_3_hash_verification
      -> phase_4_arm_score

### Phase 0: static preflight

Before geometry or hash computation, enforce source/protocol manifest identity,
canonical fixture-subject owner binding, input-role/path allowlist, complete S131
roles, static types, uniqueness, ten-arm mapping, and recursive marker rejection.
The scan rejects angle-bracket values, COMPUTED_*, metadata_only, REQUIRED,
SEE_SECTION, AS_R50, PLACEHOLDER, TODO, descriptive measurement expressions,
non-hex hashes, and uppercase hashes in every supplied non-computed field. It
explicitly skips only the h2_provenance subtree, which phase 2 handles.

Any missing or stale owner artifact is OWNER_REVIEW_REQUIRED. Any schema, path,
marker, role, or arm mismatch is REJECT_FIXTURE. No computed field, H2-dependent
hash, or arm transition occurs.

### Phase 1: computed materialization

Using only JSON/text synthetic fixture values, materialize state_pre_cells,
event_instance, threshold/update budget, world-point projections, R56 rounded-pixel
and quantized-depth visibility records, projected_pixels, visibility_masks,
computed_visibility_sets, and computed_visibility_counts. Computed values are
generated from declared geometry and never copied from expected declarations.
Materialization writes no hash or score. Missing/duplicate/non-finite/wrong-count
or expected-to-computed substitution is REJECT_FIXTURE.

### Phase 2: R70/R72 H2 gate

Read h2_packet.json and boundary_artifact.json only now. Require exact R72 fields:
frame_label, pose_name T_c2w, pose_direction camera_to_world, convention and
formulas, lowercase source/boundary hashes, finite numeric max_abs_error,
error_threshold 0.000001, and status PASS. Recompute forward and inverse
homogeneous errors from the boundary artifact and require the packet value to equal
their maximum and be at most the threshold.

Missing, marker-valued, malformed, direction-conflicting, stale, or above-threshold
H2 is H2_UNIDENTIFIABLE. No fixture-context hash, arm hash, or score follows this
failure.

### Phase 3: complete hash verification

Recompute all nine required domains from explicit canonical path lists:

1. computed.projected_pixels_sha256;
2. computed.visibility_masks_sha256;
3. computed.computed_visibility_sets_sha256;
4. computed.computed_visibility_counts_sha256;
5. contract_manifest_sha256;
6. fixture_context_sha256;
7. base_input_sha256;
8. arm_rule_sha256;
9. arm_input_sha256.

For the nine R62 hash domains only, the excluded-from-all-domains set is explicit:
expected declarations, target truth,
future-camera answers, post-state, post-evidence, rendered output, supplied hash
values, owner review hash, and any terminal metrics. H2 identifiers may enter
fixture_context only after phase 2 PASS. Supplied hashes are never inputs to their
own recomputation; every row records hash name, domain prefix, raw hash, supplied
hash, and equality. All arms for one event share the recomputed base hash and may
differ only in the frozen typed rule hash. Any mismatch is REJECT_FIXTURE.

### Phase 4: synthetic arm score

Only after all previous gates pass, run the closed ten-arm state machine with
computed-only visibility, access-matched inputs, channel-specific denominators,
outside-support conservation, no-reveal identity, and strong-control comparison.
Return REJECT_CONTRACT for invariant/conservation failure,
REJECT_NON_IDENTIFIABLE for a complete strong-control tie,
UNTESTABLE_NO_DENOMINATOR for a zero denominator, and
PASS_CONTRACT_REPLAY only for synthetic contract conformance.

## Enforceable stdlib, audit-hook, and path guards

Before the first input open, the runner installs a closed standard-library import
allowlist and an audit hook. The hook rejects socket/connect, process creation,
dynamic module loading, GPU/device APIs, and every open outside the resolved
input-role or new output-role roots. All paths must be regular non-symlink files
under input_root, with role-specific JSON/text suffixes; absolute paths, traversal,
aliases, and hard-linked external inputs are rejected. The runner records every
successful open.

CLI flags for GPU, Slurm, real C8, replay, model loading, or arbitrary input paths
are rejected. The runner does not launch subprocesses, import numerical/model
packages, or inspect external environment paths. Any denied access attempt aborts
before scientific input read and is recorded as a boundary violation.

## Minimal owner-review deliverable

The first reviewable package must contain, all with real hashes:

1. the source-pinned stdlib runner package and its source_code_manifest.json;
2. protocol_manifest.json and the canonical fixture envelope with all S131 roles,
   ten arms, and no marker/placeholder values;
3. review_artifact.json binding the exact canonical fixture subject;
4. independently reviewed R70/R72 h2_packet.json and boundary_artifact.json;
5. a static review report checking phase order, path/role guards, manifest domains,
   all nine hashes, exclusions, and terminal mapping.

Only after those artifacts are independently accepted may a separate CPU-only
conformance run create a new output directory. Until then, the actionable terminal
remains NO_COMMAND_AVAILABLE. No real C8, replay, GPU/Slurm, learned model, receipt
edit, or validation-flag change is authorized.

## Decision

**R77 status: R75 CORRECTIONS APPLIED / FUTURE-ONLY PLAN / NO EXECUTION.**
All proposed paths remain absent. Project flags remain
new_method_validated=false and novelty_authorization=NONE.
