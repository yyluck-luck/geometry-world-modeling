# S141 result — fine-tuning the VMem generator: domain LoRA helps (+0.33 dB, transfers to RGB-D); the warp-conditioned variant fails in PSNR; memory still does not help

Protocol: `PROTOCOL.md` (frozen at 7cefe20e before training; Amendment 1 at a67cb62a, before any evaluation output).
External review: codex `gpt-6-astra` (ultra) R253 (retrieval), R254 (hostile review), R255 (ideation); verification by
self-audit (`results/SELF_AUDIT_CHECKS.json`, all checks pass). `new_method_validated=false`, `novelty_authorization=NONE`.

## Execution
- Data: 2000 fixed clips from 7-Scenes fire/heads/office/pumpkin/redkitchen/stairs (chess and RGB-D Scenes excluded;
  monitor split office/seq-10, redkitchen/seq-14). Latents/CLIP for 7400 frames. B training warps: 2032 clips, KPS OK
  2032/2032, mean coverage 0.54.
- Training (TACC gpu13, RTX 3090): A on GPU 3, B on GPU 4, 10000 steps each, 1.32–1.40 s/step, 8.7 GB peak. Final
  adapters verified (step 10000, 512 LoRA tensors, finite; B + 2 warp-branch tensors): A 635e6e31…, B 0dd40c86….
- Monitor-split validation loss (ε-MSE, 6 fixed σ levels) stayed flat for both (A 0.0479 → 0.0491, B 0.0479 → 0.0492;
  `results/tacc/runs/*/train_log.jsonl`). The denoising loss on new sequences did not improve measurably.
- Fidelity gate: base S139 output = A (zero-init) = B (zero-init), byte-identical (913394e0…).
- Evaluation: chess 24 windows × seeds 3–6 (A_static, A_mem, B_mem; exploratory B_static), RGB-D Scenes 16 windows ×
  seeds 3–6 (A_static, B_static); all final adapters, all RTX 3090, all cells complete and finite. Base comparators
  (S139/S136 RTX 3090 outputs, 256 cells) match their generation receipts.
- Note: the chess-A pass ran under the evaluation chain started before Amendment 1 (generator without the finite guard;
  its 192 outputs were checked finite separately). Its official score file and an independent re-score agree exactly in
  PSNR (SSIM within 7.5e-8, float32 convolution order).

## Pre-registered results (`results/S141_ANALYSIS.json`; window mean over seeds 3–6, window-bootstrap 95% CI)
Means, chess PSNR: base_static 11.49, base_mem 11.28, A_static 11.94, A_mem 11.61, B_mem 11.02, B2 warp(mem) 14.57.
SSIM: base_static 0.487, base_mem 0.468, A_static 0.494, A_mem 0.486, **B_mem 0.505**, warp 0.432.

| contrast | Δ PSNR (dB) | 95% CI | wins | verdict | Δ SSIM | verdict |
|---|---|---|---|---|---|---|
| **PRIMARY A: A_mem − base_mem** | **+0.330** | [+0.078, +0.585] | 17/24 | **IMPROVES** | +0.018 | IMPROVES |
| A_mem − A_static | −0.332 | [−0.669, +0.006] | 5/24 | INCONCLUSIVE | −0.008 | NO_MATERIAL_CHANGE |
| A_static − base_static | +0.448 | [+0.096, +0.822] | 17/24 | IMPROVES | +0.007 | NO_MATERIAL_CHANGE |
| **PRIMARY B: B_mem − B2 warp** | **−3.558** | [−3.913, −3.201] | 0/24 | **WORSENS** | +0.073 | IMPROVES |
| B_mem − base_mem | −0.260 | [−0.531, +0.020] | 8/24 | INCONCLUSIVE | +0.037 | IMPROVES |
| B_mem − A_mem (exploratory) | −0.591 | [−0.767, −0.415] | 2/24 | WORSENS | +0.019 | IMPROVES |
| base_mem − base_static (S139 replica, seeds 3–6) | −0.214 | [−0.532, +0.099] | 10/24 | INCONCLUSIVE | −0.019 | WORSENS |

Exploratory (Amendment 1, B with static contexts and their warps):
| contrast | Δ PSNR | 95% CI | Δ SSIM |
|---|---|---|---|
| B_static − B2 warp(static) | −2.129 | [−2.637, −1.599] | +0.051 |
| B_mem − B_static | +0.030 | [−0.152, +0.231] | −0.020 |
| (B_mem − B_static) − (A_mem − A_static) | +0.362 | [+0.030, +0.696] | −0.012 |
| B2 warp(mem) − B2 warp(static) | +1.458 | [+0.906, +2.051] | −0.042 |

