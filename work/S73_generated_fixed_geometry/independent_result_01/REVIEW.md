# S73 independent saved-coordinate result review

PASS_S73_INDEPENDENT_ARITHMETIC: 309/309 checks passed, with no discrepancy. This verifies numerical consistency, not correspondence truth or achieved camera pose. Reviewer `/root/c2_v9_source_primary` differs from measurement author `/root`.

One independent run used the lexical absolute venv executable on 2026-09-09, 07:38:24.447954–07:38:24.586540 UTC. External return 0, no timeout, empty stderr; external duration 0.138443 seconds and internal duration 0.063070 seconds. The external limit was fixed at 60 seconds. No retry or feature/model rerun occurred. The input is the successful `execution_02`; failed `execution_01` remains untouched.

The source reuses only this reviewer's S72 scalar helpers. F was reconstructed from the original bound S69 optical cameras and S68 K using world-ray triple products, independently of author F values. Every point-to-line distance was recomputed with scalar arithmetic. Sorted quantiles, integer threshold counts, coverage cells, availability denominators and three-way anchor joins were recomputed. NumPy was used solely for NPZ I/O and byte/descriptor handling. F comparisons use abs1e-12/rel1e-10; residual/statistic comparisons use abs1e-8/rel1e-10. Count and fraction checks are exact. Maximum observed arithmetic difference was 6.679101716144942e-13 pixels in a paired delta.

All 12 rows and 1,788 matches are retained and numerically valid. All original S72 real-row fields remain exactly equal. Every saved source index/xy maps to the common current 1,239-entry anchor table, including all observed old real IDs; pair lengths and unique source IDs agree. This validates saved-table consistency with the recorded SIFT replay assertion; it does not independently re-extract features or verify descriptor bytes. All eight generated rows have zero matches at or below each fixed 2/5/10 px cutoff. Those statements concern the accepted matches, not every image point.

| Target | Matches real / A0 / B | Median symmetric line error (px), real / A0 / B | Shared-valid anchor IDs |
|---|---|---|---:|
| 20 | 323 / 249 / 275 | 1.341619 / 21.654946 / 27.667711 | 92 |
| 21 | 160 / 195 / 241 | 3.162289 / 75.692658 / 64.210287 | 48 |
| 22 | 80 / 86 / 38 | 1.411655 / 146.125451 / 124.604210 | 6 |
| 23 | 75 / 38 / 28 | 4.224642 / 210.101816 / 224.644299 | 0 |

Every match-availability fraction uses N=1,239. Error quantiles use valid matches; threshold count/N and count/valid remain separate. All four raw intersections equal their common-valid subsets: 92, 48, 6, 0 IDs. No invalid match was silently dropped. Target20 paired signs are 90 positive and 2 negative for each generated arm; targets21/22 have all 48/6 positive. Target23 has no common anchors, so its paired median is undefined.

**Both predefined all-four-positive events remain unknown (`null`).** Their A0 paired medians are 19.349535, 70.621967, 148.586805, undefined; B medians are 25.004262, 58.473485, 120.964397, undefined. Three observed positive medians do not turn an undefined four-target event into success. The six-ID target22 intersection is especially limited, and target23's missing intersection is neither zero error nor proof of correctness/incorrectness.

The verification read 12 unique files / 1,055,407 bytes, including the saved coordinate receipts. Two NPZ containers total 90,210 bytes; only ids, optical c2ws and K_pixels_576 were decoded, totaling 1,260 array bytes. No PNG body/header, descriptor body, other appearance field, Torch/model or weight was read. The upstream nine-PNG readlist (4,075,371 bytes) was checked as recorded metadata, not independently rehashed. Actual external argv confirms the corrected venv path and fresh namespace; stdout, return and timing agree.

These outcomes provide a conditional descriptive comparison under the requested F. They do not isolate memory selection, recover actual generated camera poses, validate full optical calibration, or establish a new method. The subset is selected by matching outcomes; common anchor IDs can map to different or false physical correspondences. Approximate K, S72 real-control outlier tails, appearance/texture changes and feature availability remain limitations.

Final evidence:

- Successful worker input SHA256: `8a953c7a477ddbc84721be4fe6f9974e923a45cd6718c840a2dfb149b958ba01`.
- Independent receipt SHA256: `5357b283c494c9353b01a210317a17f9216ae9eb856d407aa1c88ec02d40f43a`.
- Independent external receipt SHA256: `bf2951b34721b39157c63edd1f81282f438daca7c13cd9444a8707bb8832d636`.
- Independent source SHA256: `6bf0dd714c093da79e95b2bb4df126a0141aee41fc980350c6a1b9bad5847e5a`.

Final self-check: 2026-09-09T07:39:21.425502+00:00. All artifacts are mode 0444; prior source and failed/successful worker evidence remain unchanged.
