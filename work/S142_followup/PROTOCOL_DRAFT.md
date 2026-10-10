# S142 protocol DRAFT — one S141-outcome-selected follow-up (conditional pre-registration)

Status: DRAFT, written 2026-10-10 while S141 evaluation runs, before any S141 evaluation output was read. To be
reviewed by codex gpt-6-astra (ultra) in a rejection round, then frozen before S141 results are opened.
`new_method_validated=false`, `novelty_authorization=NONE`. Source: codex R255 (outcome-conditional plan).

## Branch selection (fixed now, applied mechanically to the S141 PRIMARY_B verdict, PSNR)
- PRIMARY_B = IMPROVES (B_mem beats the B2 warp) → run **E1** only.
- PRIMARY_B ∈ {NO_MATERIAL_CHANGE, WORSENS, INCONCLUSIVE} → run **E2** only, unless the S141 run is an execution
  failure (failed self-audit), in which case S141 is repaired first and S142 does not start.
- E3 (pixel fusion) is not pre-registered here; it is considered only if PRIMARY_A = IMPROVES and PRIMARY_B = WORSENS,
  through a separate protocol.

## E1 — does B's gain depend on spatially aligned warp content?
Fixed final S141 B adapter, mem_vmem contexts, S140 chess warps, seeds 3–6, RTX 3090, same sampler/scorer.
Intervention: before VAE encoding, permute warp RGB pixels within each frame separately inside the covered set and
inside the uncovered set (fixed permutation, numpy seed 255); coverage map unchanged; raw contexts, CLIP, poses,
noise unchanged; the deranged warp enters both CFG branches (as in training).
- Primary: window-mean PSNR B(correct) − B(deranged) ≥ +0.2 dB with 95% CI lower bound > 0 → B uses aligned warp
  content. Otherwise the alignment-dependence explanation is rejected (B's measured gain over the warp stands).
- Secondary: SSIM; covered/uncovered split; per pair. Correct-arm outputs are the S141 B_mem outputs (identity checked
  by adapter SHA, plan, seed).
- Cost: 96 generations (~1.1 GPU-h).

## E2 — trained warp-as-context (challenger C)
Hypothesis: the pretrained clean-context path (cond `replace`) adapts more readily to aligned geometric evidence than
B's new input branch. Representation: the four context slots hold the four target-pose B2 warps (VAE latents of the
nearest-filled warp images); context poses = the target poses; CLIP embeddings from the warp images; targets noisy as
usual; no extra input branch. The original context frames are not given to the model (their content reaches it only
through the warp). LoRA r16 on all attention projections, identical optimiser/schedule/steps (10000)/seed/data clips to
S141 A; S141 training warps reused (GPU CUT3R); CLIP of warp images precomputed.
- Train-only engineering gate (R255): a disposable 500-step run on 8 fixed training clips must reduce the fixed-noise
  target ε-MSE on those clips by ≥ 10% with finite losses; then discard it and run the full 10000 steps from the base.
- Fidelity: zero-init C must reproduce the base model run with the same warp-as-context inputs byte-for-byte.
- Evaluation: S139 chess windows, mem_vmem contexts → S140 warps as context; seeds 3–6, RTX 3090.
  Primary: C − B2 warp (PSNR) ≥ +0.2 dB with CI lower bound > 0. Secondary: SSIM; covered/uncovered split; C − B_mem;
  C − base_mem; per pair. A frozen-base copy control (zero-init C) is reported descriptively (S137c: it copies).
- Interpretation boundary: success supports this complete input representation, not a causal replace-vs-concat
  conclusion (representation and camera gauge both change). Failure ends learned-consumer work for this project.

## Shared rules
Window mean over seeds 3–6; window-cluster bootstrap 95% CI (10k, rng 0); verdict ±0.2 dB / ±0.01 SSIM; per-pair means
reported (windows share history). Chess is an exposed panel for follow-ups (not untouched confirmation). Region labels:
covered / uncovered by the warp. One run, final adapter only, no evaluation-driven changes.
