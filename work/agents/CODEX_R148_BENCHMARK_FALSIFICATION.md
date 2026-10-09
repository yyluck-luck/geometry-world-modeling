# R148 Benchmark Falsification: Future Multi-System Frame-Contract Study

**Access date:** 2026-09-24  
**Scope:** bounded falsification of the possible future benchmark direction after R140/R146, using only R140, R142, R144, R146, and the primary/official sources cited by R142. No protected data, code execution, fixture/runner, GPU, Slurm, evaluation replay, receipt, or flag mutation was used.

## Question

Does a future multi-system benchmark for producer-frame contracts and same-map raw-versus-`F3` queries retain an independent scientific or evaluation gap, or is it only a repackaging of established camera, convention, and multi-view checks?

## Overlap evidence

1. **Camera correctness is already benchmarked.** COLMAP `models_test.cc` supplies maintained camera-to-image, image-to-camera, ray, depth-scaled, and pixel round trips over camera models. PyTorch3D `tests/test_cameras.py` supplies synthetic camera-frame sanity and bidirectional project/unproject checks across OpenGL, SfM, FoV, and perspective families (R142 items 10–11). These cover identity, positive-depth, projection, inverse, and tolerance-based correctness.

2. **Frame conversion contracts are already explicit.** COLMAP, Nerfstudio, and 3D Gaussian Splatting document or implement OpenCV/OpenGL axis conversion; Nerfstudio and related loaders fix pixel-center and pose conventions (R142 items 1–3 and 6). DUSt3R makes a common pointmap frame explicit and allows a canonical frame beyond raw OpenCV or `F3` (R142 item 9). Thus the producer-frame registry and `F3` operation are established contract checks, and R140's two-row hypothesis space is incomplete without a source-pinned tag.

3. **One representation with many queries is routine.** NeRF, pixelNeRF, iMAP, and 3D Gaussian Splatting reuse one scene representation/map for multiple poses, locked-map tracking, or held-out views (R142 items 12–15). Same-map query reuse and separation of map generation from query evaluation are therefore established controls.

4. **Geometric consistency and fixed-denominator scoring already exist.** MVS work uses forward/backward reprojection, depth residuals, masks, and fixed thresholds (R142 items 7–8). The R140 ID/depth table is a specific packaging of these checks.

5. **R140's literal composition is unmeasured.** R140's immutable producer map, pre-registered frame tag, 2x2 query table, and `H2_UNIDENTIFIABLE` branch are not shown in the cited sources as one named benchmark. R146 correctly classifies this as a possible construction project, but R144 shows that the underlying controls are already covered and the exact table/label is procedural.

## Falsification result

**Verdict (b): no independent benchmark gap is defensible from the current evidence. Preserve END-LINE.**

The unobserved item is only a cross-system *packaging and measurement study*: multiple producers, hidden convention labels, held-out fixtures, and a common scoreboard. That could be useful engineering infrastructure, but no independent estimand, failure mode, or scientific mechanism is established by R140/R146. The exact 2x2 table and fail-closed label do not by themselves create a benchmark gap. A claim that the field lacks this benchmark would require a broader, reproducible search and direct evidence that existing suites cannot measure the proposed property; those prerequisites are absent here.

A future benchmark might still be worth constructing as a separate evaluation resource if it demonstrates a new, decision-relevant quantity, but that is a conditional project, not a surviving gap in this research line.

## Uncertainty and what would change the verdict

- The cited-source set is bounded; it does not prove that no external benchmark exists.
- No producer matrix, hidden-label split, independent rerun, or downstream estimand has been executed.
- The conclusion concerns defensible novelty/gap status under the present evidence contract, not the practical usefulness of QA tooling.
- A revised verdict would require all of the following before any gap claim: a documented search showing no existing benchmark measures the same estimand; at least three independently maintained producer families; source-pinned frame/depth schemas; hidden convention labels and held-out geometries; a pre-registered metric such as false-unique-pass or ambiguity-rejection rate; baselines that include COLMAP/PyTorch3D round trips and ordinary declared-convention checks; and an independent rerun showing a reproducible, decision-relevant difference.

## Rejection criteria

Reject the future benchmark claim if it has any of:

- one producer, one 24-point fixture, or unknown producer frame/schema/units;
- no hidden labels or held-out geometry/poses;
- no independent estimand beyond pass/fail packaging or mean residual;
- no frozen baseline matrix and no independent rerun;
- outcome-selected map regeneration, convention relabeling, or branch-specific maps;
- a result that merely reproduces standard round-trip or reprojection checks;
- any use of protected evaluation data, receipt mutation, or validation-flag changes.

## Next action

Stop benchmark novelty development at END-LINE. Retain R140 only as internal evaluator hygiene. If an owner later authorizes a separate benchmark-construction project, begin with a source-pinned search and protocol review satisfying the prerequisites above; do not implement or execute the current R140 fixture, runner, or scoring path under this research line. Keep `new_method_validated=false` and `novelty_authorization=NONE`.
