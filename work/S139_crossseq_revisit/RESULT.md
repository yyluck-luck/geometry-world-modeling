# S139 result — on held-out cross-sequence revisits VMem retrieves useful history, but its generator does not use it

Protocol: `PROTOCOL.md` (frozen at commit 27fbfef1, before any 7-Scenes chess content was read; Amendment 1 appended).
Sites: SuperPOD H800 (step A job 674961; step B job 674991, seeds 42, 7, 1, 2) and TACC RTX 3090 (seeds 3, 4, 5, 6).
72 unique contexts × 8 seeds = 576 generations, all scored. The H800 job rebuilt the plan from the step-A receipt
byte-identically to the local plan_v2. Claim scope: held out from this project's design decisions; pretraining
exposure unverified. `new_method_validated=false`, `novelty_authorization=NONE`.

## Harness
- Convention check (KPS residual): gl wins 3/3 pairs (9–16 px vs ≥ 103 px).
- Step A: 24/24 windows OK. Memory covers all 32 bank frames in every window. KPS σ is stable across the three
  constructs. No BLOCKED window.
- Retrieval: VMem contexts are 88.5% history-sequence frames on average. mem_vmem ≠ mem_pose in 24/24 windows: with a
  32-frame bank the visibility filter keeps only the top-14 candidates, so geometry does shape the selection here,
  unlike the 12-frame panel.

## Pre-registered results (window mean over 8 seeds; `results/S139_ANALYSIS.json`)
Arm means: static_recent 11.54 dB, mem_vmem 11.36 dB, mem_pose 11.55 dB.
| contrast | Δ PSNR (dB) | 95% CI (window) | pair-cluster CI | windows + | verdict | history-fav. (16) / recent-fav. (8) |
|---|---|---|---|---|---|---|
| **PRIMARY mem_vmem − static_recent** | **−0.181** | [−0.518, +0.145] | [−0.51, +0.10] | 10/24 | NO_MATERIAL_CHANGE | **−0.334 / +0.126** |
| mem_vmem − mem_pose | −0.182 | [−0.405, +0.038] | [−0.45, −0.02] | 9/24 | NO_MATERIAL_CHANGE | −0.044 / −0.459 |
| mem_pose − static_recent | +0.002 | [−0.363, +0.324] | [−0.44, +0.32] | 13/24 | NO_MATERIAL_CHANGE | −0.290 / +0.585 |

Per pair (mem_vmem − static): seq-01→02 −0.13, seq-04→03 +0.10, seq-06→05 −0.51.

**Decision.** The prediction (memory helps when long-range history exists, more in history-favourable windows) is not
supported. The primary is NO_MATERIAL_CHANGE, and the stratum difference runs the other way (−0.33 vs +0.13). The S136
negative extends to a revisit regime on a held-out scene.

## The same contexts used geometrically (CPU baselines, as S137; `results/S139_BASELINE_CONTRASTS.json`)
Means: copy-nearest bank frame 12.22; B2 warp from static_recent contexts 13.11; from mem_pose 14.35; from mem_vmem 14.57.
| contrast | all 24 windows | history-favourable 16 |
|---|---|---|
| B2(mem_vmem) − B2(static) | **+1.46 [+0.91, +2.05]**, 19/24 | **+1.95 [+1.24, +2.68]**, 14/16 |
| B2(mem_pose) − B2(static) | +1.24 [+0.72, +1.79], 20/24 | +1.49 [+0.74, +2.23], 13/16 |
| B2(mem_vmem) − B2(mem_pose) | +0.22 [−0.15, +0.61], 12/24 | +0.46 [+0.02, +0.94], 10/16 |
| B2(mem_vmem) − VMem generation(mem_vmem) | **+3.21 [+2.84, +3.58]**, 24/24 | +3.47 [+3.05, +3.90], 16/16 |
| B2(static) − VMem generation(static_recent) | +1.57 [+0.99, +2.14], 22/24 | +1.19 [+0.48, +1.86], 14/16 |
| copy-nearest bank frame − VMem static_recent | +0.67 [+0.41, +0.96], 20/24 | +0.54 [+0.20, +0.91], 12/16 |
(B0/B2 comparisons beyond "from mem_vmem and static contexts" are exploratory. B2 is a direct geometric predictor, not a
capacity-matched generator control.)

## Reading
- **Retrieval is not the bottleneck here.** The frames VMem retrieves from another traversal carry substantially better
  geometric evidence for the targets than the recent static frames: +1.46 dB for a warp, +1.95 dB in history-favourable
  windows. In those windows the surfel-visibility selection even beats pose-only selection (+0.46 [+0.02, +0.94]). This
  is the first regime in the project where geometry-based retrieval measurably adds value.
- **The generator does not convert that evidence into better frames.** With the same contexts it is −0.18 dB vs static,
  and 3.2 dB below a warp of those contexts in every window. This matches S137c: VMem reproduces aligned same-pose
  context, but fails at cross-view transfer.

## Limits
One scene (chess), three sequence pairs (dependent through shared history banks), 24 windows, PSNR only, one frozen
consumer. 7-Scenes RGB focal 585 is the documented nominal value; relocalisation work often uses ≈ 525 for RGB. The same
K is used for every arm, so arm contrasts are unaffected but absolute geometry is approximate. The codex pre-result
review (R251) could not run (model at capacity, 7 attempts); an external review is outstanding.
