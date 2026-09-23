# C9 pose-convention test — preregistration (committed before any C9 output exists)

Owner decision C9 (2026-09-23). Development panel only; not a method validation.
`new_method_validated=false`, `novelty_authorization=NONE`.

## Question
C8 Experiment 2 found high support (B, C) but poor generation (consumption failure 11/14) and a failed surfel
depth-consistency diagnostic. The B/C test succeeds when dataset poses are read as OpenCV camera-to-world, while
VMem's `get_transformed_c2ws` and `get_cond` negate the y and z columns, i.e. VMem expects OpenGL-convention input.
Does feeding VMem OpenGL-convention poses (negate the y and z columns of every context and target c2w) change
generation, and does it restore surfel depth consistency?

## Design
- Primary: static context `[start+0, +15, +30, +45]` (no retrieval), 16 windows (scene_13/14, starts
  0,50,...,350 where targets exist), seeds 42 and 7, conventions `native` and `gl`. Runner
  `convention_test_c9.py` = `nms_s111.py` lines 1-116 verbatim + a loop that differs only by the pose conversion.
- Secondary: surfel memory rebuilt with `gl` poses (`run_support_retrieval_c9.py`, 14 windows), evaluated with
  the unchanged C8 evaluator `compute_support_masks.py`; compare own-render depth correlation and J with the
  C8 native run (job 609623).

## Harness gate (binding)
Every `native` output must be byte-identical to the sealed S111 static output of the same scene/window/seed
(job 594957) and its PSNR must equal the sealed S113 static row. If not, no delta is interpreted.

## Estimand and decision (primary)
Per window, seeds folded: `delta = PSNR(gl) - PSNR(native)`. Over the 16 windows:
- **MISMATCH_CONFIRMED** if mean delta >= +1.0 dB and delta > 0 in >= 12 of 16 windows;
- **NATIVE_CORRECT** if mean delta <= -1.0 dB and delta < 0 in >= 12 of 16 windows;
- **NO_EFFECT** if |mean delta| < 0.3 dB;
- otherwise **INCONCLUSIVE**.

## Secondary corroboration
Surfel consistency under `gl` is declared restored if median own-render depth correlation >= 0.5 (C8 native: 0.190)
and median depth ratio lies within [0.5, 2.0] for at least 12 of 14 windows.

## What each outcome means
- MISMATCH_CONFIRMED: every generation result on this RGB-D Scenes v2 harness (S103 onwards, including the
  technical report's contrasts) was produced with a camera-convention error and must be re-measured with
  converted poses before any interpretation or method work.
- NATIVE_CORRECT / NO_EFFECT: the consumption failure is not explained by pose convention; audit the denoiser's
  consumption of correctly posed evidence next.
- INCONCLUSIVE: report as such; no follow-up claim.

## Budget
About 64 generations at ~9 s plus 14 surfel builds at ~80 s: roughly 35 minutes on one H800 (~0.6 H800-h).
