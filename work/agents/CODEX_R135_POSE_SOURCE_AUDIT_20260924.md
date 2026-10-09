# R135 Pose-Source Audit (strictly bounded)

**Date:** 2026-09-24  
**Scope:** source-only inspection of the requested evaluator file, the pipeline transform definition, and one non-sealed memo. No C8/evaluation data, sealed maps, GT, predictions, runner, GPU, Slurm, receipts, or flags were opened or changed. No existing file was modified.

## Files inspected and exact references

1. `work/S130_C8_diagnostics/compute_support_masks.py`
   - Lines 6-8 declare dataset poses as camera-to-world with OpenCV axes `(x right, y down, z forward)` and depth PNG units in millimetres.
   - Lines 27-42 implement visibility as `R^T (X-t)`, positive camera `z`, pinhole projection, and depth agreement.
   - Lines 83-88 back-project target depth to target-camera `p`, then lift with `Xw = p R^T + t`.
   - Lines 44-57 (`retrieval_hits`) assume the supplied `p_cam` is already in the retrieval-map camera frame; they use positive `z`, a centred principal point, and apply no explicit Y/Z convention matrix.
   - Lines 90-92 pass raw target-camera points (`p`, and `pa` for the averaged pose) directly to `retrieval_hits`.

2. `work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py`
   - Lines 149-181 label and store inputs as camera-to-world matrices (`c2w`).
   - Lines 272-302 form renderer camera coordinates with `R^{-1}(X-t)`, require positive camera `z`, and use pinhole projection.
   - Lines 950-955 define `get_transformed_c2ws`: rotation columns 1 and 2 are multiplied by `-1`, i.e. `T_g = T_cv F` with `F = diag(1,-1,-1,1)`.
   - Lines 975-982 pass the transformed poses into scene construction/inference.
   - Lines 1123-1140 apply the same Y/Z flip before inversion to world-to-camera matrices and Plücker construction.

3. `work/agents/CODEX_R133_POSE_HYGIENE_AUDIT_20260924.md` (non-sealed memo)
   - Lines 24-42 record the evaluator's implicit retrieval-map-frame assumption and the raw `p_cam` join.
   - Lines 55-71 record the pipeline boundary flip, renderer algebra, and the absence of a producer-side statement proving the CUT3R pointmap frame.
   - Lines 73-88 mark the producer convention as unavailable/`H2_UNIDENTIFIABLE`, retain `new_method_validated=false` and `novelty_authorization=NONE`, and require a synthetic CPU identity check before scoring.

## Evidence classification

**Evaluator hygiene is supported as a source-level concern.** The evaluator's `p` is in the declared raw OpenCV camera convention, while the pipeline's rendered map path uses `T_cv F`; `retrieval_hits` contains no compensating conversion. This is sufficient to flag a possible frame-join mismatch in the evaluator contract.

**The producer-boundary explanation remains an unresolved hypothesis.** The inspected sources do not establish whether the upstream pointmap producer expects `T_cv` or `T_cv F`; therefore the map's actual metric frame is not proven by these files alone. The memo's `H2_UNIDENTIFIABLE` status is retained.

**No method claim is supported.** These lines provide convention/provenance evidence only. They do not show a new information path, selective geometry update, held-out improvement, or any validated mechanism; keep `new_method_validated=false` and `novelty_authorization=NONE`.

## One falsifiable prediction

On a CPU-only synthetic plane/cube fixture with known `T_cv`, `K`, and `F_3 = diag(1,-1,-1)`, if a retrieval map is rendered under `T_g = T_cv F`, then projecting the evaluator's target point as `F_3 p_cv` must reproduce the direct renderer camera point (same valid pixel/depth within the frozen rounding and tolerance), while projecting raw `p_cv` must disagree for points with nonzero Y or Z. This prediction is falsifiable without C8 data and distinguishes the evaluator join issue from a generic method effect.

## Stop rule

Before any real-data score is interpreted, require a source-pinned producer-frame identity fixture with finite bidirectional error `<= 1e-6` and one uniquely supported transform. If the fixture fails, or both `T_cv` and `T_cv F` remain equally plausible at the producer boundary, stop with `H2_UNIDENTIFIABLE`; do not rescore/interpret C8, submit GPU work, or reopen a method/novelty claim. Preserve `new_method_validated=false` and `novelty_authorization=NONE`.
