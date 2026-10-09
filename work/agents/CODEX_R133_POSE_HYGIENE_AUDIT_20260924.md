# R133 Pose / Coordinate-Convention Hygiene Audit

**Date:** 2026-09-24  
**Scope:** Source-only audit of the five requested paths. No code was executed, no
protected C8/evaluation data was opened, and no GPU/Slurm/receipt/flag action was
performed.

## Decision

**Classification: UNRESOLVED coordinate-convention hazard (currently an evaluator-hygiene blocker, not a falsifiable method mechanism).**

The inspected evaluator is internally explicit about one convention, and the
pipeline is internally explicit about a boundary transform, but the requested
CUT3R geometry producer source is unavailable at the exact path supplied. Thus
the producer frame and the meaning of its pointmaps/surfel coordinates cannot be
proved equivalent to the evaluator's target-camera frame. A low or changed
support score under this ambiguity cannot support a geometry-method claim.

This is stricter than calling the issue “hygiene only”: the available source does
not yet establish that the transform is correct. It also does not expose a new
information path or a validated method effect. The appropriate state is
`H2_UNIDENTIFIABLE` before any C8 score is interpreted.

## Evidence

1. **Evaluator convention and world/camera algebra.**  
   `work/S130_C8_diagnostics/compute_support_masks.py:6-7` declares dataset
   poses to be camera-to-world with OpenCV axes (x right, y down, z forward), and
   depth PNG values in millimetres. The target depth is back-projected to target
   camera coordinates and lifted with
   `Xw = p R^T + t` at lines 83-88. For bank/context visibility,
   `observed_in` applies `R^T (X-t)`, then pinhole projection and a depth
   consistency tolerance at lines 27-42. This is a coherent c2w/OpenCV contract
   if the input pose files really have that contract.

2. **Retrieval-map assumption is implicit.**  
   `compute_support_masks.py:44-57` projects target-camera points directly into
   a retrieval map using positive z, a standard pinhole, and a centered principal
   point. It applies no explicit convention matrix, no producer-frame tag, and no
   world-to-map calibration. Therefore J is valid only if the map's camera frame
   is already the same frame as `p_cam` (including sign, scale, crop, rounding,
   and depth units).

3. **Runner records both pose forms but does not prove their semantics.**  
   `work/S130_C8_diagnostics/run_support_retrieval_v2.py:56-67` loads the
   dataset pose as c2w, stores it in the pipeline, and builds the surfel scene.
   At lines 94-103 it applies `get_transformed_c2ws` to each target pose before
   rendering, while recording both `render_c2w_dataset` and
   `render_c2w_transformed`. This is useful provenance, but recording two
   matrices is not an identity or producer-frame proof. The runner also says the
   map is shared across arms (lines 68-84); any J shift from a convention mismatch
   would therefore be evaluator/render hygiene, not an arm-specific method
   intervention.

4. **Pipeline has a real boundary transform.**  
   `work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:950-955`
   deep-copies c2w matrices and multiplies rotation columns 1 and 2 by -1
   (`T' = [R F, t]), with `F = diag(1,-1,-1)`). The transformed poses are
   passed to CUT3R inference and to pointmap-to-surfel conversion at lines
   975-1037. The renderer then treats its input as a pose, forms
   `R^{-1}, -R^{-1}t), requires positive camera z, and uses pinhole projection
   at lines 272-302. These operations are compatible only if the CUT3R pointmap
   output is expressed in the corresponding transformed world/camera boundary.

5. **The same boundary is used in model conditioning.**  
   `pipeline.py:1123-1140` flips c2w columns 1 and 2 again before inversion to
   w2c and Plücker construction. Meanwhile retrieval uses transformed poses for
   rendering but untransformed c2w poses for geodesic distance and candidate
   ranking (`pipeline.py:634-667`). That split may be intentional, yet the
   inspected sources contain no producer-side statement establishing which frame
   CUT3R emits for pointmaps, depths, or camera metadata.

