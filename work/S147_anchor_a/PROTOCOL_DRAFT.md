# S147 protocol DRAFT — Anchor-A: does a warp branch trained on a frozen adapter A add useful geometric evidence?

Draft 2026-10-11 ≈ 06:30 UTC, for the codex rejection round (R273). Not frozen; nothing has run. Idea: codex R271 Rank 1
(`work/agents/CODEX_R271_IDEATION_AFTER_S145.md` §5), motivated by S141 (A works, B fails) and S145 (B's branch helps
under B's own co-trained LoRA). `new_method_validated=false`, `novelty_authorization=NONE`. Prior art makes any positive
result incremental (I3DM arXiv:2603.23413, GEN3C arXiv:2503.03751, GeoNVS arXiv:2603.14965); this is a controlled
co-adaptation test, not a method claim.

## 1. Question
With the S141 A checkpoint fully frozen (base weights and every A LoRA tensor), can a separately trained, bypassable
warp-input branch make the generator use the target-pose warp's content, beyond (i) the same branch fed a content-free
prototype, (ii) continued A training, and (iii) the simple estimators (raw warp, its VAE round trip, a development-fitted
blend)? Secondary: does freezing A matter compared with joint training from A?

## 2. Inputs (hashes checked before any run)
- VMem weights and source as S141 (TACC `$R=/mnt/gluster_dcpu/yiyangliu/gwm_s134`; `vmem/modeling/pipeline.py` 680da1c1…).
- Adapter A: `gwm_s141/runs/A/adapter_final.pt`, SHA-256 635e6e31….
- Training data: `gwm_s141/clips_s141.json` (2000 train + 32 monitor clips; six 7-Scenes rooms), latents `gwm_s141/lat`,
  S141 training warps `gwm_s141/warps/<clip>.pt` (GPU CUT3R + original KPS, [warp latent, coverage]).
- Invalid-geometry list (source-only, fixed now): the 47 clips whose warp log has a non-finite KPS median reprojection
  (equivalently NaN focals): 46 training clips and monitor clip c02028 (`work/S141_finetune/results/tacc/logs/WARP_LOG_*`).
- Development panel = the S144 development panel: 32 monitor clips (office/seq-10, redkitchen/seq-14; exposed), CPU warps
  `gwm_s144/warps_monitor_cpu` (128 files), seeds 3, 4. Comparators reused from S144 after a replay gate: ordinary A
  (A_none), raw warp B2, VAE round trip V, the dev-fitted blends BL_FC / BL_AC (`work/S144_A_wgs/results/`).

## 3. Arms (one training run each; training seed 0; identical clip order, sigma draws, noise and CFG-dropout draws)
Recipe as S141: 10,000 scheduled steps, batch 1 clip, AdamW lr 1e-4 (100-step warm-up, then constant), weight decay 0,
grad-clip 1.0, P_UNCOND 0.1, bf16 autocast, activation checkpointing; loss = ε-MSE on the four target frames.
Invalid clips: their RNG draws are consumed, but no forward/backward/optimizer step happens in any arm; attempted and valid
update counts are logged.

| arm | initialisation | trainable | branch input on target slots |
|---|---|---|---|
| **F_geo** | A + zero-init WarpInConv (5→320, as B) | branch only (A LoRA frozen) | [warp latent, coverage] |
| **F_null** | same | branch only | [prototype latent, coverage]; prototype = per-channel mean of the warp latents of all valid training clips (4 scalars, computed before training, stored in the adapter) |
| **J_geo** | same | A LoRA + branch | [warp latent, coverage] |
| **A_cont** | A (no branch) | A LoRA | — |

Branch placement as B (zeros on context slots, so the learned bias acts there; appended to both c and uc).

## 4. Engineering gates (before any development score; failure stops S147)
1. Timing/memory pilot (100 steps per arm, 1 and 2 processes per GPU): choose the packing; projected training ≤ 20 GPU-h.
2. F_geo / F_null final adapters: every LoRA tensor byte-identical to A's.
3. Replay: the S147 generator with adapter A reproduces the archived S144 A_none output (one monitor clip, seed 3) byte-for-byte.
4. Bypass: F_geo's adapter with the branch bypassed reproduces that same output byte-for-byte; step-0 adapters (F/J) reproduce it.
5. All planned cells present and finite.

## 5. Development gate (exposed; frozen rule)
Generate F_geo, F_null, J_geo, A_cont (standard sampler, no warp-guided sampling) on the 32 monitor clips × seeds 3, 4.
Clip value = mean over seeds; panel value = mean over 32 clips; descriptive 10k clip bootstrap (rng 0); per-sequence means.
- **PRIMARY:** F_geo − F_null ≥ +0.20 dB and positive in both monitor sequences.
- **PRACTICAL (all required):** F_geo − X ≥ +0.20 dB for X ∈ {A_none, A_cont, B2, V, BL_AC}; SSIM F_geo − X ≥ −0.01 for each.
- Reported, not gating: F_geo − J_geo (anchoring), J_geo − A_cont, F_null − A_cont, covered/hole regions, memory vs static
  clip kinds, and a dev-fitted F_geo/warp global blend (α grid step 0.05; optimistic).
- **GO** iff PRIMARY and every PRACTICAL comparison pass. Otherwise S147 stops after §6 (no confirmation).

## 6. Exposed diagnostic case (runs regardless of the gate; cannot rescue a failed gate)
Chess, 24 S139 windows, mem_vmem, S140 CPU warps, seeds 3–6: F_geo, F_null, J_geo, A_cont, compared descriptively with the
archived S141 A, B and B2 on the same cells. Question: does anchoring remove B's −3.56 dB deficit to the warp?

## 7. Confirmation (only on GO; specified now, data not downloaded)
12-Scenes office1 (four rooms; never downloaded by this project), downloaded and staged only after GO with the S146 staging
rules (H = sequence0, C = sequence1, 8 windows per room, 32-frame banks). Packages: nearest-4 (primary) and static.
Warps: S139 CPU B2 pipeline (CUT3R + original KPS on the four context frames); invalid geometry (non-finite KPS
reprojection) → branch bypassed for every F/J arm and B2 falls back to nearest-context copy; fractions reported, no window
dropped. Seeds 42, 7, 1, 2. Arms F_geo, F_null, J_geo, A_cont, A; comparators B2, V, the dev-frozen blend. Primary
F_geo − F_null ≥ +0.20 dB, positive in all four rooms and in ≥ 3/4 seed panels; practical comparisons as §5. Memory
statement only if F_geo(nearest-4) − F_geo(static) ≥ +0.20 dB and exceeds the same difference for A_cont. One environment:
a pilot, not an independent-environment test.

## 8. Budget, stop rules, outputs
Training ≤ 20 GPU-h; development ≤ 4; chess ≤ 5; confirmation ≤ 16; total cap 48 GPU-h (TACC gpu13 GPUs 3/4 only).
Stop on any engineering-gate failure, non-finite or missing cell, budget overrun, or a failed development gate. One pass:
no retuning, no extra layers, no second seed before a written amendment. Outputs `gwm_s147/` on gluster; code and receipts
in `work/S147_anchor_a/`.
