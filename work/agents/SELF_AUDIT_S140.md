# Self-audit of S140 (self-audit, no codex; owner 2026-10-10)

| check | result |
|---|---|
| Re-implemented sampling loop vs VMem sampler (`none` vs `ref`), seeds 42/7 | byte-identical (FIDELITY_SHA256.txt) |
| Dev warps = S137 B2-kps with corrected mapping | mean 20.0869 dB, identical to S137 |
| Chess warps = S139 B2 of mem_vmem contexts | mean 14.5724 dB, identical to S139 |
| Variant selection follows the pre-registered rule (max mean PSNR, SSIM tie-break) | W2 0.5 selected; Amendment 1 written before stage 2 |
| Stage 2: 24 windows × 8 seeds, seed→site split, contexts = S139 mem_vmem | PASS (`seeds_complete_8` true) |
| New SSIM scorer: PSNR equals S139 scorer | max abs diff 3.6e-15 over 96 outputs |
| Region-split rescoring of dev outputs leaves total PSNR unchanged | identical to the job scores (< 1e-9) |
| Sbatch export pitfall (comma in SEEDS) | caught before the dev run (job 675152 cancelled, resubmitted as 675153) |

Notes: W2 masks are latent-block level (8×8 px, coverage ≥ 0.5), so hole borders are blocky. The hole-content hypothesis
(crop bands vs disocclusions) is untested. On chess the PSNR and SSIM conclusions differ for warp vs generator; both are
reported.
