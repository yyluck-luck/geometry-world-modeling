# S144 protocol DRAFT — does the domain-adapted adapter A make warp-guided sampling useful? (codex R262 E1)

Draft 2026-10-10 ≈ 19:45 UTC (S141 results known; S143 running). To pass a codex gpt-6-astra (ultra) rejection round
before freezing. Training-free. `new_method_validated=false`, `novelty_authorization=NONE`. Design adopted from
`work/agents/CODEX_R262_IDEATION_AFTER_S141_RESULTS.md` §5–6 (shared contract and E1), summarised here.

## Arms (2 × 2 factorial; S140 W2 RePaint, strength 0.5, coverage ≥ 0.5 latent mask, same RNG draws)
F_C frozen base + original W2 (final-step clamp of covered latents to z_w); F_R frozen base, final overwrite skipped
(the RNG draw still consumed); A_C adapter A + original W2; A_R adapter A + final overwrite skipped. Every earlier
overwrite and the nearest-fill initialisation unchanged. F_C on chess = S140 RTX 3090 outputs (seeds 3–6), reused only
after an exact replay of one cell.
## Controls (strongest trivial; all scored with the same scorer and the original pixel masks)
raw B2 warp; VAE round trip D(E(B2)); RGB paste F_C-covered + B2-holes; RGB paste A_C-covered + B2-holes; global convex
blend α·A_C + (1−α)·B2 with α on a 0.05 grid fitted on the development panel (monitor clips) only; adapter A alone
(S141 A_mem outputs) as a context-only reference.
## Panels
Development: the 32 S141 monitor clips (office/seq-10, redkitchen/seq-14; their GPU warps), seeds 3, 4 — used for α and an
engineering go/no-go. Case study: chess 24 windows (S139 mem_vmem contexts, S140 CPU warps) and RGB-D Scenes 16 windows
(static contexts, S140 dev warps), seeds 3–6, RTX 3090. Both case panels are exposed (not confirmation).
## Primary
Interaction I = (PSNR(A_R) − PSNR(A_C)) − (PSNR(F_R) − PSNR(F_C)) on chess: ≥ +0.20 dB, window-bootstrap lower > 0, no
negative pair mean in 2 of 3 pairs, **and** A_R beats A_C and every control by the same rule (SSIM loss no worse than
−0.01). Secondary: A_C − F_C (does A improve WGS?), A_C − B2, regions, RGB-D block, SSIM.
## Gates, budget, stop
Zero-init/replay fidelity; exact cells; finite outputs; fresh dirs. ≤ 12 RTX 3090 GPU-hours. One run; no release-time sweep.
