# R74 synthetic CPU command discovery

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design and command discovery only. No fixture execution, real C8 read, replay, GPU/Slurm submission, receipt mutation, or validation-flag change was performed.

## Decision

**NO SUPPORTED CGLR/R62/R70/R72 RUNNER FOUND; COMMAND NOT AUTHORIZED.**

The repository contains the CGLR episode schema and design contracts, but no executable
runner that implements the R62 phase order, R70 canonical H2 packet, R72 typed-H2 checks,
ten-arm mapping, computed visibility envelope, and PASS_CONTRACT_REPLAY terminal. Supplying
an existing generic synthetic checker as the requested command would be an unsupported
substitution and could silently bypass the owner/H2 gates. The correct R74 result is therefore
NO_COMMAND_AVAILABLE, pending a dedicated runner and owner artifacts.

## Discovery evidence

| Evidence | Finding | Consequence |
|---|---|---|
| work/S131_CGLR_contract/episode_schema.json lines 2-5, 7-35 | Schema is explicitly status=CONTRACT_ONLY, with new_method_validated=false and novelty_authorization=NONE; it defines roles, controls, and pilot cutoffs only. | Schema is not an entry point or runnable fixture. |
| work/S131_CGLR_contract/DESIGN_AND_PREREGISTRATION.md lines 5-7, 98-102 | Directory is a data/evaluation contract; it says no model, Slurm, adapter, or novelty action is performed. CPU-only manifest/geometry checks are allowed in principle. | No command is provided by S131 itself. |
| find work/S131_CGLR_contract -maxdepth 2 -type f | Only DESIGN_AND_PREREGISTRATION.md and episode_schema.json are present. | No local runner/config/fixture JSON exists in the S131 directory. |
| Repository search over Python, shell, JSON, YAML files for CGLR, PASS_CONTRACT_REPLAY, OWNER_ACCEPTED, h2_provenance, synthetic-cpu (excluding design memos) | Only work/S131_CGLR_contract/episode_schema.json contains a CGLR executable-like marker; no Python or shell runner contains the R62/R70/R72 protocol. | There is no exact supported command to report. |
| work/S26_runtime_preflight/preflight.py lines 1-5, 23-28, 228-238 | Existing synthetic CPU1 preflight is an adapter/import guard with hard-coded S26 paths and an unrelated scripts/s26_consumer_baseline.py runner. | Not a CGLR conformance runner; do not invoke for R74. |
| src/retrieval_diagnostic.py lines 1-8, 29-55 | Existing synthetic fixture exercises VMem context selection and surfel retrieval. | It has no CGLR arms, H2 packet, owner gate, or contract replay. |
| work/S82_history_geometry_guidance/check_fusion_synthetic.py lines 1-8 and work/S85_fixed_geometry_warp/check_projector_synthetic.py lines 1-3 | Existing checks are isolated tensor/arithmetic tests. | They cannot establish CGLR information-pathway conformance. |

The R62/R70/R72 documents are design inputs, not executable configs:

* R62 fixes the only legal order as
  phase_0_static_preflight -> phase_1_materialize -> phase_2_H2_gate -> phase_3_hash_verification -> phase_4_arm_score
  (CODEX_R62_R60_TWO_PHASE_OWNER_GATE_CORRECTION_20260924.md lines 10-17), requires
  owner_gate.status=OWNER_ACCEPTED before phase 0 (lines 19-35), and blocks on
  OWNER_REVIEW_REQUIRED, H2_UNIDENTIFIABLE, or REJECT_FIXTURE (lines 121-123).
* R70 defines the canonical T_c2w/camera_to_world H2 fields and latest manifest chain
  (CODEX_R70_R66_R68_CANONICAL_H2_PACKET_CORRECTION_20260924.md lines 22-45, 87-126).
* R72 makes the executable H2 fields numeric and measured, rejects markers/descriptive
  strings, and keeps entry synthetic-only/CPU-only (CODEX_R72_R70_TYPED_H2_TEMPLATE_CORRECTION_20260924.md lines 10-48, 66-94).

No file currently supplies the complete owner-accepted fixture, measured H2 packet,
computed envelope, access-matched arm inputs, or recomputed hash rows required by those
contracts.

## Conditional command shape (intentionally non-runnable)

This is the interface that a future dedicated runner must expose; angle-bracket values are
deliberate blockers, not paths that exist today. It is recorded to prevent a later operator
from confusing a generic checker with the CGLR runner:

    python3 <dedicated-cglr-cpu-runner> \
      --fixture <owner_accepted_synthetic_fixture.json> \
      --h2 <independently_measured_r70_r72_h2_packet.json> \
      --mode synthetic-cpu \
      --require-owner-accepted \
      --require-h2-pass \
      --cpu-only \
      --no-real-c8 \
      --output-dir <new-disposable-output-dir>

R74 did not execute this shape. Until the runner path, fixture path, and H2 path are
materialized and independently reviewed, the actionable command is NO_COMMAND_AVAILABLE.

## Required preconditions before any future command is authorized

1. A dedicated runner exists and is source-pinned; it must implement the R62 five-phase
   order and reject invalid inputs before hashing or arm scoring.
2. The fixture has an independently reviewed owner_gate with exact status=OWNER_ACCEPTED,
   the R70 manifest ID/chain, a recomputed lowercase review hash, and
   decision_scope=synthetic_cpu_conformance_only.
3. The H2 packet passes R72 exactly: canonical T_c2w/camera_to_world labels and formulas,
   lowercase source/boundary hashes, finite numeric measured
   max_abs_error=max(err_forward,err_inverse) <= 1e-6, and status=PASS. Any missing,
   marker-valued, malformed, stale, or direction-conflicting H2 returns
   H2_UNIDENTIFIABLE before H2-dependent hashes or arm scores.
4. Phase 1 materializes computed projected pixels, visibility masks/sets/counts, state,
   event, threshold, and update budget from the fixture; expected declarations are never
   copied into computed fields.
5. All ten arm IDs, transition rules, typed parameters, access-matched base inputs, and
   raw-versus-supplied hash rows pass. Rule parameters contain no event truth, target RGB/D,
   future-camera answer, post-state, or post-hoc metric.
6. The runner proves synthetic-only and CPU-only operation before reading inputs:
   no real C8/scene_13/scene_14 RGB-D, target sensors, learned weights, network, CUDA/GPU,
   Slurm, or existing receipt/flag path may be opened. Outputs must go to a new disposable
   directory and preserve all prior receipts.

## Stop conditions

* Missing runner, fixture, or H2 artifact: NO_COMMAND_AVAILABLE.
* Owner status/hash/protocol/manifest failure: OWNER_REVIEW_REQUIRED.
* Missing, marker, malformed, direction-conflicting, or above-threshold H2: H2_UNIDENTIFIABLE.
* Computed-envelope, arm, access-match, or hash failure: REJECT_FIXTURE (or the more
  specific REJECT_CONTRACT/REJECT_NON_IDENTIFIABLE after the phase-4 rules apply).
* Any real-data, target-sensor, learned-weight, GPU, Slurm, receipt, or flag access attempt:
  abort before input read and report a boundary violation.
* A future PASS_CONTRACT_REPLAY would be synthetic contract conformance only; it cannot
  validate a learned model, establish novelty, or authorize real C8 replay.

**R74 status: COMMAND DISCOVERY COMPLETE / NO SUPPORTED RUNNER / DESIGN-ONLY.**
Project flags remain new_method_validated=false and novelty_authorization=NONE.
