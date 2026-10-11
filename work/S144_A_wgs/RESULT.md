# S144 result — stopped at the frozen development gate: adapter A does not make terminal release useful; a global blend of generation and warp beats every candidate

Protocol: `PROTOCOL.md` (frozen 56785b92; codex R262 idea, R263 rejection). Training-free. `new_method_validated=false`,
`novelty_authorization=NONE`.

## Execution and gates
- Replay: the new generator's frozen-model W2 endpoint (F_C) equals the archived S140 W2 output byte-for-byte (chess
  window 0, seed 3, 405d7fca…), so F_C/F_R and A_C/A_R come from one implementation (`results/REPLAY_SHA256.txt`).
- Development panel: the 32 S141 monitor clips (office/seq-10, redkitchen/seq-14), CPU warps from the evaluation geometry
  path (CPU vs GPU monitor warps: median 30.6 dB agreement, 94.7% identical coverage; `results/MONITOR_WARP_CPU_VS_GPU.json`),
  seeds 3, 4. All cells complete and finite; C/R trace invariants asserted in the generator.
- Timing: development 2.18 GPU-h; projected case panels 3.64 GPU-h (inside the 12 GPU-h cap).
- Blend coefficients fitted on development only (`results/ALPHA.json`): α_V 0.75, α_FC 0.55, α_AC 0.60.

## Development gate (`results/DEV_GATE.json`) — PERFORMANCE GO failed → S144 stops (frozen rule; no case panels)
| quantity (development, mean over 32 clips × 2 seeds) | value | required |
|---|---|---|
| interaction I = (A_R − A_C) − (F_R − F_C) | **−0.003 dB** | ≥ +0.20 |
| A_R − A_C (release terminal overwrite, adapter A) | +0.008 dB | ≥ +0.20 |
| A_R − B2 / − V / − P_V / − P_FC / − P_AC / − BL_V | +0.207 / +0.135 / +0.160 / +0.145 / +0.142 / +0.125 | ≥ +0.20 each |
| A_R − BL_FC / − BL_AC | **−0.185 / −0.210 dB** | ≥ +0.20 each |
| secondary: A_C − F_C; F_C − B2; F_C − V | +0.068; +0.132; +0.059 | — |

Mean development PSNR: B2 13.19, V 13.26, F_C 13.32, F_R 13.33, A_C 13.39, A_R 13.40, **BL_FC 13.58, BL_AC 13.61**, ordinary A
(context-only, no warp) 11.19. SSIM: BL_AC 0.592, BL_V 0.592, BL_FC 0.591, V 0.587, A_R 0.581, B2 0.573.

## Reading
- **The release mechanism is null.** Skipping the final covered-latent overwrite changes PSNR by < 0.01 dB for both the
  frozen and the adapted model; the hypothesised interaction does not exist on the development panel.
- Adapter A improves the warp-guided sampler only slightly (+0.07 dB) and inconsistently across the two monitor sequences.
- On this panel the frozen S140 sampler beats the raw warp (+0.13 dB), and beats its VAE round trip by only +0.06 dB, so most
  of the "covered-pixel polish" is reproduced by encoding and decoding the warp (R262's correction to S140 holds here).
- **Exploratory observation:** a single global convex blend of a generated output and the warp (α ≈ 0.55–0.6) is the
  strongest predictor (+0.19 to +0.21 dB over A_R, +0.39 over B2), in both PSNR and SSIM. α was fitted on the same
  development clips, so this advantage is optimistic; it was not evaluated on a case panel (S144 stopped by rule).

## Files
`gen_s144.py`, `score_s144.py`, `analyze_s144.py`, `build_plans_s144.py`, `warps_monitor_s144.py`, `s144_chain.sh`, plans,
`results/` (gate, alpha, scores, timing, replay, receipts).
