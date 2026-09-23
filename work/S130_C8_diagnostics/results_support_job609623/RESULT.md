# C8 Experiment 2 result — support audit (GPU job 609623 + CPU evaluator)

Scope: 14 exposed development windows (scene_13/14), one frozen consumer. Not a method validation.
`new_method_validated=false`, `novelty_authorization=NONE`. GPU: surfel memory + retrieval maps only, no diffusion;
model container saw 144 bank images, 152 poses, 0 depth files.

## Harness gate: 14/14 PASS
For every window the recomputed clean / NMS-off / leaked context lists equal the sealed census lists.

## Pose-convention diagnostic (Amendment 3): FAILS
Median own-render depth correlation 0.190 (threshold 0.5); median own-render ray coverage 0.523 (threshold 0.20).
Median retrieval-depth / dataset-depth ratios range from about 0.12 to about 1.5 in some windows and about 380-1030 in
others (scene_13 w150/w250/w300/w350, scene_14 w150). Per Amendment 3 the J-based rows are
**UNINTERPRETABLE_POSE_CONVENTION**; B and C do not depend on VMem and stay interpretable.

## B and C (dataset geometry only)

| window | B | C nms_on_clean | C nms_off | C nms_on_leaked | C static | sealed PSNR nms_on_clean (mean s42,s7) |
|---|---|---|---|---|---|---|
| scene_13 w50 | 0.892 | 0.888 | 0.887 | 0.889 | 0.818 | 15.066 |
| scene_13 w100 | 0.978 | 0.942 | 0.971 | 0.941 | 0.964 | 12.131 |
| scene_13 w150 | 0.946 | 0.932 | 0.939 | 0.932 | 0.938 | 11.107 |
| scene_13 w200 | 0.984 | 0.972 | 0.968 | 0.972 | 0.969 | 13.789 |
| scene_13 w250 | 0.928 | 0.920 | 0.919 | 0.925 | 0.892 | 14.822 |
| scene_13 w300 | 0.905 | 0.898 | 0.895 | 0.898 | 0.880 | 15.433 |
| scene_13 w350 | 0.931 | 0.923 | 0.899 | 0.923 | 0.879 | 13.318 |
| scene_14 w50 | 0.792 | 0.784 | 0.778 | 0.786 | 0.732 | 14.420 |
| scene_14 w100 | 0.788 | 0.785 | 0.783 | 0.785 | 0.685 | 16.641 |
| scene_14 w150 | 0.755 | 0.491 | 0.748 | 0.491 | 0.633 | 11.765 |
| scene_14 w200 | 0.920 | 0.911 | 0.909 | 0.910 | 0.860 | 16.417 |
| scene_14 w250 | 0.936 | 0.927 | 0.911 | 0.926 | 0.907 | 15.335 |
| scene_14 w300 | 0.873 | 0.861 | 0.856 | 0.861 | 0.808 | 13.230 |
| scene_14 w350 | 0.887 | 0.870 | 0.831 | 0.873 | 0.812 | 11.274 |

## Preregistered decisions
- Low B (true scarcity): **0/14**; in the failure stratum (PSNR <= 16.0): **0/12**.
- High C with poor PSNR (consumption failure): **11/14**; intermediate 3/14 (J uninterpretable).
- **Pilot gate for hidden-surface prediction (>= 8/14 low B in the failure stratum): NOT MET (0/12).**
- Preregistered action: audit `get_cond` / denoiser consumption; do not add a geometry predictor yet.

## Reading (bounded to this panel)
The four delivered frames already observe about 78-97% of the target surface pixels (dataset geometry), yet the
generator's PSNR is <= 16 dB in 12 of 14 windows. The failure is consumption, not missing evidence. The
support-scarcity premise behind the hidden-surface prediction candidates (CAGF / BLSC / Reveal-Event / R37) is
falsified on this panel.

The B/C test itself succeeds at 75-98% cross-frame depth consistency when the dataset poses are read as OpenCV
camera-to-world, which is strong evidence that they are OpenCV. VMem's `get_transformed_c2ws` and `get_cond` negate
the y and z columns, i.e. VMem expects OpenGL-convention input. Combined with the failed own-render depth
diagnostic, a camera-convention mismatch at the harness input is the leading candidate for the consumption
failure. It is a hypothesis, not a finding, until tested directly.
