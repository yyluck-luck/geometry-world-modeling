# S137 result — training-free geometric predictors beat the frozen VMem on this panel

Protocol: `PROTOCOL.md`. S137a was exploratory (run before the protocol). S137b was pre-registered. CPU only.
16 windows × 4 targets, VMem static contexts (offsets 0,15,30,45), C9 scorer.
`new_method_validated=false`, `novelty_authorization=NONE`.

## Numbers (mean PSNR over 16 windows; `SUMMARY_c9ref.json`)
| predictor | needs | PSNR (dB) |
|---|---|---|
| VMem static, native (C9, H800, 2 seeds) | frozen generator | 14.56 |
| VMem static, gl (C9, H800, 2 seeds) | frozen generator | 15.25 |
| B0 copy nearest context frame | RGB + pose | 15.52 |
| B2 CUT3R depth, VMem alignment as is (orig) + warp | RGB + pose | 15.68 |
| B2 CUT3R depth, S133 fix + warp | RGB + pose | 18.35 |
| **B2 CUT3R depth, KPS + warp** | **RGB + pose** | **20.08** |
| B1 dataset depth + warp (RGB-D upper bound) | RGB-D + pose | 22.05 |

Window-bootstrap 95% CIs (10k):
- B2-kps − B2-fix **+1.73 dB [+0.83, +2.79]**, 14/16 windows. B2-fix − B2-orig +2.67 [+1.01, +4.51].
  B2-kps − B2-orig +4.39 [+2.73, +6.32], 16/16.
- B2-kps − VMem static: native **+5.52 [+4.40, +6.50]**, gl **+4.83 [+3.59, +6.08]**, both 16/16.
- B0 copy − VMem static native +0.96 [+0.33, +1.57], 13/16. Against gl: +0.28 [−0.43, +1.09], 9/16.

## Pre-registered decisions (S137b)
1. **Scale carries to pixels: CONFIRMED.** kps > fix > orig in mean, and kps ≥ fix in 14/16 windows (needed ≥ 10).
   KPS is the first scale repair here with a downstream image-space benefit.
2. **Geometry alone beats the frozen generator: holds against the C9 2-seed reference.** Final verdict against the
   8-seed S136 static is pending (added when S136 scores exist).

## Reading
- On these short-baseline windows, frozen VMem is worse than copying the nearest history frame (native; tie under gl).
  A deployable RGB + pose geometric predictor (CUT3R + KPS + forward warp + nearest fill) is about 5 dB better.
  This turns C8's "consumption failure" into a number: the evidence VMem receives supports ~20 dB with no learning,
  and VMem delivers ~15 dB.
- PSNR rewards pixel alignment. Warping is aligned by construction, while a generator can produce plausible but shifted
  content. A perceptual metric could narrow the gap; this is not measured yet. The claim is about PSNR, the project's
  metric throughout.
- Exposed panel, two scenes, one frozen consumer. Not a general claim about VMem or video world models.

## Files
`geometry_baselines.py` (B0/B1), `geometry_b2.py` (B2), `summarize_s137.py`, `BASELINES_gtdepth.json`,
`B2_{orig,fix,kps}.json`, `SUMMARY_c9ref.json`, logs.