RGB-D Scenes secondary panel (exposed; static contexts; base = S136 RTX 3090 static_gl):
| contrast | Δ PSNR | 95% CI | wins | Δ SSIM |
|---|---|---|---|---|
| **A_static − base_static** | **+1.162** | [+0.612, +1.729] | 13/16 | +0.039 |
| B_static − B2 warp | −7.430 | [−8.397, −6.521] | 0/16 | −0.163 |
| B_static − base_static | −2.617 | [−3.425, −1.828] | 0/16 | −0.057 |

Region split (chess, covered/uncovered by each arm's own warp): B_mem is below the warp by 3.65 dB in covered and 3.49 dB
in uncovered pixels; versus base_mem it is −0.20 (covered) / −0.42 dB (uncovered).

## Reading
- **Domain adaptation is a real factor.** Attention-only LoRA on six other 7-Scenes rooms improves VMem on held-out chess
  (+0.33 dB memory contexts, +0.45 dB static) and transfers to a different dataset (RGB-D Scenes, +1.16 dB, exposed panel).
  The monitor denoising loss did not move, so the gain shows up only in sampling, not in the training objective's
  validation curve.
- **Fine-tuning does not make memory useful.** After adaptation, retrieved history contexts are still worse than recent
  ones (A_mem − A_static −0.33 dB, 5/24). The S139 disconnect survives domain adaptation.
- **The warp-conditioned recipe B failed in PSNR on every panel.** It is far below the warp it receives (chess −3.6 dB,
  RGB-D −7.4 dB) and below A. It does not copy or refine the warp. On chess it has the highest SSIM of all arms, on
  RGB-D it is worse than base in both metrics. The B recipe (established warp+mask conditioning; R253) under this
  budget did not learn useful warp consumption.
- One exploratory signal: with B, memory contexts are no worse than static ones (+0.03), while with A they are −0.33;
  the difference-in-differences is +0.36 [+0.03, +0.70]. Exploratory, and it comes with B's overall PSNR loss.
- **S142 branch:** PRIMARY_B = WORSENS → per the frozen S142 table, no E1/E2/E3; write up.

## Exploratory output diagnostics (after all verdicts; `results/tacc/eval/OUTPUT_DIAGNOSTICS.json`, `diag_outputs_s141.py`)
Chess mem_vmem contexts, 24 windows × seeds 3–6, framewise means:
| arm | mean signed error (grey levels) | PSNR | low-pass PSNR (σ 4 px) | high-freq. energy / target | PSNR to the warp |
|---|---|---|---|---|---|
| base_mem | +0.73 | 11.34 | 12.10 | 0.947 | 11.46 |
| A_mem | −7.96 | 11.66 | 12.34 | 0.757 | 11.88 |
| B_mem | +3.78 | 11.07 | 11.67 | 0.714 | 11.50 |
| B2 warp | −3.73 | 14.65 | 16.58 | 1.472 | — |
- B is no closer to the warp than the frozen base is (11.50 vs 11.46 dB): the warp branch had little effect on the output;
  B neither copies nor refines the warp. Its PSNR deficit is in low frequencies (layout/colour: 11.67 vs base 12.10).
- Both adapters remove high-frequency energy (0.76, 0.71 of the target's vs 0.95 for base), consistent with higher SSIM
  from fewer invented fine textures. A also darkens the output by ~8 grey levels on average while gaining PSNR.
- These are descriptive; no mechanism was tested.

## Limits
One training run per variant, one seed; 10000 LoRA steps on 2000 clips; chess examined earlier in S139/S140 (held out from
training, not untouched); window CIs on three dependent sequence pairs; training memory contexts were pose-only (eval
mem_vmem); training warps GPU vs eval warps CPU; NO_MATERIAL_CHANGE is not equivalence (R254).

## Files
`PROTOCOL.md`, scripts (`s141_common.py`, `prep_latents_s141.py`, `build_clips_s141.py`, `warps_s141.py`, `train_s141.py`,
`gen_s141.py`, `check_adapter_s141.py`, `verify_base_s141.py`, `analyze_s141.py`, `self_audit_s141.py`, chain scripts),
`clips_s141.json`, plans, `results/` (analysis, self-audit, receipts under `results/tacc/`).
