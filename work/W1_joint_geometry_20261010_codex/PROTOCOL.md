# Week 1: complete-geometry candidate headroom versus single-geometry controls

Status: PRE-RUN PROTOCOL. No candidate inference or new outcome scoring preceded this document.
The immutable execution receipt `FREEZE.json` records the UTC freeze time and hashes of this protocol,
manifest, predictor, scorer, tests, KPS implementation, and pinned inputs before any inference.

## Authorization and existing work

Owner instruction in this chat, 2026-10-10: check existing S141 results and TACC RTX 3090 availability,
freeze the protocol, run the complete-geometry upper-bound check and single-mode control in parallel,
do not duplicate existing tasks, and stop if the results do not support the hypothesis.
Base repository commit: 7cefe20ede81597b32517b49a9f0bbdf35278b10. Work occurs in isolated worktrees,
not the dirty primary checkout. No checkpoint training is authorized by this diagnostic itself.

At the initial live inventory gpu13 GPU 3/4 were running S141 A/B, with their evaluation chains already
waiting. No final A/B evaluation was present. Other gpu13 devices had resident applications. gpu14
reported NVML driver/library mismatch. Existing jobs are not interrupted or duplicated. Thus the first
geometry-only diagnostic runs on local CPU in two independent workers (c0 versus c1/c2/c3), reusing the
existing CUT3R environment and weights. Existing TACC jobs continue. GPU execution may be substituted
only as a recorded pre-outcome amendment with matched device/precision for every candidate.

## Question, scope and prior-art boundary

Do complete source-only CUT3R reconstructions of the same observed frames provide at least 10% whole-clip
geometric correspondence headroom over the canonical repaired reconstruction, and does that headroom
survive simple single-map fusion and scale-only explanations?

This is an exposed real RGB-D diagnostic of a four-order reconstruction ensemble. It is NOT posterior
calibration, a new video method, a generation result, or unseen-scene confirmation. Positive evidence
would only justify implementing the proposed consumer. Failure stops this tested candidate family.
Relevant primary sources previously read: 3D-Belief (arXiv:2605.11367), uncertainty-aware completion
(arXiv:2511.17932), VGGT-Diff (arXiv:2609.33253), and WorldWarp (arXiv:2512.19678). Multiple geometry
hypotheses, uncertainty weighting, residual consistency and warp refinement are already prior art.
The diagnostic tests whether complete candidate identities carry useful structure beyond marginal
depth/scale variation. The shared discrete-mode denoiser is NOT run in this first-week gate.

## Inputs and frozen panel

`MANIFEST.json` fixes all 16 RGB-D Scenes v2 windows: scenes 13/14, starts 0,50,...,350, four source
offsets 0/15/30/45 and four target offsets 60/75/90/105. Use each scene's camera-intrinsics.txt,
native 640x480 RGB and registered sensor depth in millimetres. Existing 7-Scenes chess depth is not
used: the current staging lacks it and its RGB/depth registration is not established in S139.
The panel was already exposed in S130-S140; no claim of untouched data or independent windows is allowed.

Source RGB follows the existing area-resize 480x640 -> 576x768, centre crop x=96:672, then CUT3R's
512x384 crop. OpenCV optical camera-to-world poses are passed directly. KPS uses seed 0, free fitted
focal, known source poses, and niter=0; original PnP-fallback scale and S138 optimization are excluded.
Weights and pinned source hashes are in PINNED_INPUTS.json. Float32, TF32 disabled after imports,
torch seed 0, four CPU threads per process. No hyperparameter or source-order search.

Candidates are the four cyclic orders [0,1,2,3], [1,2,3,0], [2,3,0,1], [3,0,1,2]. Each uses exactly the
same RGB/pose identities. Each inference starts fresh, and outputs are restored to canonical source
identity. A candidate is the complete tuple of all four predicted source depths. c0 is the single-mode
control; three alternatives are computed by the other worker. This changes processing order/root, not
input information. Candidates are proposals, not calibrated posterior samples.

## Leakage separation and receipts

The predictor reads source RGB/poses and scene intrinsics only. It does not read ANY sensor-depth PNG
or target RGB. It saves per-source depths, confidences, point clouds when available, KPS diagnostics,
identity/order, input and code hashes, environment/device/precision, runtime and output hashes.
Prediction cannot use the future score to choose an order, scale or source subset.
All 64 candidate records are completed and hashed in CANDIDATE_SEAL.json before the scorer opens source
or target sensor-depth images. The offline GT oracle is explicitly an upper bound, never a deployable
selector. Existing source/target pose text may be used for predefined geometry, never target appearance.

## Fixed measurement support and primary endpoint

