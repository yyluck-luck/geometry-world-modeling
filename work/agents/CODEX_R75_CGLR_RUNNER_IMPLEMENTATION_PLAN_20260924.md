# R75 CGLR synthetic CPU runner implementation plan

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only. This plan does not create the runner, fixture, owner artifact, H2 packet, receipt, or output directory. No fixture, real C8 data, GPU/Slurm job, or validation flag was accessed.

## Decision inherited from R74

R74 found no supported CGLR/R62/R70/R72 executable runner or fixture and recorded
NO_COMMAND_AVAILABLE. The existing S131 files are a CONTRACT_ONLY schema and design
document, not an entry point. The S26, S82, and S85 synthetic scripts are unrelated
checks and remain unendorsed.

This plan therefore specifies what must be source-pinned and reviewed before a command
can exist. The paths below are **proposed future paths**; they do not exist as a result
of R75 and must not be treated as available commands.

Evidence boundary:

* S131 schema: work/S131_CGLR_contract/episode_schema.json lines 2-5 and 7-35.
* S131 authorization boundary: work/S131_CGLR_contract/DESIGN_AND_PREREGISTRATION.md
  lines 5-7 and 98-102.
* R62 phase order and hard owner gate:
  work/agents/CODEX_R62_R60_TWO_PHASE_OWNER_GATE_CORRECTION_20260924.md lines 10-35.
* R70 canonical H2 and manifest chain:
  work/agents/CODEX_R70_R66_R68_CANONICAL_H2_PACKET_CORRECTION_20260924.md lines 22-45
  and 87-126.
* R72 typed H2 checks and CPU entry conditions:
  work/agents/CODEX_R72_R70_TYPED_H2_TEMPLATE_CORRECTION_20260924.md lines 10-48
  and 66-94.

## Proposed source-pinned package

The first implementation should be a small standard-library runner under a new,
dedicated package directory. Every item is proposed and currently absent.

| Proposed path | Responsibility | Source pin/review requirement |
|---|---|---|
| work/S131_CGLR_contract/runner/cglr_cpu_runner.py | CLI, phase orchestration, terminal status, and fail-closed process boundary. | SHA-256 recorded in the source manifest; no implicit current-working-directory inputs. |
| work/S131_CGLR_contract/runner/schema.py | Closed schema/type checks for owner gate, event table, ten arm rules, state, and input path allowlist. | Schema version and R62/R70/R72 IDs are constants; no free-form rule names. |
| work/S131_CGLR_contract/runner/materialize.py | Deterministic synthetic state, event expansion, projection, visibility_v2 masks/sets/counts, threshold, and update budget. | Pure functions over JSON fixture values; expected fields are never read as computed values. |
| work/S131_CGLR_contract/runner/h2_gate.py | R70/R72 canonical T_c2w packet validation and independent forward/inverse error check. | Exact formulas, numeric finite fields, lowercase hash regex, and error threshold are source-pinned. |
| work/S131_CGLR_contract/runner/hash_domains.py | Canonical serialization and recomputation of every R62 hash subject. | Domain path lists are explicit; supplied hashes are never hash inputs; no recursive self-hash. |
| work/S131_CGLR_contract/runner/arm_rules.py | Closed ten-arm mapping and deterministic state transitions. | Typed parameters and arm identifiers are a frozen table; event truth and target truth are rejected. |
| work/S131_CGLR_contract/runner/receipt.py | New-output-only phase records, raw-versus-supplied hash rows, source/input identities, and terminal receipt. | Refuses an existing output directory and records runner/module hashes before phase 0. |
| work/S131_CGLR_contract/runner/README.md | Reviewable interface, input/output layout, command syntax, and terminal meanings. | Must state synthetic CPU conformance only; no learned-model or novelty claim. |
| work/S131_CGLR_contract/runner/source_manifest.json | Ordered source paths, SHA-256 values, protocol IDs, and package version. | Generated only after independent review; a stale or incomplete chain blocks phase 0. |

The package should import only Python standard-library modules for the conformance
runner. Numerical helpers may be added only if their exact wheel/version and CPU
device behavior are pinned in the source manifest; importing a model, CUDA, network,
or scene loader is a hard failure.

## Immutable input and output layout

The runner must accept one explicit input root and one output root. The following is a
future layout contract, not a claim that these files exist:

    input_root/
      fixture.json
      owner_gate.json
      h2_provenance.json
      boundary_artifact.json
      source_manifest.json
      protocol_manifest.json

    output_root/                 # must not exist before launch
      phase_0_static_preflight.json
      phase_1_computed_envelope.json
      phase_2_h2_gate.json
      phase_3_hash_verification.json
      phase_4_arm_score.json
      terminal_receipt.json

Input rules:

1. Resolve every path beneath input_root; reject absolute paths, symlinks, path
   traversal, duplicate aliases, and files outside the allowlist.
2. Accept JSON and small text identity artifacts only. Do not accept RGB, depth,
   NPZ, checkpoint, scene archive, target sensor, or learned-weight paths.
3. Read every input as bytes once, hash it, and retain the byte hash in the phase-0
   record. Do not mutate or rewrite any input.
4. Treat fixture expected values and post-state/output fields as excluded from all
   base-input and arm-rule hash subjects.
5. Require output_root to be new and disposable; never overwrite an existing receipt,
   flag file, source file, or prior run.

## Phase boundaries and terminal behavior

The implementation must preserve the R62 order exactly:

    phase_0_static_preflight
      -> phase_1_materialize
      -> phase_2_H2_gate
      -> phase_3_hash_verification
      -> phase_4_arm_score

