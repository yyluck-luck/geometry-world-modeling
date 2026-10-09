# R142 Prior-Art Audit: Frame Conventions and Same-Map Checks

**Access date:** 2026-09-23  
**Search scope:** English primary papers and official implementations/documentation only. No project C8/evaluation data, protected artifacts, code execution, GPU, Slurm, runner, receipts, or flags were accessed.

## Executive verdict

**No defensible method novelty remains. Recommend END-LINE for a research/innovation claim.** R140 is a useful fail-closed evaluator-hygiene protocol, but its ingredients are established independently: explicit camera-axis conversion, project/unproject round trips, fixed pixel/depth conventions, and forward/backward reprojection consistency. The bounded search did not find the exact R140 2×2 table wording, but that absence is not evidence of novelty. Keep it as a source-pinned QA contract only, with `new_method_validated=false` and `novelty_authorization=NONE`.

## Closest primary overlaps

All sources below were inspected on 2026-09-23.

1. **COLMAP, “Camera Models” (official documentation).**  
   URL: <https://github.com/colmap/colmap/blob/main/doc/cameras.rst>  
   Evidence: lines 204-223 define positive-Z camera coordinates, perspective division, intrinsics, inverse pixel-to-ray mapping, and a corner-based pixel convention.  
   Overlap: R140’s fixed projection, positive-Z gate, intrinsics, and rounding/coordinate contract.  
   Difference: COLMAP does not propose a producer-frame hypothesis table or same-map raw/F3 branch audit.

2. **Nerfstudio, “Data conventions” (official documentation).**  
   URL: <https://github.com/nerfstudio-project/nerfstudio/blob/main/docs/quickstart/data_conventions.md>  
   Evidence: lines 199-207 explicitly distinguish OpenGL/Blender from COLMAP/OpenCV and state that Y/Z are flipped; they also fix pixel-center semantics.  
   Overlap: R140’s `F3=diag(1,-1,-1)` convention registry and pixel-rule freeze.  
   Difference: this is a documented format conversion, not a same-map ambiguity test or fail-closed H2 decision.

3. **Nerfstudio, `colmap_dataparser.py` (official implementation).**  
   URL: <https://github.com/nerfstudio-project/nerfstudio/blob/main/nerfstudio/data/dataparsers/colmap_dataparser.py>  
   Evidence: lines 1873-1885 invert COLMAP `w2c` to `c2w` and multiply rotation columns 1:3 by `-1` to convert OpenCV to OpenGL.  
   Overlap: an exact implementation pattern for the Y/Z flip that R140 tests.  
   Difference: the conversion is selected by the parser contract; there is no immutable-map cross-query confusion table.

4. **PyTorch3D, `CamerasBase` (official implementation).**  
   URL: <https://github.com/facebookresearch/pytorch3d/blob/main/pytorch3d/renderer/cameras.py>  
   Evidence: lines 2234-2245 enumerate world/view/NDC/screen spaces; lines 2367-2400 construct world-to-view, project, append depth, unproject, and assert `torch.allclose` for world and camera round trips.  
   Overlap: R140’s bidirectional camera identity and project/unproject acceptance logic.  
   Difference: the standard test assumes one declared camera convention; it does not compare raw versus F3 queries against one producer map.

5. **Google Nerfies, `camera.py` (official implementation).**  
   URL: <https://github.com/google/nerfies/blob/main/nerfies/camera.py>  
   Evidence: lines 1475-1509 back-project pixels and depth to world/local points; lines 1496-1545 project local points back to pixels; lines 1547-1554 define pixel centers.  
   Overlap: R140’s back-projection, projection, and pixel-center controls.  
   Difference: no producer frame tag, frozen map, or branch discrimination.

6. **Graphdeco/Inria 3D Gaussian Splatting, `scene/dataset_readers.py` (official implementation).**  
   URL: <https://github.com/graphdeco-inria/gaussian-splatting/blob/main/scene/dataset_readers.py>  
   Evidence: lines 1204-1217 treat NeRF transforms as c2w, flip Y/Z from OpenGL/Blender to COLMAP, invert to `w2c`, and pass `R,T` to the renderer.  
   Overlap: explicit producer/renderer convention boundary and the same axis flip family.  
   Difference: no cross-query ambiguity protocol; the transform is assumed by the data reader.

