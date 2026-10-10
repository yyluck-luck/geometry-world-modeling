# S140 protocol — warp-guided sampling (WGS): can the frozen VMem generator add value on top of geometry?

Owner standing authorization (2026-10-09). Written before any S140 run. A training-free method attempt on the consumption
side. `new_method_validated=false`, `novelty_authorization=NONE`.

## Why
S136–S139: memory/retrieval repairs do not help, and a direct geometric warp (B2: CUT3R + KPS) beats VMem's generation
by 3–6 dB. On held-out revisits, retrieval finds geometrically useful history, but generation does not use it (S139).
VMem reproduces aligned same-pose context (S137c), so the remaining question is whether its denoiser can *refine*
a geometric answer. Can it keep covered pixels aligned while generating uncovered ones better than nearest-neighbour fill?

## Method variants (sampling-loop changes only; model, weights and conditioning unchanged)
The context frames enter as in VMem: clean latents through the `replace` channel, Plücker conditioning and CLIP mean.
z_w are the VAE latents of the B2-kps warps at the four target poses. m is the latent coverage mask (72×72, block
coverage ≥ 0.5 for W2, = 1.0 for W3).
- **W1 SDEdit(s):** the target positions start at x_k = z_w + σ_k·ε, k = round((1−s)·50); Euler steps run from k. s ∈ {0.3, 0.5, 0.7}.
- **W2 RePaint(s):** W1, and after every step x_target ← m·(z_w + σ_next·ε) + (1−m)·x_target. s ∈ {0.5, 1.0}.
- **W3 replace-inpaint:** full schedule (s = 1). Target positions in the conditional `replace` tensor carry z_w with
  pixel mask m, so the denoiser substitutes the clean warp for covered latent pixels at every step (the unconditional
  branch is unchanged).

## Stage 1 — development (variant selection), exposed RGB-D Scenes panel
16 windows (scene_13/14, w0–w350), VMem static contexts (offsets 0, 15, 30, 45), gl. Warps = B2-kps of those
contexts with the corrected pixel-centre mapping (S137 Amendment 2). Seeds 42, 7. Six variants × 16 windows × 2 seeds.
References: B2-kps (deterministic) and VMem static_gl (S136, same seeds).
**Selection rule (fixed):** the variant with the highest mean PSNR over the 32 window-seed cells; tie (< 0.05 dB) →
higher SSIM. All variants are reported.

## Stage 2 — confirmation, 7-Scenes chess (S139 windows)
24 windows, contexts = S139 mem_vmem (H800 canonical), warps = B2-kps of those contexts at the target poses. Selected
variant only. 8 seeds (H800 42, 7, 1, 2; RTX 3090 3, 4, 5, 6). The S139 targets were scored before (for other arms);
the WGS variant and strength are chosen on stage 1 only.
- **Primary:** WGS − B2(mem_vmem): does the generator add value on top of geometry?
- Secondary: WGS − VMem(mem_vmem) (S139 scores, same seeds); the same contrasts in SSIM; per pair; history-favourable stratum.
Unit: window mean over seeds. Window-cluster bootstrap 95% CI (10k, rng 0). Verdict ±0.2 dB (±0.01 SSIM).

## Interpretation fixed in advance
- WGS > B2 (IMPROVES): the frozen generator can refine geometry, giving a training-free "warp-then-refine" method.
- WGS ≈ B2: the generator only preserves the warp. WGS < B2: it degrades it.
- WGS vs VMem shows how much of the S139 gap a sampling-side intervention closes.

## Leakage boundary
Warps use the context frames, their CUT3R depth and the target *poses* only. Model processes never see target RGB or
dataset depth. Scoring is separate.

## Stopping
Report after stage 2. No variant changes after stage-2 scores.
