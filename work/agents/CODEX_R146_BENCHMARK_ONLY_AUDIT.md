# R146 Benchmark-Only Audit of the R140 QA Contract

**Access date:** 2026-09-23  
**Evidence boundary:** R140, R142, R144, and only the primary/official sources cited in R142. No protected data, code execution, runner, GPU, Slurm, receipts, or flags were accessed.

## Classification

**Current verdict: reject as a benchmark paper contribution; retain as internal QA.** R140 is a well-specified synthetic identity fixture and fail-closed diagnostic, but it currently has one fixture, one proposed producer call, unknown producer output semantics, no executed benchmark results, no baseline matrix, no held-out benchmark split, and no independent downstream estimand. Those are prerequisites for a benchmark paper, not optional packaging.

A future benchmark could use R140 as a seed for a *camera-frame contract and producer-map ambiguity benchmark*, but that is a new construction project. It cannot be claimed from the current QA contract alone.

## 1. Benchmark gap that is defensible

The narrow defensible gap is **cross-pipeline frame-contract evaluation with one immutable producer map and pre-registered query conventions**. Existing cited sources cover the ingredients but not this benchmark framing:

- COLMAP `models_test.cc` and PyTorch3D `tests/test_cameras.py` provide maintained camera identity, projection/unprojection, and multi-convention tests (R142 items 10-11), but test declared camera implementations rather than a producer whose output frame is an unknown variable.
- Nerfstudio, COLMAP, 3DGS, and DUSt3R document or implement axis flips, explicit frame contracts, or learned common frames (R142 items 1-3, 6, 9), but do not supply a common benchmark that scores producer-map frame declarations against competing queries.
- NeRF, pixelNeRF, iMAP, and 3D Gaussian Splatting reuse a scene representation/map for many or held-out camera queries (R142 items 12-15), but do not benchmark raw-versus-`F3` query confusion with a fail-closed ambiguity label.

This is an evaluation gap only if the benchmark measures a reproducible, cross-system property. The absence of the exact R140 2x2 table or `H2_UNIDENTIFIABLE` string is not itself a research gap.

## 2. Construction and evaluation requirements

To become an independent benchmark, the protocol would need all of the following:

1. **Task definition:** a fixed estimand such as frame-contract identification accuracy, ambiguity-detection rate, and false-certification rate under known raw, transformed, and canonical producer frames.
2. **Fixture suite:** multiple synthetic geometries, camera poses, intrinsics, depths, image sizes, pixel-center conventions, and controlled perturbations. The 24-point R140 fixture is one seed, not a benchmark distribution.
3. **Ground-truth registry:** source-pinned producer input pose, true output frame tag, depth units, ID/depth schema, rounding, z-buffer, and immutable map hash for every case. Unknown fields must be excluded or scored as unresolved.
4. **System matrix:** multiple independently maintained producers/renderers and declared camera conventions, including at least raw OpenCV, OpenGL/Blender `F3`, and a canonical-frame case such as the DUSt3R evidence cited in R142.
5. **Controls and baselines:** ordinary producer-declared-convention checks, COLMAP/PyTorch3D-style round trips, an unconstrained residual-minimization rule, and the R140 immutable-map 2x2 rule. Baselines must be frozen before outcomes are read.
6. **Metrics:** fixed-denominator ID/depth accuracy, positive-z and in-bounds rates, ambiguity-rejection rate, false unique-pass rate, and confidence intervals across fixtures and systems. A lower residual alone cannot select a convention.
7. **Splits and leakage control:** held-out geometry/poses and a hidden convention-label split. The map must be generated once per case and reused for all query cells; no branch-specific map regeneration or outcome-based frame relabeling.
8. **Reproducibility and review:** versioned manifests, source hashes, independent reruns, negative controls, and an adjudication rule for undocumented producer frames. A benchmark paper also needs a public, inspectable artifact and an independent review protocol.

R140 currently supplies only parts of items 2, 3, 5, and 7, and explicitly marks producer API, frame tag, output schema/units, owner, and runner prerequisites as `UNKNOWN`.

## 3. Closest benchmark overlaps and remaining distinction

The closest overlaps are the maintained identity suites in COLMAP/PyTorch3D and the held-out multi-view evaluation practice in NeRF/pixelNeRF/3DGS. Those sources show that round-trip correctness and one-representation/many-query evaluation are established benchmark primitives. R140’s remaining distinction is the composition of those primitives into a source-pinned, same-map raw/F3 confusion table with fail-closed ambiguity rejection.

That composition could be a benchmark *design choice*, but it is not yet a benchmark result. Without multiple systems, hidden labels, independent estimands, and measured failure rates, it remains a project-specific QA contract.

## 4. Minimum valid benchmark experiment

The minimum authorized benchmark study would be:

- at least three independently maintained producer/renderer paths drawn from the cited convention families;
- a preregistered suite containing multiple held-out synthetic geometries and poses, with raw, transformed, and canonical-frame labels hidden from the scoring rule;
- exactly one immutable map per case and the full R140 2x2 query table for every system;
- COLMAP/PyTorch3D round-trip baselines and an outcome-selected residual baseline;
- reported frame-identification accuracy, false unique-pass rate, correct `H2_UNIDENTIFIABLE` rate, depth/ID error, and confidence intervals over cases;
- an independent rerun by a separate reviewer using only the published manifests and source hashes.

The benchmark claim would be valid only if R140’s rule improves ambiguity detection or prevents false certification on held-out systems/geometries while preserving accuracy on known contracts. A single producer, a single fixture, or a successful identity check cannot establish this claim.

## 5. Explicit rejection if treated as internal QA

If the scope remains one project producer, one 24-point fixture, one manually inspected map, or unknown producer frame/schema semantics, **reject the benchmark-paper claim**. In that state R140 is valuable evaluator hygiene: it can stop an invalid score and preserve `H2_UNIDENTIFIABLE`, but it does not define a general benchmark or demonstrate cross-system findings. Keep `new_method_validated=false` and `novelty_authorization=NONE`; do not implement or score until the construction and evaluation gates above are source-pinned and preregistered.
