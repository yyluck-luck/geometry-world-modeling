# Dataset verification for geometry-aware memory selection (real-captured sets)

**Accessibility legend:** ✅ = I confirmed an actual byte transfer (HTTP 200/206 on a data file). 🟡 = the official page(s) returned HTTP 200 and describe a download path, but I did not byte-confirm a data file. ❌ = no working path confirmed.

**Method note (TUM only):** `web_fetch` returned HTTP 200 for all three TUM RGB-D pages, but its output was swallowed by the site's very large DokuWiki navigation and truncated before the article body. I therefore extracted the article text from the **same official URLs** by direct retrieval. No `*.ezproxy.*` or mirror host was used anywhere in this report. Everything else below is from `web_fetch` (HTTP status noted) or from a direct header/range check on the cited official URL.

---

## 1. TUM RGB-D benchmark

Evidence: [main](https://cvg.cit.tum.de/data/datasets/rgbd-dataset) · [download](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/download) · [file formats](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats) · [changelog](http://www.scan-net.org/changelog) (not used) — all three TUM pages HTTP 200.

- **Year:** Sturm et al., IROS 2012 (citation block on main page). Device = **Microsoft Kinect**, "recorded at full frame rate (30 Hz) and sensor resolution (640x480)".
- **Size:** 89 downloadable sequence archives listed; the published `tgz (X.XXGB)` values sum to **≈ 88.55 GB** (fr1 14.3 + fr2 47.8 + fr3 26.5). Smallest sequence archives: `fr3/nostructure_texture_far` **0.20 GB**, `fr3/nostructure_notexture_far` **0.21 GB**. No aggregate size is stated by the site — the 88.55 GB is my sum of the published per-file values.
- **License (exact):** *"Unless stated otherwise, all data in the TUM RGB-D benchmark is licensed under a Creative Commons 4.0 Attribution License (CC BY 4.0) and the accompanying source code is licensed under a BSD-2-Clause License."* **No registration or agreement gate.**
- **RGB + depth, 1:1 pairing — YES, explicitly:** *"The color and depth images are already pre-registered using the OpenNI driver from PrimeSense, i.e., the pixels in the color and depth images correspond already 1:1."* Also: *"the depth images in our datasets are reprojected into the frame of the color camera, which means that there is a 1:1 correspondence between pixels in the depth map and the color image."*
- **Depth units/scaling — documented:** 640×480 **16-bit** PNG, *"The depth images are scaled by a factor of 5000, i.e., a pixel value of 5000 in the depth image corresponds to a distance of 1 meter... A pixel value of 0 means missing value/no data."* ROS bags store 32-bit float with `factor = 1`. Depth was pre-scaled for a constant Kinect bias `ds` (fr1 1.035, fr2 1.031, fr3 1.000).
- **Intrinsics K — YES:** per-camera RGB tables (fr1 517.3/516.5/318.6/255.3; fr2 520.9/521.0/325.1/249.7; fr3 535.4/539.2/320.1/247.6) plus IR tables and distortion `d0–d4`, plus ROS-default 525.0/525.0/319.5/239.5. Note fr3 color+IR are already undistorted (d=0).
- **Poses — motion-capture GT:** *"The ground-truth trajectory was obtained from a high-accuracy motion-capture system with eight high-speed tracking cameras (100 Hz)."* GT line format `timestamp tx ty tz qx qy qz qw`, *"timestamp (float) gives the number of seconds since the Unix epoch."*
- **TIMESTAMPS — REAL.** Every image filename is a timestamp and the GT file's first column is Unix-epoch time (quoted above). **There are no synthetic/rendered sequences in this benchmark** — every listed sequence is a real Kinect recording. The only non-SLAM groups are *Validation Files* (no public GT) and *Calibration Files*.
- **Checksums — NOT published.** No `md5`/`sha`/`checksum` string appears anywhere on the main, download, or file-formats pages (zero matches).
- **Sequence groups (all 8, verbatim):** Testing and Debugging; Handheld SLAM; Robot SLAM; Structure vs. Texture; Dynamic Objects; 3D Object Reconstruction; **Validation Files (without public ground truth)**; Calibration Files. Counts: 47 with public GT, 25 `*_validation`, 9 calibration.
- **Held-out / "unseen" — YES:** the 25 `*_validation` sequences. *"The \*_validation sequences do not contain ground truth. They can only evaluated using the online tool."* (sic). This is genuine label isolation: RGB-D ships, GT does not.
- **Leave-and-return / loop closure — YES, documented:** intro says the `desk` dataset *"covers four tables and contains several loop closures"*; sequence names include `fr2/large_with_loop`, `fr3/nostructure_notexture_near_withloop`, `fr3/nostructure_texture_near_withloop`; `fr1/360` and `fr2/360_*` are full rotations.
- **⚠ PER-SEQUENCE GT-COVERAGE TRAP (the Bonn failure mode).** The download page publishes both `Duration` and `Duration with ground-truth`; for several sequences mocap GT covers only part of the recording:

| sequence | duration | with GT | unfilled |
|---|---|---|---|
| fr2/large_with_loop | 173.19 s | 40.54 s | **−132.65 s** |
| fr2/large_no_loop | 112.37 s | 21.37 s | **−91.00 s** |
| fr2/ir_calibration | 65.02 s | 21.36 s | −43.66 s |
| fr2/desk | 99.36 s | 69.15 s | −30.21 s |
| fr2/desk_with_person | 142.08 s | 119.37 s | −22.71 s |
| fr2/pioneer_slam | 155.72 s | 145.86 s | −9.86 s |
| fr2/pioneer_slam3 | 111.91 s | 105.04 s | −6.87 s |
| fr2/pioneer_slam2 | 115.63 s | 109.49 s | −6.14 s |
| fr1/floor | 49.87 s | 44.27 s | −5.60 s |

  All `fr3/*` and most `fr1/*` sequences match to ≤ 0.09 s (full GT coverage). **Per-sequence GT-coverage auditing is mandatory for TUM too**, exactly as for Bonn.
- **Download:** per-sequence `tgz` from the download page (e.g. `fr1/xyz` 0.47 GB) plus ROS bags. Status: 🟡 — the page and links are present and HTTP 200, but I did not stream a `.tgz` byte, so the file link itself is not byte-confirmed.
- **162 GB fit:** the whole published archive set ≈ 88.6 GB → fits with room for extraction of a subset.

---

## 2. ScanNet (v1/v2)

Evidence: [scan-net.org/ScanNet](http://www.scan-net.org/ScanNet/) (200) · [GitHub README](https://raw.githubusercontent.com/ScanNet/ScanNet/master/README.md) (200) · [SensReader `SensorData.py`](https://raw.githubusercontent.com/ScanNet/ScanNet/master/SensReader/python/SensorData.py) (200) · [download-scannet.py](http://kaldir.vc.in.tum.de/scannet/download-scannet.py) (200, 13,071 B) · [changelog](http://www.scan-net.org/changelog) (200) · [ScanNet_TOS.pdf](https://kaldir.vc.in.tum.de/scannet/ScanNet_TOS.pdf) (200, 17,893 B — PDF; `web_fetch` rejects `application/pdf`, so I confirmed existence/size by direct retrieval and did **not** read its clauses → **terms content UNVERIFIED**).

- **Year:** CVPR 2017; **v2 released 2018-06-11** (changelog).
- **Size:** **1.2 TB** — `RELEASE_SIZE = '1.2TB'` in the official download script. Scale: *"2.5 million views in more than 1500 scans"*; `v2/scans.txt` = **1,513 scans** (counted), `v2/scans_test.txt` = **100 test scans** (counted). Dev subset: per-scan download (`--type .sens`) and `scannet_frames_25k.zip` (labelled `5.6GB`), `scannet_frames_test.zip` (labelled `610MB`), `DATA_EFFICIENT_FILES` labelled `1.7MB`.
- **License (exact):** *"The data is released under the ScanNet Terms of Use, and the code is released under the MIT license."* Download requires **filling out the agreement and emailing it from an institutional address** to `scannet@googlegroups.com`. So: agreement-gated by stated terms (even though some file paths are reachable anonymously — see below).
- **RGB + depth:** real Structure.io RGB-D; `.sens` = *"Compressed binary format with per-frame color, depth, camera pose and other data."*
- **TIMESTAMPS — REAL, per frame, and in the file format:** `RGBDFrame.load()` reads `timestamp_color` and `timestamp_depth` as **uint64** for every frame. **Units are not documented** (µs assumed, unverified) → timestamp *existence* is verified; epoch/unit is **UNVERIFIED**.
- **Depth units/scaling:** the `.sens` header carries a float **`depth_shift`** field (consumed by exporters as the divisor). The **exact convention/units are not documented on the pages I fetched → UNVERIFIED.**
- **Intrinsics K — YES:** `.sens` header stores `intrinsic_color`, `extrinsic_color`, `intrinsic_depth`, `extrinsic_depth` as 4×4 float32; the reader can export all four.
- **Poses — reconstruction-derived, NOT mocap:** per-frame `camera_to_world` 4×4 in `.sens`; README states poses come from the BundleFusion reconstruction pipeline. There is no motion-capture GT.
- **Checksums:** none published → **UNVERIFIED**.
- **Held-out:** **YES — 100 test scans** (`v2/scans_test.txt` counted). Changelog: *"100 new scans are now part of the evaluation test set!"* The official script downloads test scans with `FILETYPES_TEST = ['.sens', '.txt', '_vh_clean.ply', '_vh_clean_2.ply']` — i.e. **no annotation files for test scans**, which is exactly the kind of GT isolation the gate wants.
- **Leave-and-return:** not labelled as such; BundleFusion scans are natural handheld re-visiting loops. **Not documented / UNVERIFIED.**
- **Download:** `http://kaldir.vc.cit.tum.de/scannet/` via `download-scannet.py`. Byte-confirmed ✅:
  - `v2/scans.txt` → 200 (19,669 B); `v2/scans_test.txt` → 200 (1,300 B)
  - **`.sens` is served from the v1 path** — the script defaults to `use_v1_sens=True`; probe `v1/scans/scene0000_00/scene0000_00.sens` → **206**
  - `v2/scans/scene0000_00/scene0000_00_vh_clean_2.ply` → 206; `.aggregation.json` → 206
  - `v2/tasks/scannet_frames_25k.zip` → 200 (474,497,024 B)
  - ⚠ `v2/scans/<id>/<id>.sens` and `v2/.../<id>.txt` return **404** for the ids I probed → use the v1 path for `.sens`.

---

## 3. ScanNet++

Evidence: [official site](https://scannetpp.mlsg.cit.tum.de/scannetpp/) (200; canonical `kaldir.vc.in.tum.de/scannetpp/` 302s here) · [documentation](https://scannetpp.mlsg.cit.tum.de/scannetpp/documentation) (200) · [toolkit README](https://raw.githubusercontent.com/scannetpp/scannetpp/main/README.md) (200). Note: `kaldir.vc.in.tum.de/scannetpp/` responded **HTTP 200** in a curl probe while `web_fetch` refused the cross-origin redirect, and the bare host `scannetpp.mlsg.cit.tum.de/` serves an nginx welcome page — the live site is the `/scannetpp/` path.

- **Year:** ICCV 2023 Oral; **v2 released 2024-12-20** with *"1000+ scenes"*; docs say **1,006 scenes**.
- **Size (published table, exact):** default download (low-res DSLR + iPhone + meshes + semantics) **1.5 TB**; DSLR (2 MP) 371 GB; DSLR 2MP+33MP 9 TB; meshes+semantics 132 GB; point clouds 720 GB; panocam 319 GB. Smallest documented test subset: `nvs_test_small.txt` = **12 scenes** (subset of the 50-scene `nvs_test.txt`), *"no scan data"*.
- **License (exact):** *"The ScanNet++ data is released under the ScanNet++ Terms of Use, which you can agree to after signing up."* Gating = **create account → login → create application → approval → personalised download token** (tokens can expire; re-download the script from the dashboard). Strongest gate of the ten.
- **Capture devices:** sub-millimetre **laser scanners**, **33 MP DSLR** (fisheye), **iPhone** commodity RGB-D, plus **360° panocam** (released 2025-10-30 for 956 scenes).
- **RGB + depth:** ✅ real sensor depth from the **iPhone LiDAR**: `depth.bin` = *"16 bit png in millimeters"*, aligned to RGB (1920×1440 RGB / 256×192 depth); `rgb.mkv` 60 FPS. **DSLR depth is rendered from the mesh** (not sensor): *"The rendered depth maps are single-channel uint16 png, where the unit is mm and 0 means invalid depth."* Panocam depth also mm 16-bit.
- **Depth units — documented:** millimetres (iPhone, panocam, rendered DSLR); *"There are no intrinsics for Lidar depth provided by the iPhone. The user can scale the RGB intrinsic for the Lidar depth map since RGB and depth are aligned."*
- **Intrinsics K — YES:** `pose_intrinsic_imu.json → json["intrinsic"]` = 3×3 RGB intrinsic; DSLR `colmap/cameras.txt` `OPENCV_FISHEYE` with fx,fy,cx,cy,distortion; nerfstudio `transforms.json` fl_x/fl_y/k1..k4; panocam azim/elev maps.
- **Poses:** DSLR **COLMAP** model *"aligned with the 3D scans, which implies the poses are in metric scale"*; iPhone **ARKit** poses (`json["poses"]`, camera-to-world, right-handed, +Z camera direction) plus `aligned_poses` scaled into mesh space. **Not** mocap GT.
- **TIMESTAMPS:** the documentation does **not** describe a per-frame timestamp field. It documents ARKit poses + IMU (`pose_intrinsic_imu.json`) and *"exif.json: EXIF information for each frame in the video"*, and a 60 FPS video. A hardware timestamp may exist inside EXIF but is **not documented as such → UNVERIFIED**.
- **Checksums:** none published in the docs → **UNVERIFIED**.
- **Held-out (excellent):** `nvs_sem_train` 856 / `nvs_sem_val` 50 / `nvs_test` 50 / `nvs_test_small` 12 / `nvs_test_iphone` 12 / `sem_test` 50. *"To ensure fair comparison, the scenes in nvs_test split do not contain 3D information like meshes and iphone depth maps."* → explicit GT isolation.
- **Leave-and-return:** not labelled as loop-closure content; 360°/panocam capture and COLMAP registration imply revisits but this is **not documented → UNVERIFIED**.
- **Download:** registration + token gated. Pages HTTP 200 ✅; **data files not byte-confirmed** (no token) → 🟡.

---

## 4. ARKitScenes

Evidence: [README](https://raw.githubusercontent.com/apple/ARKitScenes/main/README.md) (200) · [DATA.md](https://raw.githubusercontent.com/apple/ARKitScenes/main/DATA.md) (200) · [raw/README.md](https://raw.githubusercontent.com/apple/ARKitScenes/main/raw/README.md) (200) · [threedod/README.md](https://raw.githubusercontent.com/apple/ARKitScenes/main/threedod/README.md) (200) · [LICENSE](https://raw.githubusercontent.com/apple/ARKitScenes/main/LICENSE) (200) · [download_data.py](https://raw.githubusercontent.com/apple/ARKitScenes/main/download_data.py) (200) · [arXiv 2111.08897](https://arxiv.org/abs/2111.08897) (200). Note: the GitHub UI URL redirects **apple/ARKitScenes → apple-aiml-research/ARKitScenes**; raw.githubusercontent main paths still resolve.

- **Year:** NeurIPS 2021 Datasets & Benchmarks (OpenReview `tjZjv_qh_CE`); arXiv v1 2021-11-17.
- **Size:** **5,047 scans / 1,661 unique scenes** (paper text also says *"5,048 RGB-D sequences"* / *"5,048 captures"* — internal inconsistency) and 450k frames. **3dod = 623.4 GB for 5,047 scans** (official DATA.md). **Full `raw` dataset size: UNVERIFIED** — no fetched page states it. Smallest documented unit = a single video zip (probe: `47333462.zip` = **64,939,565 B**).
- **License (exact):** README: *"Please refer to the LICENSE file for detailed information on using the dataset."* The `LICENSE` file is a **custom Apple licence**: *"personal, non-commercial, non-exclusive license ... for non-commercial purposes only"*, with an extra commercial clause keyed to a **700 million monthly-active-user** threshold before Aug 2024; contact `ARKitScenes-license@group.apple.com`. Not an OSI/CC licence. **No registration gate on download.**
- **RGB + depth:** ✅ real Apple **LiDAR** depth `lowres_depth` (256×192) + `confidence` (uint8 0–2), plus **laser-scanner GT** `highres_depth` (1920×1440) *"projected from the mesh generated by Faro's laser scanners"*, for a subset (*"available for a subset of 2,257 captures of 841 unique scenes"*). Paper: raw device data = *"Wide camera RGB, Ultra Wide camera RGB, LiDAR scanner depth, IMU"*.
- **Depth units — documented:** *"depth image - uint16 png format in millimeters."*
- **Intrinsics K — YES:** `.pincam` text files per RGB frame: `width height focal_length_x focal_length_y principal_point_x principal_point_y`; folders `lowres_wide_intrinsics`, `wide_intrinsics`, `ultrawide_intrinsics`, `vga_wide_intrinsics`.
- **Poses — ESTIMATED, not GT:** paper: *"Additionally we provide **estimated ARKit camera poses** as well as the LiDAR scanner-based ARKit scene reconstruction for all the sequences."* `.traj` = space-delimited, *"each line represents a camera position at a particular timestamp — Column 1: timestamp; Columns 2-4: rotation (axis-angle, radians); Columns 5-7: translation (in meters)."*
- **TIMESTAMPS — REAL:** filenames are timestamps — threedod README annotates `6845.70605696.png  # filenames are indexed by timestamps` (same for depth and `.pincam`), and `.traj` column 1 is a timestamp.
- **Checksums:** none published → **UNVERIFIED**.
- **Held-out:** explicit `Training` / `Validation` splits; `fold` column in the CSV splits (`3dod_train_val_splits.csv`, `raw_train_val_splits.csv`). A separate sealed *test* split is **not documented → UNVERIFIED**. Note `missing_3dod_assets_video_ids` in `download_data.py` lists 24 video_ids whose mesh/annotation/traj assets are absent (checked before download) — useful per-video caveat.
- **Leave-and-return:** capture described as *"one of the scan patterns captured with the iPad pro, the red markers show the chosen locations of the stationary laser scanner"* — venue-level revisit geometry, but **no loop-closure/leave-and-return labels → UNVERIFIED**.
- **Download — best of the ten for frictionless access:** direct HTTP from Apple's CDN, no agreement. Byte-confirmed ✅: `.../v1/threedod/metadata.csv` → 200 (154,354 B); `.../v1/threedod/Training/47333462.zip` → 200 (64,939,565 B). ⚠ `.../v1/raw/raw_train_val_splits.csv` → **403** (that specific path differs from the repo CSV), and `download_data.py` uses `https://docs-assets.developer.apple.com/ml-research/datasets/arkitscenes/v1`.

---

## 5. OpenLORIS-Scene

Evidence: [dataset page](https://lifelong-robotic-vision.github.io/dataset/scene) (200) · [download.md](https://raw.githubusercontent.com/lifelong-robotic-vision/OpenLORIS-Scene/master/download.md) (200) · [arXiv 1911.05603](https://arxiv.org/html/1911.05603v2) (200) · [HuggingFace mirror](https://huggingface.co/datasets/shixuesong/openloris-scene/tree/main) (200).

- **Year:** v1 Nov 2019 (ICRA 2020); *"New Release of May 2020"*.
- **Size:** 5 scenes, 2–7 sequences each; *"There are 22 sequences in total. The accumulated length of the data is 2244 seconds."* Official: **88 GB rosbag** (decompressed ~284 GB) or **105 GB package**. Smallest archive `cafe1-1_2-rosbag.tar` **6.3 GB** (office 8.6 GB). No dev split.
- **License (exact):** **CC BY-ND 4.0** — *"you can do anything with the data, even for commercial purposes, except distributing derivative datasets."* No registration (the old form is struck through). ⚠ BY-**ND** forbids distributing derivatives, which may conflict with releasing a derived benchmark/subsets.
- **RGB-D:** ✅ RealSense **D435i** RGB + **real sensor depth** (848×480 @30 fps), raw and colour-aligned, plus T265 fisheye, IMU, wheel odom, LiDAR.
- **Depth units — documented:** uint16 *"scaled by a factor of 1000 ... multiply them by 0.001 to get depth values in meters."*
- **K:** ✅ in `camera_info`/`imu_info`; extrinsics in `tf_static`; factory calibration, constant per scene.
- **Poses:** GT supplied — *"obtained by an OptiTrack motion capture system for the office scene, and from offline LiDAR SLAM based on the Hokuyo laser scans for other scenes"* (mocap 240 Hz).
- **TIMESTAMPS — PRESENT BUT DELIBERATELY CORRUPTED.** FAQ, verbatim: **"Do the timestamps represent the true time of each recording? No. Random biases have been added to the stamps."** This *disqualifies it for a "real hardware timestamps" gate requirement* even though ROS header stamps exist.
- **Checksums:** official page publishes **truncated** md5 only (e.g. `b55c04...3fdf`); full digests not published. HF exposes full LFS SHA-256 oids.
- **Held-out:** no held-out GT-free split documented.
- **Leave-and-return — YES:** market: *"Each trajectory is a long loop (150-220 meters)"*; office-1 *"U-shape route"*; office-3 *"a turn-around that could connect office-1 and office-2"*; corridor *"could make re-localization and loop closure a tough task."*
- **Dynamic content — YES:** *"real-world scenes with people in it"*; office-7 *"further introduced dynamic objects (persons)"*.
- **Download:** ✅ HuggingFace resolve confirmed 200 (`office1-1_7-rosbag.tar` 9,267,230,720 B; `groundtruth.zip` 11,076,559 B). Google Drive links are dead as of Dec 2025; Baidu Pan unverified.

---

## 6. Co3Dv2 (Common Objects in 3D v2)

Evidence: [repo](https://github.com/facebookresearch/co3d) (200) · [README](https://raw.githubusercontent.com/facebookresearch/co3d/main/README.md) (200) · [LICENSE](https://raw.githubusercontent.com/facebookresearch/co3d/main/LICENSE) (200) · [arXiv 2109.00512](https://arxiv.org/html/2109.00512v1) (200) · [data_types.py](https://raw.githubusercontent.com/facebookresearch/co3d/main/co3d/dataset/data_types.py) (200) · [co3d_sha256.json](https://raw.githubusercontent.com/facebookresearch/co3d/main/co3d/co3d_sha256.json) (200).

- **Year:** v1 = 2021 (ICCV'21). **v2 release year is undocumented**; all URLs sit under `co3dv2_231130` (→ 2023-11-30 by inference, not fact).
- **Size:** README: *"All zip files of the dataset occupy 5.5 TB of disk-space."* Smallest documented: single-sequence subset *"~100 sequences ... takes 8.9 GB of disk-space."* v1 stats: 1.5 M frames / ~19,000 videos / 50 categories; v2 = *"2x larger number of sequences, and 4x larger number of frames"* (**no absolute v2 count documented**).
- **License (exact):** repo `LICENSE` = **CC BY-NC 4.0**; README attributes it to *"the CO3D codebase"*. A dataset-specific terms document is absent → **whether CC BY-NC 4.0 formally covers the DATA is UNVERIFIED**. No gate.
- **RGB-D:** RGB yes. **Depth is COLMAP MVS-ESTIMATED, not sensor** (paper: *"to generate per-frame dense depth maps"*); schema `depth = png * scale_adjustment`. **No LiDAR.**
- **K:** ✅ per-frame `focal_length` + `principal_point` in **`ndc_norm_image_bounds`** (normalised, **not pixels**).
- **Poses:** COLMAP SfM + human verification; *"removes all scenes with camera tracking classified as 'inaccurate' (18% of all videos)."* SfM-derived, not mocap.
- **TIMESTAMPS:** `frame_timestamp: float` = *"timestamp in seconds from the video start"* (plus 0-based `frame_number`). **Relative, not wall-clock.**
- **Checksums — ✅ YES, the only dataset of the ten with a published full manifest:** `co3d/co3d_sha256.json`, and the downloader runs `--checksum_check` by default.
- **Held-out:** category- and sequence-level splits in the repo; no sealed annotation-free test set documented.
- **Leave-and-return:** full 360° capture (*"moving full circle around it"*) implies return to start; **not framed as loop closure → UNVERIFIED**.
- **Download:** ✅ direct HTTP, no gate: HEAD on `https://dl.fbaipublicfiles.com/co3dv2_231130/apple_000.zip` → 200, `application/zip`, 31,587,519 B. `python ./co3d/download_dataset.py` with `--single_sequence_subset` for the 8.9 GB subset.

---

## 7. RealEstate10K

Evidence: [index](https://google.github.io/realestate10k/) (200) · [download](https://google.github.io/realestate10k/download.html) (200) · [arXiv 1805.09817](https://arxiv.org/abs/1805.09817) (200). Note `github.com/google-research/google-research/tree/master/realestate10k` is **404**; the live repo is `google/realestate10k`.

- **Year:** SIGGRAPH 2018.
- **Size:** *"10 million frames ... about 80,000 video clips ... about 10,000 YouTube videos."* Archive: page says **720 MB**; server reports **752,332,631 B**. Split *"about 90% ... train, and the remaining 10% in test"* — test clip count **UNVERIFIED**. ⚠ The paper describes a much smaller set (*"~7,000 sequences with ~750K frames"*) and the project page says *"due to data restrictions, we are unable to release the same version used in the paper."*
- **License (exact):** **CC BY 4.0** (*"licensed by Google LLC under a Creative Commons Attribution 4.0 International License"*). No gate.
- **RGB-D: NO.** *"The data consists of a set of .txt files, one for each video clip, specifying timestamps and poses."* **No RGB frames and no depth are distributed — only pose files + YouTube URLs.** Disqualifying for an RGB-D gate.
- **K:** ✅ 4 normalised intrinsics (top-left (0,0) → bottom-right (1,1), scale by width/height).
- **Poses:** ORB-SLAM2 + Ceres bundle adjustment (*"derived by running SLAM and bundle adjustment algorithms"*); **arbitrary per-clip scale**, normalised so the 10th-percentile depth = 1.25 m.
- **TIMESTAMPS:** column 1 = *"timestamp (int: microseconds since start of video)"* — **video-relative, not wall-clock and not a frame index.**
- **Checksums:** none published (**UNVERIFIED**); server-side md5/crc32c exist but are not part of the dataset docs.
- **Held-out:** 10% test split; all data is poses anyway.
- **Leave-and-return:** **not documented / UNVERIFIED**.
- **Download:** ✅ canonical host works: `https://storage.googleapis.com/realestate10k-public-files/RealEstate10K.tar.gz` → **HTTP 206**, valid gzip. ⚠ the URL printed on the page (`storage.cloud.google.com/...`) now 302s to a Google sign-in and is **not** anonymously usable.

---

## 8. DL3DV-10K

Evidence: [site](https://dl3dv-10k.github.io/DL3DV-10K/) (200) · [README](https://raw.githubusercontent.com/DL3DV-10K/Dataset/main/README.md) (200) · [License.md](https://raw.githubusercontent.com/DL3DV-10K/Dataset/main/License.md) (200) · [arXiv 2312.16256](https://arxiv.org/abs/2312.16256) (200) · HF cards [Sample](https://huggingface.co/datasets/DL3DV/DL3DV-10K-Sample) / [ALL-480P](https://huggingface.co/datasets/DL3DV/DL3DV-ALL-480P) / [Benchmark](https://huggingface.co/datasets/DL3DV/DL3DV-Benchmark) (200).

- **Year:** arXiv v1 2023-12-26; README BibTeX = CVPR 2024.
- **Size:** *"10,510 videos"* / **51.2 M frames** / 4K. Variants: 480P ~730 GB, 960P ~2.8 TB, 2K ~11 TB, 4K ~44 TB, video ~7 TB. Smallest documented: **11-scene sample 79.6 GB**; 140-scene NVS benchmark *"~2.1T"* full, 960P-only *"100~150G"*.
- **License (exact):** **DL3DV-10K Terms of Use + CC BY-NC 4.0**; ToU: *"Researcher shall use the Dataset only for non-commercial research and educational purposes."* ⚠ README also says *"the latest license is open to the usage of the dataset"* — contradictory. HF access is **auto-gated** (must agree to share contact info).
- **RGB-D: NO official depth.** `--file_type` choices are only `images+poses`, `video`, `colmap_cache`. Depth exists only in a third-party derivative (DepthSplat).
- **K:** present via `colmap/sparse/0/cameras.bin` and nerfstudio `transforms.json`, **not described in prose and not opened (gated) → UNVERIFIED**.
- **Poses:** COLMAP-estimated (*"Released samples include colmap calculated camera pose"*).
- **TIMESTAMPS:** **not documented**; frames are `frame_00001.png` indices; only fps (60 or 30) is documented.
- **Checksums:** no published manifest (scene IDs are 64-hex hashes, not checksums). HF per-file LFS hashes exist but are not a published manifest.
- **Held-out:** train/val/test splits documented; annotations ship with the data → no GT isolation.
- **Leave-and-return:** only *"circle or half-circle"* / *"at least 180° or 360°"* capture guidance; **no loop-closure labels → UNVERIFIED**.
- **Dynamic content:** documented and bounded — moving objects *"under 3 secs, with a maximum allowance of 10 secs"*; Table 2: 8,064 scenes <3 s, 2,446 scenes 3–10 s.
- **Download:** ❌ dataset pages 200, but a data-file resolve returned **HTTP 401** until login + acceptance. No working anonymous path.

---

## 9. MVImgNet

Evidence: [project site](https://gaplab.cuhk.edu.cn/projects/MVImgNet/) (200) · [README](https://raw.githubusercontent.com/GAP-LAB-CUHK-SZ/MVImgNet/main/README.md) (200) · [LICENSE](https://raw.githubusercontent.com/GAP-LAB-CUHK-SZ/MVImgNet/main/LICENSE) (200) · [arXiv 2303.06042](https://arxiv.org/abs/2303.06042) (200) · [registration form](https://docs.google.com/forms/d/e/1FAIpQLSfU9BkV1hY3r75n5rc37IvlzaK2VFYbdsvohqPGAjb2YWIbUg/viewform) (200).

- **Year:** CVPR 2023.
- **Size:** 6.5 M frames / **219,188 videos** / 238 classes (215,755 valid). Release **~3.4 TB in 43 zips** (`mvi_00..mvi_42`). Smallest documented = *"MVImgNet-small (a random subset ... same scale as CO3D)"* — **exact count not documented**; `MVImgNet_by_categories` is explicitly *"incomplete"*.
- **License (exact):** *"The data is released under the MVImgNet Terms of Use, and the code is released under the Attribution-NonCommercial 4.0 International License."* Repo `LICENSE` = CC BY-NC 4.0 text. **The "MVImgNet Terms of Use" document itself was never fetched → UNVERIFIED.**
- **RGB-D: NO sensor depth.** RGB frames + binary masks only; the paper generates COLMAP MVS depth *in the pipeline*, but the documented release contains images + `sparse/0/{cameras,images,points3D}.bin` and **no depth folder**.
- **K / poses:** COLMAP SfM-estimated intrinsics and extrinsics (*"reconstruct the camera intrinsic and extrinsic ... by applying COLMAP SfM"*). Not GT.
- **TIMESTAMPS:** **not documented**; only *"equal-time-interval chosen frames"* in the pipeline description.
- **Checksums:** none documented.
- **Held-out:** category/difficulty splits in the paper; no sealed GT-free test set.
- **Leave-and-return:** only *"capture 180° or 360° view of the object"*; no loop-closure labels.
- **Source:** REAL handheld smartphone video, ~1000 crowd-sourced collectors, ~10 s clips, one principal object each — not synthetic. Masks auto-generated (CarveKit).
- **Download:** ❌ Google Form (password revealed after submission) → **password-protected Microsoft SharePoint**; actual data link not obtainable. Open issues report SharePoint auth failures and dead links through Nov 2025.

---

## 10. WildRGB-D

Evidence: [README](https://raw.githubusercontent.com/wildrgbd/wildrgbd/master/README.md) (200) · [download.py](https://raw.githubusercontent.com/wildrgbd/wildrgbd/master/download.py) (200) · [LICENSE](https://raw.githubusercontent.com/wildrgbd/wildrgbd/master/LICENSE) (200) · [HF dataset card](https://huggingface.co/datasets/hongchi/wildrgbd) (200) · [arXiv 2401.12592](https://arxiv.org/html/2401.12592v3) (200).

- **Year:** CVPR 2024 (arXiv v1 2024-01-23).
- **Size:** README: *"approximately 3.37T disk space to store zip packages, and approximately 4T to store all data."* Paper: **8,500 objects / nearly 20,000 videos / 46 categories** (abstract) vs **8,367 objects in 23,049 videos / 44 categories** after SLAM-failure filtering (paper §3.2 + Table 1) — quote both, they disagree. Smallest documented subset = **one category archive**; byte-confirmed sizes: `TV.zip` **24,379,476,927 B (~24.4 GB)**, `car.zip` 35.5 GB, `boat.zip` 44.1 GB, `bucket.zip` **47,149,053,666 B**. README concedes an earlier "3.37T" figure for zips.
- **License (exact):** repo `LICENSE` = **MIT** (*"Copyright (c) 2024 rowdataset"*); the HF dataset card also declares **`license: mit`**. ⚠ **No dataset-specific terms-of-use document was found** — MIT on captured RGB-D is unusual and may not reflect the uploaders' intent; treat the *data* licence as **MIT-per-repo but not independently confirmed**. No gate (`gated: false`).
- **RGB-D: YES, real sensor depth:** captured with an **iPhone via the Record3D app**, *"RGB images and the corresponding depth images"*. `types.json` categories = `single` / `multi` / `hand`.
- **Depth units — documented:** *"We store depths in the depth scale of 1000. That is, when we load depth image and divide by 1000, we could get depth in meters."*
- **K:** ✅ *"`metadata`: It stores the camera intrinsics including image width, height and K."*
- **Poses:** `cam_poses.txt` — *"For every line, we list the `<frame_id>` first, then following the flatten 4x4 extrinsic matrix. Our camera extrinsics follows OpenCV convention, and it's camera to world matrix."* Derived by **SLAM, not GT**: *"we generate more accurate camera poses with the mature RGBD SLAM algorithm, which leverages our captured depths"* — **BAD SLAM + Open3D SLAM**, real-world scale, videos with SLAM failure excluded (retention 99.3% objects / 91.0% videos).
- **TIMESTAMPS:** **NOT documented.** All filenames are `<frame_id>.png` and `cam_poses.txt` is keyed by `<frame_id>` → **frame indices, no capture timestamps documented**.
- **Checksums:** none documented → **UNVERIFIED**.
- **Held-out:** `nvs_list.json` (train/val) and `camera_eval_list.json` splits — frame-level, **within the same download, so no GT isolation**.
- **Leave-and-return:** 360° orbit around the object (*"go around the objects in 360 degrees"*) implies returning to the start view, but no leave-and-return/loop-closure label is documented.
- **Dynamic content:** `hand` videos contain *"a static human hand grasping the object"* — an occluder, not scene motion.
- **Download — ✅ works, anonymously:** `download.py` wgets `https://huggingface.co/hongchi/wildrgbd/resolve/main/<file>?download=true`; multi-part archives are joined with `zip -F`. Confirmed by ranged GET on `bucket.zip` → **HTTP 206, 201 bytes, `application/zip`, valid PK zip magic**. ⚠ The HF **web UI reports "The dataset is currently empty"** because the repo tree lists only `README.md` (21 B) + `.gitattributes` — the archives live in Xet storage and resolve fine; do **not** trust the UI's "empty" message.

---

## Master table

| Dataset | Year | Size (full / smallest) | License | Real timestamps? | RGB-D? | Poses? | K? | Dynamic content? | Download confirmed? |
|---|---|---|---|---|---|---|---|---|---|
| **TUM RGB-D** | 2012 | 89 archives ≈ 88.55 GB total (my sum) / 0.20 GB `fr3/nostructure_texture_far` | CC BY 4.0 (data) + BSD-2-Clause (code), no gate | **Yes** — Unix-epoch stamps in filenames + GT first column | **Yes** — real Kinect depth, **1:1 registered** | **Yes — mocap**, 8 cams @100 Hz | Yes (RGB+IR tables) | Yes ("Dynamic Objects" group) | 🟡 page 200; tgz not byte-confirmed |
| **ScanNet v1/v2** | 2017 / v2 2018 | **1.2 TB** (official script); 1,513 scans + **100 test** scans / `scannet_frames_test.zip` 610 MB | ScanNet Terms of Use (agreement emailed) + MIT code | **Yes** — `.sens` per-frame `timestamp_color`/`timestamp_depth` (uint64); unit UNVERIFIED | **Yes** — real Structure.io RGB-D, separate colour/depth intrinsics | Reconstruction-derived per-frame `camera_to_world` (BundleFusion), not mocap | Yes (4×4 in `.sens`) | Yes (people present) | ✅ 206/200 on `.sens` (v1 path), `.ply`, `.aggregation.json`, `scans.txt` |
| **ScanNet++** | 2023 / v2 2024 | 1,006 scenes; 1.5 TB default (371 GB DSLR-2MP … 720 GB point clouds) / `nvs_test_small` 12 scenes; meshes+sem 132 GB | ScanNet++ Terms of Use — account + application + token | **No** — not documented as timestamps (ARKit poses + IMU + EXIF; 60 FPS) | **Yes** — iPhone LiDAR real depth in **mm**; DSLR depth is **rendered from mesh** | COLMAP poses aligned to laser scan (metric) + ARKit poses + `aligned_poses` | Yes (3×3 iPhone; COLMAP fisheye; transforms.json) | Yes (anonymised people) | 🟡 pages 200; data token-gated |
| **ARKitScenes** | 2021 | 5,047 scans / 1,661 scenes; **3dod 623.4 GB**, raw total UNVERIFIED / single video zip ≈ 65 MB | **Custom Apple licence** — non-commercial (+700 M MAU commercial clause) | **Yes** — filenames indexed by timestamps; `.traj` col 1 = timestamp | **Yes** — Apple LiDAR real depth (**mm** uint16) + Faro laser-scanner GT `highres_depth` | **Estimated ARKit poses** (SLAM), not GT | Yes (`.pincam`) | Yes (people present) | ✅ 200 on `metadata.csv` + `Training/47333462.zip` (64.9 MB) |
| **OpenLORIS-Scene** | 2019 / 2020 | 22 seq, 2,244 s; 88 GB rosbag (284 GB raw) / `cafe1-1_2` 6.3 GB | **CC BY-ND 4.0** (no derivatives!), no gate | **NO — deliberately corrupted**: *"Random biases have been added to the stamps"* | **Yes** — D435i real depth (uint16/1000 = m) | Yes — mocap (office, 240 Hz) / LiDAR-SLAM (others) | Yes (`camera_info`) | **Yes** | ✅ HF HEAD 200 |
| **Co3Dv2** | v1 2021; v2 year undocumented | 5.5 TB all zips / single-sequence subset 8.9 GB (~100 seq) | CC BY-NC 4.0 (repo); data coverage UNVERIFIED | Relative only — `frame_timestamp` = s from video start | RGB yes; depth = **COLMAP MVS estimated** | COLMAP SfM, human-verified | Yes, **NDC** units | Not documented | ✅ HEAD 200 (`dl.fbaipublicfiles.com`) |
| **RealEstate10K** | 2018 | 10 M frames / ~80 k clips; 752,332,631 B tarball / 10% test, size UNVERIFIED | CC BY 4.0 | µs **since video start** (relative) | **NO** — only `.txt` poses + YouTube URLs; no depth | ORB-SLAM2 + BA, arbitrary scale | Yes, normalised 0–1 | Static scenes | ✅ 206 gzip at `storage.googleapis.com` |
| **DL3DV-10K** | 2023 | 10,510 videos / 51.2 M frames; 480P ~730 GB, 4K ~44 TB / 11-scene sample 79.6 GB | DL3DV ToU (**non-commercial**) + CC BY-NC 4.0; HF auto-gated | **No** — `frame_00001.png` indices | RGB yes; **NO official depth** | COLMAP SfM | Present but **not opened** (gated) | Yes, <3 s guideline | ❌ resolve 401 |
| **MVImgNet** | 2023 | 6.5 M frames / 219,188 videos; ~3.4 TB in 43 zips / "MVImgNet-small" ≈ CO3D scale (count undocumented) | Data: "MVImgNet Terms of Use" (**UNVERIFIED**); code CC BY-NC 4.0; form + password | **No** — not documented | **No sensor depth** — RGB + masks; MVS depth not in release | COLMAP SfM | Yes (COLMAP) | Not documented | ❌ form → password-protected SharePoint |
| **WildRGB-D** | 2024 | 8,500 objects / ~20 k videos (8,367 / 23,049 after cleaning); 3.37 TB zips / single category archive: `TV.zip` 24.4 GB | **MIT** (repo + HF card); no separate data ToU found → UNVERIFIED for data | **No** — `frame_id` only | **Yes** — iPhone/Record3D real sensor depth, scale **1000** | **SLAM-estimated** (BAD SLAM + Open3D), metric | Yes (`metadata` K) | Static hand in `hand` videos | ✅ 206 on `bucket.zip` (47,149,053,666 B) |

---

## Gate-fit verdict (RGB+depth, 1:1 pairing, real timestamps, K, poses, depth units, checksums, licence, GT isolation, held-out, leave-and-return)

- **Only TUM RGB-D documents the full basic stack** — real Kinect depth with **documented 1:1 registration**, real epoch timestamps, mocap poses, per-camera K, documented scale 5000, CC BY 4.0 — **plus** 25 GT-free `*_validation` sequences for held-out evaluation **plus** explicitly named loop-closure sequences (`fr1/desk`, `fr2/large_with_loop`, `fr3/*_withloop`, `fr1/360`). Its two hard misses: **no checksums**, and **mocap GT does not span the whole recording for 9+ sequences** (worst: `fr2/large_with_loop`, GT on only 40.54 s of 173.19 s) — audit GT coverage **per sequence**, exactly as Bonn required.
- **ScanNet is the best "real hardware timestamps" evidence of the ten** (per-frame `timestamp_color`/`timestamp_depth` in an open, parseable format) and ships **100 annotation-free test scans**; but licence is agreement-gated, there are **no checksums**, poses are reconstruction-derived (not GT), depth units/`depth_shift` convention and timestamp epoch are **UNVERIFIED**, and `.sens` must be fetched from the **v1** path.
- **ScanNet++ has the cleanest held-out design** (*"the scenes in nvs_test split do not contain 3D information like meshes and iphone depth maps"*, plus a 12-scene `nvs_test_small`) and real metric iPhone LiDAR depth in mm, but it is token-gated, **does not document per-frame timestamps**, and its DSLR depth is mesh-rendered rather than sensed.
- **ARKitScenes is the easiest to actually get** (no agreement, direct Apple CDN, byte-confirmed) with real mm depth, K and timestamp-keyed filenames — but the licence is a custom **non-commercial Apple** licence and poses are explicitly **estimated**.
- **Reject for this gate:** OpenLORIS-Scene (timestamps deliberately biased, and CC BY-**ND** forbids derivative datasets), RealEstate10K (no RGB, no depth — poses only), DL3DV-10K (no depth, no timestamps, non-commercial, 401-gated), MVImgNet (no sensor depth, no timestamps, unreliable password-gated SharePoint), WildRGB-D (no timestamps — frame IDs only; licence hygiene unclear), Co3Dv2 (MVS-estimated depth, relative timestamps, NDC intrinsics). Co3Dv2 does, however, publish the **only full SHA-256 manifest** in this set.

**Items explicitly UNVERIFIED:** TUM checksums; ScanNet TOS clauses, timestamp epoch, `depth_shift` convention, checksums; ScanNet++ timestamps and checksums; ARKitScenes raw-set total size, sealed test split, checksums; OpenLORIS full md5 digests; Co3Dv2 release year, absolute v2 counts, data-specific licence; RealEstate10K test clip count, checksums; DL3DV intrinsics contents, metric scale, checksums; MVImgNet Terms of Use document, depth presence in the actual release; WildRGB-D data licence, checksums, timestamps.
