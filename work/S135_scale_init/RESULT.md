# S135 result — KPS scale init; VMem retrieval is pose-NMS; TF32; memory holes; convention detector

Owner standing authorization (2026-10-09). CPU only (local M3 Max) plus existing S134 receipts.
`new_method_validated=false`, `novelty_authorization=NONE`. Ideas were tested as they were formed. This file records
what was run and what came out, with the order kept honest.

## 1. KPS — known-pose dense scale initialisation (new, `kps.py`)
VMem presets every pose but lets dust3r fix the metric scale by registering ~5 PnP camera centres to them. KPS fixes
R and t from the known poses and solves only σ (CUT3R units per metre, plus focal in closed form). It minimises the
median dense reprojection residual of view j's CUT3R points (in view 0's frame) into camera j:
x_j ∝ R_j0·P + σ·t_j0. That uses ~10^5 points instead of 5 centres.
- Synthetic (`test_kps.py`, 9/9 pass): σ recovered within 15% for 3–8 cm baselines and σ from 0.02 to 40. With zero
  baseline the residual curve is flat, so unidentifiability is detectable.
- Real stage 1, 14 windows (`ARM_*.json`, `ARMS_SUMMARY.txt`). The metric is pixel-aligned: dataset depth mapped
  through VMem's crop and CUT3R's resize/crop, median of per-pixel ratios.

| arm | in [0.5, 2] | in [0.8, 1.25] | median ratio | median \|log r\| | median corr |
|---|---|---|---|---|---|
| gl orig (VMem as is) | 5/14 | 1/14 | 0.72 (5 blow-ups) | 2.90 | 0.976 |
| gl / native S133 fix | 12/14 | 3/14 | 0.665 | 0.410 | 0.977 |
| **gl KPS (free focal)** | **14/14** | **13/14** | **0.946** | **0.055** | 0.977 |
| gl KPS-K (known K) | 13/14 | 10/14 | 0.926 | 0.130 | 0.977 |
| native KPS-K | 1/14 | 0/14 | ~1000 (σ at grid floor) | 6.94 | 0.974 |

- KPS cuts the median |log ratio| from 0.410 to 0.055, i.e. median relative scale error from about 33.5% to 5.4%
  (metric named explicitly after codex R250). Depth shape (correlation) is unchanged, as expected.
- Known intrinsics are worse than a fitted focal. CUT3R's pointmaps carry their own implicit focal, and the true K
  mismatches it.
- niter 0 and 400 gave identical ratios on the 4 windows tested (`STAGE1_*_niter0.json`). Root cause (found by codex
  R250, verified in S138): VMem's fork detaches `im_depthmaps` in `get_depthmaps`, so the alignment never optimises
  depth at all. Initialisation alone sets the map.

## 2. KPS as a pose-convention detector (new)
For each window, compare the minimum KPS reprojection error with the poses converted to gl and with them left native.
**gl is lower in 14/14 windows** (2.5–28 px vs 19–61 px). Under native, σ collapses to the grid floor because the
translation direction is inconsistent with CUT3R's camera frames. This independently confirms C8's B/C finding that
the dataset poses are OpenCV and VMem needs the gl input. It uses no depth ground truth.

## 3. VMem's retrieval is pose-distance NMS over a surfel-visibility candidate set
Code (`modeling/pipeline.py`, get_context_info): visible surfels only form a candidate multiset. Ranking is pose
geodesic distance (rotation angle + 0.1·translation in metres), and the four contexts come from pose-distance NMS.
`pose_only_retrieval.py` re-implements the post-render steps.
- With the repaired (S133-fix) map, fp32 pose-only NMS over the frames that own surfels **equals VMem's actual
  selection on the RTX 3090 in 14/14 windows** (re-run independently by codex R250). Every memory frame is a
  candidate in 13/14 windows.
- Against the H800 contexts the fp32 reimplementation matches 9/14. With TF32 input rounding (round-to-nearest)
  emulated in the 3×3 rotation product it matches **14/14**; truncation gives 7/14. CUT3R's `croco.py` globally sets
  `allow_tf32 = True`. This is a strong numerical explanation of the H800/3090 divergence, but not an instrumented
  proof of the kernel used.
- With the broken map, the candidate set shrinks to 4–5 frames in exactly the windows whose contexts the fix changes.
  That is why a ×300–700 blow-up leaves most contexts unchanged: at those depths every frame stays "visible".

## 4. Memory holes from the project's priming schedule
S111's priming adds 5 frames, then 7 at once. VMem's construct only creates surfels for the last
`target_num_frames=4` frames, so bank offsets 25/30/35 never enter memory. The static arm's offset 30 is therefore
unreachable for every sealed memory arm. VMem's intended cadence is 4 frames per construct. S136 tests a chunked
schedule.

## Consequences
- The report's memory-vs-static contrasts compare static against a pose-NMS selector restricted to 9 of 12 frames,
  run on a map that was broken in 8/14 windows but mostly irrelevant to the selection, and hardware-dependent in
  5/14 windows through TF32.
- On this panel, VMem's 3D memory acts as camera-orientation retrieval with a visibility filter. Geometry can only
  matter through that filter, which needs occlusion or out-of-view history the panel lacks. This scope comes from
  these receipts, not from all VMem regimes.

## Files
`kps.py`, `test_kps.py`, `repro_kps.py`, `run_arms.sh`, `summarize_arms.py`, `ARM_*.json`, `ARMS_SUMMARY.txt`,
`pose_only_retrieval.py`, `POSE_ONLY_native_fix{0,1}.json`, `STAGE1_*`.

## Addendum (2026-10-10): deterministic retrieval
Pose-only NMS computed with the geodesic in **float64** (numpy) on the repaired map (S134 native_fix1 receipts) equals the
actual RTX 3090 contexts in **14/14** windows and the H800 contexts in 9/14. Float64 and the 3090's fp32 give the same
selection; the H800 deviates in 5/14, consistently with TF32 rounding being permitted globally by CUT3R's croco.py.
A one-line fix makes VMem's retrieval hardware-independent: compute `geodesic_distance` in float64, or run retrieval
with `torch.backends.cuda.matmul.allow_tf32 = False`. Not applied to any S136/S139 canonical run, which keeps VMem as is.
