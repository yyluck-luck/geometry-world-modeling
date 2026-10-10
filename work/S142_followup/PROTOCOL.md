# S142 protocol — one S141-outcome-selected follow-up (frozen before any S141 evaluation output is read)

Frozen 2026-10-10 ≈ 14:40 UTC. Supersedes `PROTOCOL_DRAFT.md`, revised per codex `gpt-6-astra` (ultra) rejection round
R256 (`work/agents/CODEX_R256_S142_DRAFT_REJECTION.md`, adopted in full; its "Corrected minimal E1 / E2 specification"
sections are part of this protocol). Owner standing authorization (2026-10-09). `new_method_validated=false`,
`novelty_authorization=NONE`. At freezing time S141 A/B chess generation was still running; no S141 score or image had
been opened by the agent.

## Branch table (applied once, mechanically, to the valid S141 PSNR verdicts)
| S141 outcome | action |
|---|---|
| execution invalid or registered cells missing (self-audit fails) | repair/complete S141 only; S142 does not start |
| PRIMARY_B = IMPROVES (any A) | **E1** only |
| PRIMARY_B = INCONCLUSIVE | report uncertainty; write up (no E2, no extra seeds) |
| PRIMARY_B = WORSENS (any A) | write up (no E2, no E3) |
| PRIMARY_B = NO_MATERIAL_CHANGE and PRIMARY_A = IMPROVES | **E2** pilot; full E2 only if its gate passes |
| PRIMARY_B = NO_MATERIAL_CHANGE and PRIMARY_A ≠ IMPROVES | write up |

## E1 — registration sensitivity of B's warp-appearance path
Final S141 B adapter, S139 chess mem_vmem plan, S140 warps, seeds 3–6, RTX 3090. Two arms: every nearest-filled warp
shifted horizontally by +16 px and by −16 px on the 576×576 model grid (reflect padding, same shift for all frames,
windows, seeds), applied before the same VAE encoding; coverage tensor, contexts, CLIP, cameras, noise unchanged;
shifted latents in both CFG dicts; caches keyed by intervention. **Scoring always uses the original warp RGB and masks.**
B(correct) = S141 B_mem outputs, reused only after receipt matching and one exact unchanged replay.
- Primary: d = mean over seeds of PSNR(B_correct) − ½[PSNR(B_+16) + PSNR(B_−16)], window mean; ≥ +0.2 dB with
  window-bootstrap CI lower bound > 0 (10k, rng 0) **and** no negative mean in 2 of the 3 sequence pairs.
- Secondary: each direction; SSIM; covered/uncovered (original masks); stable-label interior region (≥ 32 px from the
  border, coverage label equal at x, x−16, x+16); per pair; pair-cluster uncertainty (descriptive).
- Reading: positive → B's quality depends on registration of the warp appearance under this perturbation (not
  "geometric reasoning", not retrieval benefit). Miss → not supported by this intervention; if the CI upper bound is
  < +0.2 dB that practical effect is excluded for this panel only.
- Budget: 192 generations + 1 replay (≈ 2–4 GPU-h). Then write up.

## E2 — trained warp-as-context restoration package C (only in its branch)
Specification exactly as R256 "Corrected minimal E2": context slots and z[:4] = VAE latents of the four target-pose
warps (also in unconditional training examples), context cameras/K = the target cameras, CLIP from the warp images,
targets noisy, no extra branch, no coverage input; LoRA r16 recipe of S141 A, 10000 steps, seed 0; effective target CFG
1.2 for C and C0 alike. Zero-init C must match an adapter-free model on the same C inputs byte-for-byte.
- Pilot gate (one disposable run, first 500 steps of the normal stream): on the 8 fixed monitor clips c02006, c02016,
  c02000, c02003, c02001, c02002, c02009, c02010 (seed 3, final sampler), continue only if mean PSNR(C500 − W) ≥ +0.2
  and mean PSNR(C500 − C0) ≥ +0.2, each positive in ≥ 5/8 clips, each SSIM difference > −0.01, and all tensors/outputs
  finite with adapters changing and frozen weights unchanged. No retry.
- Full run (fresh, from base): C and frozen C0 on the 24 chess windows, seeds 3–6. Useful trained refinement requires
  **both** C − W and C − C0 ≥ +0.2 dB with CI lower bound > 0 and no sign reversal in 2 of 3 pairs. Secondary: C − B_mem,
  C − A_mem, C − base_mem; SSIM (a material SSIM decline makes a PSNR win a trade-off); covered/uncovered; VAE round-trip
  and C0-to-W residuals (copying is a hypothesis, not assumed).
- Hard cap 10 RTX 3090 GPU-hours summed across cards; if the full run plus controls cannot fit after the pilot timing,
  stop before it. End the budgeted learned-consumer search afterwards regardless of sign (a management rule, not a
  claim that learned consumption cannot work).

## Shared rules
Final adapters only; fresh output directories; exact cell counts; finite-output guard; S141 Amendment-1 hardening
carried over. Chess is an exposed panel (follow-up, not untouched confirmation). Region labels = covered / uncovered by
the warp. No temporal-quality, novelty or population claims.
