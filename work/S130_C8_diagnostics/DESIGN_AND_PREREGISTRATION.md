# C8 diagnostics: preregistration and design

Status: preregistered design only. No GPU job, diffusion run, training, fine-tuning, new data, or new weights has been executed by this directory. The owner-approved cap is 20 H800-hours. The pinned VMem sources remain untouched. `new_method_validated=false` and `novelty_authorization=NONE`.

## Scientific boundary

These diagnostics decide whether a future hidden-surface prediction method is worth testing. They do not validate a method. The existing development panel is exposed `scene_13`/`scene_14` data, not held-out evaluation.

The current code facts are in `work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py`: slot 0 is passed as `extrinsics_src` at lines 1135-1140; the translation scale uses the centered position of camera 0 at lines 1098-1119; context embeddings are mean pooled at line 1124; the retrieval query uses an averaged pose and `target_K*0.65` at lines 635-645. Existing order-balanced evidence is `work/S107_order_balanced/ARM_SCORES.json` and the sealed finite-panel bundle is `docs/report/bundle/S113_SCORES.json`.

## Experiment 1: slot-0 factor separation

### Fixed population and arms

The population is exactly the S107 run encoded in `work/S103_selector_free_baseline/orderbalanced_s107.py`: `scene_13`, `seq-01`, bank IDs `0,5,...,55`, target IDs `60,75,90,105`, resolution 576, 50 denoising steps, CFG 2.0, CFG-min 1.2, fp32, seed 42, and the two primary multisets:

| multiset | order A | order B | reason |
|---|---|---|---|
| M1 | `[55,55,40,40]` | `[40,55,55,40]` | slot 0 changes 55→40 |
| M2 | `[50,50,45,45]` | `[45,50,50,45]` | slot 0 changes 50→45 |

The paired order is a permutation of the same physical cameras and images. A, B are crossed with four conditioning conventions:

- **N**: native VMem behavior: order-dependent ray reference and order-dependent scale.
- **R**: ray reference fixed to the physical camera in A slot 0; native scale remains.
- **S**: translation scale fixed to the physical camera in A slot 0 after the native centering operation; native ray reference remains.
- **RS**: both ray reference and scale fixed to A slot 0.

All context images, poses, intrinsics, target cameras, random seed, denoiser, and scorer are held fixed. The wrapper in `factorized_conditioning.py` patches only the input-conditioning call; it never changes the pinned source.

### Estimands and predictions

For multiset `m`, convention `q`, and seed `s`, the primary estimand is
`delta(m,q,s) = PSNR(order B, q, s) - PSNR(order A, q, s)`. Report the per-seed value, MAE difference, and the mean across the preregistered seed set. The reference RGB frames must be byte-identical across A/B within each multiset and seed.

Primary prediction: if the slot-0 effect is mainly coordinate reference and scale, then `|delta(M1,RS,42)| < 0.15 dB` and `|delta(M2,RS,42)| < 0.15 dB`. This is a diagnostic threshold, not a significance test.

Decision table:

| result | interpretation | next action |
|---|---|---|
| RS below 0.15 dB for both | coordinate/scale confound explains the effect | canonicalise/fix these factors in every later comparison; do not call the order effect a method |
| R below 0.15, S not below | ray reference dominates | fix the ray gauge; do not interpret as temporal order |
| S below 0.15, R not below | translation scale dominates | fix scale; inspect remaining ray conditioning |
| neither R nor S below, but RS below | interaction of reference and scale | use RS as the canonical control and report the interaction |
| RS not below for either multiset | residual tensor-order/temporal-position effect is plausible | only then design a separate order mechanism audit; no method claim follows |

### CPU equivalence gate

Before any GPU dispatch, `cpu_equivalence_test.py` must run with the exact VMem `get_translation_scaling_factor`, `get_cond`, and `get_plucker_coordinates` path, random latent tensors, and real context poses from an S107 receipt. Under RS, order B must equal a context-slot permutation of A for `concat`, `dense_vector`, `replace`, and `crossattn` with max absolute difference at most `1e-6` (the inverse/flip operations are performed in float32); target slots must match. Under N, the ray tensors must differ after the same permutation. Missing dependencies or missing real pose receipts are a **BLOCKED** result, never a fabricated pass.

## Experiment 2: support audit

### Fixed population and arms

