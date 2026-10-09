# R76 hostile audit of the R75 CGLR runner plan

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only hostile review. No runner, fixture, owner artifact, H2 packet, receipt, real C8 input, GPU/Slurm job, or validation flag was created or accessed.

## Decision

**REVISE BEFORE IMPLEMENTATION.**

R75 correctly preserves the R62 phase order, places the H2 gate before H2-dependent
hashes, keeps the owner gate hard, and rejects real-data/GPU scope. The plan is not yet
owner-review ready because its proposed input layout is inconsistent with R62's
fixture-contained owner gate, its source-manifest names are ambiguous, and several
boundary requirements are stated as intentions rather than enforceable checks. These
are concrete schema and authorization gaps, not reasons to execute a generic runner.

## What passes

1. R75 lines 89-95 reproduce the R62 order exactly:
   static preflight, computed materialization, H2 gate, hash verification, then arm
   score.
2. R75 lines 120-131 keep invalid H2 before all H2-dependent hashes and arm scores.
3. R75 lines 151-157 restrict PASS_CONTRACT_REPLAY to synthetic contract conformance.
4. R75 lines 161-176 explicitly reject scientific inputs, network/GPU/Slurm, and
   mutable outputs.
5. R75 labels all proposed paths as future paths (lines 13-15, 31-46), so it does
   not falsely claim that a runner currently exists.

These parts should be retained.

## Required corrections

### 1. Make the owner gate fixture-contained and define one canonical input envelope

**Finding: MAJOR.** R62 says the fixture must contain owner_gate before phase 0
(CODEX_R62_R60_TWO_PHASE_OWNER_GATE_CORRECTION_20260924.md lines 19-35). R75 instead
lists fixture.json, owner_gate.json, and h2_provenance.json as peer files (lines 58-64)
without declaring which object is the fixture or how the owner gate is bound to it.
An implementation could accept an OWNER_ACCEPTED file that is not the fixture being
scored.

**Exact fix:** change the future layout to one canonical fixture.json containing
owner_gate, protocol/manifest IDs, S131 episode fields, state, event, and ten arms.
Keep review_artifact.json, h2_packet.json, boundary_artifact.json, and
protocol_manifest.json as separately hashed references under the same input root.
Require fixture.owner_gate.review_artifact_sha256 to equal the recomputed
review_artifact.json hash and require the owner gate to bind the exact fixture hash
or canonical fixture subject. H2 may remain a separate phase-2 input, but its reference
and hash must be explicit; phase 0 must exclude only the h2_provenance subtree from
generic marker checks, as required by R64.

### 2. Enforce the complete S131 episode schema without opening sensor data

**Finding: MAJOR.** R75 says schema.py will check types, but never enumerates the
required S131 fields. The schema requires independent_split, four context frames,
pre-reveal/reveal/future-query IDs, frame/camera/intrinsics hashes, reveal and
untouched mask paths, sealed target RGB-D, and slot-0 canonicalization
(episode_schema.json lines 7-21). Omitting these checks permits a fixture that is not
the preregistered episode.

**Exact fix:** phase 0 must require every S131 field and exact role cardinality.
Mask paths may resolve only to numeric JSON/text fixtures under input_root; the
sealed target RGB-D fields remain booleans or hash references and are never opened.
Permit future_query_frame_ids and camera metadata, but reject future-query RGB/depth
answers and target sensor files. Record the role-aware allowlist in the phase-0
receipt.

### 3. Separate code source manifest from run protocol and eliminate self-hash ambiguity

**Finding: MAJOR.** R75 uses source_manifest.json both as a proposed package artifact
(line 46) and as an input-root file (line 63), while R70 uses
source_manifest_sha256 for the H2 packet. The plan does not state whether this hash
covers the runner code, protocol manifest, or itself.

**Exact fix:** define two distinct future artifacts:
source_code_manifest.json for the ordered runner/module hashes, and
protocol_manifest.json for R52/R62/R64/R68/R70/R72 IDs and schema hashes.
The H2 source_manifest_sha256 must bind the reviewed source_code_manifest subject.
Exclude the manifest's own supplied hash field from its canonical subject, and record
the exact file list and canonicalization rules. Phase 0 must reject a stale source
manifest before reading fixture data.

