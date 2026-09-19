# S71 independent saved-coordinate result review

PASS for the specified arithmetic verification. Reviewer: `/root/c2_v9_source_primary`, different from the measurement author `/root`. All 305 comparisons passed; no discrepancy or blocker was found. This verifies saved-coordinate calculations, not the truth of the feature correspondences.

One execution ran on 2026-09-09 from 05:13:52.212956 to 05:13:52.287958 UTC, return 0, no timeout, empty stderr. External elapsed time was 0.074828 seconds; arithmetic elapsed time was 0.016543 seconds. No retry or feature extraction occurred.

The verifier used independently written standard-library arithmetic: sorted linear quantiles, signed destination-minus-source differences, per-axis extrema, `math.hypot`, and scalar homogeneous projection with `math.fsum`. It did not import the measurement script, NumPy, OpenCV, or model code. The recorded fit and inlier mask were held fixed; no homography was refitted. Absolute 1e-9 and relative 1e-12 comparison tolerances were numerical tolerances, not scientific acceptance thresholds. The largest discrepancy was 1.3612263489702613e-13 pixels.

All 12 ordered pairs, 4,459 matched point pairs, and 4,138 fitted-inlier residuals were checked. Counts, keypoint-ID bounds and one-to-one pairing, coordinate shape/finiteness/domain, all/inlier displacement quantiles, median x/y offsets, spans, normalized spans, finite homogeneous projections, every recorded inlier residual, and residual medians agree. All four repeat controls have exactly zero coordinate displacement; their fitted-H residuals are only floating-point roundoff.

| Target | Pair | Matches | Inliers | All-match median displacement (px) | Inlier residual median (px) |
|---|---|---:|---:|---:|---:|
| 20 | reference_A0 | 180 | 93 | 39.494 | 1.49126 |
| 20 | reference_B | 190 | 117 | 43.0724 | 1.49227 |
| 20 | A0_A1_repeat_control | 1281 | 1281 | 0 | 3.21555e-13 |
| 21 | reference_A0 | 122 | 48 | 107.86 | 1.19817 |
| 21 | reference_B | 78 | 28 | 115.835 | 1.32215 |
| 21 | A0_A1_repeat_control | 1172 | 1172 | 0 | 1.27106e-13 |
| 22 | reference_A0 | 25 | 11 | 200.693 | 0.689525 |
| 22 | reference_B | 23 | 10 | 196.769 | 1.18838 |
| 22 | A0_A1_repeat_control | 651 | 651 | 0 | 1.02476e-13 |
| 23 | reference_A0 | 3 | No fit | 373 | — |
| 23 | reference_B | 7 | No fit | 297.006 | — |
| 23 | A0_A1_repeat_control | 727 | 727 | 0 | 3.45765e-13 |

The eight reference/generated comparisons contain six descriptive fits and two insufficient fits. Target 23 retains only 3 and 7 matches and no H. At target 22, only 11 and 10 inliers support the fits; their source y-spans cover about 18.7% and 15.4% of the coordinate extent. Neither low fitted residuals nor the sparse-match displacement medians establish whole-frame motion, camera obedience, scene planarity, or a memory mechanism. Refined RANSAC inliers are not additionally required to satisfy a new hard 3-pixel residual cutoff.

The verification consumed seven unique evidence/source/log files totaling 1,217,779 bytes, including the 1,204,088-byte coordinate receipt. The exact readlist, identities, per-statistic comparisons, independent residual vectors, and actual times are in `receipt.json`. Preliminary inspection and final identity checks read these same evidence files again. No PNG, scientific tensor, depth, weight or model body was read. The upstream 16-PNG / 7,219,446-byte readlist was checked only as recorded metadata against the fixed contract; image identities were not independently rehashed here.

The actual external execution, worker receipt, accepted source and contract, versions, stdout and empty stderr are mutually bound. Source files and inputs remain unchanged. This is a different-author team arithmetic audit of the saved exploration, not independent validation of SIFT correspondences or an external model replication. It does not change S70 scores or establish a new method.

Final evidence:

- Worker input SHA256: `33b6d6fa066aff7ba0e2857a8d21f954d2d410dca46aed43aac839c32277dff6`.
- Independent receipt SHA256: `180ae3f5b5974cc9b0806a5985720635e098772b388570671a7f0261558d471f`.
- Independent external receipt SHA256: `795dddd9e046ba2b0b66c1f8d153ceb3b7160aca8215cdcd56db606bf4dd8650`.
- Independent recomputation source SHA256: `3e67c9cd2f0d69066c58b34e91916ec303db18e07b78cd4980aaee7da626e12a`.

Final identity checks completed at 2026-09-09T05:14:55.715904+00:00. All review artifacts are immutable mode 0444.