The population is the 14 paired windows used by the sealed S113 panel: scenes `scene_13` and `scene_14`, window starts `[50,100,150,200,250,300,350]`, bank IDs `start + [0,5,...,55]`, target IDs `start + [60,75,90,105]`, and seeds `[42,7]`. The arm labels are exactly `static`, `memory_nms_off`, `memory_nms_on_clean`, and `memory_nms_on_leaked` where available in the sealed receipts. Existing arm/context receipts are authoritative; no context list is reconstructed from target RGB.

### Masks

Use the dataset RGB-D depth and poses only in the independent evaluator. For each target pixel `u`, back-project its dataset depth into world coordinates, then project that 3D point into each bank/context camera. A bank/context observation is valid when the projected pixel is in bounds, source depth is finite and positive, and
`abs(z_source - z_projected) <= max(0.05 m, 0.05 * z_projected)`.

- `B(u)`: valid in at least one of the 12 bank frames.
- `C(u)`: valid in at least one of the four delivered context frames for the arm.
- `J(u)`: the same target 3D point projected into VMem's averaged-target retrieval image using the VMem pose transform and `0.65*K`; nearest retrieval pixel within 1.5 pixels, nonnegative `surfel_index_map`, finite retrieval depth, and the same depth tolerance. This explicit mapping accounts for the retrieval render's 512x288 geometry and does not treat retrieval index exposure as ground-truth visibility.

Save masks per target camera and aggregate fractions by window and arm. Relate them descriptively to sealed per-window PSNR/MAE only; n=14 is a finite development panel and supports no population inference.

### Predeclared cutoffs and decision table

A support fraction is **low** if `<0.20`, **high** if `>=0.50`, and intermediate otherwise. A generated result is **poor** if PSNR `<=16.0 dB` (fixed before reading the new masks). For each window, use the mean over its four target cameras.

| observed pattern | interpretation | action |
|---|---|---|
| high B, low J | surfel indexing/exposure failure | inspect index projection and surfel map; stop hidden-geometry method work |
| high B, low C | delivery/selection failure | fix delivery/context before proposing prediction |
| low B | physical support scarcity | hidden-surface prediction remains justified as a hypothesis |
| high C and poor PSNR | consumption/generation failure | audit `get_cond`/denoiser consumption; do not add a geometry predictor yet |
| no dominant pattern | unresolved | keep the method unselected and collect no new training evidence |

A method direction is allowed to proceed to a later pilot only if at least 8/14 windows show low B in the failure stratum and neither indexing nor delivery accounts for at least 8/14; this is a gate for a pilot, not validation.

## Execution and falsification

The GPU component only rebuilds the existing surfel memory and saves retrieval index/cosine/depth/frame-count maps; it does not run diffusion. Every job runs inside tmux, uses the existing Apptainer/Conda recipe in `work/S103_selector_free_baseline/nms_s111.slurm` and `orderbalanced_s107.slurm`, and writes a receipt containing source/weights/image hashes, git SHA, host, Slurm job ID, window list, seeds, command, outputs, wall time, and `new_method_validated=false`.

If the CPU gate is blocked, do not dispatch Experiment 1. If required pose/context receipts are absent on the cluster, do not synthesize them. If support masks cannot be aligned without using target RGB, mark the window `UNTESTABLE` and stop aggregation. Any result that violates the predeclared depth or cutoff definitions is a protocol failure, not a favorable method outcome.

## Amendment 1 — before any Experiment 1 GPU run (2026-09-23, by Claude after code review)

Written and committed before any C8 generation exists. It changes the runner, not the hypotheses or the 0.15 dB threshold.

1. **Runner replaced.** `run_slot_factor.py` (design-round draft) is superseded by `run_slot_factor_v2.py`, generated from `work/S103_selector_free_baseline/orderbalanced_s107.py` with minimal edits (53 diff lines). Reasons found in review: the draft built models through `VMemPipeline(cfg)` instead of the S107 recipe, read sampler settings from the config instead of the S107 constants (50 steps, CFG 2.0, CFG-min 1.2, guider 1), and saved outputs under a name the contract scorer does not read. v2 also removes a stale S106 receipt line (`results['A_baseline_spread']`) that would raise `KeyError` after all arms finish; the same line exists in the original S107 script.
2. **Convention N uses the unchanged native path** (`get_translation_scaling_factor` then `get_cond`, exactly as in S107). R, S, RS use `factorized_conditioning.build_conditioning`, whose RS equivalence was verified by the CPU gate (max permuted difference 5.96e-08; N 2.77, R 3.55, S 1.60), rerun verbatim by Claude on SuperPOD with identical output, using a pose receipt whose eight matrices equal the S105 stage pose files exactly.
3. **Harness gate (binding).** Order A = S107 ordering o0 and order B = o3 of each multiset. Convention N at seed 42 must reproduce the S107 outputs byte-for-byte:
   - `M1_55x2_40x2__o0` `fb82bbf80d608468e925426e467195b0cca9596560e0887a011fd10bc1e728da`
   - `M1_55x2_40x2__o3` `20fb0dbe8403945c3aed78ff3234efbebc71f6b97a51a354a5ed793f1510ec49`
   - `M2_50x2_45x2__o0` `66bd6714a6d988d460f7822702bc7a8b21a9ff7bb5d981da139b1c87f5979cf8`
   - `M2_50x2_45x2__o3` `169ab1d256c4a4a0ad9cfa64f01d2b385eb53cea8e8f72542404c3e3925e2d02`
   (SHA-256 of `/home/yliutz/gwm_probe_receipts/S107/job-594733/*_target_rgb_fp32.npy`). `analyze_slot_factor.py` additionally requires identical per-frame integer metric sums. **If the gate fails, no delta is interpreted.**
