# Learned Geometry on a Local Workstation: Calibrated CUT3R Pair and Sequence Diagnostics

Supplementary course technical report · S4–S5 · 5 September 2026

## Abstract

This report examines local execution and measured-depth agreement of a fixed pretrained CUT3R model in two successive diagnostics. Both use the official 224 linear intermediate checkpoint, documented signed-RoPE and input-transfer adaptations, and a depth scale fitted only at the start of each input sequence. In S4, two fixed TUM RGB images were processed on CPU and MPS. On the second image's 37,325 valid measured pixels, calibrated CPU mean absolute depth difference was 32.324 mm, median absolute difference was 24.368 mm, and the 90th percentile was 67.788 mm. All 14 CPU/MPS output arrays satisfied the prescribed numerical tolerance with the same CPU-derived scale. S5 then processed three fixed 24-image temporal blocks on CPU, using one measured calibration depth per block. Across the eight primary assessment images, mean per-image MAE was 72.121 mm, mean per-image median absolute difference was 50.171 mm, and mean per-image 90th percentile was 148.629 mm. Mean relative-to-start rotation and translation-vector differences were 2.052° and 60.389 mm under a shared pointmap–pose scale assumption. S4 and S5 use different assessment images and contexts, so their scores do not establish a temporal deterioration rate. All data come from one environment. The results support bounded, calibrated learned-geometry diagnostics, not a new estimator, a view-retrieval improvement, or video-generation quality.

## 1. Introduction

