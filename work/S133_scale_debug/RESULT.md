# S133 result — the surfel scale blow-up is a silent PnP fallback in VMem's surfel construction

Protocol: `PROTOCOL.md` (owner-authorized 2026-10-09). Local CPU, FP32, stage 1 only (first surfel
construction, 5 frames, niter 400, lr 0.01). Not a method validation.
`new_method_validated=false`, `novelty_authorization=NONE`.

## Root cause (verified by reproduction and instrumentation)
1. VMem pairs every frame with frame 0 (star graph), then calls dust3r global alignment with `init="mst"`
   although all camera poses are preset.
2. MST fixes view 0 and recovers views 1–4 with `fast_pnp`, using only pixels with CUT3R confidence > 3.
3. On these 3DMatch frames CUT3R confidence is often low (median 1.0–1.8 in the failing windows), so the
   PnP mask is empty or tiny, `fast_pnp` returns None, and `minimum_spanning_tree` **silently substitutes
   the identity pose**.
4. `align_multiple_poses` then registers the (partly) coincident MST camera centres to the known poses
   with a similarity transform. With all centres at the origin, s ≈ 300–700 (blow-up); with some at the
   origin, s ≈ 0.02–0.08 (collapse). The point cloud is multiplied by s and 400 fixed-pose iterations do
   not undo it. Stage 2 inherits the depths through `preset_depth`.

## 14-window result (median over 5 bank frames of optimized depth / dataset depth)

| window | min CUT3R conf median | PnP ok (orig) | ratio orig | s orig | ratio fix | s fix |
|---|---|---|---|---|---|---|
| scene_13 w50  | 3.33 | 4/4 | 0.445 | 0.47 | 0.445 | 0.47 |
| scene_13 w100 | 1.43 | 2/4 | **0.074** | 0.075 | 0.875 | 0.894 |
| scene_13 w150 | 1.64 | 0/4 | **877** | 707 | 0.700 | 0.606 |
| scene_13 w200 | 1.81 | 2/4 | **0.038** | 0.032 | 0.637 | 0.516 |
| scene_13 w250 | 1.42 | 0/4 | **371** | 315 | 0.518 | 0.455 |
| scene_13 w300 | 1.46 | 0/4 | **646** | 546 | 0.898 | 0.797 |
| scene_13 w350 | 1.49 | 0/4 | **389** | 339 | 0.771 | 0.678 |
| scene_14 w50  | 2.05 | 4/4 | 0.644 | 0.525 | 0.604 | 0.492 |
| scene_14 w100 | 1.11 | 2/4 | **0.019** | 0.018 | 0.542 | 0.478 |
| scene_14 w150 | 1.03 | 0/4 | **508** | 511 | 0.333 | 0.331 |
| scene_14 w200 | 2.91 | 4/4 | 0.568 | 0.528 | 0.573 | 0.533 |
| scene_14 w250 | 3.86 | 4/4 | 0.801 | 0.787 | 0.801 | 0.787 |
| scene_14 w300 | 5.13 | 4/4 | 0.772 | 0.802 | 0.772 | 0.802 |
| scene_14 w350 | 5.54 | 4/4 | 0.906 | 0.873 | 0.906 | 0.873 |

Values are from the `native` arms. The `gl` arms are identical to three significant figures: flipping camera
axes does not move camera centres, so the pose convention cannot cause or cure this failure.

- PnP success count separates the catastrophic classes: 0/4 → blow-up (5/5), 2/4 → collapse (3/3). The six 4/4
  windows have no catastrophic failure (ratios 0.445–0.906), though 13 w50 at 0.445 is below the [0.5, 2] gate.
  (Wording corrected after codex R250.)
- The blow-up windows are exactly the five C8/C9 windows. Magnitudes agree with the H800 runs to the same
  order (CPU 371–877 vs C8 render 380–770).
- **New: three collapse windows** (scene_13 w100/w200, scene_14 w100) are the same bug with the opposite sign.
  The H800 C8 log confirms it independently: stage-1 render depth max 0.23 / 0.10 / 0.13 m in these windows
  versus 1.0–3.4 m in normal ones (`work/S130_C8_diagnostics/remote_support_609623/support-609623.out`).

## Decision (rules fixed in PROTOCOL.md before the 14-window run)
- Blow-up removed: **yes**. Fix arms have 0 windows with ratio > 10 (orig: 5 > 100).
- Scale certified, [0.5, 2] in ≥ 12/14: **met exactly, 12/14** (orig 5/14). The two failures are
  scene_13 w50 (0.445, unchanged by the fix) and scene_14 w150 (0.333).
- Residual: the fixed scale is biased low (median ratio 0.668; corrected from "0.70" after codex R250). This is a separate, smaller problem, consistent
  with similarity registration over 4–7 cm baselines. Per protocol it is not tuned here.

## What this changes
In 8 of the 14 panel windows, VMem's spatial memory was built on a point cloud mis-scaled by more than 10×
(5 windows ×300–900, 3 windows ×0.02–0.08). C8's harness reproduced the sealed context lists 14/14 with this
pipeline, so the sealed memory-arm retrievals (S103/S111, and the report's `memory_* − static` contrasts)
were selected from this broken map in those windows. The map was malfunctioning in those windows. Whether that changed the
retrieved contexts is a separate question: S134/S135 later found the contexts unchanged in most of them. The report should say so. The C8 "consumption failure" reading and
the C9 surfel diagnostics need re-reading in the same light.

## Limitations
- Stage 1 only. Stage 2, retrieval, and generation with the fix are not run.
- Local CPU, not byte-identical to H800, but the same windows fail with the same order of magnitude.
- The ratio checks scale only, not depth shape. Own-render depth correlation was not recomputed.
- The fix is a minimal candidate. It is not upstream VMem behaviour, and any downstream result using it must
  be labelled as a patched consumer.

## Files
`repro_stage1.py` (instrumented reproduction), `STAGE1_{native,gl}_fix{0,1}.json` (all per-window probes:
s, MST centres, PnP mask sizes, confidence, depth medians), `log_*.txt`, `STAGE1_REPRO.json` (smoke runs).
