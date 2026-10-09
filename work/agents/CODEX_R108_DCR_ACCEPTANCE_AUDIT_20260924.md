# R108 DCR asymmetric-falsifier acceptance audit

Date: 2026-09-24 (Asia/Shanghai)  
Scope: read-only acceptance audit. No fixture execution, no GPU/Slurm, no
protected C8/evaluation reads, and no flag or frozen-contract change.

## Verdict: REVISE once

R107 closes the symmetry and self-consistency gap, but it does not enumerate
the typed producer-boundary H2 fields required by R46/R70/R72. “Run `T_cv F` +
`F_3` and negative controls” is not sufficient to prove which frame the actual
CUT3R pointmap producer emits. A helper-only algebra pass remains insufficient
(`work/agents/CODEX_R70_R66_R68_CANONICAL_H2_PACKET_CORRECTION_20260924.md:47-73`).
The correction below is the final acceptance form; it does not reopen the
method search.

## Exact acceptance fields

### 1. H2/source-boundary object (required before acceptance)

The fixture packet must contain one canonical object with actual values, not
markers:

```text
frame_label ∈ {optical_cv, vmem_gl}
pose_name = T_c2w
pose_direction = camera_to_world
pose_convention = homogeneous_4x4_OpenCV_x_right_y_down_z_forward
source_manifest_sha256 = 64 lowercase hex
boundary_artifact_sha256 = 64 lowercase hex
identity_formula = inv(T_c2w) @ X_world == p_frame
forward_formula = X_world_recomputed = T_c2w @ p_frame
inverse_formula = p_frame_recomputed = inv(T_c2w) @ X_world
max_abs_error = finite measured number
error_threshold = 0.000001
status = PASS
```

The reviewer must recompute forward and inverse homogeneous-vector errors from
the immutable boundary artifact and require
`max_abs_error=max(err_forward,err_inverse)<=error_threshold`. This is the
typed R72 rule (`work/agents/CODEX_R72_R70_TYPED_H2_TEMPLATE_CORRECTION_20260924.md:14-48,50-64`).
Missing, stale, conflicting, descriptive, or marker-valued fields return
`H2_UNIDENTIFIABLE` before any H2-dependent hash or score.

### 2. Asymmetric geometry and convention fields

The R107 fixture must materialize and hash:

* off-axis plane/cube world points at at least three positive metric depths,
  nonzero surface normals, and three nonzero-rotation/nonzero-translation
  cameras;
* `K` with `fx != fy`, noncentral `cx,cy`, explicit width/height, crop/resize
  matrix, and half-pixel convention;
* integer-millimetre depth storage plus the exact conversion to metres;
* nearest-even pixel rounding, `q=1e-6` depth quantization, positive-depth and
  front-facing predicates, and nearest `(z_q,cell_id)` occlusion;
* camera-keyed projected-pixel and visibility records, including non-visible
  predicate records, as required by R56
  (`work/agents/CODEX_R56_R54_ORACLE_FREE_CORRECTION_20260924.md:20-37,120-126`).

The forward renderer and evaluator must have separate code roots/manifests and
must not share a projection helper. The accepted path is `T_cv F` for the map
plus `F_3 p_cv` for evaluator points. Raw `T_cv`, `F T_cv`, and inverse-pose
parses are mandatory negative controls; only the source-supported path may
match.

### 3. Ordering and terminal statuses

Apply the gates in this order: owner acceptance → materialize the asymmetric
computed records → H2 typed/bidirectional gate → hash verification → CPU
identity comparison. Do not open real C8/evaluation data or run a model. This
preserves R46's source-boundary-before-replay requirement
(`work/agents/CODEX_R46_POSE_CONVENTION_DCR_AUDIT_20260924.md:68-77`).

## Explicit stop condition

Return `H2_UNIDENTIFIABLE` and reject DCR immediately if any H2 field is absent
or ambiguous, the bidirectional error exceeds `1e-6`, the source-boundary frame
label conflicts with the pose formulas, depth units/K/crop/rounding cannot be
frozen, the independent implementation hashes are not distinct, or any
negative-control transform also passes. A failed computed visibility or zero
metric denominator is `REJECT_FIXTURE`/`UNTESTABLE_NO_DENOMINATOR` and also
stops before real-data use. These are R46 no-go conditions
(`work/agents/CODEX_R46_POSE_CONVENTION_DCR_AUDIT_20260924.md:91-103`).

## Remaining blocker and scope

R100 still finds the owner/H2/fixture/runner packet absent and
`NO_COMMAND_AVAILABLE` (`work/agents/CODEX_R100_POST_R99_READINESS_RECHECK_20260924.md:8-46`).
Even a future PASS would validate only a convention-controlled DCR benchmark;
it would not reopen END-LINE, assert method novelty, or change
`new_method_validated=false` / `novelty_authorization=NONE`.

