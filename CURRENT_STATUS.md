# Current status — read this first (updated 2026-10-10, after S133–S140)

One page. Everything else in the repository is supporting evidence or history.

## Project in one sentence
A diagnostic study of a frozen VMem configuration (surfel-memory video world model + CUT3R) on exposed windows from
two 3DMatch RGB-D scenes: does its geometry-based memory help, and if not, why?

## Answer so far (S133–S137, 2026-10-09)
On this panel, VMem's memory does not help, and repairing it does not change that. Training-free geometry does
far better than the frozen generator.
1. **The surfel map was broken in 8/14 windows** (S133). A silent PnP identity fallback in dust3r's MST init scaled
   the cloud ×300–900 or ×0.02–0.08.
2. **KPS, a known-pose dense scale init (new),** cuts the stage-1 median |log scale ratio| from 0.410 to 0.055, i.e.
   relative error from about 33.5% to 5.4% (S135; 9/9 synthetic tests). It improves a downstream warp predictor by
   +1.75 dB [+0.85, +2.82] over the S133 fix (S137). Its reprojection residual also identifies the pose convention
   (gl wins 14/14).
3. **VMem's retrieval is pose-distance NMS** over a surfel-visibility candidate set. On the repaired map, fp32
   pose-only NMS equals the actual RTX 3090 selection 14/14. It matches H800 14/14 only with TF32 input rounding
   emulated (CUT3R's croco.py permits TF32 globally); that is a strong explanation of the 5/14 H800/3090 divergence,
   not a kernel-level proof. It is also why map repairs barely move retrieval (S135).
4. **The project's priming (5 then 7 frames) left bank offsets 25/30/35 out of memory.** VMem only adds surfels for the
   last 4 frames per construct (S135). Chunked priming fixes coverage (12/12).
5. **The camera convention matters: gl − native = +0.89 dB [+0.25, +1.47], 12/16 windows, 8 seeds** (static arm;
   +0.83 / +0.95 in the H800 / 3090 seed blocks) (S136). The sealed static results used native.
6. **A fully repaired memory shows no detectable gain over static.** gl + KPS + chunked priming passes the map gate
   14/14 (corr 0.785), yet mem_rep_gl − static_gl = −0.06 dB [−1.15, +0.94] (wide CI; not an equivalence test). The
   report's memory − static −0.485 dB (2 seeds) becomes −0.22 dB [−0.82, +0.39] at 8 seeds (INCONCLUSIVE) (S136).
7. **Training-free geometry beats the frozen generator** (S137, against the 8-seed static; a diagnostic contrast,
   not a matched generator control). Copying the nearest history frame +1.16 dB vs native static. CUT3R + KPS forward
   warp (RGB + pose) +5.73 dB vs native and +4.84 dB vs gl, 16/16 windows. SSIM agrees on this panel (+0.11 / +0.14),
   but not on held-out chess, where VMem's frames have higher SSIM than the warp (S140). The advantage is pixel alignment.
8. **Same-pose behaviour** (S137c, 8 seeds). Given aligned target-pose warps as context, VMem reproduces them
   (+0.000 dB [−0.044, +0.053]): pre-warping lifts it +4.8 dB over static, purely by copying. With grey holes it copies
   the grey (−5.4 dB). Its own content for uncovered pixels is worse than nearest fill (hybrid −1.3 dB; SSIM too).
9. **VMem never optimises depth** (codex R250 finding, verified in S138). Its CUT3R fork detaches `im_depthmaps`, so
   the 400-iteration alignment is a no-op for depth. Re-enabling optimisation *hurts*: scale shrinks (|log r| worse
   in 12/14 with KPS; downstream −0.20 dB). The right repair is KPS with no depth optimisation.

10. **Held-out cross-sequence revisits (S139, 7-Scenes chess, pre-registered).** With 32-frame banks drawing on another
   traversal, VMem retrieves history frames (88.5%) that are geometrically better: their warp is +1.46 dB
   [+0.91, +2.05] above the static frames' warp. Yet its generation from them ties static (−0.18 dB [−0.52, +0.15]),
   and the history-favourable stratum is not better (−0.33). The bottleneck is the generator's cross-view use of
   context, not retrieval.

11. **Warp-guided sampling (S140, training-free consumption fix).** Dev panel +0.79 dB over the warp (6-way
   selection); held-out chess **+0.02 dB [−0.10, +0.13]**, so it does not replicate. Covered pixels +0.24 dB (23/24),
   holes −0.24 dB. S139 re-checked in SSIM: memory − static −0.019 [−0.032, −0.006] (worse).

## Earlier results still standing
- Duplicate-slot repair: closed negative, −0.016 dB vs a +0.20 dB bar (`docs/report/TECHNICAL_REPORT_20260918.md`).
- Slot 0 is a coordinate/scale intervention (`work/S130_C8_diagnostics/results_slot_job609617/RESULT.md`).
- Support is not scarce: 78–97% of the target surface is observed (`work/S130_C8_diagnostics/results_support_job609623/RESULT.md`).

## What the report must change
State the native-convention handicap (~0.9 dB, static arm), the broken map, the memory holes, the depth-optimisation
no-op, the TF32 hardware dependence, and the 8-seed memory − static (−0.22 dB, inconclusive). Add the training-free baselines as the reference that any
memory claim must beat.

## Next candidates (each needs a protocol file)
- Finish the write-up: `docs/report/TECHNICAL_REPORT_20261010.md` (v2, includes S139).
- S139 self-audited (`work/agents/SELF_AUDIT_S139.md`); codex optional from 2026-10-10 (owner).
- Science on this frozen consumer is exhausted. Retrieval/memory repairs (S133–S139) and a sampling-side fix (S140)
  do not make it use geometry. Fine-tuning the generator would be the next step, outside a frozen-model study.

## Closed or retired
Duplicate-slot / NMS tuning; hidden-surface / support-scarcity predictors; generic selector scores (crowded:
Keepsake 2610.06588, AnchorWeave 2602.14941); the R112–R249 owner-packet gate loop (AGENTS.md).

## Limitations that always apply
One frozen consumer, two exposed scenes (not held-out), 14–16 windows, PSNR (plus SSIM in S137c), 8 seeds for S136.
CPU stage-1 evidence (S133/S135) is not byte-identical to GPU runs.

## External review
codex R250 (`work/agents/CODEX_R250_S133_S137_AUDIT.md`) verified the S133 mechanism, the KPS algebra, the S136
numbers and the S137 arithmetic. It refuted several wordings (now corrected), found the B2 half-pixel mapping error
(fixed: ≤ 0.016 dB change), and found the depth-optimisation no-op (S138).

## Where things are
Stage results `work/S133_scale_debug/`, `work/S134_tacc_fixed_map/`, `work/S135_scale_init/`,
`work/S136_repaired_memory/`, `work/S137_geometry_baselines/`, `work/S138_depth_opt/`, `work/S139_crossseq_revisit/`, `work/S140_warp_guided/` (each has PROTOCOL.md + RESULT.md) · report v2 `docs/report/TECHNICAL_REPORT_20261010.md` · report
`docs/report/TECHNICAL_REPORT_20260918.md` · ledger `RESEARCH_MEMORY.md` (newest first) · events
`research_events.jsonl` · rules `AGENTS.md`, `RESEARCH_PRINCIPLES.md`.
