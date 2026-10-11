# P1: Cross-pair residual-band fusion — frozen 2026-10-10T17:51Z

Status: FROZEN before any new pixel analysis. Exploratory falsification pilot; not a new-memory or CCF-A novelty claim. Owner authorized one bounded distinct pilot after S141. B is stopped; the W2 source selector stays closed. No generation, training adapter, context selection, or S143 work is permitted here.

## Hypothesis and scope

The relative reliability of the existing geometric rendering and video-generation residual depends jointly on image region and spatial frequency, and a small policy learned on other traversals transfers to a held-out traversal. If a six-coefficient policy cannot outperform simpler equally trained fusion, retire this exact implementation. This does not refute all fusion families or source-adaptive policies.

This is a spending gate for a possible future source-heldout reliability estimator. The present experiment is supervised across traversal pairs, not source-only adaptation. It cannot establish novelty: adaptive geometric/diffusion fusion and frequency-aware guidance already exist.

## Fixed data and allowed inputs

- Reuse the complete S140 confirmation plan, its 24 chess windows, and archived generation arm `mode=W2, strength=0.5`. That historical sampler arm name is distinct from the retired W2 source-selector project; no W2 jobs will be executed.
- Use existing G arrays in `/mnt/gluster_dcpu/yiyangliu/gwm_s134/out/s140_confirm_tacc/gen`, filled RGB warp W and original binary valid mask M in `data/S140_warps_chess`, and the exact target RGB preprocessing from `score_s140.py`.
- The three target sequences are seq-02, seq-03 and seq-05. Pair is fixed by `POSE_ARMS.json`. Leave one complete sequence pair out; fit on the other two pairs using seeds 3,4 only; evaluate the excluded pair using seeds 5,6 only. Rotate all three folds. No target from a held-out pair may enter that fold's training sufficient statistics. Verify target/context reference disjointness across folds before execution. The chess room is previously exposed, not an unseen scene.
- G uses the original per-frame `pred_u8` conversion, then uint8/255; W uses filled uint8/255. Thus G and W baseline scores are exactly reconcilable with S140. No query depth or geometric ground truth is loaded. Training target RGB is explicit supervision. Test RGB is read only after all fold coefficients and all test predictions are sealed.
- Hash exact plan, pair mapping, raw generation arrays, warp files, target RGB, original receipts, baseline score and source files. Verify G hashes against archived run receipts before execution. Record versions, code/protocol/input fingerprint and persistent job identity before dispatch.

## Fixed policy and equally trained controls

Spatial Gaussian filters use SciPy ndimage, float64, reflect boundaries, sigma 2 and 8, truncate 4; never filter time or channels. For R=G-W, P0=L8(R), P1=L2(R)-L8(R), P2=R-L2(R).

Candidate F = clip(W + sum_b [M*a_covered,b + (1-M)*a_hole,b]*Pb(R), 0, 1). Coefficients are shared over RGB, seeds and windows within a fold, each bounded [0,1]. Fit the complete **preclip** RGB squared-error objective, retaining all band cross-terms. Equal weighting of window/seed examples; each has four equally weighted frames at the same resolution. Solve box-constrained quadratic normal equations by active-set enumeration, with deterministic tie ordering. No iterative tuning. This is not an oracle or a certified bound on clipped-output PSNR.

Controls, all mandatory:
1. W, unchanged warp.
2. G, unchanged archived generation.
3. constant: one learned residual coefficient.
4. region: two learned covered/hole residual coefficients.
5. bands: three learned band coefficients shared across regions.
6. covered_G: fixed covered G / holes W paste.
7. lowW_highG: fixed L8(W)+(I-L8)(G).
8. lowG_highW: fixed L8(G)+(I-L8)(W).
9. smoothW: spatial sigma=1 Gaussian(W), reflect, truncate=4.
10. medianW: spatial 3x3 median(W), reflect.
11. smoothG: spatial sigma=1 Gaussian(G), reflect, truncate=4.

Learned controls use identical training folds, seeds, full preclip loss and [0,1] bounds. Candidate and controls are clipped and quantized to uint8 before scoring. Do not select controls after viewing outcomes.

## Metrics, gates and concentration

Primary: four-frame pooled RGB PSNR per seed, then mean of seeds 5,6 per window, then equal window means. Never pool SSE across seeds instead. SSIM uses original S140 luminance, Gaussian 11/sigma1.5, valid interior, mean over frames. Save per-window/per-seed values, coefficients, training sufficient statistics and output hashes. Report descriptive 10,000-window bootstrap RNG0, and per-pair means; three pairs do not support strong generalization inference.

All numerical thresholds below are ANALYTICAL preregistered decisions, not results. Continue only if **all** hold:
- Mean candidate PSNR minus every simpler control >= 0.2 dB.
- Mean candidate SSIM minus W >= 0, and minus the strongest control by overall PSNR >= 0. Ties resolved by the control order above.
- Relative to that strongest control, at least two of three pair means are positive, and no pair mean is below -0.2 dB.
- After removing the two windows with largest candidate-minus-strongest-control gains, remaining equal-window mean is >=0.1 dB. Report also top-two share of total positive gains.

Any failed gate stops the concrete policy. No sigma, mask, bound, seed, scene, metric, or data-split adjustment after results. Operational bugs may be fixed with dated amendments only when outcomes have not been interpreted; integrity failures are not negative scientific results. A pass justifies considering source-heldout adaptation; it does not validate a new method or guarantee a paper contribution.

## Execution and resource boundary

CPU only, two computational threads, nice priority, hard 60-minute wall limit, <=4 GiB new artifacts. No GPU allocation or CUDA execution (0 RTX3090 GPU-hours). Use existing remote Python environment. Persistent unique tmux job; one active pilot. An input-only preflight must succeed before fitting. Seal coefficients and all test-prediction hashes before entering the target scorer. Keep input/output provenance and failed artifacts. Do not silently substitute S141 outputs if S140 files are missing.

Independent checks: analytic box-solver cases and comparison to SciPy bounded least squares on synthetic fixtures; independent audit of fold identities, gate arithmetic, baseline agreement and saved coefficients. Repository tests relevant to changed utilities; no repository-wide unrelated refactoring. Outcome is actionable only after independent numerical verification.

## Closest retrieved prior work and rejection boundaries

- *High-Fidelity Novel View Synthesis via Splatting-Guided Diffusion*, arXiv:2502.12752, https://arxiv.org/abs/2502.12752 — splatting-guided diffusion and adaptive texture fusion. Broad geometry/generation fusion is known.
- *GeoNVS: Geometry Grounded Video Diffusion for Novel View Synthesis*, arXiv:2603.14965, https://arxiv.org/abs/2603.14965 — geometry-conditioned feature fusion. Broad adaptive multiscale fusion is known.
- *WAVE: Warp-Based View Guidance for Consistent Novel View Synthesis Using a Single Image*, arXiv:2506.23518, https://arxiv.org/abs/2506.23518 — warp-based and frequency-aware guidance. Frequency conditioning is not a novelty claim.
- *Reconstruct, Inpaint, Test-Time Finetune: Dynamic Novel-view Synthesis from Monocular Videos*, arXiv:2507.12646, https://arxiv.org/abs/2507.12646 — test-time adaptation from observed video is also not a broad novelty claim.

The other considered candidate, native-attention addressing with preserved attention mass, is more expensive and overlaps recent geometry-addressed memory. Source-heldout fitting needs pseudo-target predictions absent from current caches. Only this cross-pair policy is authorized in the present cycle. Stop on weak evidence rather than renaming it as a new contribution.
