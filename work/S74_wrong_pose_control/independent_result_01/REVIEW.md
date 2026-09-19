# S74 independent wrong-label arithmetic review

PASS_S74_INDEPENDENT_ARITHMETIC: 146/146 numerical/identity checks passed; no discrepancy. Reviewer `/root/c2_v9_source_primary` is different from measurement author `/root`.

One run occurred on 2026-09-09, 08:11:24.411581–08:11:24.540825 UTC, return 0, no timeout, empty stderr. External time was 0.129079 seconds; internal time 0.071327 seconds, under the preset 30-second bound. No rerun, image/SIFT/model execution or alternative label permutation occurred.

The verifier independently reconstructed F from the original pinned S69 optical camera/K data using scalar world-ray triple products and scalar K inversion. Unit-F separation used a direct sum of nine squared component differences/sums and square root, not author functions. Both correct and swapped point-to-line residuals were recomputed, despite the worker correctly reusing original correct values. Every old ID/xy and reused correct residual remains exactly preserved for all 638 matches. Source/target/common coverage, valid/invalid indices, every residual and paired delta, quantiles/maxima, threshold counts, M/V/N denominators, signs and event logic agree. The separation file's content and timestamp agree with the source-defined pre-residual stage.

F/separation tolerances were abs1e-12/rel1e-10; residual/statistic tolerances abs1e-8/rel1e-10. Counts, reused identities, invalid masks and denominator fractions were checked exactly. Maximum arithmetic discrepancy was 9.237055564881302e-13 pixels in a paired delta. These tolerances are numerical checks, not scientific effect thresholds.

The sign-invariant unit-F separations are 0.020504666496253637 for 20↔23 and 0.004955268938006605 for 21↔22. They are nonzero, dimensionless quantities in the fixed pixel coordinate system, not pose distances or pixel errors. No sufficient-separation threshold was applied.

| Actual→swapped target label | Matches | Correct median px | Wrong median px | Paired median wrong−correct px | Positive / negative / zero |
|---|---:|---:|---:|---:|---:|
| 20→23 | 323 | 1.341619 | 107.736411 | 105.664575 | 322 / 1 / 0 |
| 21→22 | 160 | 3.162289 | 38.875584 | 35.394241 | 157 / 3 / 0 |
| 22→21 | 80 | 1.411655 | 42.094455 | 40.807063 | 80 / 0 / 0 |
| 23→20 | 75 | 4.224642 | 98.670903 | 93.931676 | 71 / 4 / 0 |

All 638 matches are valid in both residual arms, with no paired deletion. **The fixed all-four-positive-paired-median event is true.** The negative deltas (1, 3, 0, 4 by target) remain; the result does not say every match gets worse. The event demonstrates sensitivity to this single predefined label permutation on the selected real correspondences. It does not certify calibration, match truth, a general wrong-pose detector, or the cause of S70's generated framing mismatch. The same-scene correlations, approximate K and real-control tails remain. It neither fills S73's empty target23 intersection nor changes S73's UNKNOWN events.

Read scope: 13 unique evidence/source/log/NPZ files, 650,428 bytes. The two NPZ containers total 90,210 bytes, with only ids (72 B), c2ws (1,152 B) and K_pixels_576 (36 B) decoded: 1,260 array bytes. NumPy was used for NPZ I/O/byte descriptors only; no other appearance arrays, pixel/image headers, descriptors, GT body or weights were read. Actual worker inputs were the two fixed accepted-real JSON files. Complete independent residual vectors, comparisons, source/input identities and timestamps are in receipt.json.

Final evidence:

- Actual worker receipt SHA256: `3e7c878265a7ff124a15f15db378ab2e71e2648a9d769bc424cfae5d09503c37`.
- Independent receipt SHA256: `1778794979e78d978ef38adf865cfac3254ea589d547a8128c78d3a9dbce1045`.
- Independent external receipt SHA256: `e95623b2a63747bfb6f6182ae0218f9b6187ae5117f19f04ee2fc566e6f5713b`.
- Independent source SHA256: `041e3a3f21e648834e20090237857b1cd2557a40fe698b9faea73b643527eb12`.

Final self-check completed 2026-09-09T08:12:09.460380+00:00. All review artifacts are mode 0444. Existing scientific outputs and frozen sources remain unchanged.
