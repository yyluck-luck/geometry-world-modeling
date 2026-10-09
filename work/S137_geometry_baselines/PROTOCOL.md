# S137 protocol — training-free geometric predictors vs frozen VMem

Owner standing authorization (2026-10-09). `new_method_validated=false`, `novelty_authorization=NONE`.

## S137a — already run (exploratory, recorded before this protocol was written)
`geometry_baselines.py`, CPU, 16 windows × 4 targets, VMem static contexts (offsets 0,15,30,45). Scorer and model-grid
transform copied from C9. The VMem reference is C9's H800 static scores (seeds 42/7).
- B0 copy (nearest context by VMem's pose geodesic): 15.52 dB, beats VMem static native in 13/16 windows.
- B1 dataset-depth forward warp + nearest fill: 22.05 dB, beats VMem in 16/16 windows.
- VMem static: native 14.56 dB, gl 15.25 dB.
B1 uses history-frame depth from the RGB-D dataset, so it is an RGB-D upper bound, not an RGB-only method.

## S137b — pre-registered here, before running
**Question.** Does a deployable, RGB + pose-only geometric predictor beat VMem? Does the scale repair carry through
to image quality?
**B2.** Run CUT3R on the four static context frames with their known poses (gl convention, as VMem would after the
convention fix) and a star graph rooted at frame 0. The global alignment is VMem's (niter 400, lr 0.01), with
INIT ∈ {orig (VMem as is), fix (S133), kps (S135)}. The optimised depth maps are mapped back to the 640×480 grid
(CUT3R's crop covers rows 60–420, cols 80–560; elsewhere is a hole). Forward-warp + nearest fill as B1.
No dataset depth is used.
**Metrics.** PSNR (C9 scorer), window = 4 targets. Compared against VMem static (C9 2-seed now; S136 8-seed when
available) and against B0/B1.
**Pre-registered expectations and decision.**
1. Scale carries to pixels if B2-kps > B2-fix > B2-orig in mean PSNR, with B2-kps ≥ B2-fix in ≥ 10/16 windows.
2. "Geometry alone beats the frozen generator" if B2-kps exceeds VMem static (native and gl) in mean, with
   window-bootstrap CI > 0 against the 8-seed S136 static when available. Otherwise reported against C9 2-seed only.
3. Every negative is reported as it comes.

## S137c — later (cluster), design only
Hybrid: warp where B2 has coverage, VMem output elsewhere. Warp-as-context: replace one VMem context with the B2 render
at the target pose. Each needs its own amendment before running.

## Amendment 1 (2026-10-09 ~17:15 UTC) — S137c pre-registered before any S137c run
Inputs: B2-kps model-grid warps for each window/target (`data/S137_warps`). Each holds `filled` (nearest-filled) and
`valid` (splat coverage). They are built from the four static context frames and the target poses only.
**c-1 Hybrid (CPU, after S136 scoring):** prediction = warp where valid, else VMem's S136 static output (per seed;
gl and native). PSNR vs C9 scorer reference. Compared with B2-kps (warp + nearest fill) and with VMem static.
**c-2 warp4 (GPU, both sites, 8 seeds split as S136, gl convention):** VMem conditioned on four *virtual* contexts:
the warps at the four target poses, with context poses = target poses. Two variants: `warp4_fill` (nearest-filled
warps) and `warp4_hole` (uncovered pixels set to mid-grey, 0 in VMem's [−1, 1] input). Same sampler, cfg and seeds
as static.
**Decisions (verdict rule: ±0.2 dB, window-bootstrap CI):**
- Consumption test: warp4_fill − B2-kps. WORSENS means VMem degrades even an aligned same-pose input (consumption
  loss). NO_MATERIAL_CHANGE means it preserves it. IMPROVES means it refines it, a training-free "warp-then-generate".
- warp4_* − static_gl: does geometric pre-warping help the frozen generator?
- hybrid − B2-kps: does VMem fill holes better than nearest fill?

## Amendment 2 (2026-10-09 ~19:00 UTC) — codex R250 corrections, before rerunning
- `geometry_b2.py` mapped CUT3R depth back to 640×480 without the pixel-centre term, shifting the lookup by about
  0.53 CUT3R px. Corrected: x = round(((u+0.5)·1.2 − 96)·512/576 − 0.5), y = round((v+0.5)·1.2·512/576 − 64 − 0.5).
  B2 (orig, fix, kps) is rerun with the corrected map. The corrected numbers replace the old ones in the summary;
  old files are kept as `B2_*_v1map.json`.
- warp4 consumed the v1-map warps. Its key contrasts are therefore reported against the v1-map B2-kps, the exact
  images VMem was given. The corrected B2 is reported separately.
- Wording: B2 is a direct geometric warp, not a capacity-matched generator control. Contrasts are diagnostic, not
  causal evidence about VMem's internal "consumption".