### Phase 0: static preflight

Perform no geometry, H2-dependent hashing, or arm transition. Check source-manifest
identity, protocol/manifest IDs, path allowlist, static types, uniqueness, forbidden
markers, owner status, and the complete ten-arm identifier/rule mapping. The owner
object must have status=OWNER_ACCEPTED, an independently recomputable review hash,
the R70 manifest ID or full ordered chain, and synthetic_cpu_conformance_only scope.

Any missing/stale/malformed owner authorization stops with OWNER_REVIEW_REQUIRED.
Any schema, marker, path, or arm-rule violation stops with REJECT_FIXTURE.

### Phase 1: computed materialization

Build only from declared synthetic fixture inputs: state_pre_cells, event_instance,
threshold/update budget, world-point projections, rounded-pixel and quantized-depth
visibility records, projected_pixels, visibility_masks, computed_visibility_sets, and
computed_visibility_counts. Expected visibility declarations may be compared later,
but never copied into computed fields. Materialization writes a phase record but no
hash or score.

Any missing field, duplicate cell, non-finite value, wrong count, or expected-field
substitution stops with REJECT_FIXTURE.

### Phase 2: H2 gate

Validate the R72 packet only after phase 1 and before H2-dependent hash extraction:
frame label, pose_name=T_c2w, pose_direction=camera_to_world, exact convention and
formulas, lowercase source/boundary hashes, finite numeric max_abs_error, numeric
error_threshold=1e-6, and status=PASS. Recompute the forward and inverse homogeneous
errors from the immutable boundary artifact and require their maximum to equal the
packet value within serialization tolerance.

Missing, marker-valued, malformed, stale, direction-conflicting, or above-threshold
H2 stops with H2_UNIDENTIFIABLE. No fixture-context hash, arm hash, or arm score may
be produced after this failure.

### Phase 3: hash verification

Recompute and record raw-versus-supplied rows for:

* computed projected pixels, visibility masks, visibility sets, and visibility counts;
* contract manifest;
* fixture context;
* shared base input per event;
* arm rule per arm;
* arm input as the canonical recomputed base/rule pair.

All arms for one event must share the same recomputed base hash. Only typed rule
subjects may differ. Supplied values are compared, never used recursively. Any
missing, non-hex, uppercase, unequal, or self-referential hash stops with
REJECT_FIXTURE.

### Phase 4: arm score

Only after all prior gates pass, run the closed ten-arm state machine on synthetic
values. Apply computed-only visibility, access-matched inputs, channel-specific
denominators, conservation/outside-support checks, no-reveal identity, and
strong-control comparison. Return REJECT_CONTRACT for invariant/conservation failures,
REJECT_NON_IDENTIFIABLE for a complete strong-control signature tie, and
UNTESTABLE_NO_DENOMINATOR for zero denominators. PASS_CONTRACT_REPLAY is allowed only
as synthetic contract conformance; it cannot validate a learned model or novelty.

## CPU and no-data safeguards

The runner must fail before opening any scientific input if any of these checks fail:

* process device is CPU and no CUDA, GPU, Slurm, network, subprocess, or model import
  is reachable;
* all environment and CLI switches are synthetic-only; reject GPU/Slurm/real-C8 flags;
* every path is within the declared input root and has an allowed JSON/text role;
* forbidden tokens and roles include real C8, scene_13, scene_14, RGB, depth, target,
  future-query answer, checkpoint, learned weight, results, and receipt paths;
* the source manifest, fixture, owner gate, H2 packet, and protocol manifest are
  immutable during the run;
* output_root is new, and an interrupted run leaves its partial receipt for review
  rather than retrying in place.

The runner should expose an audit record proving which allowed files were opened and
that no denied path, network, GPU, or child process was touched. This record is a
boundary check, not scientific evidence.

## Minimal reviewable deliverable

Before any command is authorized, an owner-review package should contain:

1. The source-pinned runner package above, with a complete source_manifest.json.
2. A schema-only synthetic fixture and protocol manifest with all ten arm mappings,
   computed-field placeholders replaced by deterministic materialization rules, and
   no RGB/depth/checkpoint paths.
3. An independently reviewed R70/R72 H2 packet and immutable boundary artifact; no
   descriptive strings or marker values remain.
4. A static reviewer report showing the five-phase order, path allowlist, domain
   exclusions, hash recomputation, and stop-code mapping.
5. A separate CPU-only conformance test receipt produced in a new output directory
   only after owner acceptance and H2 PASS. That receipt must be linked by SHA-256
   and must leave project flags, real C8 receipts, and validation state unchanged.

Until all five items exist, the command remains NO_COMMAND_AVAILABLE. The first
reviewable implementation should be source/contract review only; it must not include
real-data access, a learned-model import, a replay, or a GPU dispatch.

## Stop conditions and unresolved blockers

* No source-pinned runner or incomplete source manifest: stop before phase 0.
* Missing OWNER_ACCEPTED review: OWNER_REVIEW_REQUIRED.
* Missing or invalid R72 H2 evidence: H2_UNIDENTIFIABLE.
* Any scientific-data path, output overwrite, network/GPU/Slurm access, or mutable input:
  abort as a boundary violation.
* Any computed/expected leakage, arm mismatch, access mismatch, or hash discrepancy:
  REJECT_FIXTURE or REJECT_CONTRACT as specified above.

**R75 status: IMPLEMENTATION PLAN COMPLETE / DESIGN-ONLY.**
No runner was implemented or executed. Project flags remain
new_method_validated=false and novelty_authorization=NONE.
