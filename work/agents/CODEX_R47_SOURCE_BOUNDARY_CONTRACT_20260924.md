# R47 source-boundary CPU contract for C8 H1/H2

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only, read-only contract. This document converts the R46 findings into a small owner-reviewable CPU test. It does not run a real-data re-score, edit a frozen receipt, submit Slurm/GPU work, or change new_method_validated=false / novelty_authorization=NONE.

## 1. Question and decision boundary

The contract answers one infrastructure question before any corrected C8 or DCR claim:

> Which camera frame is used at (H1) the retrieval-map query and (H2) the CUT3R pointmap boundary, and is one metric depth scale transferable from calibration to held-out windows?

It does not test a geometry-completion method. A pass permits a separately reviewed convention-consistent benchmark replay. A fail leaves C8 J as UNINTERPRETABLE_POSE_CONVENTION and leaves RCA/BRD closed on the current panel.

### H1: evaluator query-frame omission

The frozen producer renders with T_g = T_cv F, where F=diag(1,-1,-1,1). The frozen CPU evaluator projects target points as p_cv and sends them directly to retrieval_hits. The source-supported repair is

    p_cv = R_cv^T (X - t_cv)
    p_g  = F3 p_cv,       F3 = diag(1,-1,-1)

and the same conversion must be applied to the averaged-target query. This is the exact join defect established in R46. It does not prove that T_cv F was the correct pose to give CUT3R.

### H2: CUT3R source-boundary ambiguity

CUT3R's depth-to-camera code uses x=(u-cx)z/f, y=(v-cy)z/f, z=depth and applies a cam2world pose. The current VMem scene builder passes T_cv F into CUT3R before scene alignment. H2 is therefore tested by a source-boundary fixture, not by choosing the candidate with the best C8 score:

    P0 (optical hypothesis): CUT3R receives T_cv.
    P1 (current VMem path): CUT3R receives T_cv F.

The fixture must identify which hypothesis preserves a known metric world point under CUT3R's own formulas. If both remain plausible, the real-data convention is unresolved.

## 2. Exact source and receipt anchors

The owner review must use the following immutable paths and line ranges:

| Role | Path and lines | Contract fact |
|---|---|---|
| Frozen C8 producer | work/S130_C8_diagnostics/run_support_retrieval_v2.py:35-38, 94-103 | Loads raw c2w; calls get_transformed_c2ws; renders 512x288 maps with 0.65*mean(surfel_Ks) focal; saves both pose forms. |
| VMem pose transform | work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:950-955 | get_transformed_c2ws right-multiplies c2w columns 1/2 by -1, i.e. T_cv F. |
| VMem renderer | pipeline.py:265-303 | Uses R^-1(X-t), positive camera y projection, z near/far planes. |
| VMem conditioning | pipeline.py:1123-1140 | Applies the y/z flip in get_cond before inversion and Plucker coordinates. |
| Frozen evaluator | work/S130_C8_diagnostics/compute_support_masks.py:24-25, 44-57, 81-100 | Loads depth /1000, builds OpenCV p_cv, and currently queries maps without F3. |
| CUT3R geometry | work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R/src/dust3r/utils/geometry.py:199-232 | Unprojects positive-y/positive-z camera points and maps them with cam2world. |
| CUT3R optimizer | .../extern/CUT3R/cloud_opt/dust3r_opt/optimizer.py:102-121, 251-261 | preset_pose is cam2world; depth points are transformed by geotrf(im_poses, rel_ptmaps). |
| Adapter convention note | work/S102_gate0_3dmatch/adapter_v1/rgbd_scenes_v2.py:205-233 | C@F is labelled “VMem input convention only”; optical c2w is retained separately. |
| Existing predictor review | work/S103_selector_free_baseline/make_adapter_review_20260917.py:101-104 | Pre-flipping is deliberately avoided because get_cond flips once. |
| Frozen receipt | work/S130_C8_diagnostics/remote_support_609623/C8_SUPPORT_RETRIEVAL_RECEIPT.json | Receipt and maps are read-only inputs; do not rewrite. |
| Prior diagnosis | work/agents/CODEX_R46_POSE_CONVENTION_DCR_AUDIT_20260924.md | H1/H2 rationale, no-go conditions, and R46 CPU identity check. |

The owner should hash these files before any future execution and place hashes in a new R47 receipt. No hash or receipt in remote_support_609623/ may be replaced.

## 3. Command-discovery step (required, but no execution in R47)

