# S72 exact-source review

PASS for the explicitly declared exploratory source, with a preprocessing limitation. This is not an image/geometry result. Author: `/root`; independent source reviewer: `/root/c2_v9_source_primary`.

The complete frozen script and contract were reviewed; stdlib compilation and metadata binding checks passed. Optical source→target pose, F direction and Frobenius normalization, both point-to-line distances and their mean in pixels are consistent. No extra VMem axis flip, per-arm scale, fitted F/H, RANSAC filtering or eight-match threshold is introduced. All four fixed pairs and insufficient baseline/no-match/invalid-line outcomes are retained. The source carries actual fr2_desk identities. Camera/K-cache and target-image pins match accepted metadata.

One distinction must remain explicit: the uint8 anchor uses OpenCV INTER_AREA, whereas the saved S70 target references used original Torch FP32 area preprocessing and truncation. Spatial size/crop geometry matches; numerical preprocessing equivalence does not follow. The contract deliberately declares OpenCV, so this is not source/contract drift. It is an additional qualification on observer results, because kernels/rounding can change features. This review cannot support an “identical S68/S70 preprocessing” claim. If that stronger claim is intended, use the original helper path before running.

Runtime values remain unobserved here. The source only decodes the camera archive's ids/c2ws and the appearance archive's K_pixels_576, although their whole container bytes are read for SHA verification. Caught exceptions preserve prior work; a forced external stop can leave a partial namespace. COMPLETE means diagnostic execution, including explicit insufficiency, rather than scientific PASS. Approximate K/no-undistortion, interpolated GT, sparse/false matches and dynamic objects continue to limit interpretation.

No scientific arrays, image headers/pixels, GT bodies, weights, model imports, feature extraction or geometry computation were consumed/executed by this source review. A later different-author arithmetic review can verify the saved known-F calculation; it will not prove correspondence truth or memory causality.

Source SHA256: `41d169c2db58353f441ebd2318394001ae134172f2b2fa52de1203dd740c143e`.

Contract SHA256: `4bcadd5c79e85d2e35c7b1b25e9a1e3fc4ef412b0c7c78741c834292595ca7c7`.

Review JSON SHA256: `3501bf883230d01d0748b971306309675f0f145ee9996659ce348ce5d78df162`.

Finalized at 2026-09-09T06:34:12.854317+00:00. Files are mode 0444.
