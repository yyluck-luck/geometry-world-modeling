# R67 hostile audit of the R66 H2/owner-readiness checklist

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only audit. No provenance is fabricated and no fixture, real C8 data, replay, GPU/Slurm job, receipt, or validation flag is executed or changed.

## Verdict

**REVISE once.** R66 is otherwise conservative about authorization, source hashes, reviewer evidence, and synthetic-only scope. One concrete identity-direction mismatch remains in the H2 checklist: the declared formula and the CPU recomputation use incompatible transform directions.

## Finding: camera/world transform direction is inconsistent

R66 declares the H2 field:

```text
identity_formula = inv(T_frame) @ X == p_frame
```

and describes `T_frame/c2w` as an exact camera-to-world matrix. Under that convention, `X` is a world point and `p_frame` is a camera-frame point. The forward world-point reconstruction must be:

```text
X_world = T_c2w @ p_frame
```

with homogeneous coordinates. The inverse check is:

```text
p_frame = inv(T_c2w) @ X_world
```

R66 §4 instead instructs the reviewer to compute:

```text
X_world_recomputed = inv(T_frame) @ p_frame
```

That treats `T_frame` as world-to-camera and contradicts both the `c2w` label and the declared identity formula. A reviewer could therefore pass an inverse convention while the producer boundary uses the opposite convention.

## One minimal correction

Use one notation and record the matrix direction explicitly in the boundary artifact. Replace the R66 identity block with:

```json
{
  "pose_name": "T_c2w",
  "pose_direction": "camera_to_world",
  "identity_formula": "inv(T_c2w) @ X_world == p_frame",
  "forward_check": "X_world_recomputed = T_c2w @ p_frame",
  "inverse_check": "p_frame_recomputed = inv(T_c2w) @ X_world"
}
```

The independent reviewer must run both checks using homogeneous 4-vectors, record the exact matrix and vectors, and require both maximum absolute errors to be at most `1e-6`:

```text
X_world_recomputed  = T_c2w @ [p_frame; 1]
p_frame_recomputed  = inv(T_c2w) @ [X_world; 1]
err_forward = max(abs(X_world_recomputed - [X_world; 1]))
err_inverse = max(abs(p_frame_recomputed - [p_frame; 1]))
```

The H2 object should set `max_abs_error = max(err_forward, err_inverse)`. A producer that genuinely exposes a world-to-camera matrix must instead record `pose_direction=world_to_camera` and use the explicitly inverted formulas; it may not rely on the ambiguous name `T_frame`.

## Audit items that pass

* **Authorization:** R66 scopes `OWNER_ACCEPTED` to synthetic CPU conformance and explicitly excludes C8 replay, novelty, GPU/Slurm, receipts, and flags.
* **Source identity:** required paths, byte hashes, immutable source identifiers, and line references are concrete and independently recomputable.
* **Boundary evidence:** the artifact requires frame labels, matrix convention, point units, operation direction, per-coordinate errors, and a reviewer decision. The transform-direction correction above makes it internally consistent.
* **Leakage control:** R66 forbids target RGB/depth, future camera answers, learned weights, and real-data claims; it keeps scene_13/scene_14 out of independent evidence.
* **CPU entry gate:** owner artifact, H2 PASS, computed-only visibility, all hash equality, ten-arm mapping, deterministic CPU scope, and immutable output/input snapshots are all required before scoring.

## Stop conditions

Until the transform-direction correction is applied, do not accept H2 or start the synthetic CPU run. After correction:

* missing/ambiguous/failed H2 remains `H2_UNIDENTIFIABLE`;
* source/boundary hash or checklist schema failure remains `REJECT_FIXTURE`;
* owner authorization remains `OWNER_REVIEW_REQUIRED` until an actual review artifact is supplied;
* no real C8, replay, GPU/Slurm, receipt, or validation-flag action is unlocked.

## Decision

**R67: REVISE once.** Fix the `c2w`/world-to-camera direction mismatch in the H2 checklist, then the readiness packet is suitable for independent owner review. No provenance or reviewer value was fabricated in this audit.
