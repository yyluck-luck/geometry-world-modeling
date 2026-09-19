# 3DMatch RGB-D Scenes v2 scene13 adapter evidence

Recorded 2026-09-16 (Asia/Shanghai). This note is scoped to the **development adapter** and the one previously exposed `seq-01/frame-000000` qualification frame. It does not qualify scene14, held-out windows, a VMem forward, or a method.

## Primary source facts

- The converted RGB-D Scenes v2 README states that each pose is an RGB-D Mapping estimate, gives quaternion plus global position, and places the first frame at the global origin (`sources/rgbd_scenes_v2_README.txt`, lines 5–16).
- The 3DMatch project page's dataset-format section states: `frame-XXXXXX.color.png` is 24-bit RGB; `frame-XXXXXX.depth.png` is 16-bit, aligned, millimetres, invalid=0; and `frame-XXXXXX.pose.txt` is a 4×4 camera-to-world matrix in metres. The same page says `camera-intrinsics.txt` is a 3×3 depth-camera matrix. The downloaded HTML is retained in `sources/3dmatch_project.html`.
- The pinned 3DMatch source snapshot is GitHub repository `andyzeng/3dmatch-toolbox`, commit `4c6b2f613adb8bdcc9a62cb04134b7e1379b1a36` (see `sources/SOURCE_MANIFEST.json`). Its `depth-fusion/utils.hpp` divides the 16-bit depth by 1000 and optionally suppresses values over 6 m. The adapter preserves raw zeros and does **not** impose that optional 6 m fusion truncation as a measurement rule.
- `training/match.hpp` unprojects pixels as `(pix+0.5-c)*z/f` and projects with `round(f*x/z+c-0.5)`. The pinned VMem `utils/util.py` uses pixel grids `arange+0.5`. These two sources support the adapter's explicit half-pixel centre convention.
- The same 3DMatch snapshot's `depth-fusion/demo.cu` indexes a raster with integer `round(...)` coordinates. This is a separate rasterisation convention. The adapter records this discrepancy instead of silently presenting one convention as a universal sensor truth.

## Adapter decisions

1. **Pixel centres:** use `u+0.5,v+0.5` for unprojection and continuous projection. This is frozen as a development compatibility choice because it agrees with the training source and VMem's ray grid. It is not a claim that the converted dataset documents a unique physical pixel-centre convention.
2. **Metric depth:** `z_m = uint16_raw / 1000`, valid iff `raw != 0`; no filling, clipping, six-metre suppression, or interpolation is applied to native depth. A separate nearest-cell adapter is provided for any later explicitly frozen resized-depth contract.
3. **Pose:** parse the converted 4×4 matrix as camera-to-world in metres. Keep frame order as identity; do not infer hardware timestamps. The `optical_c2w_to_vmem_input` helper gives the original VMem input-axis conversion separately and never relabels the metric pose.
4. **VMem image/K preprocessing:** match pinned `transform_img_and_K(..., size=(576,576), mode="crop")`: native 640×480 → area-resized 768×576 → crop left 96/top 0. K is scaled by 1.2 and shifted by that crop, yielding `[[648.0254784,0,288],[0,648.0254784,288],[0,0,1]]` for the observed scene13 K.
5. **Roles:** the qualification manifest contains only `camera-intrinsics.txt` and frame000000 RGB/depth/pose. The general loader requires explicit role/hash bindings and rejects future roles, archive paths, symlinks, and traversal. Runtime isolation still belongs to the Gate0 container/namespace/ACL layer; this Python guard is not a sandbox.

## Real qualification output

`QUALIFICATION_RESULT.json` is `PASS_QUALIFICATION_ONLY`. It reports native 640×480 RGB/depth, depth zero count 61,908, positive count 245,292, positive raw minimum 507, raw maximum 2,767, exact projection round-trip maximum error `1.1368683772161603e-13` px over 128 deterministic valid pixels, the VMem crop/K result, and successful denied-role/path tests. The run used `.venv-cut3r/bin/python`; no model was constructed and no GPU job was submitted.

The result is a software/data-contract qualification record. It must not be copied into a Gate0 PASS field without completing source-specific adapter review, staged history-window isolation, future-output seal order, independent scene/held-out contract, and independent pre-run review.
