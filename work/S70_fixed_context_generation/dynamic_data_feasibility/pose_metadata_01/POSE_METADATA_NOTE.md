# Coffee Martini camera metadata: actual bounded retrieval

Recorded UTC: 2026-09-09T03:24:42.118813+00:00. Status: **PASS_POSE_METADATA_ONLY**. This is public-data preparation; no video body, image decode, model, or change to the running S70 experiment.

Recommend **training cam06 + heldout cam00** for a later bounded two-stream inspection. Before reading poses, the fixed rule was the nearest non-cam00 Euclidean camera center, with camera-ID tie breaking. cam06 is nearest at **1.0730474992699424 original scene units**, with a **7.897850045594962°** optical-axis difference. cam05 is next at1.088017850776411. The recommendation uses geometry, not compressed size or future pixel quality. Distances are in the unscaled reconstruction coordinate system, not certified meters. Geometric proximity does not certify shared visibility or a contact-free interval.

The two compressed MP4 member bodies total **130,923,253 B (124.85814380645752 MiB)**; their uncompressed files total130,909,089 B. This fits a later150 MiB download including ordinary local ZIP headers. Their headers have not yet been read, so actual compressed-body starts remain to be resolved from each local header. Both streams are raw-deflate ZIP members and require full bounded member decompression/CRC verification before MP4 inspection; no random-frame download shortcut has been established.

Actual pose read: first attempt03:22:20.315029–03:22:20.504931Z failed in TLS before any response body (0 B); its source and receipt remain intact. A fresh retry03:22:52.976508–03:22:54.954419Z returned0 in1.977920 seconds. Three exact HTTP206 ranges consumed **2,246 archive B**:30 B local fixed header,59 B filename/extra, and2,157 B compressed pose member. The local extra length is28 B, different from the central-directory24 B; it was parsed rather than assumed. Raw deflate produced exactly**2,576 B**, CRC32**52c2222a**, NPY SHA256**b82479fe530b6bf6792c718276aa69bd499a5ee777491eb5da66121c4247cf50**. NumPy1.26.4 read it once with `allow_pickle=False`: **shape[18,17], dtype<f8, 2,448 numeric B**, actual numeric read03:22:54.952806–03:22:54.953378Z. All entries are finite; rotations passed the fixed1e-6 orthogonality/determinant checks; all H/W/focal and near/far intervals are positive and ordered. No media was accessed by these checks.

## Convention and identity

The [official Neural3D dataset README](https://github.com/facebookresearch/Neural_3D_Video) identifies cam00 as heldout central reference and explicitly maps rows to **sorted existing MP4 names**; missing streams have no pose row. Its pose-format link leads to [NeRF](https://github.com/bmild/nerf/blob/master/load_llff.py) and the [official LLFF format](https://github.com/Fyusion/LLFF#using-your-own-poses-without-running-colmap). Locally pinned source lines: `../neural3d_README.md:20–25`; `nerf_load_llff.py:64–66,249–259`; `llff_README.md:222–238`; `nerf_ray_helpers.py:133–140`.

Each first15 values reshape into3×5: camera-to-world3×4 followed by[H,W,f]; last2 are scene depth bounds. Raw LLFF columns are[down,right,backwards], with viewing direction−column2. Original NeRF loader converts them to[column1,−column0,column2]=[right,up,backwards]. The JSON additionally reports explicit OpenCV optical c2w=[column1,column0,−column2,center]. Only axes are changed; centers remain the original column3. We did **not** invoke the full loader, read images, resize intrinsics, recenter poses, rescale by bounds, or spherify.

All18 rows contain **H=2028, W=2704, f=1460.7543404163334**. Under the format's documented equal-focal and centered-principal-point model, the derived pixel K is `[[1460.7543404163334,0,1352],[0,1460.7543404163334,1014],[0,0,1]]`. This is a declared format interpretation, not a separately measured distortion/principal-point calibration. Actual MP4 decoded dimensions and PTS remain unverified. Full precision raw matrices, derived optical c2w/K, bounds and checks are in `retry_01/CAMERAS.json`.

| Row | Camera | Center x,y,z (original scene units; display rounded) | Near | Far | Distance to cam00 | Optical-axis angle° |
|---:|---|---|---:|---:|---:|---:|
| 0 | cam00 | 0.443965, -1.103503, -0.349927 | 8.831384 | 109.775424 | 0.000000 | 0.000000 |
| 1 | cam01 | 5.519666, -0.987788, 0.610935 | 6.844494 | 113.355765 | 5.167145 | 34.874425 |
| 2 | cam02 | 4.681453, -1.026767, 0.076041 | 7.044561 | 117.805395 | 4.259536 | 28.031666 |
| 3 | cam04 | 2.615963, -1.051985, -0.649421 | 8.473499 | 112.334439 | 2.193155 | 13.187145 |
| 4 | cam05 | 1.521655, -1.079743, -0.497580 | 5.788118 | 113.639925 | 1.088018 | 7.571712 |
| 5 | cam06 | -0.622808, -1.126392, -0.236332 | 5.953714 | 109.632696 | 1.073047 | 7.897850 |
| 6 | cam07 | -1.692721, -1.133587, -0.109216 | 8.998587 | 103.890174 | 2.150412 | 14.628911 |
| 7 | cam08 | -2.764425, -1.161238, 0.008712 | 8.588033 | 97.654613 | 3.228888 | 20.966023 |
| 8 | cam09 | -3.538101, -1.135143, 1.031229 | 7.656341 | 80.869010 | 4.214907 | 28.112327 |
| 9 | cam10 | -4.185562, -1.157087, 1.743770 | 9.003959 | 65.701400 | 5.081236 | 34.589741 |
| 10 | cam11 | 6.190375, 1.804186, 0.120410 | 6.434862 | 117.687679 | 6.457329 | 14.714602 |
| 11 | cam12 | 5.207584, 1.768597, -0.020612 | 7.320015 | 344.327584 | 5.572205 | 6.981418 |
| 12 | cam13 | 3.243560, 1.719795, -0.671582 | 8.198190 | 111.089532 | 3.989012 | 17.278216 |
| 13 | cam14 | 1.976148, 1.684714, -0.572871 | 8.245131 | 111.354506 | 3.189271 | 11.184940 |
| 14 | cam16 | -0.210154, 1.649269, -0.331662 | 7.654980 | 111.783291 | 2.829481 | 3.506431 |
| 15 | cam18 | -2.455518, 1.596160, -0.093848 | 6.852220 | 99.816194 | 3.969982 | 17.229842 |
| 16 | cam19 | -4.221041, 1.575957, 1.014144 | 6.715722 | 316.139293 | 5.549997 | 18.568924 |
| 17 | cam20 | -5.084449, 1.576100, 1.512379 | 6.022324 | 100.796403 | 6.419643 | 24.704668 |

Minimum next observation, if root proceeds: fetch only cam00/cam06 with their actual local headers, exact compressed lengths and CRCs, then inspect stream metadata/frame PTS before any explicitly scoped frame decode. Confirm common physical times and visible dynamic object support from observed images. Future frames remain scoring answers, never conditioning; annotations would be extra information unless given equally. Calibration alone does not establish a valid state-sufficiency experiment or a model result.
