# Datasets & Evaluation Protocols for Long-Horizon / Memory-Based Video World Models

**Survey date:** September 2026 · **Sub-area:** DATASETS AND EVALUATION PROTOCOLS
**Purpose:** unblock a project whose gate requires RGB + depth, 1:1 RGB–depth pairing, **real hardware timestamps**, intrinsics K, camera poses, documented depth units, SHA checksums, clear license, and strict future-GT isolation.

**Evidence rules used here.** Every claim comes from a page I fetched, or from bytes I downloaded and parsed. `UNVERIFIED` marks anything I could not confirm. Accessibility is stated explicitly: **✅ byte-confirmed** = I actually transferred bytes or got HTTP 200/206 on a data file; **🟡 page-confirmed** = official page returns 200 and describes the path, but I did not stream the payload; **❌ no working path**.

**Headline result.** Exactly **two** verified dataset families pass the hard gate end-to-end: **TUM RGB-D** (the only one documenting the complete stack: real epoch timestamps + explicit 1:1 registration + mocap poses + K + depth factor 5000 + CC BY 4.0) and **Bonn RGB-D Dynamic** (same TUM format, real epoch timestamps, plus a static-scene GT point cloud alongside dynamic sequences). I verified both by downloading and parsing their bytes, not by trusting their documentation. **ICL-NUIM's failure is real and I reproduced it independently.**

---

## 1. Dataset table

Legend for timestamps: **REAL** = hardware/capture Unix-epoch or device stamps confirmed in bytes or in a source file format; **frame-idx** = integer frame numbers only; **relative** = seconds since clip start, not wall-clock; **none** = no sequences released at all.

