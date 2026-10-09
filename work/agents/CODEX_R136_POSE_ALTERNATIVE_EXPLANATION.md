# R136 Pose Alternative-Explanation Falsification

**Date:** 2026-09-24  
**Scope:** source-only adversarial check using the three R135 sources plus one non-sealed pipeline callsite. No C8/evaluation data, sealed maps, GT, predictions, runner, GPU, Slurm, receipts, or flags were accessed. No existing file was modified.

## Alternative under test

The strongest alternative to the R135 frame-mismatch explanation is that an upstream step neutralizes the apparent mismatch in one of two ways:

1. the producer internally undoes the Y/Z flip and emits pointmaps/surfels in the raw OpenCV frame; or
2. retrieval-map generation uses the same raw frame as the evaluator, despite the visible pipeline transform.

## Source evidence and exact references

- `work/S130_C8_diagnostics/compute_support_masks.py:6-8` declares raw dataset c2w/OpenCV axes; `:83-88` constructs `p_cv` and `Xw`; `:44-57` and `:90-92` send raw `p_cv`/`p_a` directly to `retrieval_hits` with no explicit `F_3 = diag(1,-1,-1)` conversion.
- `work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:950-955` defines `T_g = T_cv F` by negating c2w rotation columns 1 and 2.
- The visible pipeline callsite at `pipeline.py:975-988` passes `c2ws_transformed` to `run_inference_from_pil`; `:990-1004` receives pointcloud/depth outputs; and `:1031-1037` converts each pointmap to surfels using the same `c2ws_transformed[frame_idx]`. This boundary is therefore explicitly transformed on both the producer call and pointmap-to-surfel conversion.
- `pipeline.py:272-302` renders with `R^{-1}(X-t)` and positive camera z; `:1123-1140` applies the Y/Z flip before inversion for conditioning.
- `work/agents/CODEX_R133_POSE_HYGIENE_AUDIT_20260924.md:55-71` records that the producer-side pointmap frame is not stated by the inspected source, while `:73-88` requires a synthetic CPU identity check before scoring.

## Verdict: **UNRESOLVED**

The visible callsite does not support the claim that retrieval-map generation intentionally stays in the raw frame: it passes the flipped pose into the producer and again into pointmap-to-surfel conversion. This weakens the raw-frame alternative.

The alternative is not rejected, however. The body of `run_inference_from_pil`/the upstream producer is outside this bounded source set, so these lines cannot prove whether that producer internally cancels `F` or emits points in `p_cv`. Consequently the source evidence supports an evaluator-hygiene risk, but cannot uniquely identify the map frame or certify that the mismatch survives upstream.

No method claim follows from either hypothesis. Keep `new_method_validated=false` and `novelty_authorization=NONE`.

## One discriminating synthetic CPU check

Construct a metric plane/cube with known `T_cv`, `K`, and world points `X`. Compute

`p_cv = inv(T_cv) X`, `p_g = inv(T_cv F) X`, and `F_3 p_cv` with `F_3=diag(1,-1,-1)`.

For each candidate producer contract, generate a tiny retrieval map and compare both evaluator inputs (`p_cv` and `F_3 p_cv`) against the direct renderer coordinates. The raw-frame alternative predicts `p_cv` agrees and `F_3 p_cv` disagrees; the transformed-frame explanation predicts `F_3 p_cv` agrees and raw `p_cv` disagrees for nonzero Y/Z points. Accept a candidate only if finite bidirectional coordinate/reprojection error is `<=1e-6` under the frozen rounding and depth-unit rules. This test distinguishes upstream neutralization from an evaluator-only join omission without using C8 data.

## Stop rule

If the synthetic fixture does not uniquely select one producer frame, if either candidate has non-finite error or error `>1e-6`, or if the producer contract remains unavailable, stop with `H2_UNIDENTIFIABLE`. Do not reinterpret or rescore real C8 values, submit GPU work, or reopen a method/novelty claim. Preserve `new_method_validated=false` and `novelty_authorization=NONE`.