7. **Xu & Tao, “Multi-Scale Geometric Consistency Guided Multi-View Stereo,” CVPR 2019 (primary paper).**  
   URL: <https://arxiv.org/abs/1904.08103>  
   Evidence: the paper defines reprojection-error consistency (Eq. 8, arXiv page lines 101-103) and converts each depth map to world points before projecting into neighboring views (lines 125-126).  
   Overlap: R140’s fixed depth/reprojection checks and bidirectional geometric consistency.  
   Difference: this is an MVS estimator/consistency cost, not a producer-frame identity audit with a fixed map and competing sign queries.

8. **Vats et al., “GC-MVSNet: Multi-View, Multi-Scale, Geometrically-Consistent Multi-View Stereo,” primary paper.**  
   URL: <https://arxiv.org/abs/2310.19583>  
   Evidence: lines 60-67 and 70-80 describe forward-backward reprojection of one reference depth through multiple source views, with per-pixel inconsistency masks and camera parameters.  
   Overlap: R140’s same geometry/depth consistency and fixed pass/fail mask.  
   Difference: it evaluates depth consistency across views; it does not hold one producer map fixed while testing raw versus F3 query conventions.

9. **Wang et al., “DUSt3R: Geometric 3D Vision Made Easy,” CVPR 2024 (primary paper and official code).**  
   Paper: <https://arxiv.org/abs/2312.14132>  Repo: <https://github.com/naver/dust3r>  
   Evidence: the paper states that pairwise pointmaps share the coordinate frame of the first image (lines 72-82), and that global alignment expresses reconstructions in a common frame (lines 232-236).  
   Overlap: explicit pointmap frame identity and immutable common-frame reasoning.  
   Difference: DUSt3R relaxes fixed projective-camera assumptions and recovers cameras from pointmaps; it does not define R140’s raw/F3 same-map confusion table.

10. **COLMAP, `models_test.cc` (official camera-model test suite).**  
    URL: <https://github.com/colmap/colmap/blob/main/src/colmap/sensor/models_test.cc> (raw source inspected: <https://raw.githubusercontent.com/colmap/colmap/main/src/colmap/sensor/models_test.cc>)  
    Evidence: lines 31-49 (`TestCamToCamFromImg`) project a camera point to an image and invert it with `EXPECT_NEAR(..., 1e-6)`; lines 51-69 (`TestCamFromImgToImg`) round-trip pixels through camera coordinates at depths 0.5, 1.0, and 2.0; lines 71-89 (`TestCamRayFromImgToImg`) require unit-ray norm `1e-12` and pixel recovery `1e-6`; lines 145-169 run these checks over camera models and pixels.  
    Overlap: this is an exact, maintained camera-frame identity/round-trip test, stronger than R140’s generic project/unproject requirement.  
    Difference: COLMAP tests one declared camera model rather than producer-map raw/F3 branch confusion; that difference is packaging, not a new identity method.

11. **PyTorch3D, `tests/test_cameras.py` (official camera tests).**  
    URL: <https://github.com/facebookresearch/pytorch3d/blob/main/tests/test_cameras.py> (raw source inspected: <https://raw.githubusercontent.com/facebookresearch/pytorch3d/main/tests/test_cameras.py>)  
    Evidence: lines 307-310 set a camera at `[0,0,-1]` (“camera pointing along negative z”) and assert an identity look-at rotation with tolerance `2e-7`; lines 463-521 project random 3-D points, unproject with world/camera options across OpenGL, SfM, FoV, and perspective camera families, and assert `torch.allclose(..., atol=1e-4)`.  
    Overlap: direct synthetic frame sanity and bidirectional project/unproject recovery.  
    Difference: tests are parameterized by a selected camera class and do not freeze one producer map while competing raw/F3 queries are compared.

12. **Mildenhall et al., “NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis,” ECCV 2020 (primary paper).**  
    URL: <https://arxiv.org/abs/2003.08934> (English HTML inspected: <https://ar5iv.labs.arxiv.org/html/2003.08934>)  
    Evidence: lines 5-7 describe a single optimized continuous scene function queried along camera rays; lines 17-22 describe rendering arbitrary viewpoints from the learned representation; lines 110-117 report held-out test views.  
    Overlap: one fixed scene representation is queried by many camera poses and evaluated on held-out views.  
    Difference: NeRF is a view-synthesis method, not a frame-convention ambiguity audit; same-map query reuse is foundational prior art.

