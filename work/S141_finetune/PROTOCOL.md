# S141 protocol — fine-tuning the VMem generator to use cross-view and geometric evidence (TACC RTX 3090)

Owner authorization 2026-10-10: "Willing to dedicate GPU time to fine-tuning the generator; prioritize using TACC's
GPUs". Written before any training. Self-audit replaces codex (owner 2026-10-10). This is the first S-stage that changes
model weights. `new_method_validated=false`, `novelty_authorization=NONE`; any positive result is a candidate only.

## Why
S136–S140: the frozen generator does not use retrieved history (S139) and cannot be steered to refine geometry at
sampling time (S140, held-out). Architecture: cross-frame mixing is (a) TimeMix attention at the *same pixel* across
frames and (b) global 3D attention only at the 9×9 / 18×18 / 36×36 latent scales (`modeling/modules/transformer.py`).
Content that moves between views can transfer only coarsely. Two hypotheses are tested by fine-tuning:
- **A (domain):** the failure is a domain gap (Kinect-like indoor RGB-D, 640×480, these intrinsics and motions).
  A LoRA fine-tune on the same task and domain should help.
- **B (geometry-conditioned):** the generator needs pixel-aligned geometric evidence. Feed the CUT3R+KPS forward warp
  of the contexts at each target pose as an extra input, and train it to use (and inpaint around) that warp.

## Data (disjoint from every evaluation scene)
- Train: Microsoft 7-Scenes **fire, heads, office, pumpkin, redkitchen, stairs** (all sequences), every 5th frame.
  SHA-256 of each archive is recorded. The evaluation scene **chess is excluded**; so are RGB-D Scenes v2 13/14.
- Intrinsics fx = fy = 585, cx = 320, cy = 240 (same nominal value as chess evaluation); gl pose convention (S135/S139).
- Clips (fixed list, seed 0, 2000 clips): pick a current sequence C and a start s on the 5-frame grid with
  s+105 < len(C). Targets are C s+60, +75, +90, +105. Contexts are, with probability 0.5, `static` (C s, +15, +30, +45),
  otherwise `memory`: VMem's pose-only NMS over a bank of 20 frames from another sequence H of the same scene plus 12
  recent C frames (as S139). Monitor split (never trained on): office/seq-10 and redkitchen/seq-14 as current sequence,
  32 clips, used only for a validation-loss curve (6 fixed sigma levels, fixed noise). Built clip list: 1004 static /
  1028 memory (`clips_s141.json`, SHA-256 c2fbdd49e877…). Archive SHA-256s in `zips.sha256`.
- Variant B warps: CUT3R + KPS depth of the 4 context frames, forward-warped to each target pose with nearest fill
  (exactly the S137/S140 B2 pipeline with the corrected mapping), plus 72×72 coverage. Precomputed per clip
  (`warps_s141.py`). For speed CUT3R runs on the GPU for the training warps. Check on 3 chess windows (context frames
  and poses only): GPU warps match the S140 CPU warps at 28–42 dB with identical coverage. Evaluation uses the S140
  CPU warps unchanged.

## Model and training (identical for A and B except the warp input)
- Base: the verified VMem weights (SHA 675dc486…), frozen. LoRA r = 16, α = 16 on `to_q`, `to_k`, `to_v`, `to_out[0]` of
  every `Attention` (spatial, cross-attention, time-mix). B adds a zero-initialised Conv2d(5→320, 3×3) branch on
  [warp latent (4), coverage (1)] summed into the first input conv. Context positions get zeros. The warp channels
  are dense geometric conditioning like the Plücker map, so they appear in both the conditional and unconditional
  dicts. At step 0, A and B equal the base model exactly. **Fidelity gate:** before the evaluation, `gen_s141.py`
  with adapters at their zero initialisation must reproduce the base S139 RTX 3090 output byte-for-byte (A and B).
- Objective: VMem's denoising objective on target frames: sigma index uniform over the 1000 discrete levels, ε-MSE
  through VMem's `DiscreteDenoiser` (contexts enter clean via `replace`). The condition is dropped to VMem's
  unconditional dict with p = 0.1 (keeps CFG).
- AdamW lr 1e-4 (100-step warm-up, then constant), batch 1 clip per GPU, bf16 autocast, gradient checkpointing,
  **10000 steps per variant** (≈ 5 passes over the 2000 clips), seed 0. A and B train in parallel, one RTX 3090 each
  (gpu13 GPU 3 and 4, the only idle GPUs; gpu14 is unusable because of a driver mismatch). The step count was raised
  from a first draft of 3000 after a 40-step engineering smoke run (1.38 s/step, 8.7 GB peak with activation
  checkpointing; no evaluation data involved), to use the GPU budget the owner allotted. **Only the final adapter
  (step 10000) enters the confirmatory evaluation**; intermediate adapters are saved every 1000 steps for exploratory
  use only.

## Evaluation (pre-registered; held-out chess = S139 windows)
Generation is the same sampler as S136–S140 (50 steps, cfg 2.0), gl, seeds 3, 4, 5, 6 on RTX 3090. The base outputs for
those seeds and windows already exist (S139/S140 TACC runs), so every comparison is same hardware, same seeds.
Arms: A-static, A-mem (S139 static_recent / mem_vmem contexts), B-mem (mem_vmem contexts + S140 chess warps).
- **Primary A:** A-mem − base-mem (PSNR). Also A-mem − A-static (does fine-tuning make memory useful?).
- **Primary B:** B-mem − B2 warp (does a geometry-trained generator beat the warp?). Also B-mem − base-mem.
- Secondary: SSIM for all of the above; covered/hole PSNR split for B; RGB-D Scenes 13/14 panel (exposed; static
  contexts, B with S140 dev warps) for cross-dataset transfer.
Unit: window mean over 4 seeds. Window-cluster bootstrap 95% CI (10k, rng 0). Verdict: ±0.2 dB / ±0.01 SSIM with the CI.

## Decision
A IMPROVES on held-out chess → domain gap is a real factor. B IMPROVES over B2 → a geometry-conditioned generator adds
value over geometry alone (the first evidence in this project that generation can beat reprojection on held-out data).
Both NO_MATERIAL_CHANGE → a 10000-step LoRA is insufficient (a scale/architecture question, reported as such).

## Leakage
No chess or RGB-D Scenes 13/14 frame enters training. Evaluation targets are read only by the scorer.

## Stopping
One training run per variant. No evaluation-driven hyperparameter changes. Report after evaluation.
