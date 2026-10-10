# S144 protocol — does the domain-adapted adapter A make the S140 warp-guided sampler useful? (frozen)

Frozen 2026-10-10 ≈ 20:00 UTC, before any S144 output. Supersedes `PROTOCOL_DRAFT.md`. Idea: codex R262 E1; corrected by
codex `gpt-6-astra` (ultra) rejection round R263 — its §3 "Corrected minimal S144 specification" is adopted in full and is
part of this protocol (`work/agents/CODEX_R263_S144_S145_REJECTION.md`). Training-free. `new_method_validated=false`,
`novelty_authorization=NONE`. Runs on TACC RTX 3090 after S143 releases the GPUs.

Summary of the binding points (R263 §3 governs where this summary is shorter):
- Arms from ONE generator (`gen_s144.py`): per backbone (frozen base F, adapter A 635e6e31…), one S140 W2 trajectory
  (strength 0.5, steps 25–49, latent mask pooled coverage ≥ 0.5, every sampler_step and replacement draw preserved) with two
  endpoints: C (original terminal overwrite) and R (terminal overwrite skipped, its RNG draw still consumed). Estimand:
  whole-trajectory adapter × terminal-clamp interaction. Name: "S140 W2, RePaint-style latent replacement".
- Replays: new F_C vs archived S140 W2 RTX 3090 chess output (one fixed cell, full array equality; RGB-D W2 archives exist
  only on H800, so no RGB-D archival replay — disclosed); C/R trace invariants (identical uncovered latent cells and context
  slots before decode, identical consumed random tensors); loader/mapping checks for the monitor route.
- Controls: B2; V = D(E(B2)); pastes P_V, P_FC, P_AC (covered from G, holes from B2) and reverse A_C paste; global blends
  α_G·G + (1 − α_G)·B2 for G ∈ {V, F_C, A_C}, α on {0, 0.05, …, 1} fitted on development mean clip PSNR (seed-averaged;
  ties → smaller α), frozen before case scoring; adapter A alone (S141 A_mem) as reference. Canonical uint8 conversion
  once; blends computed in float and rounded once.
- Development: the 32 S141 monitor clips with CPU warps from the evaluation geometry path (CPU CUT3R + KPS), seeds 3, 4.
  Engineering GO and Performance GO exactly as R263 §3.5 (development I ≥ +0.20 dB; A_R beats A_C and every mandatory
  control by ≥ +0.20 dB with SSIM loss ≤ 0.01; nonnegative within both monitor sequences). If Performance GO fails, S144
  stops and reports the failed screen (no sweep, no A_C-only continuation).
- Case panels (only after GO): chess 24 windows (S139 mem_vmem, S140 CPU warps) and RGB-D Scenes 16 windows (static,
  S140 dev warps), seeds 3–6. Primary on chess: paired per-window I = (A_R − A_C) − (F_R − F_C) ≥ +0.20 dB, window-bootstrap
  lower bound > 0 (10k, rng 0), nonnegative in 2 of 3 pairs, AND A_R beats A_C and every mandatory control by the same rule
  with SSIM loss ≤ 0.01. Secondary: A_C − F_C, A_C − B2, regions (original pixel masks), RGB-D, SSIM.
- Cap 12 RTX 3090 GPU-hours incl. development, controls, replay; complete-cell timing pilot before the full run. Exposed
  panels; no memory-benefit, novelty or video-quality claim.