R47 only discovers the command surface. The owner must record the output of the following read-only queries before authorizing a future contract run:

    rg -n "compute_support_masks|run_support_retrieval_v2|support_audit_v2\\.slurm|C8_SUPPORT_MASKS|C8_SUPPORT_RETRIEVAL" work/S130_C8_diagnostics scripts
    sed -n '1,125p' work/S130_C8_diagnostics/compute_support_masks.py
    sed -n '1,120p' work/S130_C8_diagnostics/support_audit_v2.slurm

The discovery record must state:

1. the future CPU-only contract script path (it does not exist as part of R47 unless an owner adds it later);
2. the frozen receipt input and a new output directory outside remote_support_609623/;
3. dataset, source, and map paths, with no target RGB mounted into any producer process;
4. whether the command is fixture-only, source-boundary-only, or an owner-approved held-out replay.

There is no sbatch, srun, apptainer --nv, model load, or real-data re-score command in this cycle. A command that writes C8_SUPPORT_MASKS.json, C8_SUPPORT_RETRIEVAL_RECEIPT.json, or any frozen map is automatically rejected.

## 4. Synthetic fixture (mandatory first stage)

The fixture runs entirely in NumPy or equivalent CPU arithmetic and writes a new, self-contained receipt. It must contain:

* three proper c2w cameras with non-collinear translations and at least one non-identity rotation;
* an explicit OpenCV optical convention (x right, y down, z forward), metric depth in metres, K=[[300,0,320],[0,300,240],[0,0,1]], and a declared 640x480 source image;
* a non-degenerate plane plus cube points, including positive and negative image-y coordinates, so an unnoticed y/z flip cannot pass accidentally;
* a retrieval map size of 512x288, centre principal point, focal 0.65*f, and the exact nearest-pixel rule (round, Euclidean distance <=1.5) used by compute_support_masks.py;
* explicit tests for a half-pixel principal-point alternative and for a known depth unit conversion.

The fixture verifies:

1. Xw = T_cv p_cv and inv(T_cv F) Xw = F3 p_cv to absolute error <=1e-6;
2. H1 raw query (p_cv) fails the transformed-map identity on deliberately asymmetric points, while H1 repaired query (F3 p_cv) passes;
3. CUT3R's depthmap_to_camera_coordinates plus geotrf recovers the known world points under the optical pose hypothesis P0; the P1 pre-flip is reported as a separate, expected counterexample unless an independently declared input frame makes it valid;
4. all positive-depth, in-bounds fixture points appear in the declared denominator, with no hidden selection by RGB or future camera.

If the fixture cannot distinguish H1, or if its source-boundary labels are not explicit, stop before using a real receipt.

## 5. Candidate set and controls

The candidate set is fixed before seeing any held-out result:

| ID | Candidate | Use |
|---|---|---|
| H1-raw | Query map with p_cv | Frozen evaluator baseline; expected frame-mismatch negative control. |
| H1-F | Query map with F3@p_cv and F3@pa_cv | Documented VMem-render-frame repair. |
| H1-pre | Pre-multiply world pose F@T_cv | Algebraic negative control; not source-supported. |
| H1-inv | Treat raw pose as w2c / use inverse rotation | Convention negative control; contradicts the c2w contracts. |
| H2-P0 | CUT3R pointmap receives T_cv | Optical/CUT3R geometry hypothesis. |
| H2-P1 | CUT3R pointmap receives T_cv F | Current VMem scene-builder path. |
| Unit-1 | Renderer depth in declared metres | Primary scale candidate. |
| Unit-1e3 / Unit-1e-3 | Multiply renderer depth by 1e3 or 1e-3 | Unit controls only; no post-hoc choice. |
| K-source | Recorded 0.65*mean(surfel_Ks), map centre | Primary intrinsic contract. |
| K-half / K-resize | Half-pixel or explicit resize/crop alternatives | Intrinsic controls; selected only by source fixture. |

No additional transform, learned alignment, per-window correction, target-RGB registration, or future-view fitting may be introduced after seeing scores.

## 6. Calibration and held-out split

The contract has a scene-level split to prevent adjacent-frame leakage:

This is a calibration/held-out **analysis split within the already exposed C8
development panel**. `scene_14` must not be called project-blind, model-unseen, or
independent held-out data; the split only prevents fitting the contract on the same
scene windows that are later scored.

