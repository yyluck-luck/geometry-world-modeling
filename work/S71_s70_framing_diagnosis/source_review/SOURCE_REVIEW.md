# S71 bounded source review

PASS, no source blocker. Different-author review by `/root/c2_v9_source_primary`, 2026-09-09 05:05:02 UTC to 2026-09-09T05:06:35.693837+00:00. Both exact source files are 0444 and match the supplied hashes. Full source/contract inspection and a standard-library AST compile were performed; zero image bodies, SIFT calls, H fits or models.

The loops cover targets20–23 × reference/A0, reference/B and A0/A1: all12 pairs from16 fixed native RGB images. Both-direction L2 nearest-two matching uses strict ratio<0.75 followed by mutual identity; every retained pair is saved with keypoint IDs and coordinates. OpenCV points are `(x,y)`, displacement is destination−source, and row-vector projection `[x,y,1] @ H.T` correctly maps source to destination. Quantiles are p25/p50/p75/p95. Spans divide by575, the coordinate extent, not pixel area. RANSAC uses the frozen min8, 3px, 2000 iterations, confidence0.995 and seed71 settings. Empty/insufficient/no-finite fits remain explicit; failed A/A controls produce a nonzero completion status. The create-only directory and caught exceptions retain available results. Root's existing60-second external supervisor records hard timeout/termination separately; an inner receipt is not promised after a forced kill.

The scientific restriction is appropriate: these are hypotheses about feature correspondence on already-viewed outputs. Sparse/repeated/hallucinated matches and parallax can mislead a homography. Residuals are in-sample, conditional on RANSAC's selected consensus, and the 3px fitting parameter is not an independently guaranteed bound on every refined residual. Neither a low residual nor nonzero displacement establishes a physical camera error, a planar scene, true3D, or a memory mechanism. No warped score replaces S70.

After the actual run, the saved coordinates, H and masks suffice for the planned limited independent arithmetic: verify every pair's counts/control result, displacement statistics/spans and homogeneous projection/residuals. That review must not claim independent correspondence truth or feature regeneration. No fixture suite was needed for this straightforward fixed arithmetic.

Exact inputs:

- CONTRACT.json SHA `0a38f1bf3e3e56622f4937e6684b2bad3cc3138fcae5ee8896e5ba31ba366707`
- measure.py SHA `47410568a1719066a7775a6c20701ca08e8f91b1c7fd8d5b284ef9462050c78f`
