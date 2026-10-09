# R144 END-LINE Challenge: Could Any Method Distinction Survive?

**Access date:** 2026-09-23  
**Allowed evidence:** R140 and R142 artifacts plus only the primary/official sources cited there. No project data, protected artifacts, code execution, runner, GPU, Slurm, receipts, or flags were accessed.

## 1. Strongest surviving candidate

**Candidate:** a fail-closed *same-map frame-confusion audit*: call the producer once, freeze one source-pinned map and input pose, query that identical map with `Q_RAW` and `Q_F3`, require one uniquely passing row, and reject all ambiguous outcomes as `H2_UNIDENTIFIABLE`.

This is the strongest possible distinction left by R140 because the cited sources establish the component controls separately. R140 makes the map immutable before hypothesis selection, freezes the frame tag before reading query outcomes, and forbids selecting a convention by a smaller residual. R142 §“Precise remaining distinction” correctly describes this as an exact procedural combination.

## 2. Closest overlap and adjudication

The candidate does **not** survive as a defensible reconstruction/view-synthesis method novelty:

- COLMAP’s official `models_test.cc` (<https://github.com/colmap/colmap/blob/main/src/colmap/sensor/models_test.cc>, lines 31-89 and 145-169 cited in R142 item 10) already performs camera-to-image, image-to-camera, ray, depth-scaled, and pixel round trips with tight tolerances over many models. This subsumes the synthetic identity-test ingredient.
- PyTorch3D’s official `tests/test_cameras.py` (<https://github.com/facebookresearch/pytorch3d/blob/main/tests/test_cameras.py>, lines 307-310 and 463-521 cited in R142 item 11) combines explicit camera-frame sanity with bidirectional project/unproject recovery across OpenGL, SfM, FoV, and perspective conventions. This subsumes the multi-convention identity ingredient.
- NeRF, pixelNeRF, iMAP, and 3D Gaussian Splatting (R142 items 12-15) establish reuse of one scene representation/map for many camera queries, locked-map tracking, or held-out target views. This subsumes the same-map/query-separation ingredient.
- Nerfstudio, COLMAP, 3DGS, and DUSt3R (R142 items 1-3, 6, and 9) show that axis flips, explicit frame contracts, or canonical common frames are routine and that the producer frame may be something other than raw OpenCV or `F3`.

No cited source uses R140’s exact 2×2 table plus the literal `H2_UNIDENTIFIABLE` label, but that is an audit packaging choice. The cited overlap covers the underlying technical controls; the unobserved string/table is not evidence of a new estimator, renderer, representation, or causal mechanism. Therefore the candidate survives only as internal evaluator hygiene or a possible benchmark specification, not as a publishable method claim under the present evidence contract.

## 3. Falsifier and minimum authorized experiment

**Falsifier:** a source-pinned producer and map schema could show that the R140 protocol detects a convention ambiguity that standard camera tests and same-map query controls cannot detect, with a downstream estimand that changes under the ambiguity while all ordinary round trips pass. Conversely, if the R140 2×2 result is exactly predicted by standard project/unproject plus the producer’s declared frame tag, the candidate is only a composition of existing checks.

**Minimum authorized experiment (not authorized in this cycle):**

1. Owner signs the R140 manifest and source hashes.
2. H2 source-pins the producer call, input pose convention, output map frame tag, ID/depth schema, and depth units; unknown fields remain a hard stop.
3. A CPU-only synthetic fixture makes exactly one producer call and writes one immutable map.
4. The runner evaluates both `Q_RAW` and `Q_F3` against that same map with the fixed `N_den=24`, positive-z/bounds/ID/depth rules, and R140’s unique-pass criterion.
5. A pre-registered downstream, target-independent estimand is evaluated on held-out queries. The candidate would survive only if it changes that estimand relative to the ordinary declared-convention control, under independent review and without selecting the convention from outcomes.

Until these prerequisites exist, this experiment is a protocol proposal rather than evidence. No project scoring, protected data, GPU, Slurm, runner, receipts, or flags are needed or permitted for this decision.

## 4. Final decision and reason to keep END-LINE

**Verdict: no surviving method distinction. Keep END-LINE.** The only candidate is a fail-closed composition of known identity tests, frame-conversion contracts, and same-representation multi-query evaluation. R140’s immutable-map ordering and `H2_UNIDENTIFIABLE` stop rule improve evaluator hygiene, but the R142 overlaps leave no evidence that they constitute a new reconstruction, view-synthesis, geometry, memory, or causal method. The exact table wording is an unverified packaging difference and cannot authorize a novelty claim.

Stop before implementation or scoring if any producer API, map frame tag, output schema/units, owner sign-off, or runner registry remains `UNKNOWN`; if the same-map result lacks a unique pass/fail pattern; or if the proposed downstream estimand and held-out evidence are not pre-registered. Preserve `new_method_validated=false` and `novelty_authorization=NONE`.
