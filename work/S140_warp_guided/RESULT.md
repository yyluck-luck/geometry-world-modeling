# S140 result — warp-guided sampling: a dev-panel gain that does not replicate on held-out chess (PSNR); SSIM nuance

Protocol: `PROTOCOL.md` (frozen at commit 8b7bf146 before any run; Amendment 1 after stage 1). Self-audit, no codex
(owner 2026-10-10). `new_method_validated=false`, `novelty_authorization=NONE`.

## Fidelity
The re-implemented sampling loop (`none`) is **byte-identical** to VMem's sampler (`ref`) for seeds 42 and 7
(`results/dev/FIDELITY_SHA256.txt`). WGS variants differ from VMem only by the intended changes.

## Stage 1 — development, exposed RGB-D Scenes panel (16 windows × 2 seeds; `results/DEV_ANALYSIS.json`)
| variant | PSNR | SSIM | − B2 (dB) | covered / holes Δ vs warp |
|---|---|---|---|---|
| **W2 RePaint s=0.5 (selected)** | **20.87** | **0.730** | **+0.785 [+0.56, +1.00]**, 15/16 | +0.13 / **+1.85** |
| W2 RePaint s=1.0 | 20.61 | 0.730 | +0.526 [−0.13, +1.09] | +0.12 / +1.21 |
| W1 SDEdit s=0.3 | 20.24 | 0.729 | +0.156 | −0.58 / +1.31 |
| W1 SDEdit s=0.5 / 0.7 | 18.94 / 17.91 | | −1.15 / −2.18 | |
| W3 replace-inpaint | 18.60 | 0.698 | −1.49 | −0.92 / −1.82 |
| B2 warp / VMem static_gl | 20.09 / 15.25 | 0.721 / — | | hole fraction 0.337 |

## Stage 2 — confirmation, 7-Scenes chess (S139 windows, mem_vmem contexts; 24 windows × 8 seeds, H800 + RTX 3090)
`results/CONFIRM_ANALYSIS.json`. Means: WGS 14.59 dB, B2 14.57 dB, VMem 11.36 dB (PSNR); SSIM WGS 0.457, B2 0.432, VMem 0.470.
| contrast | Δ | 95% CI | wins | verdict |
|---|---|---|---|---|
| **PRIMARY WGS − B2 (PSNR)** | **+0.020 dB** | [−0.095, +0.134] | 14/24 | **NO_MATERIAL_CHANGE** |
| WGS − B2 (SSIM) | +0.025 | [+0.015, +0.036] | 19/24 | IMPROVES |
| WGS − VMem (PSNR) | +3.229 dB | [+2.861, +3.600] | 24/24 | IMPROVES |
| WGS − VMem (SSIM) | −0.013 | [−0.038, +0.011] | 10/24 | INCONCLUSIVE |
| B2 − VMem (SSIM) | −0.039 | [−0.069, −0.009] | 7/24 | WORSENS |
| region: covered / holes, WGS − warp (PSNR) | +0.244 / −0.241 | [+0.19, +0.30] / [−0.44, −0.05] | 23/24 / 8/24 | hole fraction 0.448 |

## Reading
- **The pre-registered primary does not replicate.** The dev gain (+0.79 dB, 6-way selection on an exposed panel)
  shrinks to +0.02 dB on held-out windows. That is the reason for the dev/confirm split.
- **Mechanism, from the region split.** The generator reliably polishes covered pixels (+0.24 dB, 23/24), probably
  cleaning splat cracks and speckle. Its value in holes is scene-dependent: +1.85 dB on RGB-D Scenes, −0.24 dB on
  chess. Hypothesis, not tested: RGB-D Scenes holes are mostly CUT3R crop bands whose content the contexts do show;
  chess holes are disocclusions that no context observed.
- **SSIM tells a different story from PSNR on chess.** VMem's own output has the best SSIM (0.470); the warp has the
  worst (0.432; nearest-fill streaks in 45% holes). WGS lifts the warp's SSIM by +0.025, still not above VMem.
  "Geometry beats the generator" (S137/S139) therefore holds for **PSNR**. Under large disocclusion it does not hold
  for **SSIM**.

## S139 re-checked in SSIM (same 576 outputs; `results/s139_ssim/S139_SSIM_ANALYSIS.json`)
New scorer validated: PSNR equals the S139 scorer to 3.6e-15. SSIM means: static_recent 0.489, mem_pose 0.480,
mem_vmem 0.470.
| contrast | PSNR (pre-registered) | SSIM |
|---|---|---|
| mem_vmem − static_recent | −0.18 [−0.52, +0.15] NO_MATERIAL_CHANGE | **−0.019 [−0.032, −0.006] WORSENS** (8/24) |
| mem_vmem − mem_pose | −0.18 [−0.40, +0.04] | −0.010 [−0.020, −0.001] |
| mem_pose − static_recent | +0.00 | −0.009 [−0.023, +0.004] |
The S139 conclusion survives the second metric and is sharper: by SSIM, generating from retrieved history is worse
than from recent frames.

## Files
`gen_s140.py`, `score_s140.py`, `score_ssim_plan.py`, `build_plans_s140.py`, `analyze_dev_s140.py`,
`analyze_confirm_s140.py`, plans, `results/` (dev, confirm per site, s139_ssim), warps in `data/S140_warps_*` (gitignored).