* Calibration: all seven frozen scene_13 windows (w0050, w0100, w0150, w0200, w0250, w0300, w0350). Use only own-ray pairs and the synthetic/source-boundary receipt to freeze H1/H2, depth scale, and intrinsic convention.
* Held-out: all seven frozen scene_14 windows with the same starts. Apply the frozen choice without refitting. Do not aggregate pixels from held-out windows into calibration.

The owner may reverse the scene order only before seeing any corrected score, and must record the choice plus source hash. If no split choice is recorded before execution, the contract is UNTESTABLE.

## 7. Scale estimator and transfer rule

For a frozen candidate, let z_i be the projected metric target depth and r_i the finite renderer depth at a valid own-ray pixel after H1 frame conversion. On calibration only, estimate one scene-level scalar:

    lambda = median_i (r_i / z_i),   over r_i>0, z_i>0 and valid own-ray pixels.

Do not estimate one scalar per window, target, pixel, or future camera. If the calibration denominator is empty, non-finite, or non-positive, mark UNTESTABLE_SCALE. On held-out data, apply the frozen lambda and report r_i/(lambda*z_i) without refitting. The existing depth tolerance remains binding:

    TOL(z) = max(0.05, 0.05*z)

Transfer is judged with the already frozen depth predicate, not a new ratio cutoff: after applying the calibration lambda, report the fraction of held-out own-ray pairs satisfying |r_i/lambda-z_i| <= TOL(z_i), together with the preregistered own-render correlation >=0.5 and J_own_ray>=0.20. These are diagnostics of registration, not a method success threshold. A window with fewer than 11 valid own-ray pairs has undefined correlation and is UNTESTABLE, matching the current script's >10 requirement. If the frozen lambda cannot produce a finite, depth-consistent held-out distribution under this existing predicate, reject the common-metric contract. The median ratio is reported descriptively and is not used to select a transform.

## 8. Denominators and reporting

Denominators are frozen and must be reported explicitly:

* Target pixel universe: each target depth PNG, rows all, columns [80,560) at stride 2 (compute_support_masks.py:17, 83-85), after excluding depth<=0. Call its size N_eval(t).
* Ray denominator: N_eval(t). J_own_ray is the count of pixels with positive render z, in-map projection, nearest distance <=1.5, valid surfel index, and finite renderer depth, divided by N_eval(t).
* Depth-hit denominator: N_eval(t). J_own, averaged-target J, and J_cos add the frozen depth tolerance (and cosine condition for J_cos) to the ray predicate; do not divide by N_ray.
* Correlation denominator: only valid own-ray pairs; if count <=10, report UNTESTABLE_CORRELATION, never zero.
* Window aggregation: arithmetic mean of the four target-frame fractions, preserving per-target values. Do not pool pixels across windows or reweight by valid depth counts.
* Scale denominator: all finite positive own-ray pairs in calibration; report count, median, and robust spread. Held-out uses the frozen calibration scalar and reports the same quantities.
* Synthetic denominator: all fixture points that are positive-depth and in bounds under the declared camera/map convention; report counts before and after each control.

## 9. Stop and rejection criteria

Stop the contract and label the result UNTESTABLE_* or REJECTED_CONVENTION when any of these occurs:

1. the synthetic identity or CUT3R source-boundary fixture fails;
2. H1-F fixes the evaluator algebra but H2-P0/P1 cannot be decided from source formulas and the independent fixture;
3. more than one candidate remains equally valid after the fixture and calibration source checks;
4. calibration has no finite positive scale denominator, or one frozen scale fails any held-out window's ratio/pose gate;
5. a scale, transform, K mapping, or tolerance is selected using held-out depth/RGB/PSNR or future-camera output;
6. target RGB, target depth, or future poses enter the producer/fixture used to choose a candidate; target depth may enter only the separate declared CPU scoring stage;
7. a receipt, map, validation flag, or source file is mutated, or a command submits GPU/Slurm work;
8. the apparent correction only improves a generic append-only/completion control equally. In that case DCR may remain descriptive, but no mechanism claim survives.

No corrected C8 result may be called physical support evidence until H1, H2, and the common metric scale all pass. No DCR real-data benchmark claim may be issued if the result is UNTESTABLE_*; synthetic fixture results may be reported as a calibration artifact only.

## 10. Owner-review output

The eventual owner-approved run should create a new receipt outside the frozen C8 directory containing: source hashes; fixture definition; selected H1/H2 candidate; calibration/held-out scene lists; focal/crop/units; lambda; all denominators; per-target/window metrics; negative-control metrics; command text; host/runtime; and flags. This R47 design does not create that receipt and does not authorize its execution.
