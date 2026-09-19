# S72 independent numerical review

PASS for arithmetic consistency: 125/125 checks passed, no discrepancy. This is not a camera/calibration PASS. Reviewer `/root/c2_v9_source_primary` is different from measurement author `/root`.

Exactly one independent execution ran 2026-09-09 06:41:29.094187–06:41:29.235206 UTC, return 0, no timeout, empty stderr. External duration was 0.140874 seconds; internal duration including the NumPy import was 0.071209 seconds. The preset external limit was 60 seconds. No retry, image read, SIFT extraction, model, or author-function import occurred.

The verifier read the pinned original S69 optical camera NPZ and S68 history19 K field, checked their body descriptors, and rederived relative R/t from scalar dot products. It obtained each F entry independently as a world-ray scalar triple product, rather than reusing the worker's skew/matrix multiplication. It used scalar Gauss-Jordan K inversion, scalar point-to-line distances, sorted linear quantiles, integer threshold counts and direct spatial-cell counting. A second direct ray-triple evaluation checks the constraint numerators. NumPy was used only for NPZ decoding and array metadata/byte conversion.

All four targets and all 638 matches remain. Every line pair was numerically valid; invalid count is zero for each target. Counts, keypoint-ID domains and uniqueness, native xy shape/finiteness, R/t/baseline, raw/normalized F, both per-point distances and their mean, all quantiles, exact ≤2/5/10 px fractions, spans and grid cells agree. Maximum observed arithmetic difference was 4.0467629247586956e-13 pixels. Matrix/baseline comparisons used abs1e-12/rel1e-10; residual/statistic comparisons used abs1e-8/rel1e-10, solely as numerical tolerances.

| Target | Matches | Baseline (m) | Median (px) | p95 (px) | ≤2 px | ≤5 px | ≤10 px | Maximum (px) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 323 | 0.110376 | 1.341619 | 4.194949 | 73.99% | 95.36% | 97.52% | 299.802571 |
| 21 | 160 | 0.197094 | 3.162289 | 6.137990 | 33.12% | 85.62% | 98.12% | 109.223155 |
| 22 | 80 | 0.271672 | 1.411655 | 3.357396 | 71.25% | 96.25% | 96.25% | 298.343463 |
| 23 | 75 | 0.347208 | 4.224642 | 121.102955 | 32.00% | 58.67% | 84.00% | 422.454103 |

These are means of the two point-to-epipolar-line distances, not squared Sampson errors. Denominators include all numerically valid matches. Baselines are far above the predefined 1e-9 m insufficiency threshold; the smallest normalized line norm is about 0.00413, above 1e-12. Valid denominators do not establish correct matching. The target23 p95 of 121.103 pixels, its 16% of matches above 10 pixels, and the large maxima in every pair are retained. Modest medians must not erase those tails or imply that all matches support the declared camera model. No extra geometric filtering or success threshold was applied.

The single verification readset is 10 unique files / 353,391 bytes. Of these, the two NPZ containers total 90,210 bytes; exactly three fields were decoded: ids (72 B), optical c2ws (1,152 B), and K_pixels_576 (36 B), totaling 1,260 array bytes. Other appearance fields and camera timestamp arrays were not decoded. Whole-container SHA reads necessarily include serialized bytes of unused fields. Preliminary inspection read JSON only; final checks read this verifier's outputs. No image bytes were read here.

The worker's nine-entry input readlist matches the fixed source/metadata/camera/K/five-PNG identities; its 2,305,568 image bytes are upstream recorded reads. The worker's anchor tensor SHA matches the independently read accepted S68/S69 metadata, confirming its recorded assertion against the original history19 tensor. This audit did not recompute anchor pixels or rehash the exported PNG; its export SHA remains an upstream claim. Source, contract, outer return, stdout/stderr and actual completion times are consistent.

This result verifies the computation from accepted requested cameras and saved SIFT coordinates. It does not independently validate feature-match truth, physical calibration, requested-pose obedience by generated images, or memory causality. Approximate K/no undistortion, interpolated poses, incorrect matches, moving content and spatial support remain alternative explanations for residuals. The real fr2_desk controls support a qualified descriptive observer, not an automatic camera-correct verdict.

Final evidence:

- Worker input SHA256: `7711703643cb03e447a05fcd452142912d727e659372561d1efe4b7903d13d53`.
- Independent receipt SHA256: `c988b0e75aab7283efdee1afe512d28d9e13b8d44d52acf07b5d22b124223be5`.
- Independent external receipt SHA256: `c33651156723352d9a3610aa20df173afc60fc6553da33d34cc22cfad684c707`.
- Independent source SHA256: `856e6f6295809415238bac520acddb8114fdcc0604cb5369c11feea4fdbe1eac`.

Final self-check completed 2026-09-09T06:42:47.899978+00:00. All review artifacts are mode 0444, with older artifacts unchanged.