13. **Yu et al., “pixelNeRF: Neural Radiance Fields from One or Few Images,” CVPR 2021 (primary paper and official project).**  
    Paper: <https://arxiv.org/abs/2012.02190>  Project: <https://alexyu.net/pixelnerf>  
    Evidence: English HTML lines 5-7 condition one scene representation on one/few images and synthesize novel views; lines 15-19 define query points/view directions and explicitly state that the predicted representation is in the input-image camera coordinate system rather than a canonical frame.  
    Overlap: one representation is reused for multiple target queries while the frame contract is explicit.  
    Difference: pixelNeRF chooses a camera-coordinate contract; it does not test two conventions against one frozen map. Its explicit view-space choice also contradicts treating raw/F3 as the only plausible producer frames.

14. **Sucar et al., “iMAP: Implicit Mapping and Positioning in Real-Time,” ICCV 2021 (primary paper).**  
    URL: <https://arxiv.org/abs/2103.12352> (English HTML inspected: <https://ar5iv.labs.arxiv.org/html/2103.12352>)  
    Evidence: lines 15-16 align live RGB-D observations to rendered predictions from one MLP scene map; lines 52-54 state that a camera pose renders color/depth and that tracking optimizes pose against a locked network while mapping updates it.  
    Overlap: explicit locked-map versus query-pose separation, which is the causal control R140 requires.  
    Difference: iMAP uses the lock for tracking stability, not for a raw/F3 confusion table or an H2 stop rule.

15. **Kerbl et al., “3D Gaussian Splatting for Real-Time Radiance Field Rendering,” TOG/SIGGRAPH 2023 (primary paper and official repository).**  
    Paper: <https://arxiv.org/abs/2308.04079>  Repo: <https://github.com/graphdeco-inria/gaussian-splatting>  
    Evidence: English HTML lines 21-24 define one optimized 3-D Gaussian scene representation and a renderer; lines 162-163 compare against ground truth from held-out test views; lines 207-219 state that every eighth photo is held out and that left-out views and distant paths are rendered from the trained representation.  
    Overlap: one immutable trained map is queried on held-out camera views.  
    Difference: held-out rendering validates reconstruction quality, not producer-frame identity; same-map cross-query reuse is standard contemporary practice.

## Precise remaining distinction

R140’s only remaining distinction is procedural and narrow: **one producer output is frozen before hypothesis selection, its input pose and frame tag are pre-registered, and both raw and `F3` queries are evaluated against that identical map with fail-closed `H2_UNIDENTIFIABLE` handling.** The surveyed sources provide the ingredients separately, but no inspected source claims this exact audit packaging. That is a QA/integration distinction, not a new reconstruction, view-synthesis, or memory mechanism. It cannot support a paper novelty claim without an independent downstream estimand and held-out evidence.

## Contradictory evidence and scope limits

- DUSt3R’s canonical pointmaps/common-frame alignment shows that a producer may emit a learned canonical frame rather than either raw OpenCV or `F3`-flipped metric camera coordinates. Therefore R140’s two query branches are incomplete until the producer frame tag is source-pinned; otherwise the correct result is `H2_UNIDENTIFIABLE`.
- Nerfstudio, COLMAP, 3DGS, Nerfies, and PyTorch3D show that axis conversion, pixel conventions, and round-trip projection checks are routine engineering contracts. Calling the `F3` flip or the identity test itself novel is contradicted by these implementations.
- MVS papers already use fixed denominators/thresholds and forward-backward reprojection consistency. R140 cannot claim those checks as a new geometric method.
- The search did not find a paper using R140’s exact 2×2 table. This is a bounded-search observation only; it is not evidence that the protocol is publishably novel.

## Falsifiable implication

If R140 is only a convention audit, then a standard PyTorch3D-style project/unproject round trip plus an MVS-style forward/backward reprojection applied to the **same immutable map** must produce the same raw-versus-`F3` pass/fail cell as R140. If a future implementation produces a different cell, the discrepancy falsifies the protocol implementation or the pre-registered frame tag (most likely units, pixel centers, or an undocumented canonical transform); it cannot be presented as a method gain.

## Decision and stop rule

Retain R140 only as internal evaluator hygiene. Recommend **END-LINE** for novelty/innovation framing. Do not implement or score until the producer API, output frame tag, depth units, and map schema are source-pinned; otherwise stop at `H2_UNIDENTIFIABLE`, preserve `new_method_validated=false`, and preserve `novelty_authorization=NONE`.
