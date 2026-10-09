# R46 pose-convention and DCR audit

Date: 2026-09-24 (Asia/Shanghai)  
Scope: read-only audit of the existing C8 receipt, evaluator, pinned VMem/CUT3R source, and CPU contracts. No GPU, no Slurm submission, and no validation-flag edits.  
Current flags remain: `new_method_validated=false`; `novelty_authorization=NONE`.

## Decision in one paragraph

The low C8 `J` value is currently uninterpretable because the evaluator joins points in the raw dataset camera frame to maps rendered with a y/z-flipped VMem pose. This is a deterministic frame mismatch, independent of model quality. The receipt audit verifies the producer-side transform for all 56 target renders exactly; the CPU algebraic replay gives a maximum point-frame error of `8.88e-16` when the missing flip is restored. `B` and `C` are unaffected because they use only the dataset pose/depth path. A second, upstream hypothesis remains open: the same `T_cv F` pre-flip is passed into CUT3R, whose pointmap code uses OpenCV-style positive-y/positive-z camera coordinates. The source and receipt therefore establish H1 (evaluator join omission) but do not yet prove that H2 (pre-flipping CUT3R's metric pose) is correct. This finding does not rescue RCA or BRD: their current support claim remains closed/unsupported pending a new contract. DCR is defensible only as a convention-controlled **benchmark setting** after the CPU checks below pass; it must not be presented as a method mechanism or as evidence for hidden-surface scarcity.

## Inspected evidence and exact source locations

### C8 receipt and existing interpretation

* `work/S130_C8_diagnostics/remote_support_609623/C8_SUPPORT_RETRIEVAL_RECEIPT.json:1-7` records schema `c8-support-retrieval-v2`, `MAPS_COMPLETE_NO_DIFFUSION`, host `dgx-45`, job `609623`; the receipt contains 14 windows and four target renders per window (`56` maps).
* The same receipt records `retrieval_focal` and `retrieval_size=[512,288]` (for example `:151-158`) and stores both `render_c2w_dataset` and `render_c2w_transformed` for each target (first render begins at `:160-190`).
* `work/S130_C8_diagnostics/remote_support_609623/C8_SUPPORT_MASKS.json:5-18` shows the original window fields. The companion analysis reports `B=0.755--0.984`, high `C`, `J=0--0.092`, and only 3/14 windows passing the preregistered own-render pose check (`work/S130_C8_diagnostics/SUPPORT_AUDIT_ANALYSIS_609623.md:16-35`). Those `J` values must remain labelled `UNINTERPRETABLE_POSE_CONVENTION` until the join is replayed.

### The producer-side convention

* `work/S130_C8_diagnostics/run_support_retrieval_v2.py:35-38` loads RGB, raw dataset c2w, and scene intrinsics; `:94-103` renders each target with `tc=raw c2w`, `transformed=pipe.get_transformed_c2ws(tc)`, focal `0.65 * mean(surfel_Ks)`, and a `512x288` map. The receipt therefore documents which pose was actually used by the renderer.
* `work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:950-955` implements `get_transformed_c2ws` by multiplying c2w rotation columns 1 and 2 by `-1`. In homogeneous notation, `T_g = T_cv F`, with `F=diag(1,-1,-1,1)`.
* `pipeline.py:975-988` passes those transformed c2ws into `run_inference_from_pil`; `pipeline.py:1123-1140` applies the same y/z flip on the conditioning path before inversion and Plücker construction.
* `pipeline.py:274-303` (the renderer body) computes camera coordinates as `R^-1(X-t)`, rejects `z<=0.1`, and projects with positive image y. Thus the map's camera point is the point in the transformed frame, not the raw dataset frame.
* `work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R/surfel_inference.py:174-213` passes supplied poses to `preset_pose` and returns `scene.get_im_poses`; `extern/CUT3R/cloud_opt/dust3r_opt/optimizer.py:102-121` explicitly documents the poses as camera-to-world. `optimizer.py:251-261` converts depth points from camera to world with those poses. There is no source justification for silently treating the input as world-to-camera.
* `work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R/src/dust3r/utils/geometry.py:199-232` unprojects depth as `x=(u-cx)z/f`, `y=(v-cy)z/f`, `z=depth` and applies a cam2world pose. This is evidence for a positive-y/positive-z camera pointmap contract inside CUT3R.
* `work/S102_gate0_3dmatch/adapter_v1/rgbd_scenes_v2.py:227-233` labels `C@F` as “VMem input convention only” and says the original metric optical c2w is kept separately. `work/S103_selector_free_baseline/make_adapter_review_20260917.py:101-104` says the predictor deliberately does not pre-flip because `pipeline.py:1128` flips once in `get_cond`. These files make H2 a source-level candidate: `construct_and_store_scene` may be giving CUT3R a VMem input convention rather than a CUT3R metric convention.

### The evaluator-side join

* `work/S130_C8_diagnostics/compute_support_masks.py:6-8` declares dataset c2w with OpenCV axes `(x right, y down, z forward)` and depth PNG in millimetres; `:24-25` loads c2w and divides depth by `1000`.
* `compute_support_masks.py:27-42` computes B/C using `R^T(X-t)` and the raw dataset depth. These masks do not use VMem's transformed pose.
* `compute_support_masks.py:44-57` treats its argument as a standard pinhole camera point and samples a retrieval map.
* `compute_support_masks.py:81-92` back-projects the target depth into `p_cv`, forms `Xw`, then calls `retrieval_hits(p, maps[t])` and `retrieval_hits(pa, maps[avg_t])` directly. No `F[:3,:3]` is applied before sampling maps rendered with `T_cv F`.
* `DESIGN_AND_PREREGISTRATION.md:121-123` correctly states both conventions and the preregistered pose diagnostic, but it does not state the required point-frame conversion in the evaluator. The omission is the contract gap.

## Exact algebraic finding

Let `T_cv=[R,t]` be the dataset c2w and `p_cv=R^T(X-t)` be a target point in the dataset camera frame. The renderer receives `T_g=T_cv F`; therefore

```text
p_g = (T_cv F)^-1 X = F_3 R^T (X-t) = F_3 p_cv,
F_3 = diag(1,-1,-1).
```

The frozen evaluator supplies `p_cv` to a map whose camera frame is `p_g`. It therefore compares the wrong y and z coordinates and can still obtain a ray/index hit while failing depth agreement. This explains the combination of non-trivial `J_own_ray`, very small `J`, and depth ratios in the hundreds without making any claim about VMem memory.

I replayed this identity over every render record in the local receipt: all `56/56` stored transformed poses equal `T_cv @ F` with maximum absolute pose error `0.0`; for deterministic test points, `inv(T_cv@F) X` equals `F_3 p_cv` with maximum absolute error `8.88e-16`. This is a CPU receipt invariant, not a GPU result and not a corrected C8 score. It establishes H1 relative to the stored maps. It does not decide whether the producer should have used `T_cv` rather than `T_cv F` when constructing CUT3R surfels.

## Upstream H2 warning: CUT3R pose input may be a separate bug

The evaluator omission is the highest-confidence defect in the frozen join, but the source chain has a second risk. CUT3R's depth-to-camera code is OpenCV-like (`geometry.py:199-203`), and its optimizer treats supplied poses as cam2world (`optimizer.py:102-121`, `:251-261`). VMem's `construct_and_store_scene` nevertheless passes `T_cv F` at `pipeline.py:975-983`. The adapter contract calls this multiplication “VMem input convention only” (`rgbd_scenes_v2.py:227-233`) and keeps optical c2w unchanged; the selector-free review explicitly warns against pre-flipping before `get_cond` (`make_adapter_review_20260917.py:101-104`).

The remote stdout contains a related scale/geometry symptom: repeated CUT3R output depths reach the renderer far limit (`work/S130_C8_diagnostics/remote_support_609623/support-609623.out:320`, `:410-412`, `:590`, `:680-682`, `:815-817`), including maxima around `998`, `995`, `535`, and `999`. These lines are diagnostic output, not proof of a pose bug; a renderer far-limit or depth-scale issue can have other causes. H2 therefore requires a CPU synthetic/source replay that compares `T_cv` and `T_cv F` at the CUT3R pointmap boundary before any real-data correction is accepted.

## Candidate transformations and scales (ordered by source support)

| Candidate | Definition | Status and purpose |
|---|---|---|
| Documented frame repair (H1) | Keep renderer `T_cv F`; pass `p_g=F_3 p_cv` and `p_{a,g}=F_3 R_a^T(X-t_a)` to `retrieval_hits`. | Primary CPU replay. Directly implied by the pinned renderer algebra, but it does not validate the upstream CUT3R input. |
| Source-boundary repair (H2) | At the CUT3R boundary, compare leaving optical c2w as `T_cv` versus applying `T_cv F`; keep the VMem `F_3` conversion only in `get_cond`/renderer where source requires it. | CPU synthetic/source replay only. Accept only if CUT3R's own depth/pose identity passes and the convention is documented. |
| Raw identity | Pass `p_cv` as the current evaluator does. | Rejected as a map/evaluator join for C8; retained only as the frozen baseline for the audit diff. |
| Pre-multiply world flip | `F T_cv` (including a world-translation flip). | Algebraic negative control; no source code supports this interpretation. |
| Inverse-pose parse | Treat raw pose as w2c or transpose the supplied rotation. | Negative control; contradicts dataset contract and CUT3R `preset_pose(... cam-to-world)`. |
| Metric depth scale | `d_dataset=d_png/1000`; test renderer/map scale `lambda` only after frame repair. | The current evaluator fixes `/1000`; CUT3R global alignment may leave a metric-scale issue that must be measured, never guessed. |
| Intrinsic/crop alternatives | Receipt focal `0.65*mean(surfel_Ks)`, map centre `(W/2,H/2)`, `512x288`; test only source-recorded crop/principal-point mappings and half-pixel convention. | Secondary diagnostics after frame repair; do not tune on future RGB or `J`. |

## Decisive CPU-only contract

Run a new owner-reviewed CPU replay; do not overwrite the frozen receipt.

1. **Synthetic identity fixture (before real-data selection).** Construct a metric plane/cube, three known c2w cameras, OpenCV axes, depth in metres, and an explicit `K`. Render a point map with the same `R^-1(X-t)` projection. Verify that raw c2w back-projection followed by `F_3` produces the same pixels/depth as the transformed render, including the chosen principal-point and rounding rule. A failure rejects the implementation, not the method.
2. **CUT3R source-boundary fixture (H2).** Run a no-GPU algebraic replay of the CUT3R camera-pointmap and cam2world formulas for both `T_cv` and `T_cv F`; verify which one preserves known metric points and positive-depth ordering. Do not infer the answer from C8 PSNR or `J`. If a real CUT3R stage dump is available, compare own-view depth/pose identity before any map re-score.
3. **Frame replay on all 14 windows.** For every target and averaged target, replay `J_own_ray`, depth correlation, depth ratio, `J_own`, and `J` for H1, H2-consistent maps, and the negative controls. Reuse the already preregistered per-window pose gate (`median own-render depth correlation >=0.5` and median `J_own_ray >=0.20`; `DESIGN_AND_PREREGISTRATION.md:122`) without changing cutoffs. A candidate must pass the gate on held-out windows that failed solely because of the frame join and must not be selected by future PSNR.
4. **Scale check with a held-out split.** On a calibration subset, estimate one positive global `lambda` from own-ray depth ratios only; freeze it, then evaluate the remaining windows. Report the ratio distribution before and after scaling. A scale that varies materially by window/scene, or only works when fitted on the scored target, is a failed common-metric contract.
5. **Depth-unit and intrinsic checks.** Confirm `/1000` from raw PNG metadata/source; compare the recorded `surfel_Ks`, `0.65` focal, centre principal point, map size, resize/crop matrix, and half-pixel choice against the source. Test documented alternatives on the synthetic fixture and then held-out windows. No target RGB may choose a convention.
6. **Uniqueness and provenance.** Record source hashes, pose matrix determinants/orthogonality, transform formula, units, K mapping, and split before scoring. If two transformations remain equally consistent, the real-data convention is unresolved and the DCR result is not interpretable.

## DCR as a benchmark setting (conditional specification)

DCR may be retained as a **measurement protocol**, without importing a method claim, only when the contract above passes. The benchmark should freeze:

* a convention registry: c2w vs w2c, camera axes, depth units, map frame (`F_3` conversion), image resize/crop matrix, principal point, focal convention, rounding/tolerance, and source hashes;
* an append-only reveal schedule: sealed pre-reveal context, delayed RGB-D reveal event, and at least two held-out camera queries; query RGB/depth never chooses the transform, mask, or branch;
* geometry-only support masks and a synthetic identity fixture independent of any learned completion model;
* generic append-only/completion controls and a camera-separated control, so any gain is an estimand of the reveal event under calibrated geometry rather than evidence for a named architecture;
* separate calibration and scoring windows, with preregistered transforms/scales and an immutable receipt for each arm.

The resulting claim is limited to: “under a frozen camera/depth convention, this reveal-conditioned benchmark measures the change in held-out query behavior.” It does not claim RCA, BRD, DCR, or any other mechanism is validated. If the real dataset cannot satisfy the convention contract, DCR can still be reported on the synthetic calibrated fixture; it must not be used to explain C8's VMem panel.

## Rejection and no-go conditions

Reject the real-data DCR contract and stop the mechanism line if any of the following holds:

* the synthetic identity fixture fails, or no source-supported transform passes the frame replay;
* H1 can be repaired algebraically but H2 remains unresolved at the CUT3R pointmap boundary (a corrected evaluator cannot certify an upstream-invalid map);
* no common positive metric scale transfers from calibration to held-out windows, or scale is selected from scored targets/future RGB;
* multiple transforms (raw, flipped, pre-multiplied, inverse) remain equally plausible because source metadata is incomplete;
* pose/depth units, resize/crop, or principal-point semantics cannot be frozen before scoring;
* a corrected result depends on target RGB, future references, post-hoc masks, or a changed evaluator threshold;
* the corrected effect collapses to generic append-only/completion controls, in which case DCR remains descriptive and no mechanism claim survives.

Until these checks pass: do not submit GPU jobs, train an adapter, run S132/future scoring, alter validation flags, reinterpret old `J` as hidden-surface scarcity, or revive RCA/BRD as a method claim. The current safe decision remains `CLOSED_UNSUPPORTED` for RCA/BRD on C8 and `DCR=conditional benchmark only`.

## Files inspected

`work/S130_C8_diagnostics/remote_support_609623/C8_SUPPORT_RETRIEVAL_RECEIPT.json`; `work/S130_C8_diagnostics/remote_support_609623/C8_SUPPORT_MASKS.json`; `work/S130_C8_diagnostics/SUPPORT_AUDIT_ANALYSIS_609623.md`; `work/S130_C8_diagnostics/DESIGN_AND_PREREGISTRATION.md`; `work/S130_C8_diagnostics/compute_support_masks.py`; `work/S130_C8_diagnostics/run_support_retrieval_v2.py`; `work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py`; `work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R/surfel_inference.py`; `work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R/cloud_opt/dust3r_opt/optimizer.py`; `work/S130_C8_diagnostics/S107_pose_receipt.json`; `work/S130_C8_diagnostics/POSE_CONVENTION_AUDIT_609623.md`.