The broader course project studies geometry-aware view memory for spatial video generation. In that setting, an upstream geometric estimate may influence which previous images are available as reference context. VMem uses a surfel-indexed view memory for this purpose, while CUT3R maintains a persistent state for continuous 3D perception. The two systems therefore provide different parts of the intended research pipeline: selecting visual context and estimating scene geometry, respectively. This supplement examines the latter part using the actual office images already selected in the local project. [1: VMem](https://v-mem.github.io/), [2: CUT3R](https://cut3r.github.io/)

The preceding S0–S3 work established local memory and retrieval diagnostics, including a real RGB-D control that supplied Kinect measurements directly to the memory component. That control did not test learned geometric estimates, because it bypassed CUT3R. Consequently, even a fully verified S3 result could not answer whether the available machine could execute the upstream model, whether its output conventions were interpreted correctly, or how its predictions agreed with measured depth. The present study addresses this gap in the project's evidence rather than a claimed gap in the literature. The earlier findings remain documented in the separate [S0–S3 technical report](TECHNICAL_REPORT.md).

The bounded question is whether a fixed pretrained CUT3R checkpoint can process fixed RGB inputs locally and produce interpretable geometric outputs when calibration is restricted to the first image. The data come from TUM RGB-D, which supplies Kinect RGB and depth observations together with a motion-capture trajectory reference. Depth measurements serve as a comparison reference; neither those measurements nor their registration are treated as noiseless surface geometry. S4 tests a two-image interface, and S5 extends the same calibration principle to three short temporal blocks. [3: TUM RGB-D paper](https://jsturm.de/publications/data/sturm12iros.pdf)

Three issues govern the interpretation. First, successful model import and checkpoint loading do not ensure a successful forward pass on the available device. Second, predicted self-view points, camera poses, and other-view points must be interpreted according to the actual selected head. Third, resizing, depth validity, and scale fitting must match a fixed protocol so that apparent agreement is not created by fitting the assessment image or changing its evaluation mask.

The diagnostics separate execution checks from measurement comparisons. S4 uses the same checkpoint, RGB inputs, precision behavior, and runtime adaptations on CPU and MPS; both devices retain the CPU first-image scale. S5 uses CPU only, initializes state independently for each temporal block, and retains each block's own first-image scale for its remaining images. Depth is assessed in the self-camera view, and relative pose is compared with the motion-capture reference interpolated at RGB timestamps. Saved predictions and measurements provide the inputs for independent recomputation.

The report contributes a reproducible execution record, an explicit calibration and scoring procedure, and depth and pose observations at pair and short-sequence lengths, with a separate two-image device comparison. These are course-project diagnostic outputs, not a new reconstruction algorithm. Their value is to identify what the learned-geometry interface has actually demonstrated before connecting it to memory updating or video generation.

## 2. S4 model, inputs, and runtime

### 2.1 Fixed model and data

The experiment used the independent official CUT3R repository at commit `8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf` and its 224 linear intermediate checkpoint. The official repository distinguishes this checkpoint from the final 512 DPT checkpoint; this study does not claim to reproduce the latter's results. The downloaded file contained 2,994,205,002 bytes, with SHA-256 `7a7d83e47f822e040980c8f5aff4c15aa94366d469d3ceae51fa30cc2f62327d`. All 748,443,655 model parameters loaded with matched keys. Parameters, external inputs, and saved outputs were FP32, with execution first on CPU and then on MPS on an M3 Max workstation with 64 GB memory. [Official checkpoint documentation](https://github.com/CUT3R/CUT3R#download-checkpoints)

This FP32 label does not describe every intermediate operation. The retained official CroCo encoder casts its query and key tensors to FP16 before RoPE and then restores the original dtype; the decoder explicitly uses FP32 for this operation. These upstream conversions were preserved on both devices. No model or output was changed when this precision description was clarified, and the experiment must not be described as exclusively FP32 computation. [Recorded precision clarification](S5_PRECISION_CLARIFICATION.md), [fixed encoder attention implementation](https://github.com/CUT3R/CUT3R/blob/8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf/src/croco/models/blocks.py), [fixed decoder attention implementation](https://github.com/CUT3R/CUT3R/blob/8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf/src/dust3r/blocks.py#L112)

The two inputs were the first two indices in the pre-existing S2 QA selection, indices 0 and 34. The frozen input manifest records their selection before any CUT3R output. Their RGB timestamps were 1305031102.175304 and 1305031103.475274, approximately 1.30 s apart, within one `freiburg1_xyz` environment. Only RGB was supplied to the model. Depth and dataset poses were used by the subsequent evaluator, not as model inputs. The term held-out below refers to the second image's depth being withheld from parameter fitting; the second RGB image was, necessarily, an input to prediction. [Frozen input manifest](../data/cut3r/inference_inputs.json)

Table 1. Fixed image associations and evaluation support. Measurement support is reported relative to the entire 224×224 crop.

| Item | First image: calibration | Second image: assessment |
|---|---:|---:|
| RGB timestamp | 1305031102.175304 | 1305031103.475274 |
| Associated depth timestamp | 1305031102.160407 | 1305031103.463886 |
| RGB minus depth time | 14.897 ms | 11.388 ms |
| Valid measured pixels in crop | 35,699 | 37,325 |
| Fraction of crop with valid measurement | 71.148% | 74.388% |

### 2.2 Documented runtime adaptations

The first CPU attempt loaded the checkpoint but failed during the forward pass: pose tokens used positions `(-1, -1)`, which the official pure-PyTorch rotary-position fallback could not use as lookup indices. An external signed-RoPE adapter was introduced using the signed-angle interpretation of the fixed upstream CUDA implementation. Its nonnegative-position output was compared with the original fallback, and synthetic CPU/MPS checks were recorded. There was no CUDA hardware comparison. This is an explicit compatibility adaptation, not evidence that the unmodified execution path succeeds on this machine. [Runtime amendment](S4_RUNTIME_AMENDMENT.md), [adapter audit](CUT3R_ROPE_ADAPTER_AUDIT.md)

After the adapted CPU run succeeded, the initial MPS attempt encountered an input-transfer problem. The final runner used blocking staging before entering official inference on both devices and checked that all 14 staged tensor fields retained their values. The final CPU predictions matched the earlier successful CPU predictions exactly. Both original failure records were retained. The final CPU and MPS runs completed at 23:13:07 and 23:13:20 on 5 September 2026, respectively, in Asia/Shanghai time. Their metadata identifies the shared runner, adapter, checkpoint, input hashes, and successful finite outputs. [CPU metadata](../results/CUT3R_cpu_2frames_signedrope_sync/run_metadata.json), [MPS metadata](../results/CUT3R_mps_2frames_signedrope_sync/run_metadata.json)

### 2.3 Output semantics

The actual downstream head was `LinearPts3dPose`. Its self-view pointmap, pose, and other-view pointmap are separately predicted; the other-view branch uses `cross_proj`. A different class in the same file, `LinearPts3dPoseDirect`, constructs the other-view points by transforming self-view points, but the selected factory did not instantiate that class. This distinction was corrected in a recorded amendment before the successful model outputs. [Fixed head factory](https://github.com/CUT3R/CUT3R/blob/8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf/src/dust3r/heads/__init__.py), [fixed head implementation](https://github.com/CUT3R/CUT3R/blob/8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf/src/dust3r/heads/linear_head.py), [protocol amendment](S4_PRE_RUN_AMENDMENT.md)

Accordingly, self-view Z provides the predicted camera depth. The decoded `camera_c2w` matrices provide the pose outputs. The difference between the transformed self-view points and separately predicted other-view points is retained as a descriptive consistency check, not imposed as an algebraic identity and not used to remove pixels.

## 3. S4 measurement protocol

### 3.1 Resizing and validity

The official 224 preprocessing branch resized each 640×480 RGB image to 299×224 using LANCZOS and then cropped `[37, 0, 261, 224]` to obtain 224×224 input. Depth was converted from its integer representation using the dataset's factor of 5000 units per metre, without applying another Freiburg scale correction. Depth and validity were resized by nearest-neighbour sampling and cropped with the same rectangle. [Fixed RGB loader](https://github.com/CUT3R/CUT3R/blob/8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf/src/dust3r/utils/image.py), [TUM format documentation](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats)

The measurement mask was computed on the original depth image. A pixel was retained only if every depth in its 5×5 neighbourhood was positive and finite and differed from the centre by at most 50 mm. The original image's outer two-pixel border was excluded. This rule was fixed before scoring. It removes invalid measurements and local depth discontinuities but does not imply that the remaining measurements are error-free. Model confidence was not used for pixel selection, and large residuals within the resulting evaluation mask were retained. [Frozen protocol](S4_TWO_FRAME_PROTOCOL.md)

### 3.2 First-image scale and held-out depth

Let $d_i(u)$ denote measured depth at retained pixel $u$ in image $i$, and let $z_i^{\mathrm{CPU}}(u)$ denote the CPU self-view depth. The shared scale was

$$
s=\operatorname{median}_{u\in M_0}
\frac{d_0(u)}{z_0^{\mathrm{CPU}}(u)},
$$

where $M_0$ includes valid first-image measurements with finite, positive predicted depth. The protocol required at least 100 such pixels. It prohibited fitting a translation offset, rotation, or second-image scale. The same $s$ was used for both CPU and MPS. The fitted scale is a measured calibration of this input pair, not a claim that the model's unscaled units are intrinsically metres.

For device $a$, the assessed residual was $r_i^a(u)=s z_i^a(u)-d_i(u)$ on the valid measurement mask intersected with finite, positive predictions. Reported statistics include mean absolute error (MAE), median absolute error, the 90th percentile of absolute error, signed mean residual, the fraction within 30 mm, and mean absolute relative error $\operatorname{mean}(|r|/d)$. Prediction coverage uses the valid measured pixels as its denominator; measured-mask coverage uses all pixels in the crop. Both quantities are needed to state the evaluated support. The first image's scores are calibration descriptions; only the second image provides the held-out depth result.

### 3.3 Relative pose and device checks

Reference c2w poses $G_0,G_1$ were interpolated at RGB timestamps using linear translation and quaternion spherical interpolation, with no extrapolation and a maximum allowed bracket gap of 0.1 s. The observed bracket gaps were approximately 0.0100 and 0.0101 s. This uses the RGB times rather than the associated depth times; no motion correction was applied to the registered depth measurements.

The predicted and reference relative transforms were $P_0^{-1}P_1$ and $G_0^{-1}G_1$. Only the predicted relative translation was multiplied by $s$. Rotation was scored by the angle of the relative rotation discrepancy, and translation by the Euclidean difference between the two relative translation vectors. No GT-based rigid or similarity alignment was fitted. Applying the depth-derived scale to translation assumes that the predicted pointmap and pose translations share a compatible scale; the selected head does not enforce their complete algebraic agreement.

CPU/MPS agreement was evaluated separately from measurement accuracy. For every element of all 14 saved output arrays, CPU served as the reference in the prescribed test

$$
|x_{\mathrm{MPS}}-x_{\mathrm{CPU}}|
\leq 10^{-3}+10^{-3}|x_{\mathrm{CPU}}|.
$$

All arrays also had to have matching shapes and finite values. Device-specific refitting of the geometric scale was prohibited.

## 4. S4 results

### 4.1 Depth and evaluated coverage

The first CPU image provided 35,699 calibration pixels and a scale of 1.1583864704346218. Both devices predicted positive, finite self-view depth at every valid measured pixel in both crops. Thus prediction coverage was 100% within the measurement mask, while Table 1 shows the smaller fractions of the full crops that contained eligible measurements.

Table 2. Calibrated depth differences on the second, held-out image. All scores use the CPU first-image scale and the same 37,325 measured pixels. Positive signed residual means predicted depth exceeds measured depth.

| Metric | CPU | MPS |
|---|---:|---:|
| MAE | 32.324 mm | 32.321 mm |
| Median absolute difference | 24.368 mm | 24.363 mm |
| 90th-percentile absolute difference | 67.788 mm | 67.790 mm |
| Signed mean difference | +28.892 mm | +28.888 mm |
| Fraction within 30 mm | 55.721% | 55.727% |
| AbsRel | 0.041099 | 0.041096 |

The first-image calibration description remained imperfect. CPU MAE was 81.474 mm, its median was 20.481 mm, and its 90th percentile was 234.358 mm; the corresponding MPS values were 81.475, 20.480, and 234.272 mm. Under the separate assumption that unscaled model units were metres, second-image CPU MAE would be 78.775 mm. This unscaled comparison describes a unit assumption, while the calibrated values describe the stated measurement-assisted protocol. Neither the lower error of the second image nor the difference between scaled and unscaled scores establishes improvement through time. [Full depth results](../results/S4_cut3r_pair_verified/summary.json)

![RGB inputs, measurements, predictions, and retained residuals](../results/S4_cut3r_pair_verified/figures/depth_and_residuals.png)

Figure 1. The two actual RGB crops, measured depths, scaled predictions, and depth differences. Grey regions in measured-depth and residual panels lie outside the predeclared measurement mask; predicted depth is shown across the full crop. The saved figure uses common depth and residual ranges, and its residual range extends to the observed maximum. Image source: TUM RGB-D, [CC BY 4.0 license](https://cvg.cit.tum.de/data/datasets/rgbd-dataset#license). [Figure specification](../results/S4_cut3r_pair_verified/figures/captions.md)

### 4.2 Relative pose and pointmap consistency

Table 3. One relative-pose comparison between the two RGB timestamps. Predicted translation uses the CPU first-image scale.

| Quantity | CPU | MPS |
|---|---:|---:|
| Rotation difference | 0.929059° | 0.929211° |
| Translation-vector difference | 19.835704 mm | 19.829506 mm |
| Reference relative displacement | 371.938476 mm | 371.938476 mm |
| Reference relative rotation | 10.325203° | 10.325203° |

The predicted rotations passed the finite-value, orthogonality, and determinant checks. The independent quaternion decoder agreed with the stored c2w matrices within float32 precision. As expected from the separate prediction branches, transformed self points were not identical to other-view points: the CPU maximum coordinate-wise differences were 0.139652703 and 0.018527423 model units for the first and second images. These values were recorded without converting the diagnostic into a mandatory identity or changing the assessment mask. [Independent pose and consistency checks](../results/S4_independent_audit/recomputed_summary.json)

### 4.3 Device agreement and independent recomputation

All 14 CPU/MPS arrays were finite and satisfied the prescribed tolerance. The largest absolute element difference was 0.0006508827209472656 in the second-image `conf_self` array. This is a confidence-value difference, not a depth error in millimetres. The small differences in Table 2 were obtained with the shared CPU scale, so independent calibration did not hide a device discrepancy.

An independent NumPy/Pillow implementation reproduced the evaluation without importing the project's scoring, data-association, or pose-interpolation functions. It rebuilt the original integer-depth neighbourhood masks and the resized masks, recomputed first-image scale and both devices' scores from NPZ arrays, reconstructed reference poses with a separate quaternion implementation, and checked hashes and runtime identity. All 185 checks passed. The independently reconstructed masks matched the saved masks pixel for pixel; both RGB crops also matched a separate invocation of the official loader exactly after normalization. These checks concern the bounded saved experiment, not every possible model execution. [Independent audit](S4_INDEPENDENT_AUDIT.md), [numerical evidence](../results/S4_independent_audit/recomputed_summary.json), [RGB verification](../results/S4_independent_audit/official_crop_check.json)

Recorded forward-pass times were 0.878 s on CPU and 6.284 s on MPS. Each value came from a single un-warmed run. These records describe execution of this pair and do not constitute a throughput benchmark or a general device ranking.

## 5. S5: three causal 24-image blocks

### 5.1 Frozen extension and state semantics

After observing the S4 results, a separate S5 protocol was frozen before any S5 inference. It reused the existing S3 selections: three nonoverlapping temporal blocks of the same `freiburg1_xyz` environment, each containing 24 RGB images in timestamp order. Block B0 retained its development label; B1 and B2 retained their test labels. All 72 image identities, associated depths, timestamps, and hashes were saved in the input manifest. No image was selected or removed according to S4 or S5 performance. [S5 protocol](S5_SEQUENCE_PROTOCOL.md), [frozen S5 inputs](../data/cut3r/S5_inputs.json)

Each block ran in a new CPU process with eight threads and seed 0, using the same model, signed-RoPE adapter, blocking staging, and retained upstream precision behavior as S4. The process called official inference on all 24 views. The decoder updated its state in timestamp order, and all view reset flags were false. State was initialized anew at the start of each block. [Fixed state and reset implementation](https://github.com/CUT3R/CUT3R/blob/8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf/src/dust3r/model.py#L816) Parameters, external inputs, and saved arrays were FP32, while the official encoder's internal FP16 RoPE conversion remained in place.

The first 20 images formed the preceding RGB context; the last four were the designated assessment tail. Every assessed RGB image entered the causal estimation sequence. A later tail prediction could therefore depend on the RGB of an earlier tail image, although measured assessment depth never entered inference. This is a causal RGB reconstruction assessment, not unseen-image video extrapolation or a retrieval map constructed only from the first 20 images. The distinction matters if these outputs are later connected to view-memory retrieval.

One scale was fitted to the first image of each block using the same measured-depth mask and median-ratio rule as S4. That scale remained fixed for the following 23 images. No per-image scale, trajectory alignment, translation offset, ICP, or GT-fitted rotation was applied. The depth comparison reused the S4 resizing, crop, validity mask, and metrics. Pose at frame $t$ was assessed through $P_0^{-1}P_t$ and $G_0^{-1}G_t$, with predicted relative translation multiplied by the block's scale. Thus S5 used three calibration-depth images, rather than demonstrating uncalibrated metric RGB-only estimation.

Table 4. S5 calibration and actual execution records. Each block spans approximately 8.836 s of source observations. Forward times are single-run descriptions, without warm-up.

| Block | Split | First-image scale | Calibration pixels | CPU forward time |
|---|---|---:|---:|---:|
| B0 | Development | 1.1584206027 | 35,699 | 9.545 s |
| B1 | Test | 1.1277299277 | 41,427 | 9.323 s |
| B2 | Test | 1.1285109313 | 37,669 | 9.376 s |

All three complete 24-image runs produced saved outputs. Reported peak process RSS was approximately 6.425 GB in each process, using decimal bytes. These three executions are a resource record, not a hardware benchmark or evidence of constant memory with sequence length. S5 did not repeat the sequence runs on MPS. [S5 run metadata](../results/CUT3R_S5_cpu/sequence_metadata.json), [S5 evaluation summary](../results/S5_cut3r_sequence/summary.json)

### 5.2 Primary eight-image assessment

The primary test comprises frames 20–23 in B1 and B2, giving eight actual images. Each depth metric was calculated within an image first and then averaged with equal image weights. In particular, the reported mean median and mean p90 are averages of per-image quantiles; they are not pooled-pixel quantiles. The same image weighting was used for relative-to-start pose differences.

Table 5. S5 primary test, averaged over the eight designated images. Valid-measurement counts range from 33,343 to 38,500 pixels per image. Every valid measured pixel had a finite, positive predicted depth, so prediction coverage within that mask was 100%.

| Metric | Mean over primary images |
|---|---:|
| Per-image MAE | 72.121 mm |
| Per-image median absolute difference | 50.171 mm |
| Per-image 90th-percentile absolute difference | 148.629 mm |
| Per-image signed mean difference | +55.355 mm |
| Per-image fraction within 30 mm | 35.177% |
| Per-image AbsRel | 0.065396 |
| Relative-to-start rotation difference | 2.052259° |
| Relative-to-start translation-vector difference | 60.388853 mm |

Table 6 preserves every primary image. It shows variation that is concealed by the overall mean: the lowest within-30-mm fraction is 5.215%, while the largest MAE is 122.776 mm, both in B1 frame 20. The signed residuals are not positive in every image; B1 frame 23 has a signed mean of −35.642 mm. No remaining residuals were removed based on their magnitude. [All per-image records](../results/S5_cut3r_sequence/records.json)

Table 6. All eight S5 primary images. Depth errors are in millimetres; pose differences are relative to the first image of the same block, using its frozen scale.

| Block / frame | Valid pixels | MAE | Median | p90 | Within 30 mm | Rotation difference | Translation-vector difference |
|---|---:|---:|---:|---:|---:|---:|---:|
| B1 / 20 | 33,343 | 122.776 | 92.701 | 224.668 | 5.215% | 2.430° | 88.579 mm |
| B1 / 21 | 36,427 | 96.625 | 83.577 | 187.020 | 9.894% | 2.780° | 84.755 mm |
| B1 / 22 | 38,477 | 48.651 | 32.258 | 119.658 | 45.386% | 3.099° | 48.610 mm |
| B1 / 23 | 38,014 | 43.326 | 32.105 | 86.451 | 45.817% | 4.192° | 56.350 mm |
| B2 / 20 | 38,500 | 78.370 | 48.581 | 147.672 | 36.384% | 0.925° | 46.955 mm |
| B2 / 21 | 38,264 | 69.295 | 41.058 | 145.246 | 43.764% | 1.203° | 50.027 mm |
| B2 / 22 | 38,077 | 62.669 | 38.648 | 139.886 | 46.078% | 0.968° | 52.710 mm |
| B2 / 23 | 38,372 | 55.253 | 32.438 | 138.432 | 48.874% | 0.821° | 55.125 mm |

### 5.3 Development and full-sequence descriptions

The four B0 tail images were retained as a separate development description. The complete noncalibration description includes all 23 post-first images in each of the three blocks, for 69 images. These 69 already include the eight primary images; they are not an additional independent test set. The three first images remain calibration descriptions.

Table 7. S5 summary by predeclared role. Each value is a mean of per-image metrics; rows overlap where explicitly stated.

| Role | Images | MAE | Mean median | Mean p90 | Within 30 mm | AbsRel |
|---|---:|---:|---:|---:|---:|---:|
| Primary B1+B2 tails | 8 | 72.121 mm | 50.171 mm | 148.629 mm | 35.177% | 0.065396 |
| Development B0 tail | 4 | 84.374 mm | 40.371 mm | 227.981 mm | 39.427% | 0.057863 |
| All noncalibration images, including the primary eight | 69 | 96.461 mm | 65.047 mm | 198.667 mm | 26.266% | 0.076950 |

The B1 and B2 tail MAEs were 77.845 and 66.397 mm, respectively. Their mean relative rotation differences were 3.125° and 0.979°, and mean relative translation-vector differences were 69.573 and 51.204 mm. These block summaries describe temporal subsets of the same environment, not independent-scene replication. Figure 2 displays every frame, including values outside the primary tails, so the report does not infer sequence behavior from selected endpoints.

![S5 depth and relative pose differences across every image in all three blocks](../results/S5_cut3r_sequence/figures/sequence_errors.png)

Figure 2. All 24 frames in each temporal block, with elapsed source time on the horizontal axis. The first point is a calibration description; shaded regions identify the last four frames. Only the shaded B1 and B2 images form the primary test. Depth, translation-vector, and rotation differences are shown in separate panels, each starting at zero and including all observed values. The curves are descriptive; they are not a fitted drift model. [Figure specification](../results/S5_cut3r_sequence/figures/captions.md)

## 6. Interpretation and limitations

The experiments close a specific local feasibility gap: a fixed learned estimator has produced saved geometric outputs from actual RGB inputs at two-image and 24-image lengths, and the outputs support measurement-calibrated comparisons. This is stronger evidence than a model import check or a synthetic compatibility test. The scope remains small. S4 contains one calibration image, one assessment image, and one relative motion; S5 contains three short temporal blocks and eight designated primary images within one environment. Pixels within an image and images within this sequence are dependent observations. No confidence intervals or cross-environment generalization claims are derived from those counts.

The reported depth residuals combine model output, measured depth, preprocessing, temporal association, and calibration assumptions. Kinect depth is a sensor observation, while motion capture supplies the trajectory reference; neither removes all measurement or registration error. The nonzero RGB/depth time offsets also remain. The positive signed residual on the assessed image records the direction of disagreement but does not isolate its cause. The head's separately predicted representations further mean that good self-view depth agreement alone cannot validate the complete other-view geometry or pose-scale relationship.

S4 and S5 must not be read as better-scoring versions of S3. S3 evaluated sparse memory projections built from measured RGB-D observations and compared memory-update rules; the learned-geometry stages evaluate dense self-view depth after initial-image calibration. The input source, prediction object, support mask, calibration and aggregation differ. S3's sparse common-pixel coverage and the learned stages' coverage within a valid-measurement mask have different denominators. Subtracting their MAEs or presenting them as a method ranking would lack a matched comparison. The S3 negative finding about unchanged final retrieval in the main raw-input condition remains a separate observation. [S3 results](S3_RESULTS.md)

Nor does the difference between S4's single-image score and S5's primary average measure a temporal error-growth rate. The assessment images, source times, initial states, and available RGB contexts differ. Within S5, the plotted errors also vary with the observed image and camera motion; the diagnostic has no matched state-reset or context-length control that would isolate the effect of accumulated state. A rising or falling portion of a curve alone does not identify a causal mechanism. S5's later tail images additionally have access to earlier tail RGB, which is appropriate for the stated causal estimation task but must not be mistaken for query-excluded memory retrieval.

The study also does not establish a new geometry or memory method. CUT3R supplies the pretrained estimator, TUM supplies the measured data, and this project supplies a bounded execution and assessment record. The external adapters are documented compatibility changes whose CUDA equivalence was not tested here. Successful independent CUT3R execution does not show that the VMem fork, its complete cleaning and filtering, or its generation model will behave equivalently. Any claim that geometric changes improve selected context or generated spatial consistency requires a connected experiment with those outcomes measured directly. [1: VMem](https://v-mem.github.io/), [2: CUT3R](https://cut3r.github.io/)

## 7. Conclusion

The local learned-geometry interface is operational for the fixed S4 pair and three S5 short sequences, with explicit runtime adaptations and calibration restricted to each sequence's first image. The two stages provide concrete depth and pose measurements while preserving the distinction between causal RGB estimation, calibrated metric comparison, device agreement, and downstream memory quality. The evidence is suitable for documenting this course-project stage. Broader scene coverage, matched tests of state behavior, view-memory benefits, and video-generation quality require further experiments. The report and its supporting checks require human academic review before course submission.

## References

1. Runjia Li, Philip Torr, Andrea Vedaldi, and Tomas Jakab. VMem: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory. ICCV, 2025. [Conference paper](https://openaccess.thecvf.com/content/ICCV2025/papers/Li_VMem_Consistent_Interactive_Video_Scene_Generation_with_Surfel-Indexed_View_Memory_ICCV_2025_paper.pdf), [author project](https://v-mem.github.io/).
2. Qianqian Wang, Yifei Zhang, Aleksander Holynski, Alexei A. Efros, and Angjoo Kanazawa. Continuous 3D Perception Model with Persistent State. CVPR, 2025. [Author project and paper](https://cut3r.github.io/), [author manuscript](https://arxiv.org/abs/2501.12387), [official implementation](https://github.com/CUT3R/CUT3R).
3. Jürgen Sturm, Nikolas Engelhard, Felix Endres, Wolfram Burgard, and Daniel Cremers. A Benchmark for the Evaluation of RGB-D SLAM Systems. IEEE/RSJ International Conference on Intelligent Robots and Systems, 2012. [Author manuscript](https://jsturm.de/publications/data/sturm12iros.pdf), [official dataset](https://cvg.cit.tum.de/data/datasets/rgbd-dataset).

## Reproducibility record

The [S4 protocol](S4_TWO_FRAME_PROTOCOL.md) is read together with the [pre-run semantic amendment](S4_PRE_RUN_AMENDMENT.md), [runtime amendment](S4_RUNTIME_AMENDMENT.md), and [precision clarification](S5_PRECISION_CLARIFICATION.md). The completed [S4 evaluation summary](../results/S4_cut3r_pair_verified/summary.json) records source hashes, input associations, calibration, and device scores. [Saved S4 measurement comparisons](../results/S4_cut3r_pair_verified/measurement_comparison.npz), the [evaluation-source archive](../results/S4_cut3r_pair_verified/evaluation_source.zip), and the [independent recomputation](../results/S4_independent_audit/recompute.py) provide its numerical trail. S5 is specified by its [separate frozen protocol](S5_SEQUENCE_PROTOCOL.md), [input manifest](../data/cut3r/S5_inputs.json), [complete per-frame records](../results/S5_cut3r_sequence/records.json), and [evaluation summary](../results/S5_cut3r_sequence/summary.json). Original failures and successful device runs remain in separate result directories. The S0–S3 report and its PDF/PPTX snapshots remain a record of the earlier stage.


## Independent verification of this supplement

The S5 independent implementation passed 4,516 checks, reconstructing the 72 original-depth masks and targets, three calibration scales, all per-image depth and relative-pose metrics, and the eight-image primary and 69-image descriptive aggregates. It did not invoke the main preprocessing or scoring functions. All targets and masks matched element by element. [S5 independent audit](S5_INDEPENDENT_AUDIT.md), [verification record](../results/S5_independent_audit/verification.json). A separate fresh-context review verified all three references and their associated external claims against primary sources; its scope did not include recomputing experiments. [Citation audit](LEARNED_REPORT_CITATION_AUDIT.md).