4. **Seeds.** Seed 42 is primary and the only seed used by the decision table. Seed 7 is added for all 16 arms as a report-only robustness check.
5. **Guidance is not a confound.** `MultiviewCFG` (guider 1) applies `MultiviewScaleRule`, which lowers CFG only for target cameras that coincide with an input camera (translation difference < 1e-5, rotation < 10 degrees, same K), using a minimum over inputs. That test is order-invariant and effectively scale-invariant, so it is not an additional slot-0 pathway.
6. **Budget.** S107 took 8.55-9.08 s per arm (24 arms, job 594733). 32 arms plus model load is about 6 minutes on one H800, roughly 0.1 H800-hours, far inside the 20-hour cap.

## Amendment 2 — before any Experiment 2 GPU run (2026-09-23, by Claude after code review)

Written and committed before any C8 support map exists. Cutoffs (0.20 / 0.50 / PSNR 16.0 dB / 8-of-14 gate) and the depth tolerance are unchanged.

1. **Missing computation found.** The design-round code saved retrieval maps and aggregated `B/C/J` fields, but no script computed the masks. A CPU evaluator (`compute_support_masks.py`) is added; it is the only process that reads target depth.
2. **Runner v2** (`run_support_retrieval_v2.py`): same S111 priming and two-stage surfel construction; renders once per target instead of once per arm per target (maps do not depend on the arm); additionally saves `surfel_to_timestep`, the CUT3R `surfel_Ks`, the retrieval focal (0.65 x mean focal), render size, and the per-target render poses. Without these, `J` cannot be computed.
3. **Isolation.** `support_audit_v2.slurm` stages only bank color+pose and target pose for the 14 windows; the model container never sees target RGB or any depth file. The stage is hashed into `STAGE_MANIFEST_SHA256.txt`.
4. **Harness gate (binding).** For every window, the recomputed context lists must equal the sealed census lists in `docs/report/bundle/LEAK_REGIME_CENSUS.json`: `memory_nms_on_clean` = `clean_nms_on.retrieved_frame_ids`, `memory_nms_on_leaked` = `leaked_nms_on_same_build.retrieved_frame_ids`, `memory_nms_off` = `recency_nms_off.retrieved_frame_ids`. A window that fails is `UNTESTABLE` (different surfel memory than the sealed runs) and is excluded from the 8-of-14 count, which then cannot be met.
5. **Evaluation region.** Masks are computed on the target pixels the model actually sees: the model grid resizes 640x480 to 768x576 and crops columns 96:672, i.e. original columns 80-559, all rows. Pixels with no valid target depth are excluded from denominators. Pixel stride 2.
6. **J definitions.** Primary `J` follows the preregistered text: project the target 3D point into VMem's averaged-target retrieval image (for k=4 this is the render at the last target pose), focal 0.65 x mean CUT3R focal, principal point at the render centre, nearest pixel within 1.5 px, `surfel_index_map >= 0`, finite retrieval depth, same depth tolerance. Reported alongside, not used by the decision table: `J_own` (render at the pixel's own target pose), `J_cos` (additionally `cos_value >= 0`, matching VMem's own frame counting), and `J_ray` (no depth test). The median ratio retrieval-depth / projected-depth is reported to show whether the depth test is on a common scale.
7. **Scores.** Window-level PSNR per arm comes from the sealed S113 scores; if an arm has no sealed per-window PSNR, its consumption row is `UNTESTABLE_MISSING_SCORE`.
