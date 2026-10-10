# S143 protocol — does the context package the warp prefers match the one VMem's generator prefers? (exploratory)

Frozen 2026-10-10 before any S143 generation or warp score exists. Supersedes `PROTOCOL_DRAFT.md`, corrected per codex
`gpt-6-astra` (ultra) rejection round R260 (`work/agents/CODEX_R260_S143_DRAFT_REJECTION.md`, §3 adopted except where
stated). Idea source: R258/R259. Owner: standing authorization + "use my codex to create new ideas" (2026-10-10).
Training-free. `new_method_validated=false`, `novelty_authorization=NONE`.

**Status: exploratory case study on an exposed panel.** Consumer-specific evidence utility is not a new principle (FAR,
arXiv:2609.34677, already defines consumer predictive utility). The question is narrow: on the S139 chess panel, does
choosing an ordered four-frame context package by the B2 warp's PSNR leave generated PSNR that a two-seed hindsight
selector recovers on other seeds?

## Pool (per window; construction reads bank RGB/poses and target poses only)
Rules: 1 static_recent, 2 mem_pose, 3 mem_vmem (memberships imported from the S139 plan, not recomputed);
4 nearest-4 (fp64 poses, angle + 0.1·translation, mean over the four targets, bank-index ties);
5 coverage-greedy over the 32 bank frames: per-bank-frame depth from one CUT3R + KPS call on the full bank (bank order,
root 0, all known poses, depths=None, niter=0, S139 kps.install defaults, corrected depth mapping); per frame and target a
1/4-resolution forward-splat support mask (positive depth, in-bounds, no fill); greedily maximise the summed union support
over the four targets (bank-index ties; four distinct frames). The build aborts unless the single KPS record is OK with
finite sigma, reprojection error and focals (R260). Bank-conditioned depth is used **only** to construct rule 5;
6 random (numpy default_rng(259), one choice(32, 4, replace=False) per window in manifest order).
Every set is sorted by bank index; identical sets merge and keep all rule labels (ties between sets: lowest rule).
Output `POOL.json` (with KPS logs and greedy gains).

## Measurements
- Q_W(w, s): B2 warp of exactly the four ordered frames of s (S139 CPU pipeline: CUT3R + KPS niter 0, SPLAT 1, nearest
  fill), scored once per (window, set) by `score_warps_s143.py` (pooled four-target integer SSE → PSNR; SSIM as S140).
- Q_G(w, s, seed): VMem base (gen_s141.py VARIANT=A, ADAPTER=NONE = base, fidelity-verified), seeds 3, 4, 5, 6, RTX 3090,
  ctx_group = ctx_key = window__set (unique per ordered evidence); scored by score_s140.py (per-run PSNR/SSIM).
- Gate before the run: one unchanged replay (S139 mem_vmem, window seq-02_from_seq-01_s0150, original order, seed 3)
  must equal the archived S139 output SHA-256 exactly; exact cell counts; finite outputs; fresh directories; complete
  windows per GPU.

## Primary (name: R_2seed_hindsight)
c_W(w) = argmax_s Q_W; c_G(w, F) = argmax_s mean_{seed∈F} Q_G; F1 = {3,4}, F2 = {5,6}.
R(w) = ½{[Q_G(c_G(w,F1), F2) − Q_G(c_W, F2)] + [Q_G(c_G(w,F2), F1) − Q_G(c_W, F1)]}; R = mean_w R(w).
**Claim** ("on this exposed panel and slot policy, the B2-PSNR selector leaves a held-seed VMem-PSNR shortfall relative to
a target-informed two-seed selector") only if all hold:
(a) R ≥ max(+0.20 dB, null95_panel, null95_indep) — null 95th percentiles from the frozen simulations below;
(b) window-bootstrap 95% lower bound > 0 (10k, rng 0); (c) no negative pair mean in 2 of the 3 sequence pairs;
(d) mean best-minus-worst Q_W spread ≥ 1 dB.
Null simulations (frozen in `analyze_s143.py`, analysis rng 143, 100000 draws, selection re-run in every draw, c_W fixed
from the observed warps): residuals r = per-cell seed scores minus the cell mean; equal-mean Gaussian panels generated
as z·E/√3 with z ~ N(0, I_4) — (i) full-panel factor (keeps cross-set and cross-window covariance), (ii) independent
windows (per-window factor). One-sided tail (1 + #null ≥ obs)/(B + 1). Model-based diagnostics, not exact p-values.
Global-rule control: cross-fitted single best rule; window-specific structure is claimed only if per-window selector −
global rule ≥ max(+0.20, its null95) with lower bound > 0; otherwise "globally biased geometric proxy".

## Secondary / descriptive
All Q_W/Q_G pairs; per-window Spearman (Q_W, Q_G); per-rule means of Q_W and Q_G; best-minus-second Q_W margins; pair
means and leave-one-pair-out R; SSIM at the PSNR-selected identities; SSIM-reselected R (exploratory, separately labelled);
copy-nearest within each set and from the whole bank (larger choice pool, labelled).

## Interpretation and stopping
A miss = no demonstrated shortfall with this pool and selector budget (not equivalence). Invalid geometry, fidelity
failure or missing cells = invalid assay, not a negative result; no post-score pool replacement or window deletion.
Seeds 3–6 are reused discovery seeds; this is not confirmation. Cap 8 RTX 3090 GPU-hours (≤ 6 × 24 × 4 generations +
replay). One run.
