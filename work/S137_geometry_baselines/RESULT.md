# S137 result — training-free geometric predictors beat the frozen VMem on this panel (PSNR and SSIM)

Protocol: `PROTOCOL.md`. S137a was exploratory (run before the protocol). S137b was pre-registered. CPU only.
16 windows × 4 targets, VMem static contexts (offsets 0,15,30,45), C9 scorer.
`new_method_validated=false`, `novelty_authorization=NONE`.

## Numbers (mean PSNR over 16 windows; B2 rows use the corrected pixel-centre mapping, Amendment 2;
`SUMMARY_s136ref_v2map.json`. Old-mapping values in `SUMMARY_c9ref.json` / `SUMMARY_s136ref.json` differ by ≤ 0.016 dB.)
| predictor | needs | PSNR (dB) |
|---|---|---|
| VMem static, native (S136, 8 seeds; C9 2-seed 14.56) | frozen generator | 14.36 |
| VMem static, gl (S136, 8 seeds; C9 2-seed 15.25) | frozen generator | 15.25 |
| B0 copy nearest context frame | RGB + pose | 15.52 |
| B2 CUT3R depth, VMem alignment as is (orig) + warp | RGB + pose | 15.68 |
| B2 CUT3R depth, S133 fix + warp | RGB + pose | 18.33 |
| **B2 CUT3R depth, KPS + warp** | **RGB + pose** | **20.09** |
| B1 dataset depth + warp (RGB-D upper bound) | RGB-D + pose | 22.05 |

Window-bootstrap 95% CIs (10k), corrected mapping, against the 8-seed S136 static:
- B2-kps − B2-fix **+1.75 dB [+0.85, +2.82]**, 14/16 windows. B2-fix − B2-orig +2.65 [+1.01, +4.48].
  B2-kps − B2-orig +4.41 [+2.74, +6.35], 16/16.
- B2-kps − VMem static: native **+5.73 [+4.70, +6.69]**, gl **+4.84 [+3.81, +5.88]**, both 16/16.
- B0 copy − VMem static: native +1.16 [+0.56, +1.79], 14/16. gl +0.27 [−0.29, +0.92], 9/16 (tie).

## Pre-registered decisions (S137b)
1. **Scale carries to pixels: CONFIRMED.** kps > fix > orig in mean, and kps ≥ fix in 14/16 windows (needed ≥ 10).
   KPS is the first scale repair here with a downstream image-space benefit.
2. **Geometry alone beats the frozen generator: CONFIRMED under the pre-registered panel rule**, against the
   8-seed S136 static (see above). This is a diagnostic PSNR contrast on this panel, not method validation.

## Reading
- On these short-baseline windows, frozen VMem is worse than copying the nearest history frame under native
  (a tie under gl). An RGB + pose geometric predictor (CUT3R + KPS + forward warp + nearest fill; it needs CUT3R and a
  known pose stream) is about 5 dB better. B2 is a direct geometric warp, not a capacity-matched generator control,
  so this is a diagnostic contrast, not causal evidence about VMem's internals (codex R250).
- SSIM agrees (S137c below): warp − VMem static +0.110 (gl) / +0.140 (native), 14–15/16 windows.
- Exposed panel, two scenes, one frozen consumer, forward-splat renderer with cracks. B1 is an RGB-D upper bound.
  Not a general claim about VMem or video world models.

## S137c (Amendment 1; 8 seeds, both sites; `results_c/S137C_ANALYSIS.json`)
Reference for warp4 = the v1-map B2-kps warps VMem was actually given (Amendment 2).
| contrast | Δ | 95% CI | wins | verdict |
|---|---|---|---|---|
| warp4_fill − B2-kps (VMem given aligned target-pose warps) | **+0.000 dB** | [−0.044, +0.053] | 7/16 | NO_MATERIAL_CHANGE |
| warp4_hole − B2-kps (holes mid-grey) | −5.427 dB | [−6.760, −4.002] | 0/16 | WORSENS |
| warp4_fill − static_gl | +4.829 dB | [+3.819, +5.853] | 16/16 | IMPROVES |
| warp4_hole − static_gl | −0.599 dB | [−1.869, +0.663] | 7/16 | INCONCLUSIVE |
| hybrid (warp where covered, VMem elsewhere) − B2-kps, gl / native | −1.289 / −1.818 dB | both < 0 | 3/16, 2/16 | WORSENS |
| SSIM warp − VMem static, gl / native | +0.110 / +0.140 | both > 0 | 14/16, 15/16 | IMPROVES |
| SSIM hybrid_gl − warp | −0.059 | [−0.084, −0.036] | 2/16 | WORSENS |

Reading: when its context sits at the target poses, VMem reproduces it (±0.05 dB). Pre-warping therefore lifts VMem by
+4.8 dB, but only because VMem copies the warp; it adds no refinement. Given grey holes it copies the grey instead of
inpainting. Its own content for uncovered pixels is worse than nearest-neighbour fill (PSNR and SSIM). On this panel
the generator does not add value on top of geometry.

## Exploratory (not pre-registered)
A naive 2×2 splat footprint (offsets 0..1) to close forward-warp cracks lowers PSNR. B1 drops 22.05 → 21.76 and B2-kps
20.08 → 19.73, probably from the half-pixel shift and blur. Kept at 1-pixel splats. Visual check of the warps
(14 w150, 14 w300): objects are aligned with the target, and cracks appear where the target camera is closer. A better
renderer would likely raise B2 further, so the B2 > VMem conclusion is conservative.

## Files (also)
`geometry_baselines.py` (B0/B1), `geometry_b2.py` (B2), `summarize_s137.py`, `BASELINES_gtdepth.json`,
`B2_{orig,fix,kps}.json`, `SUMMARY_c9ref.json`, logs.