The scorer alone reads registered source/target depths, treating 0 and depths >=10 m as invalid.
Source samples are native pixel coordinates on a stride-4 grid within the predetermined CUT3R crop.
For the primary interior stratum both sensor pixels and their four-neighbours must be finite positive
depth, with <=0.05 m local jumps. Project measured source points into a target with the supplied K/poses;
require positive z, rounded target pixel in bounds, target depth interior valid, and <=0.05 m difference
between projected z and measured target z. This support depends on measurements and the fixed crop,
NEVER on candidate depth, confidence, coverage or error. Save counts per source/target pair.

For each tuple compute continuous target image coordinates from the measured source depth and from
the candidate source depth, using the identical native K and poses. The corrected half-pixel mapping
from S137 maps CUT3R depth onto native source pixels. Let EPE be the Euclidean coordinate difference.
Primary tuple loss = min(EPE / sqrt(640^2+480^2), 1). Nonpositive/nonfinite depth, a behind-camera point,
or an out-of-image candidate projection receives loss 1; it never disappears from the denominator.
Report capped EPE in native-pixel equivalents too. Do not mix CUT3R fitted-focal point clouds into this
native-K depth endpoint. It measures sensor-relative correspondence consistency, not perfect geometry.

E(w,m) averages all fixed source-target tuples in a window. A complete oracle chooses ONE candidate m
to minimize E(w,m) jointly across all four sources and all four targets. Primary H =
1 - mean_windows(E_oracle) / mean_windows(E_c0), with equal window weights. Report each scene separately.
Report per-target and per-tuple oracle ceilings as diagnostics only. A per-tuple improvement cannot pass
the whole-clip gate. The secondary non-interior stratum uses the same measurement-visibility rule with
finite valid depths but no neighbour-jump exclusion; it cannot substitute for the primary.

## Single-map and nuisance controls (all fixed before outcomes)

1. Every fixed-order single candidate c0-c3, evaluated separately.
2. Median inverse-depth fusion across all four candidates, source-ID aligned, ignoring locally invalid
   values and retaining all-invalid locations as invalid. One fused source-depth tuple for the clip.
3. A source-only medoid: choose the candidate with the smallest average pairwise median absolute
   log-depth difference on jointly valid source pixels. Ties use candidate ID. No GT is used.
4. Scale-only family: for each m compute a source-only scalar a_m = exp(median(log(d_m/d_c0))) over
   jointly valid source crop samples. Form d_scale_m = a_m*d_c0. Compare its whole-clip oracle.
5. Scale-normalized candidate family d_m/a_m, including c0, with its complete oracle. This is a nuisance
   diagnostic, not a claim that independent depth scaling preserves full 3D consistency.
6. Per-target and per-tuple oracle diagnostics, clearly separated from complete candidates.

Photometric warp/generation scores are not part of this gate; missing geometry must not be replaced by
PSNR. A positive result will require a separate frozen generation protocol, including mode-ID permutation.

## Exact stop rule

Complete all predeclared candidates unless an engineering failure prevents valid execution. Missing files,
bad provenance, failed KPS or an empty primary support in any window yields INCOMPLETE/INVALID, never a
scientific negative. No windows may be removed after outcomes. Local invalid predictions remain penalized.

STOP_TESTED_FAMILY if any of these conditions holds:
- Whole-clip H < 0.10, or the improvement is not positive in both scenes.
- Relative improvement of the complete oracle over the better aggregate error of median-fusion and
  source-medoid single-map controls is <0.05.
- Relative improvement of the complete oracle over the best aggregate fixed order c0-c3 is <0.05.
  This optimistic diagnostic prevents a globally better processing order from being mistaken for a
  need for multiple modes; report FIXED_ORDER_REPAIR as an explanation when this nuisance gate fails.
- Relative improvement of the complete oracle over the scale-only oracle is <0.05, OR the scale-normalized
  complete-candidate oracle has <0.10 headroom over c0.

These additional 5% nuisance margins are design choices frozen before scoring, not established clinical
or statistical constants. Report exact values and all controls regardless of the verdict. A supported gate
is GO_TO_CONSUMER_PILOT only, not method validation. At most two scenes support descriptive effects;
do not claim population significance from bootstrapping their overlapping windows.
No automatic expansion of candidates, tuning after scores, new training, or renamed second attempt.

## Run, tests and outputs

Stage: work/W1_joint_geometry_20261010_codex in the isolated codex/week1-geometry-modes worktree.
Predictor helper is developed separately on codex/week1-candidate-runner and integrated before freeze.
Output tree: receipts/, candidates/, logs/, scores/, RESULT.md. Exact commands go in RUN_COMMANDS.sh.
Run repository unittest suite and new scorer tests (analytic camera projection, fixed invalid denominator,
occlusion support, whole-clip versus pixel oracle, source-order restoration, and seal mismatch). No root
linter is configured. Small deterministic tests are implementation checks, not measured research results.
S141 final-result status is reported separately; no intermediate training loss is called an evaluation.
Final claims keep new_method_validated=false and novelty_authorization=NONE.
