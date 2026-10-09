# S137 protocol — training-free geometric predictors vs frozen VMem

Owner standing authorization (2026-10-09). `new_method_validated=false`, `novelty_authorization=NONE`.

## S137a — already run (exploratory, recorded before this protocol was written)
`geometry_baselines.py`, CPU, 16 windows × 4 targets, VMem static contexts (offsets 0,15,30,45). Scorer and model-grid
transform copied from C9. The VMem reference is C9's H800 static scores (seeds 42/7).
- B0 copy (nearest context by VMem's pose geodesic): 15.52 dB, beats VMem static native in 13/16 windows.
- B1 dataset-depth forward warp + nearest fill: 22.05 dB, beats VMem in 16/16 windows.
- VMem static: native 14.56 dB, gl 15.25 dB.
B1 uses history-frame depth from the RGB-D dataset, so it is an RGB-D upper bound, not an RGB-only method.

## S137b — pre-registered here, before running
**Question.** Does a deployable, RGB + pose-only geometric predictor beat VMem? Does the scale repair carry through
to image quality?
**B2.** Run CUT3R on the four static context frames with their known poses (gl convention, as VMem would after the
convention fix) and a star graph rooted at frame 0. The global alignment is VMem's (niter 400, lr 0.01), with
INIT ∈ {orig (VMem as is), fix (S133), kps (S135)}. The optimised depth maps are mapped back to the 640×480 grid
(CUT3R's crop covers rows 60–420, cols 80–560; elsewhere is a hole). Forward-warp + nearest fill as B1.
No dataset depth is used.
**Metrics.** PSNR (C9 scorer), window = 4 targets. Compared against VMem static (C9 2-seed now; S136 8-seed when
available) and against B0/B1.
**Pre-registered expectations and decision.**
1. Scale carries to pixels if B2-kps > B2-fix > B2-orig in mean PSNR, with B2-kps ≥ B2-fix in ≥ 10/16 windows.
2. "Geometry alone beats the frozen generator" if B2-kps exceeds VMem static (native and gl) in mean, with
   window-bootstrap CI > 0 against the 8-seed S136 static when available. Otherwise reported against C9 2-seed only.
3. Every negative is reported as it comes.

## S137c — later (cluster), design only
Hybrid: warp where B2 has coverage, VMem output elsewhere. Warp-as-context: replace one VMem context with the B2 render
at the target pose. Each needs its own amendment before running.