| Dataset | Year | Real timestamps? | RGB-D? | Poses? | Dynamic content? | License | Approx size | Download path verified? | Fit to gate |
|---|---|---|---|---|---|---|---|---|---|
| **TUM RGB-D** ([main](https://cvg.cit.tum.de/data/datasets/rgbd-dataset), [formats](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats), [download](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/download)) | 2012 | **REAL** — Unix-epoch floats; verified in bytes (`rgb.txt` header `# timestamp filename`, values `1341847980.722988 …`) | **Yes** — real Kinect; **explicitly 1:1 pre-registered** | **Yes — mocap**, 8 cams @100 Hz (verified 8710 poses @ exactly 100.0 Hz) | Yes — `fr3_sitting_*`, `fr3_walking_*`, `fr2_desk_with_person` | **CC BY 4.0** (data) + BSD-2-Clause (code), no gate | 89 archives ≈ 88.6 GB total; smallest 0.20 GB; primary pick 1.58 GB | **✅** byte-confirmed (downloaded 1,483,556,251 B; Content-Length matched); every URL I checked returned HTTP 200 | **YES** — the only full pass. Misses only published checksums. ⚠ audit per-sequence GT coverage |
| **Bonn RGB-D Dynamic** ([official](http://www.ipb.uni-bonn.de/data/rgbd-dynamic-dataset/)) | 2019 | **REAL** — verified in bytes (`1548266469.85…`, Jan 2019) | **Yes** — Kinect, depth registered to RGB, TUM format | **Yes — Optitrack Prime 13 mocap** (verified 30.0 Hz) | **Yes — 24 dynamic sequences** (boxes, balloons, people) | Not stated on page → **UNVERIFIED** license | All sequences **16.4 GB** (16,395,422,367 B); per-sequence 182 MB–5.8 GB; subsampled static GT cloud 676 MB | **✅** byte-confirmed (downloaded `rgbd_bonn_balloon.zip` 243,818,512 B) | **YES** (license caveat) — and the **only real-captured set with static-scene GT *plus* dynamic sequences** |
| **ScanNet v1/v2** ([site](http://www.scan-net.org/ScanNet/), [README](https://raw.githubusercontent.com/ScanNet/ScanNet/master/README.md)) | 2017 / v2 2018 | **REAL** — `.sens` per-frame `timestamp_color`/`timestamp_depth` (uint64); epoch/unit UNVERIFIED | Yes — Structure.io RGB-D | Reconstruction-derived (`camera_to_world`, BundleFusion) — **not mocap GT** | Yes (people) | ScanNet Terms of Use (agreement emailed) + MIT code | **1.2 TB**; 1,513 + 100 test scans; `scannet_frames_test.zip` 610 MB | **✅** 206 on `.sens` (**v1 path only**; v2 404s), `.ply`, `.aggregation.json` | **PARTIAL** — real timestamps + **100 annotation-free test scans** (great GT isolation), but agreement-gated, no checksums, poses not GT, depth units UNVERIFIED |
| **ScanNet++** ([site](https://scannetpp.mlsg.cit.tum.de/scannetpp/)) | 2023 / v2 2024 | **Not documented** — ARKit poses + IMU + EXIF only → UNVERIFIED | Yes — iPhone LiDAR real depth (**mm**); DSLR depth is **mesh-rendered** | COLMAP aligned to laser scan (metric) + ARKit | Yes (anonymised) | ScanNet++ Terms of Use — account + application + token | 1,006 scenes; default 1.5 TB; smallest test subset `nvs_test_small` 12 scenes | 🟡 pages 200; data token-gated | **PARTIAL** — cleanest held-out design (`nvs_test` ships no meshes/depth), metric mm depth, but no documented timestamps and token-gated |
| **ARKitScenes** ([README](https://raw.githubusercontent.com/apple/ARKitScenes/main/README.md)) | 2021 | **REAL** — filenames timestamp-indexed; `.traj` col 1 = timestamp | Yes — Apple LiDAR, **mm** uint16 + `confidence`; Faro laser-scanner `highres_depth` GT for a subset | **Estimated ARKit poses** (explicitly "estimated"), not GT | Yes (people) | **Custom Apple licence**, non-commercial (+700 M MAU clause); **no gate** | 3dod **623.4 GB**; raw total UNVERIFIED; single video zip ≈ 65 MB | **✅** 200 on `metadata.csv` (154,354 B) + `Training/47333462.zip` (64,939,565 B) | **PARTIAL** — most frictionless real RGB-D with real timestamps, but non-commercial custom licence, poses not GT, no checksums |
| **OpenLORIS-Scene** ([page](https://lifelong-robotic-vision.github.io/dataset/scene)) | 2019/2020 | **NO — deliberately corrupted.** FAQ: *"Do the timestamps represent the true time of each recording? No. Random biases have been added to the stamps."* | Yes — D435i real depth (uint16/1000 = m) | Yes — mocap (office, 240 Hz) / LiDAR-SLAM | Yes | **CC BY-ND 4.0** (forbids derivative datasets) | 88 GB rosbag / 284 GB raw; smallest 6.3 GB | ✅ HF HEAD 200 | **NO** — timestamps are corrupted by design; BY-ND blocks derived benchmarks |
| **Co3Dv2** | v1 2021; v2 year UNVERIFIED | **relative** — `frame_timestamp` = s from clip start | RGB yes; depth = **COLMAP MVS-estimated** | COLMAP SfM, human-verified | Not documented | CC BY-NC 4.0 (repo) | 5.5 TB all zips; single-sequence subset 8.9 GB | ✅ HEAD 200 | **NO** — estimated depth, relative timestamps, NDC intrinsics. **Only dataset here publishing a full SHA-256 manifest** |
| **RealEstate10K** | 2018 | **relative** — µs since video start | **NO — poses only (`.txt`) + YouTube URLs; no RGB, no depth in the release** | ORB-SLAM2 + BA, arbitrary scale | Static | CC BY 4.0 | 10 M frames / ~80 k clips; tarball 752,332,631 B | ✅ 206 gzip at `storage.googleapis.com` | **NO** — ships no RGB and no depth |
| **DL3DV-10K** | 2023 | **frame-idx** (`frame_00001.png`), fps only | RGB yes; **NO official depth** | COLMAP SfM | Yes, bounded (<3 s guideline) | DL3DV ToU (non-commercial) + CC BY-NC 4.0; HF auto-gated | 10,510 videos; 480P ~730 GB … 4K ~44 TB; 11-scene sample 79.6 GB | **❌** data resolve **401** | **NO** — no depth, no timestamps, non-commercial, login-gated |
| **MVImgNet** | 2023 | **not documented** | **No sensor depth** (RGB + masks; MVS depth not in release) | COLMAP SfM | Not documented | Data "Terms of Use" **UNVERIFIED**; code CC BY-NC 4.0 | ~3.4 TB in 43 zips | **❌** form → password-protected SharePoint | **NO** |
| **WildRGB-D** ([GitHub](https://github.com/wildrgbd/wildrgbd)) | 2024 | **NO** — `frame_id` only | **Yes** — iPhone/Record3D real depth, scale **1000** | **SLAM-estimated** (BAD SLAM + Open3D), metric | Static hand in `hand` videos | MIT (repo + HF card); data ToU not separately found → UNVERIFIED | 3.37 TB zips; smallest category `TV.zip` 24.4 GB (`bucket.zip` 47,149,053,666 B) | **✅** 206 on `bucket.zip` — HF UI falsely says "empty"; archives are in Xet storage | **NO** — no timestamps; licence hygiene unclear |
| **SpatialVID** ([HF](https://huggingface.co/datasets/SpatialVID/SpatialVID)) | 2025/26 | **NO** — YouTube source offsets only, in a separately gated RAW repo | Depth **estimated** (MegaSaM + Depth-Anything V2/UniDepth), not sensor | **estimated** poses (`poses.npy`) | Yes (dynamic masks) | CC-BY-NC-SA-4.0; HF **gated** (`auto`) with a form | 2.7 M clips / 7,089 h; **7.7 TB**; RAW = YouTube IDs + timestamps ~2.21 GB | 🟡 gated | **NO** — gated, non-commercial, estimated depth/poses, no hardware timestamps |
| **CityWalker** ([GitHub](https://github.com/ai4ce/CityWalker)) | 2025 | Not documented (web video) | No depth | Estimated (DPVO odometry) | Yes (urban) | Not stated (UNVERIFIED) | 6.8 GB (18 archives + `pose_label.zip`) | **✅** ungated on HF | **NO** — no depth, no documented timestamps |
| **MBench data** ([project](https://peanutup.github.io/MBench-project/), [HF](https://huggingface.co/datasets/studyOverflow/MBench-Data)) | 2026 | UNVERIFIED | No GT depth (DepthAnything-v3 artifact used for eval) | Estimated, not GT | Yes | UNVERIFIED on HF card (code MIT) | **678 GB**; 547 real `source_video.mp4` + 100 `reference.png` | **✅** ungated, enumerable | **NO for the gate**, useful as a real-captured long-video memory test |
| **MIND** ([arXiv](https://arxiv.org/abs/2602.08025), [HF](https://huggingface.co/datasets/CSU-JPG/MIND)) | 2026 | **frame-idx** (UE5 synthetic) | **No depth** | Synthetic engine GT (`action.json`) | Yes (scripted) | **MIT**, ungated | **34.8 GB** (250 videos, 1080p/24fps) | **✅** ungated | **NO for the gate** (no depth, no real timestamps) — best **memory-eval protocol** carrier |
| **R2M-Bench** ([arXiv](https://arxiv.org/abs/2608.27328), [HF](https://huggingface.co/datasets/GD-ML/R2MBench)) | 2026 | None (protocol) | No | Commanded trajectories + per-frame K/extrinsics in repo | N/A | **MIT** | **181 MB** (100 reference PNGs); trajectories in GitHub | **✅** ungated | **Protocol only** — you generate the rollouts; ideal **metric harness** |
| **LoopNav** ([arXiv](https://arxiv.org/abs/2505.22976), [HF](https://huggingface.co/datasets/kevinLian/LoopNav)) | 2025/26 | frame-idx (Minecraft) | No | Yes (sim) | Yes | UNVERIFIED (none on card) | ~775 GB (250 h / ~20 M frames) | **✅** ungated | **NO for the gate** — synthetic Minecraft; strong **A→B→A loop protocol** |
| **iWorld-Bench** ([HF](https://huggingface.co/datasets/EmbodiedCity/iWorld-Bench-Dataset)) | 2026 | frame-idx (rendered sim) | No | Yes — `cameras/*.txt` intrinsics+extrinsics | Yes | UNVERIFIED | ~970 GB | **✅** ungated | **NO for the gate** — simulator; has a dedicated **200-task loop-closure memory track** |
| **WorldScore** ([HF](https://huggingface.co/datasets/Howieeeee/WorldScore)) | 2025 | None (protocol) | No | Camera trajectories as text | 1,000 dynamic examples | **MIT** | ~6.1 GB (3,000 examples) | **✅** ungated | **Protocol** — next-scene generation w/ camera control |
| **ICL-NUIM** ([official](https://www.doc.ic.ac.uk/~ahanda/VaFRIC/iclnuim.html)) | 2014 | **frame-idx — I reproduced the failure.** Downloaded the TUM-compatible archive: entries are `rgb/1439.png`, `depth/1419.png`; the only `.txt` is `associations.txt` with lines `0 depth/0.png 0 rgb/0.png` | **Yes** + **GT 3D surface model** (living room) | **Yes** — perfect synthetic GT, TUM format | No (static scene) | **CC BY 3.0** | 6 trajectories (living room + office), 1.7–3.3 GB each | **✅** HTTP 200 (711,444,709 B) | **NO** — fails timestamps exactly as you found. `*_loop` trajectories are otherwise ideal revisit content |
| **Replica** | 2019 | **none** — no image sequences released | No (mesh + HDR textures) | No | No | Replica Research Terms (non-commercial) | 33.86 GB (17 parts) | 🟡 release API 200; payload not pulled | **NO** — you must render RGB-D/poses yourself |
| **ReplicaCAD / Habitat 2.0** | 2021 | **none** | No (assets only) | No | No | **CONFLICT**: card CC BY 4.0 vs bundled `LICENSE.txt` CC BY-NC 4.0 | ~1 GB; smallest 132 MB | **✅** HF resolve 200 | **NO** — scene assets, not sequences |
| **HM3D** | 2021 | **none** | No (meshes) | No | No | Matterport academic EULA + API token | ~36 GB glb; minival 390 MB | 🟡 token-gated | **NO** |
| **Matterport3D** | 2017 | **not documented** (yaw-indexed filenames) | **Yes** — 194,400 RGB-D | Yes | No | Matterport3D ToU, signed form emailed | UNVERIFIED | **❌** email-gated (403 on ToS host) | **NO** — no timestamps, gated. Depth convention *is* documented (0.25 mm/value, ÷4000 = m) |
| **PointOdyssey** | 2023 | **frame-idx** (`rgb_%05d.jpg`) | Yes | Yes | **Yes** (instance seg + per-point visibility + 3D trajs) | **CONFLICT**: HF card MIT vs repo CC BY-NC-SA 4.0 | ~185 GB; **sample 3.32 GB** | **✅** HF resolve 200 | **NO** — no real timestamps; fails your ~3.3 GB download objection too |
| **RTMV** | 2022 | **frame-idx** (`00000.json`) | Yes | Yes | Yes (seg masks, entity poses, **static point cloud**) | CC BY-NC 4.0 (HF re-upload); original UNVERIFIED | 675 GB (40-scene re-upload); smallest tar 12.06 GB | **✅** HF resolve 200 | **NO** — no timestamps; too large; TLS issues you hit are consistent with the original host |
| **RTMV-X** | — | — | — | — | — | — | — | **❌** | **NOT A VERIFIABLE DATASET** — no mention in the RTMV paper, project page (live 404), HF, or any search. Do not cite |
| **TartanAir V1/V2** | 2020 / 2023 | **frame-idx** (pose lines at 10 Hz, no time column) | Yes | Yes | Partial (semantic + flow masks) | CC BY 4.0 (data); BSD-3 / MIT (tools) | 3 TB (V1); mono test track **7.65 GB**; stereo 17.51 GB | 🟡 pages 200; payload not pulled | **NO** — no timestamps. Does publish **MD5** for the 3 test tracks |
| **Dynamic Replica** | 2023 | `frame_timestamp` float exists but **synthetic** ("seconds from the video start") | Yes — stereo RGB-D | Yes | **Yes — per-frame fg/bg masks + instance seg + flow + long-range trajectories over a static Replica background** | Meta Dynamic Replica License, click-through, non-commercial | 1.8 T train / **`real` split 152 MB** / valid 106 GB / test 328 GB | **✅** SHA-256 manifest fetched (`scripts/dr_sha256.json`) | **NO for the timestamp gate** — but **the strongest static-vs-dynamic GT separation** and it publishes **SHA-256** |

---

## 2. Top 3 recommendations

### 1. TUM RGB-D — use the `fr3` subsets. **This is the unblock.**
**Concrete reason:** it is the only dataset I verified that satisfies every gate item that is actually a *data* property — real Unix-epoch hardware timestamps, RGB+depth already pre-registered **1:1**, published K per camera, mocap GT poses, documented depth units (16-bit PNG, ÷5000 = metres, 0 = missing), CC BY 4.0, direct HTTP download, no registration, and it fits the 162 GB quota ~100× over. Critically for your crux, its loop closure is *extensive*, not nominal: in `fr3_long_office_household` I measured **109,280 pose-pairs within 0.30 m with a >10 s time gap** (min revisit distance 0.018 m, largest gap 78.6 s, 1261 distinct mocap frames). It also has a ready-made GT-free held-out set (25 `*_validation` sequences) and dynamic-person sequences, all with full GT coverage on `fr3`.
Verified byte-level: 2585 RGB frames, 2509 depth frames, 8710 mocap poses at exactly 100.0 Hz; 2488/2585 RGB frames pair to depth within 20 ms; depth median nonzero 12075 → **2.415 m** at ÷5000.
**Single biggest risk:** **mocap GT does not span the whole recording for several sequences** — the TUM download page publishes both `Duration` and `Duration with ground-truth`, and they diverge badly: `fr2/large_with_loop` has GT on only **40.54 s of 173.19 s** (and `fr2/large_no_loop` 21.37/112.37, `fr2/desk` 69.15/99.36, `fr2/desk_with_person` 119.37/142.08). This is *exactly* the Bonn failure that already burned you. Mitigation: **all `fr3` sequences match to ≤0.09 s** (I verified `fr3_long_office_household` = 87.09 s duration vs 87.10 s with GT against the bytes), so stay inside `fr3`/`fr1`. Secondary risk: TUM publishes **no checksums** — you must hash and record your own (I computed SHA-256 `c7cd8e1afb87c80e5744a356214819b110fa09b4744fa4ba0cc2382f9ba59e9c` for `fr3_long_office_household.tgz`). Tertiary risk: it is a small single-room scene (5.12 × 4.89 m), so it can validate the gate and the revisit mechanism but **cannot** support a "long-horizon" claim.

### 2. Bonn RGB-D Dynamic — for the *static-changed vs hallucinated* discrimination.
**Concrete reason:** it is the **only real-captured dataset I found that ships both a static-scene ground truth and dynamic-object content**: the official page provides a full ground-truth point cloud of the static environment (394,109,339 points; PLY ASCII) plus a subsampled section (54,676,774 points, 676 MB), recorded with a **Leica BLK360** terrestrial laser scanner, *alongside* 24 dynamic sequences where people manipulate boxes and balloons. That is exactly the substrate needed to separate "the object genuinely changed" from "the model hallucinated." It is in the TUM format, so your existing tooling applies, and it has real timestamps: I verified `rgb.txt` values like `1548266469.85281` (Jan 2019), 439 RGB / 440 depth / 441 mocap poses at 30.0 Hz, 438/439 paired within 20 ms, and depth ÷1000 would give an implausible 14.3 m while ÷5000 gives a sensible **2.86 m** — confirming the TUM factor-5000 convention applies.
**Single biggest risk:** the **license is not stated on the official page** (UNVERIFIED) — your gate demands a clear license, and this is the one item Bonn cannot evidence. Secondary risk: you have already been bitten here (a frame with completely missing sensor GT); I confirmed full GT coverage in `rgbd_bonn_balloon`, but coverage is per-sequence and must be audited for each. Also, Bonn has no explicit leave-and-return/loop-closure labelling — the lab is small, so revisit structure must be constructed by you rather than taken from the dataset.

### 3. ARKitScenes — the pragmatic second real-timestamp source.
**Concrete reason:** if TUM's single-room scale is too limiting, ARKitScenes is the lowest-friction real RGB-D source that also has real timestamps: **no agreement gate at all**, direct Apple CDN, byte-confirmed (`metadata.csv` 200 + `Training/47333462.zip` 200, 64.9 MB), real Apple LiDAR depth in **millimetres** with a `confidence` channel, K in `.pincam` files, timestamp-indexed filenames, and a laser-scanner `highres_depth` GT for a 2,257-capture subset. Per-video zips (~65 MB) let you sample without committing to 623 GB.
**Single biggest risk:** the license is a **custom non-commercial Apple licence** (with a 700 M-MAU commercial clause) — restrictive and not an OSI/CC license, which may fail a "clear license" review that expects CC-BY-style terms. Second risk: poses are **explicitly "estimated ARKit camera poses"**, not mocap ground truth, so any loop-closure-error metric computed against them inherits SLAM drift — use them as a *reference*, not as truth.

---

## 3. MEMORY EVALUATION METRICS

All URLs below were fetched directly.

### 3.1 R2M-Bench — relative revisit memory (the most methodologically careful protocol found)
[arXiv:2608.27328](https://arxiv.org/abs/2608.27328) · [GitHub](https://github.com/AMAP-ML/R2MBench) · [HF data](https://huggingface.co/datasets/GD-ML/R2MBench)
Its central argument is exactly the trap a memory-evaluation project must avoid: *"High similarity between first-visit and return frames does not necessarily show that a video world model remembered the scene; the intervening rollout may simply have changed very little."* A near-static or slow-motion rollout inflates absolute revisit similarity.
- **Protocol:** mine commanded leave-and-return pairs from the pose sequence; compare each pair against two controls **from the same rollout**:
  - *gap-matched baseline pairs* — ordinary long-gap self-similarity at comparable temporal separation;
  - *short-range reference pairs* — consistency available over nearby frames.
- **Revisit pair criterion:** positions within τ_pos, yaw within τ_rot, and temporal gap `j − i ≥ max(0.2T, 10)`.
- **Metrics:** **MemoryGain (MG)** = direct revisit advantage over the gap-matched baseline; **Normalized Memory Ratio (NMR)** = MG divided by the short-to-baseline dynamic range, giving a dimensionless cross-metric score.
- **Five families:** Appearance Fidelity, Scene Identity Preservation, Object Identity, Local Geometric Correspondence, Persistent State Reasoning.
- **Validation:** Overall NMR correlates with human consistency judgements at Spearman ρ = 0.547 (95% CI [0.45, 0.63]); its within-model correlation with generated motion is 0.072 vs **0.207 for raw revisit similarity** — i.e. relative calibration substantially reduces the "slow-motion shortcut". 100 reference scenes × 3 templates (out-and-back, translation–rotation, closed-loop) = 300 instances.
- **Released data:** reference images only (100 PNGs, 181 MB, MIT). You generate the rollouts. **This is a metric harness you can port onto TUM**, where real GT frames exist.

### 3.2 DreamX-World 1.0 — revisit consistency with gain-based scoring
[arXiv:2606.16993](https://arxiv.org/abs/2606.16993) (GitHub: [AMAP-ML/DreamX-World](https://github.com/AMAP-ML/DreamX-World))
- **Revisit pair detection** from camera extrinsics: position **t** and yaw θ; pair requires `|θi − θj| ≤ τθ` (τθ = 2°), `‖ti − tj‖₂ ≤ τt` (τt = 0.1), minimum temporal gap `|j − i| ≥ ⌊0.2T⌋` "to focus on long-horizon memory".
- **Metrics on each revisit pair:** pixel fidelity (PSNR, SSIM), perceptual consistency (LPIPS), semantic identity (DINO-Sim), place recognition (VPR-Sim), geometric structure (SP-Match — SuperPoint keypoints matched with LightGlue, reported as matching ratio `r_match = N_match / min(Ni, Nj)`), plus CLIP-Video as an absolute temporal-smoothness measure.
- **Gain-based scoring:** because "absolute similarity scores can be inflated by slow camera movement rather than genuine memory", all metrics are reported as **gains** over non-revisit baseline pairs with a matched temporal-gap distribution (`S_revisit − S_baseline`, sign-flipped for LPIPS). This is the same insight as R2M-Bench, independently arrived at.
- Model-side memory mechanism worth contrasting against your geometry-aware selector: *geometry-based retrieval* using camera pose + view overlap rather than temporal distance, with memory frames given RoPE embeddings corresponding to their original temporal location.

### 3.3 MIND — revisit MSE and long-context memory loss
[arXiv:2602.08025](https://arxiv.org/abs/2602.08025) · [project](https://csu-jpg.github.io/MIND.github.io/)
- Defines a **memory segment** M = {f1…fT} and an action sequence; the model must predict future frames. Two losses:
  - **Memory consistency:** `L_mem = ‖f̂_t − f_{t'}‖²₂`, where `f_{t'}` is the ground-truth frame at the revisited scene — i.e. a squared error against the *actual earlier view*.
  - **Long-context memory:** `L_lcm = (1/k) Σ ‖f̂_{T+i} − f_{T+i}‖²₂`.
- **Action accuracy:** recover camera trajectories from generated video via **ViPE**, remove scale/coordinate discrepancy with a **Sim(3) Umeyama** alignment, then compute translational and rotational **relative pose error (RPE)**.
- **Also:** LAION aesthetic predictor + MUSIQ for imaging quality; action-space generalization as MSE under varied movement/rotation increments.

### 3.4 MBench — hierarchical memory taxonomy and M-Score
[arXiv:2606.00793](https://arxiv.org/abs/2606.00793) · [project](https://peanutup.github.io/MBench-project/)
- Decomposes memory into **three axes / 12 quantifiable sub-dimensions**: Entity Consistency (Object Consistency, Human Consistency — geometry + texture stability), Environment Consistency (stability of the "stage"), Causal Consistency.
- **M-Score** is a harmonic mean of relational consistency and trigger coverage:
  `M-Score_k = 2 × (S_rel_k × C_trig_k) / (S_rel_k + C_trig_k)` — the stated intent is to "penalize overly conservative models with low trigger coverage while rewarding models that maintain high consistency under frequent, complex world-state transitions." That design directly targets the degenerate "generate nothing, stay consistent" solution.
- Rule-based quantitative matrices + VLM judging; built on real-captured long videos (DL3DV, Tanks and Templates, OpenHumanVID, SpatialVID, Physics-aware-video).

### 3.5 LoopNav — loop-based spatial consistency and SGCS
[arXiv:2505.22976](https://arxiv.org/abs/2505.22976) · [HF](https://huggingface.co/datasets/kevinLian/LoopNav)
- Protocol built around **A→B→A** loops: the A→B segment is the *exploration/context* input and B→A is the *generated* return. **Explore-then-generate** isolation of the future from the context — directly relevant to your "strict isolation of future ground truth from the selector" requirement. Variants include A→B→C→A.
- **SGCS (Scene Graph Consistency Score):** sample aligned frames from generated and GT videos, extract category-wise object masks with **SAM 3**, do **bipartite matching on centroid distance**, and aggregate category-level consistency with **area weighting**. Explicitly designed to be robust to geometric misalignment while capturing object-presence and spatial-layout inconsistency — a useful complement to pixel metrics.
- The paper also documents a **synthetic-perturbation validation** of the metric (colour change, small translation/rotation, scaling, object deletion, object position swapping), plus a "Context Coverage in ABCA" analysis — a good template for validating any memory metric you build.

### 3.6 Classical trajectory metrics — ATE and RPE (what to use for the geometry half)
[TUM RGB-D evaluation tools](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/tools)
- **Absolute Trajectory Error (ATE)** — *"well-suited for measuring the performance of visual SLAM systems"*; the script's default output is the **RMSE absolute translational error in meters after alignment** (so it captures global loop-closure/registration error).
- **Relative Pose Error (RPE)** — *"well-suited for measuring the drift of a visual odometry system, for example the drift per second"*; computes the error in relative motion between pairs of timestamps.
These are the right primitives for a **loop-closure error** term in a world-model setting where you have real poses (TUM, Bonn, WildRGB-D, ARKitScenes) and are the standard against which generated-vs-GT camera trajectories should be scored. Pair them with the revisit-selective protocols above so that "remembered the place" is measured relative to a within-rollout baseline rather than in absolute terms.

### 3.7 Other evaluation surfaces
- **iWorld-Bench memory track** ([HF](https://huggingface.co/datasets/EmbodiedCity/iWorld-Bench-Dataset)): **200 loop-closure tasks** with "cyclic reciprocal-path" structure, alongside 4,000 action-control and 700 camera-following tasks, with aligned `videos/*.mp4` + `cameras/*.txt` (intrinsics/extrinsics). Simulator-rendered, but the task taxonomy is a good design reference.
- **WorldScore** ([arXiv:2504.00983](https://arxiv.org/abs/2504.00983), [HF](https://huggingface.co/datasets/Howieeeee/WorldScore)): evaluates next-scene generation with explicit camera trajectories along controllability / quality / dynamics axes; 3,000 examples incl. 1,000 `dynamic`. Protocol + prompts, not captured video.
- **Omni-WorldBench** ([arXiv:2603.22212](https://arxiv.org/abs/2603.22212)): interaction-centric 4D world modeling with agent-based Omni-Metrics; **data not released** (repo has only README + assets).

---

## 4. DATASETS THAT WOULD UNBLOCK THE PROJECT

### Primary — satisfies the timestamp gate today
**TUM RGB-D, `freiburg3` sequences.** Direct HTTP, no registration, CC BY 4.0, all URLs return HTTP 200 with exact byte counts I verified:

| Sequence | Bytes | Why |
|---|---|---|
| `freiburg3_long_office_household` | **1,483,556,251** | **Primary pick.** Large loop closure, full GT coverage (87.09/87.10 s), 5.12 × 4.89 m extent, 22.20 m path. Verified in bytes. |
| `freiburg3_nostructure_texture_near_withloop` | 781,054,296 | Texture-rich loop closure; full GT (56.48/56.49 s). |
| `freiburg3_nostructure_notexture_near_withloop` | 484,772,347 | **Smallest** loop-closure option; full GT (37.74/37.72 s). Page lists "0.53 GB"; actual Content-Length is smaller. |
| `freiburg3_walking_xyz` | 527,550,055 | **Dynamic people + moving camera** for stale-memory tests; full GT (28.83/28.84 s). |
| `freiburg3_sitting_xyz` | 775,406,859 | Dynamic people, slow motion; full GT (42.50/42.51 s). |
| `freiburg1_360` / `freiburg1_desk` | 417,954,230 / 344,011,403 | 360° turn / "several loop closures"; full GT. |
| `freiburg3_long_office_household_validation` | 1,532,741,250 | Held-out, **but ships NO GT poses** — only for the online tool. |

URL pattern: `https://cvg.cit.tum.de/rgbd/dataset/freiburg3/rgbd_dataset_<name>.tgz`
Self-computed SHA-256 (TUM publishes none) for the primary pick:
`c7cd8e1afb87c80e5744a356214819b110fa09b4744fa4ba0cc2382f9ba59e9c`

**Suggested held-out construction:** hold out `fr3_long_office_household` as the test scene; use the other `fr3`/`fr1` recordings as context. Do **not** use `_validation` sequences as held-out test data if your pipeline needs poses. Build leave-and-return test cases by slicing the mocap trajectory — the revisit structure is genuinely there (109,280 revisit pose-pairs at <0.30 m / >10 s in the primary pick alone).

### Secondary — real timestamps *plus* static/dynamic GT separation
**Bonn RGB-D Dynamic.** `https://www.ipb.uni-bonn.de/html/projects/rgbd_dynamic2019/rgbd_bonn_dataset.zip` — 16,395,422,367 B (16.4 GB), HTTP 200 confirmed. Per-sequence zips 182.8 MB–5.8 GB also confirmed (e.g. `rgbd_bonn_balloon.zip` 243,818,512 B). Static GT point cloud: `rgbd_bonn_groundtruth.zip` (4.0 GB) or `rgbd_bonn_groundtruth_1mm_section.zip` (676,032,657 B). Camera intrinsics are published on the page (fx 542.822841, fy 542.576870, cx 315.593520, cy 237.756098) with distortion d0–d4.

### Tertiary — real timestamps, no gate
**ARKitScenes.** `https://docs-assets.developer.apple.com/ml-research/datasets/arkitscenes/v1/threedod/...` — `metadata.csv` (154,354 B) and per-video zips (e.g. `Training/47333462.zip`, 64,939,565 B) confirmed HTTP 200 without any agreement. 3dod is 623.4 GB, but single videos are ~65 MB so you can sample incrementally.

### Also worth noting
- **Dynamic Replica** publishes a **SHA-256 manifest** (`scripts/dr_sha256.json`) and provides the strongest static-vs-dynamic GT separation (static Replica background + per-frame fg/bg masks + instance seg + flow + trajectories). It is the only way in this survey to *mechanically* distinguish "object genuinely changed" from "model hallucinated" — but it is click-through-licensed, synthetic, and has no real hardware timestamps. `real` split is only 152 MB; `valid` is 106 GB.
- **The gate itself should be revised in one place.** No dataset in this survey publishes checksums *and* real hardware timestamps *and* RGB-D *and* poses *and* a clear license. The single item you will almost certainly have to self-serve is **SHA checksums**: only Co3Dv2 (full SHA-256 manifest) and Dynamic Replica and TartanAir (MD5 for 3 test tracks) publish any. TUM, Bonn, ScanNet, ScanNet++, ARKitScenes and WildRGB-D publish none. Recommendation: replace "dataset publishes checksums" with "we record a checksum manifest at download time and pin it" — otherwise the gate is unsatisfiable by construction.

### Practical size notes for your quota
162 GB free on NFS + 200 GB shared home. Everything recommended fits with enormous margin: TUM primary + all `fr3` extras < 6 GB; all of TUM ≈ 88.6 GB; Bonn full 16.4 GB + static GT 4.0 GB; ARKitScenes is sampled per-video (~65 MB each). Items that **do not** fit comfortably: ScanNet (1.2 TB), ScanNet++ (1.5 TB default), DL3DV (730 GB–44 TB), MBench data (678 GB), MIND (34.8 GB — fits), LoopNav (775 GB), iWorld-Bench (970 GB), PointOdyssey (185 GB), RTMV (675 GB). At `/tmp` I had 381 GB free on the local volume, so stage large downloads there rather than on the shared NFS.

---

## 5. Search queries used

1. `long-horizon memory video world model benchmark revisit loop closure 2026 dataset`
2. `video world model memory evaluation benchmark Revisit Consistency 2025`
3. `RGB-D dataset real hardware timestamps camera poses 2025 SLAM evaluation`
4. `TUM RGB-D benchmark dataset sequences hardware timestamps license download size`
5. `Bonn RGB-D Dynamic dataset ground truth timestamps license download size`
6. `OpenLORIS-Scene dataset RGB-D timestamps license download`
7. `DynaBench dynamic scene dataset benchmark world model`
8. `SpatialVID dataset camera poses depth 2025 world model`
9. `MBench memory benchmark world model 2026 long-horizon`
10. `ScanNet++ dataset license timestamps download access`
11. `dataset long-horizon video world model loop closure revisit RGB-D poses 2026`
12. `SpatialVID large-scale video dataset spatial annotations camera pose depth license size`
13. `CityWalker dataset long video world model 2025 download`
14. `ARKitScenes dataset timestamps license download size`
15. `WildRGB-D dataset download license size poses timestamps`
16. `ScanNet dataset .sens timestamps intrinsics license download size`
17. `TartanAir dataset license download size ground truth depth poses`
18. `Dynamic Replica dataset license download size depth poses`
19. `RealEstate10K dataset license download size poses`
20. `TUM RGB-D dataset license terms of use creative commons`
21. `ICL-NUIM dataset living room office timestamps frame indices download size`
22. `ScanNet++ dataset download request form license timestamps iPhone`
23. `Replica dataset no timestamps frame indices download`
24. `"TUM RGB-D" dataset license CC BY 4.0 terms`
25. `cvg.cit.tum.de datasets license terms of use TUM RGB-D benchmark`

Pages fetched directly (official sources; no `*.ezproxy.*` mirrors used): arXiv abs/HTML for 2602.08025, 2602.02393, 2606.16993, 2608.27328, 2606.00793, 2505.22976, 2504.00983, 2509.09676, 2411.17820, 2603.22212, 2605.03941, 2606.31672; cvg.cit.tum.de (main/download/file_formats/tools/ground-truth); ipb.uni-bonn.de dataset page; doc.ic.ac.uk ICL-NUIM; HuggingFace dataset cards and APIs (CSU-JPG/MIND, GD-ML/R2MBench, studyOverflow/MBench-Data, kevinLian/LoopNav, Howieeeee/WorldScore, SpatialVID/SpatialVID, ai4ce/CityWalker, EmbodiedCity/iWorld-Bench-Dataset, TontonTremblay/RTMV, aharley/pointodyssey, hongchi/wildrgbd); GitHub raw READMEs (ScanNet, ARKitScenes, Replica-Dataset, ReplicaCAD, dynamic_stereo, MVImgNet, DL3DV-10K, wildrgbd); plus raw byte downloads of TUM `fr3_long_office_household` and Bonn `rgbd_bonn_balloon`, and a direct-URL probe of the ICL-NUIM TUM-compatible archive.
