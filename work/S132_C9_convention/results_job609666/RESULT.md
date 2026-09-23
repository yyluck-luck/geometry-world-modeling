# C9 result — pose-convention test (job 609666)

Development panel, one frozen consumer. Not a method validation. `new_method_validated=false`, `novelty_authorization=NONE`.
GPU about 0.65 H800-hours (37 min on dgx-25). Model containers saw 0 depth files.

## Harness gate: PASS
All 32 `native` outputs are byte-identical to the sealed S111 static outputs (job 594957) and their PSNR equals
the sealed S113 static rows (32/32 and 32/32).

## Primary (static context, 16 windows, seeds folded): **INCONCLUSIVE**
Mean delta PSNR(gl) - PSNR(native) = **+0.687 dB**; positive in **12/16** windows. Preregistered MISMATCH_CONFIRMED
required mean >= +1.0 dB and >= 12/16; only the second condition holds.
Per-window deltas range from -2.530 to +3.715 dB (scene_14 w200 -2.53, scene_14 w100 -2.38, scene_13 w100 -1.92;
scene_14 w50 +3.72, scene_14 w150 +2.83, scene_13 w50 +2.19, scene_13 w250 +2.19).

## Secondary (surfel memory rebuilt with gl poses, unchanged C8 evaluator): **NOT RESTORED**
- Median own-render depth correlation: native 0.190 -> gl **0.594** (criterion >= 0.5 met); correlation rose in 11/13 windows.
- Windows with median depth ratio in [0.5, 2]: native 7/14 -> gl **7/13** (criterion >= 12 not met).
- The five windows with depth ratios of roughly 400-960 are the **same windows under both conventions**
  (scene_13 w150/w250/w300/w350, scene_14 w150), with nearly unchanged ratios. That scale failure is therefore
  **not caused by the pose convention**; it is a separate failure of the surfel reconstruction on those windows.
- The gl surfel run blocked on scene_13 w200 (`IndexError: list index out of range`); 13/14 windows completed.

## Reading (bounded)
The camera convention materially changes VMem's behaviour on this dataset (surfel depth agreement improves in most
windows; generation moves by up to +/-3.7 dB per window), but converting to OpenGL does not improve generation
consistently, and the preregistered thresholds for a confirmed mismatch are not met. The pose-convention
hypothesis is neither confirmed nor refuted. With only two seeds per window and seed-to-seed differences of about
1.5 dB observed in C8 Experiment 1, per-window deltas are noisy; more seeds would be needed to resolve it.
Independently, five windows show a convention-independent surfel scale blow-up that needs its own diagnosis.