6. **Required producer source is unavailable.**  
   The exact requested path
   `extern/CUT3R/src/dust3r/utils/geometry.py` does not exist in the inspected
   workspace. No substitute file was opened. Consequently this audit cannot
   verify the CUT3R H2 producer convention, any internal `T_cvleftrightarrow
   T_cv F` boundary, or whether pointmap z/depth signs are already converted.

7. **Stop-rule alignment.**  
   `work/agents/CODEX_R131_STOP_RULE_CHALLENGE_20260924.md:24-28` says the
   hidden-surface line remains END-LINE while the upstream CUT3R H2 convention is
   unresolved and low J is not model evidence. Lines 41-43 require source/boundary
   provenance, comparison of `T_cv` and `T_cv F`, and finite bidirectional
   identity error `<= 1e-6`; otherwise use `H2_UNIDENTIFIABLE` before scoring.
   Lines 56-63 reject effects that are convention, scale, shuffle, reveal-camera,
   or RGB-only artifacts. The memo keeps
   `new_method_validated=false` and `novelty_authorization=NONE`.

## Review-only CPU protocol (only after future gates pass)

**Protocol P-HYGIENE-CPU, synthetic plane/cube fixture.**

1. Freeze a content-addressed synthetic fixture with a plane and cube, known
   `T_cv`, `F=diag(1,-1,-1)`, intrinsics, image size/crop/rounding, and depth
   units. Do not use target RGB, target depth, or J to choose any transform.
2. Obtain the source-pinned CUT3R producer output for the same fixture and test
   both hypotheses: producer boundary `T_cv) and `T_cv F`. Reproject points
   in both directions and report finite bidirectional identity error. If either
   hypothesis is not finite and <= 1e-6, stop with `H2_UNIDENTIFIABLE`.
3. With the transform fixed, run CPU-only map algebra on the synthetic surfels:
   (a) consistently transformed render/evaluator pair, (b) untransformed
   dataset-pose control, and (c) one-sided/wrong-convention control. Keep a
   fixed denominator and report ray-hit, depth-ratio, pixel-rounding, and
   positive-z rates. This isolates evaluator hygiene before any model score.
4. Only if (1)-(3) pass, use a frozen source-pinned event table for reveal versus
   third-camera evaluation with no-reveal, wrong-component, shuffled/no-transport,
   append-only, generic, and robust-gate controls. Repeat across held-out
   cameras/scenes/horizons. This is a review protocol, not authorization to
   execute the historical C8 runner.

## Competing explanation

An apparent low J, depth-ratio shift, or arm difference can be explained by a
frame mismatch at the CUT3R/VMem boundary: applying `F` on one side only,
using positive-z checks in the wrong frame, or comparing transformed-map
coordinates against untransformed target-camera points. Other evaluator-level
confounders visible in the sources are centered-principal-point projection
(`compute_support_masks.py:44-57`), the runner's resized/cropped RGB path
(`run_support_retrieval_v2.py:35-38`), focal scaling by 0.65
(`run_support_retrieval_v2.py:91-103`), and depth/pixel rounding. These can
change J without any geometry-aware state transition, selective update, or
future-information pathway.

## Rejection criteria

Reject a pose/convention explanation as a method mechanism when any of the
following holds:

- The plane/cube identity fixture fails, is non-finite, exceeds 1e-6, or leaves
  the producer frame ambiguous; mark `H2_UNIDENTIFIABLE` and do not score.
- A consistent transform removes the apparent effect, or the wrong-convention
  control reproduces it.
- Generic, append-only, mask-only, residual-untyped, shuffled/no-transport, or
  robust-gate controls tie or win.
- The effect is reveal-camera-only, depends on scale/crop/support artifacts,
  leaks target/future information, changes RGB without held-out geometry, lacks a
  fixed denominator, or fails across held-out cameras/scenes/horizons.
- Evidence consists only of source comments, a model load, context-list
  differences, or a low J. Those are provenance/diagnostic observations and do
  not establish a mechanism.

**Audit ruling:** keep END-LINE, `NO_REOPEN`, `new_method_validated=false`,
and `novelty_authorization=NONE`. No method claim is reopened by this
source-only audit.