### 4. Make output creation atomic and compatible with preserved partial receipts

**Finding: MODERATE.** R75 says output_root must not exist before launch and also says
an interrupted run leaves a partial receipt (lines 66 and 84-85, 171-172). Without an
explicit creation point, an implementation may create outputs before owner rejection
or overwrite a pre-existing directory.

**Exact fix:** require the caller to supply a new, absent output path. After CLI,
source-code, and path-boundary checks but before phase 0, atomically create the
directory with a launch sentinel and immutable run ID. Never create it before those
checks; never reuse it. On any later failure, write a terminal/partial receipt there
and leave the directory for review. If creation races or the path already exists,
stop with a boundary error and do not choose another path automatically.

### 5. Replace declarative no-data claims with enforceable process guards

**Finding: MAJOR.** R75 says no CUDA, network, subprocess, or model import is
reachable (lines 161-176), but does not state how this is proven before the first
input open. A string scan or CLI flag alone cannot prevent a hidden import or
symlink/path escape.

**Exact fix:** make the initial runner stdlib-only with a closed import allowlist;
reject dynamic imports and subprocess modules. Install an audit hook before any
input-root open to reject sockets, process creation, GPU/device APIs, and paths
outside the allowlist. Resolve and reject symlinks and path traversal, enforce
regular-file type and input-role suffixes, and record every successful open. Treat
any denied access attempt as a pre-read boundary failure. A third-party numerical
dependency is out of scope for this first runner and requires a new owner review.

### 6. Materialize the R62 hash checklist and remove placeholder ambiguity

**Finding: MODERATE.** R75 describes hash categories (lines 133-147) but does not
name every required field from R62 lines 101-113, and its minimal deliverable says
computed-field placeholders are replaced by rules (lines 182-185). A literal marker
could survive into a submitted fixture.

**Exact fix:** list and require recomputation of all nine domains:
computed.projected_pixels_sha256, computed.visibility_masks_sha256,
computed_visibility_sets_sha256, computed_visibility_counts_sha256,
contract_manifest_sha256, fixture_context_sha256, base_input_sha256,
arm_rule_sha256, and arm_input_sha256. Define one explicit excluded-from-all-domains
set containing expected declarations, post-state, post-evidence, target truth,
rendered outputs, supplied hashes, and owner review hash. Reject every placeholder,
angle-bracket value, descriptive measurement string, and TODO before canonicalization
or hashing; do not describe placeholders as an acceptable intermediate artifact.

### 7. Close two remaining scope ambiguities

* R75 allows numerical helpers if their wheel is pinned (lines 48-51). Remove this
  exception from the first deliverable: stdlib-only is the boundary. Any dependency
  requires a separately reviewed package and a new source manifest.
* R75 forbids tokens such as results and receipt paths (lines 167-168) while also
  requiring output receipts and S131 future-query role identifiers. Apply the deny
  list only to input path contents and sensor roles; permit the designated new
  output directory and non-sensitive future-query camera IDs. Reject future-query
  answers and target RGB/depth by role and file type, not by the word future alone.

## Owner-review acceptance criteria after correction

The revised plan is ready for implementation only when it contains:

1. One canonical fixture envelope with owner_gate binding the exact fixture/review
   artifact, plus separate and explicitly hashed H2/boundary artifacts.
2. Complete S131 field/cardinality checks and role-aware synthetic JSON path rules.
3. Distinct source-code and protocol manifests with non-recursive hash domains.
4. Atomic new-output creation and preserved partial-failure receipts.
5. Enforced stdlib-only import/audit/path guards installed before input reads.
6. The complete nine-domain hash table and exhaustive pre-canonicalization marker
   rejection.

Until these corrections are incorporated, the correct terminal remains
NO_COMMAND_AVAILABLE. No fixture or runner should be implemented or executed.

**R76 status: REVISE / HOSTILE AUDIT COMPLETE / DESIGN-ONLY.**
Project flags remain new_method_validated=false and novelty_authorization=NONE.
