# S145 result — under B's own LoRA the warp branch helps; removing it, or gating it to target frames, makes B worse

Protocol: `PROTOCOL.md` (frozen 56785b92 before any S145 output; R263 §4 adopted in full; implementation 205a682c).
Idea: codex R262 E2; rejection round R263. Training-free diagnosis, not a method. `new_method_validated=false`,
`novelty_authorization=NONE`.

## Execution and gates
- Checkpoint: S141 B `adapter_final.pt`, SHA-256 0dd40c86… checked before the run; every one of the 384 new cells records
  this hash. All B LoRA tensors are kept in every arm.
- Replay gate: the S145 generator with the intervention disabled (`BRANCH=orig`) reproduces the archived S141 B output
  byte-for-byte (chess window 0, seed 3, 68c5e197…). This licenses reusing the S141 B_original and A scores.
- Four new arms × 24 chess windows (mem_vmem, S140 CPU warps) × seeds 3–6 = 384 cells, all on RTX 3090, all finite and
  scored. Permutation moved 98.8% of cells on average (min > 50%), so it is not close to the identity.
- Budget: 4.27 GPU-h of generation (replay + four arms), under the 6 GPU-h cap. Run 2026-10-11 03:17–05:40 UTC.
- Teacher-forced probe on the 32 monitor clips × 6 sigmas × 5 conditions, with c, uc and guided predictions (2,880 rows),
  bf16 autocast as in training. Diagnostic only.

## Results (`results/S145_ANALYSIS.json`; window = mean over seeds 3–6; 24 windows; 10k window bootstrap)
| contrast (PSNR, dB) | mean [95% CI] | windows > 0 | pairs 01→02 / 04→03 / 06→05 | verdict |
|---|---|---|---|---|
| **PRIMARY B_off − B_original** | **−0.423 [−0.678, −0.181]** | 7/24 | −0.31 / −0.66 / −0.30 | WORSENS |
| **SECONDARY B_target_only − B_original** | **−0.334 [−0.393, −0.272]** | 0/24 | −0.38 / −0.27 / −0.36 | WORSENS |
| B_bias_only − B_original | −0.538 [−0.785, −0.297] | 4/24 | −0.54 / −0.74 / −0.33 | WORSENS |
| B_permuted − B_original | −0.438 [−0.567, −0.318] | 1/24 | −0.46 / −0.45 / −0.40 | WORSENS |
| B_off − A (practical reference) | −1.013 [−1.280, −0.745] | 3/24 | −1.06 / −1.28 / −0.70 | WORSENS |
| B_target_only − A | −0.925 [−1.109, −0.743] | 0/24 | | WORSENS |
| B_off − B2 (raw warp) | −3.980 [−4.387, −3.586] | 0/24 | | WORSENS |
| B_target_only − B2 | −3.892 [−4.229, −3.558] | 0/24 | | WORSENS |

Mean PSNR: B2 14.572, A 11.605, **B_original 11.015**, B_target_only 10.681, B_off 10.592, B_permuted 10.577, B_bias_only 10.476.

| contrast | SSIM | covered-region PSNR | hole-region PSNR |
|---|---|---|---|
| B_off − B_original | −0.025 WORSENS | −0.46 WORSENS | −0.32 WORSENS |
| B_target_only − B_original | −0.061 WORSENS (0/24) | −0.31 WORSENS | −0.34 WORSENS |
| B_bias_only − B_original | −0.042 WORSENS | −0.55 WORSENS | −0.48 WORSENS |
| B_permuted − B_original | −0.021 WORSENS | −0.41 WORSENS | −0.47 WORSENS |
| B_off − A | −0.006 NO_MATERIAL_CHANGE | −0.98 WORSENS | −1.09 WORSENS |
| B_off − B2 | +0.048 IMPROVES | — | — |

Mean SSIM: B_original 0.505, A 0.486, B_permuted 0.485, B_off 0.480, B_bias_only 0.463, B_target_only 0.444, B2 0.432.

## Reading (R263 §4.4 wording)
- **Primary negative.** Removing the whole branch does not improve this B backbone; it costs 0.42 dB. Under B's fixed,
  co-trained LoRA the branch contributes positively, in PSNR, SSIM and both regions.
- **The context-bias hypothesis is not supported.** Gating the branch to target frames (removing the learned bias b from
  the four context slots) is worse in every one of the 24 windows. B's LoRA appears to have adapted to that constant
  context-slot offset; taking it away hurts.
- **The input-dependent terms matter.** Bias-only (the five inputs zeroed, so W(e) = 0) is the worst arm (−0.54 dB).
  Permuting the warp latent within exact coverage strata costs −0.44 dB. Per R263 this shows sensitivity only, not that B
  uses the warp "correctly".
- **Practical position unchanged.** No arm reaches A (B_off −1.01 dB; B_original itself is −0.59 dB below A) or the raw
  warp (−3.9 dB). B's deficit therefore sits in what B's LoRA learned jointly with the branch, not in the branch's
  inference-time contribution. Descriptive, not pre-registered: B_original has the highest SSIM of any generated arm
  (0.505 vs A 0.486), so B trades PSNR for structure. B_off beats raw B2 in SSIM (+0.048) mainly because the raw warp
  leaves holes unfilled.
- **What S145 cannot say.** Removing B's branch cannot tell us how B's LoRA would have trained without it (R263). An
  A-anchored retraining is outside S145 and is not scheduled.

## Teacher-forced probe (diagnostic; `results/PROBE.json`, relative change in guided target ε-MSE vs the correct input)
| sigma | 0.41 | 2.27 | 6.37 | 13.6 | 30.1 | 63.6 |
|---|---|---|---|---|---|---|
| zero5 (= bias-only input) | −0.2% | −2.3% | −10.1% | −5.0% | +8.9% | +6.2% |
| zero latent, coverage kept | −0.9% | −1.5% | −7.4% | +8.2% | +16.0% | −5.3% |
| per-stratum mean latent | −0.6% | −0.7% | −5.0% | +9.7% | +11.3% | −10.5% |
| permuted | −0.6% | −1.0% | −4.3% | +10.6% | +12.9% | −7.5% |

The correct warp beats the spatial corruptions only at σ 13.6–30.1, and beats every condition only at σ 30.1. At σ ≤ 6.4,
every corruption lowers ε-MSE. The probe does not predict the rollout ranking: the bias-only input (zero5) has lower one-step
error than the correct warp at four of six sigmas (σ ≤ 13.6), yet bias-only is the worst generated arm. Per R263 the probe uses the GPU monitor warps and training
precision, so differences from the CPU-warp chess rollouts are not interpretable as ablation effects. The derived clean-latent
MSE (σ²·ε-MSE) is the same metric in different units.

## Limits
One exposed room (chess, 24 windows, three sequence pairs), one retrieval (mem_vmem), one B checkpoint, four seeds, PSNR/SSIM
on 640×480 targets. Inference-time ablations of a trained network do not identify training-time causes.

## Files
`PROTOCOL.md`, `probe_s145.py`, `analyze_s145.py`, `s145_chain.sh`, plans, `POSE_ARMS.json`, `self_audit_s145.py`; `results/`:
analysis, scores, probe, replay hashes, run receipts and code hashes per arm, `SELF_AUDIT_CHECKS.json` (75/75 pass;
independent recomputation matches to 1.8e-15). Generator: `../S144_A_wgs/gen_s144.py` (`BRANCH` ablations).
