# R132 C8 pose/convention hygiene innovation audit

Date: 2026-09-24 (Asia/Shanghai)  
Scope: source-only, read-only audit. I inspected the C8 support producer/evaluator, the pinned VMem pipeline, CUT3R/DUSt3R geometry helpers, and existing non-sealed pose/support memos. I did **not** open protected C8/evaluation data, sealed maps, ground truth, predictions, or run any runner.

## Decision

**Primary classification: (a) evaluator/provenance hygiene only.** The static source shows an unbound coordinate-frame boundary between the C8 map renderer and the CPU evaluator. This can explain an invalid or uninterpretable `J` measurement; it does not expose a new geometry-aware mechanism and does not support a method claim.

The numerical meaning of `J` remains **unresolved until a convention-controlled synthetic review passes**. That unresolved measurement must not be promoted to a hidden-surface failure, RCA/BRD evidence, or method novelty. `new_method_validated=false` and `novelty_authorization=NONE` remain unchanged.

## Static evidence

| Source | Verified fact | Consequence |
|---|---|---|
| `work/S130_C8_diagnostics/run_support_retrieval_v2.py:56-66` | Dataset poses are read as raw matrices, stored in `pipe.c2ws`, and passed to scene construction. | The producer boundary receives an untyped pose convention. |
| `modeling/pipeline.py:950-955,975-983` | `get_transformed_c2ws` deep-copies each pose and right-multiplies the camera basis by `D=diag(1,-1,-1,1)` (columns 1 and 2 are negated) before CUT3R. | The CUT3R/surfel map uses a transformed camera convention; the code comment says this is to match the dataset convention but does not declare the source convention or an inverse map for evaluators. |
| `extern/CUT3R/src/dust3r/utils/geometry.py:177-206,209-232` | CUT3R's public camera-depth helper forms `(x,y,z)=((u-cx)z/fx,(v-cy)z/fy,z)` and `depthmap_to_absolute_camera_coordinates` applies a supplied c2w. | CUT3R's helper is OpenCV-style optical geometry; the producer's `D` transform must be bound to an explicit frame contract rather than inferred from a comment. |
| `extern/CUT3R/cloud_opt/dust3r_opt/optimizer.py:251-267` | `get_pts3d` builds camera pointmaps and projects them to world with `geotrf(im_poses, rel_ptmaps)`; `preset_pose` is documented as c2w. | Surfel positions are in the world frame implied by the transformed poses. The evaluator needs the exact map/world-frame relation. |
| `modeling/pipeline.py:272-302` | Surfel rendering inverts the pose (`R^-1`, `-R^-1 t`), culls on positive camera `z`, and projects with the render focal/principal point. | Rendering expects points and the query pose to share the transformed map frame. |
| `run_support_retrieval_v2.py:94-103` | Each map receipt records both `render_c2w_dataset` and `render_c2w_transformed`; maps are rendered with the transformed target pose. | The receipt contains evidence of two pose forms, but no typed declaration of which frame the map points use. |
| `compute_support_masks.py:83-92` | The evaluator back-projects target depth with the raw pose, forms `Xw`, and calls `retrieval_hits(p, maps, ...)` with the **untransformed** target camera point `p`; it does not apply `D` or use `render_c2w_transformed`. | This is a concrete map/evaluator boundary mismatch. If the map frame is the transformed optical frame, the evaluator is querying it with the wrong camera coordinates. |
| `compute_support_masks.py:6-7,32,86-92` | The evaluator declares raw poses as OpenCV x-right/y-down/z-forward and uses the internally self-consistent `p=(Xw-t)R` / `Xw=pR^T+t` algebra. | The B/C physical-support path can be internally consistent while J is not; support fractions cannot repair the missing map-frame contract. |
| `docs/S9_B_CALL_TRACE_REVIEW.md:26` and `work/S130_C8_diagnostics/SUPPORT_AUDIT_ANALYSIS_609623.md` | Prior audit records the fixed Y/Z column flip; the support audit reports low `J`, median own-render depth correlation about 0.190, and ratios in the hundreds, classifying the result as `UNINTERPRETABLE_POSE_CONVENTION`. | Existing evidence independently points to convention/scale/indexing hygiene, not a geometry-method failure. |

A useful algebraic check is: for a raw c2w `T` and native camera point `p`, the transformed pose is `T' = T D`. If the source boundary declares the map camera frame to be `D p`, then the evaluator must project with `p_map = D p`; if it declares a different world-frame conversion, that conversion must be supplied and hashed. The current evaluator performs neither. This statement is a static consequence of the code paths; it is not a claim about which convention the model actually emits.

## Why this is not a method mechanism

The observed low `J` is produced before any hidden-surface predictor or memory method is introduced. A missing/ambiguous frame transform can lower `J`, invert depth signs, or generate large depth ratios even when the map contains the relevant geometry. Conversely, fixing the evaluator could raise `J` without changing the model. Therefore:

* no causal effect on a predictor is identified;
* no geometric completion mechanism is isolated;
* no novelty difference from standard camera-frame conversion, rendering, or scale handling is established;
* a CPU convention correction cannot validate a method or reopen the END-LINE decision.

The strongest competing explanation is ordinary OpenCV/graphics-axis conversion (the `D` transform), compounded by unbound map-frame provenance. A secondary competing explanation is focal/depth scale or image-resize mismatch: rendering uses a surfel focal derived from the model and multiplied by `0.65`, while the evaluator uses the receipt focal and center; depth units and tolerance must still be bound. These explanations are simpler than a hidden-surface mechanism and are sufficient to explain the observed diagnostic symptoms.

## Closest prior-art / comparison boundary

The inspected CUT3R/DUSt3R helpers already implement the standard ingredients: c2w pose application, camera/world inversion, pinhole projection, positive-depth culling, and OpenCV optical axes. The pipeline's Y/Z basis conversion is an engineering convention adapter. A proposal that only adds or repairs this conversion is an evaluator/provenance correction or reproduction of standard camera geometry, not a new geometry-aware memory operator. Any stronger method claim would require an independent mechanism and matched geometric controls after the convention issue is closed.

## CPU-only review protocol if all prerequisites later pass

This is a **design-only** protocol. It may be considered only after an owner-provided, independently reviewed synthetic-only packet contains typed source-boundary H2 evidence, immutable source/boundary hashes, and an accepted review artifact. It must remain CPU-only and must not read real C8 data, sealed maps, ground truth, predictions, or learned weights.

1. **Freeze the frame contract.** Record `frame_label` (`optical_cv` or `vmem_gl`), `pose_name=T_c2w`, direction, exact convention, `D` (if applicable), intrinsics, image size, crop/resize, pixel-center rule, depth units, and formulas for `X_world=T_c2w p_frame` and `p_frame=inv(T_c2w)X_world`. Require measured bidirectional H2 error `<=1e-6`.
2. **Materialize asymmetric synthetic geometry.** Use off-axis planes/cubes at at least three positive metric depths, nonzero normals, and at least three cameras with nonzero rotation and translation. Set `fx != fy`, noncentral principal point, explicit width/height, integer-mm depth storage with exact mm-to-m conversion, nearest-even pixel rounding, and a fixed depth quantization rule.
3. **Use independent implementations.** The forward renderer and CPU evaluator must have separate code roots/manifests and must not share a projection helper. The renderer should generate map-space depth/index/cosine records with camera-keyed provenance.
4. **Compare the source-supported path.** Evaluate the declared path (for example, `T_cv D` plus `D p_cv`, if and only if the source boundary proves that relation) against mandatory controls: raw `T_cv`, inverse pose, missing `D`, and any alternative sign/order. Require only one path to match the synthetic ground-truth records within the frozen pixel/depth tolerances.
5. **Report denominators and diagnostics.** For every camera and depth layer, report attempted points, positive-depth points, in-frame points, ray hits, depth-consistent hits, occlusion decisions, depth-ratio median, correlation, and all failures. Do not drop non-visible or failed points.
6. **Interpretation.** A passing path reclassifies the old `J` result as needing remeasurement under the corrected evaluator; it does not validate a method. A failing or ambiguous path stops before any real-data use.

## Rejection and stop criteria

Reject or stop with the stated terminal status if any of the following occurs:

* owner packet, source/boundary hashes, or typed H2 is missing/stale/ambiguous → `OWNER_REVIEW_REQUIRED` / `H2_UNIDENTIFIABLE`;
* `T_c2w` direction, frame label, `D`, units, crop/resize, principal point, pixel rounding, or positive-depth rule is not frozen → `REJECT_FIXTURE`;
* the independent renderer/evaluator share a projection helper or source identity is not recomputable → `REJECT_FIXTURE`;
* raw, transformed, inverse, or another negative-control path also matches → `REJECT_NON_IDENTIFIABLE`;
* synthetic point/visibility denominator is zero, records are incomplete, or a sign/scale mismatch remains → `UNTESTABLE_NO_DENOMINATOR` or `UNINTERPRETABLE_POSE_CONVENTION`;
* corrected synthetic path passes but the former real-data `J` remains low, depth correlation remains poor, or ratios remain extreme → keep the result uninterpretable and do not reopen method search;
* any request would read protected C8/evaluation data, execute a runner, dispatch GPU/Slurm, mutate receipts/flags, or run S103/S132/GRC before the required gates → hard stop.

## Final status

`POSE_CONVENTION_HYGIENE_ONLY; J_SEMANTICS_UNRESOLVED; NO_METHOD_REOPEN`

The next useful action is a complete owner/H2 synthetic-only packet followed by the fresh readiness audit described above. No GPU experiment or C8 replay is authorized by this audit.
