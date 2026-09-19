# Held-out 资格分层与最短 Gate0 方案（补充审计，2026-09-15）

## 结论先行

在本地项目中没有找到 ICL-NUIM 或 SceneNN 的 RGB-D 原始包、解包目录或模型输入记录；找到的 Bonn 文件属于 `rgbd_bonn_static_close_far` 的局部 RGB/depth 响应与派生结果，TUM fr1/fr2 也已经被下载或用于开发。因此当前 **合格的新 held-out 组数仍为 0**。这份审计没有下载新数据、没有解码新帧、没有运行模型，也没有把任何候选送入正式 GRC。

最短可行路线是：在方法和 GRC 配置冻结后，从官方 ICL-NUIM 入口获取一个尚未在本地出现的单一轨迹包，先做数据访问级留出（`data_access_heldout`），再生成不可变 manifest，最后把未来 RGB/depth/pose 与预测完全隔离。由于本轮已经阅读官方数据页，不能宣称“零元数据暴露”；若老师要求零暴露测试集，必须改用此前没有查过页面/序列信息的新采集或由导师提供的组。

## 本地实际账本与资格

| 来源与本地路径/证据 | 原始数据状态 | GT/派生状态 | 许可与字段证据 | Held-out 判断 | 原因 |
|---|---|---|---|---|---|
| TUM Freiburg 1 xyz：`data/tum/rgbd_dataset_freiburg1_xyz/`、`data/tum/rgbd_dataset_freiburg1_xyz.tgz`；下载账本 `data/tum/download_manifest.json` | `raw_seen` | RGB/depth/groundtruth 已可见并进入开发链 | 官方 TUM 页声明 30 Hz、640×480、动捕轨迹并默认 CC BY 4.0；官方格式页定义时间戳、RGB/depth、pose、深度因子 5000 | **不合格** | 已下载并使用，是 development-seen |
| TUM Freiburg 2 desk：`data/tum/fr2_desk_download/`、`data/tum/fr2_desk_timestamp_guard/` | `raw_seen` | 时间戳守卫及轨迹文件已存在 | 同上 | **不合格** | 本地已有原始/派生材料，不能回收为正式留出 |
| TUM Freiburg 3 候选（long office household 等） | `raw_unseen`，但 `metadata_seen` | 未发现原始包 | 官方页给出统一格式/许可 | **不合格（保守）** | S8/S14 已读序列页面并讨论其身份；物理房间关系也未证实 |
| Bonn `rgbd_bonn_static_close_far`：`data/bonn_s15a_history*`、`data/bonn_s15c_depth/`，以及 `results/S15A_*`、`results/S15C_*` | `raw_seen`（局部成员/PNG 响应） | 已产生 history、depth 和 score/prediction 派生物；`data/bonn_s15c_depth/receipt.json` 为局部成员访问记录 | Bonn 官方页说明深度已配准、K 与非零畸变、OptiTrack pose；页面提供科研引用但当前页没有独立数据许可全文 | **不合格** | 同一序列已经被读取和用于 S15A/S15C；不能把剩余未取成员包装成全新组 |
| ICL-NUIM living-room `lr kt0/kt1/kt2/kt3` | `raw_unseen`（本地仅有冻结说明与下载脚本，未发现数据包） | GT 尚未打开 | [ICL 官方页](https://www.doc.ic.ac.uk/~ahanda/VaFRIC/iclnuim.html)说明 RGB-D、camera poses、living-room surface GT；`lr kt0` 1510 帧、30 Hz、51 s，kt2 882 帧、30 Hz、30 s；页面明确 CC BY 3.0 | **候选：`data_access_heldout_pending`** | 官方元数据已读，所以不是 zero-exposure；若在方法冻结后首次取得字节，可作为有记录的 data-access held-out |
| SceneNN 单场景 | `raw_unseen`（本地没有 `*.oni`/`trajectory.log`/scene mesh） | 无本地 GT | [HKUST-VGD 官方仓库](https://github.com/hkust-vgd/scenenn)说明 ONI raw RGB-D、16-bit 深度 mm、`trajectory.log` 帧索引及 camera-to-world 4×4、`asus.ini/kinect2.ini` 内参；教育/科研免费使用 | **候选但被 timestamp 门阻断** | 官方 README 只保证 frame index，没有明确原始时间戳/采样频率；必须先验证时间字段，否则不能支撑 proposal 的时序未来误差 |

### 资格标签含义

- `metadata_seen`：曾读过官网序列名、结构或统计信息；即使没有读像素，也不再是零暴露。
- `raw_seen`：任何原始帧、depth、pose 或其范围响应曾进入本地；正式测试排除。
- `GT_seen`：未来帧对应的深度/pose/surface GT 或由其计算的指标曾被打开；永久排除该帧/序列。
- `data_access_heldout_pending`：字节在方法冻结后首次获得，但公开元数据已提前读过；只有 Gate0 全部通过后才可进入受限实验。
- `zero_exposure_heldout`：此前没有序列/帧/GT 的元数据接触，并有独立来源记录；当前没有任何本地候选达到此标签。

## 官方字段与许可核对

1. **ICL-NUIM**：官方页面明确 living room 提供 depth maps、camera poses、3D surface ground truth，并称兼容 TUM RGB-D PNG；`lr kt0` 为 1510 帧、30 Hz、51 秒，另给 `TrajectoryGT`；页面 License 段明确 CC BY 3.0。页面只证明公开许可与字段，不证明本机尚未下载，后者由本地文件扫描支持。
2. **SceneNN**：官方仓库明确每个场景可有 `oni/<scene>.oni` raw RGB-D、`trajectory.log`（帧索引加 camera-to-world 4×4）和 Asus/Kinect2 内参，深度为 16-bit millimeter；许可段只给教育/科研免费使用，商业用途需联系作者。没有看到原始时间戳格式的保证，因此不能在 Gate0 前把它当作时间对齐数据。
3. **Bonn**：[官方发布页](https://www.ipb.uni-bonn.de/data/rgbd-dynamic-dataset/)说明 24 dynamic + 2 static、OptiTrack Prime 13 pose、深度已注册到 RGB、RGB 相机畸变参数非零，并给出坐标变换链。官方页当前未给独立数据许可文本；无论许可是否随后确认，当前本地 `static_close_far` 已被使用，不能作 held-out。
4. **TUM**：[官方基准页](https://cvg.cit.tum.de/data/datasets/rgbd-dataset)说明 30 Hz 640×480 RGB-D 与动捕 ground truth，默认数据 CC BY 4.0；[官方格式页](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats)明确 RGB/depth 预注册、PNG 深度因子 5000、pose 行格式 `timestamp tx ty tz qx qy qz qw`。本地 TUM 目录已有开发使用，不能回收为正式 held-out。

## 最短可执行 Gate0（ICL-NUIM 首选）

### A. 方法冻结与访问边界

在取得包之前，保存 GRC selector、候选池、预算 `k`、风险阈值、随机种子、预测步长与输出路径的 SHA；禁止打开任何未来 RGB/depth/pose/GT。保留 `work/S102_gate0/ICL_NUIM_HELDOUT_FREEZE_20260915.md` 作为冻结说明。下载只允许进入一个新的、版本化的目录，例如 `datasets/icl_nuim/v1/`，不能覆盖 `data/` 开发目录。

### B. 小而完整的来源选择

优先选择 `lr kt2`（官方页面标称 882 帧、约 1.9 GB）或当前已冻结的 `lr kt0`（1510 帧、约 3.3 GB）。选择只能依据事先记录的预算与完整 RGB-D/pose/GT 字段，不依据结果。ICL 是 synthetic benchmark，报告中必须单独标记，不能把它当作真实传感器泛化证据。注意：官方页的锚点文件名可能是 `living_room_traj2_loop.tgz` 这类命名，不能从“kt2”标签猜 URL；下载前必须打开对应官方锚点并把最终 URL、HTTP 响应与哈希写入 receipt。若沿用已冻结的 `lr kt0`，只使用 `work/S102_gate0/fetch_icl_nuim.sh` 中记录的确切 URL。

### C. 不可变 acquisition receipt

记录：官方 URL、开始/结束 UTC、HTTP 状态、实际字节数、ETag/Last-Modified（若有）、完整包 SHA-256、命令、运行主机和下载脚本版本。若官方 URL、大小或哈希异常，停止，不解包、不评分。

### D. 解包后的结构 Gate0

只做结构和配对检查，不运行 VMem/CUT3R/GRC：

- RGB、depth、pose 的 frame identity 一一对应；
- 时间顺序可由官方 timestamp 或冻结的 30 Hz 帧时间规则解释；
- 相机内参、pose 坐标约定、深度单位（ICL/TUM-compatible 因子）记录并通过独立脚本检查；
- calibration/development 与 future held-out frame 列表在任何 GT 打开前生成并哈希；
- 未来 GT 目录权限/路径与预测输出分离，预测 seal 先写，之后才允许读取 GT；
- 任何坏帧、缺帧、重名、时间倒序、深度单位不明或 pose 解析失败都使状态回到 `BLOCKED`。

### E. 建议的最小 manifest（模板，不是通过结果）

```json
{
  "schema": "GRC-gate0-heldout-v1",
  "dataset": "ICL-NUIM",
  "sequence": "lr_kt2",
  "source_url": "https://www.doc.ic.ac.uk/~ahanda/VaFRIC/iclnuim.html",
  "license": "CC BY 3.0 (official page)",
  "exposure_class": "data_access_heldout_pending",
  "metadata_seen_before_acquisition": true,
  "raw_bytes_seen_before_acquisition": false,
  "gt_bytes_seen_before_prediction_seal": false,
  "official_frame_rate_hz": 30,
  "official_frame_count": 882,
  "rgb_depth_pose_pairing": "PENDING",
  "timestamp_contract": "PENDING",
  "intrinsics_depth_scale_pose_convention": "PENDING",
  "archive_sha256": "PENDING",
  "split_sha256": "PENDING",
  "prediction_seal_sha256": "PENDING",
  "gate0_status": "BLOCKED_UNTIL_RECEIPT_AND_STRUCTURE_CHECK"
}
```

### F. 正式 GRC 的硬门

只有当 receipt、结构配对、许可、曝光审计、split hash、GT 隔离和独立复核全部为 PASS，才可把 Gate0 状态改为 `PASS_DATA_ACCESS_HELDOUT`。这仍然只能支持“数据访问级 held-out”结果；跨场景方法结论至少还需要另一个独立来源并完成同样审计。当前 `work/S102_gate0/GATE0_RESULT.json` 的 `BLOCKED_DEVELOPMENT_DATA_NOT_HELD_OUT` 必须保持不变。

## 本轮实际动作与可复核文件

- 时间：2026-09-15 02:49:26 +08:00（2026-09-14 18:49:26 UTC）。
- 读取本地目录清单，确认 Bonn/TUM 实际文件；搜索未发现 ICL-NUIM 或 SceneNN 原始数据包。
- 读取并核对 `work/S102_gate0/ICL_NUIM_HELDOUT_FREEZE_20260915.md`、`work/S102_gate0/GATE0_RESULT.json`、`docs/S14_NEW_SCENE_IDENTITY_AUDIT.md`、`docs/S14_BONN_METADATA_ACCESS_RESULT.md` 与 Bonn/TUM receipt；没有修改既有结果。
- 只读官方页面：ICL-NUIM、SceneNN、Bonn RGB-D Dynamic、TUM RGB-D benchmark 及 file formats；没有点击整包下载，不解码新照片/GT。
- 对冻结 ICL `lr kt0` 入口做了仅响应头的 `curl -sSIL` 可达性检查（2026-09-14T18:54:25Z）：HTTP 200、`Content-Length=711444709`、`Content-Type=application/x-gzip`、ETag=`"2a67c8e5-511158e8acdc0"`、`Last-Modified=Thu, 12 Mar 2015 11:19:27 GMT`；没有读取正文。该响应头只证明当前 URL 可达，不替代整包 SHA 或内容许可核验。
- 本轮引用的本地账本 SHA-256：`data/bonn_s15a_history/receipt.json`=`09b5f6cb8713c9c3cc6a41facf0293abee6dda104044c4b19a43d0c0623c3d22`；`data/bonn_s15c_depth/receipt.json`=`7795b64d637175532c82e9fce2deecc603005ca8a01685554220d6cfcb85c04c`；`data/tum/download_manifest.json`=`bca355ff124cea0a11a1b1d3483a74fff6b476307eeb046ec91c45410b4ef386`；既有 Gate0 结果=`work/S102_gate0/GATE0_RESULT.json`=`79b8240ff9ca7365b59b03b2563750fc6c00677192785780633103bea4df1e27`；ICL 冻结=`work/S102_gate0/ICL_NUIM_HELDOUT_FREEZE_20260915.md`=`27deacd97cd1fd1a5fda57e869b3dcae2dc356380d724cd891984d99109b4257`。
- 新增本文件；写入后应由根任务重新计算 SHA，并将 SHA 加入中心交接记录。

## 给根任务的决定

1. 立即决定：`formal_GRC_allowed=false`，直到有新的、通过 Gate0 的 held-out 来源。
2. 最短路线：保留 ICL-NUIM `lr kt2` 为 data-access held-out 候选，先冻结方法与 receipt，再在有足够磁盘/学校 GPU 环境时下载；不要把当前 TUM、Bonn 或任何 S102 development 结果送入正式 GRC。
3. 若坚持“零元数据暴露”或真实场景要求，当前公开候选都不够：需要导师/实验室提供新采集 RGB-D+pose，或先获得另一公开来源的明确许可、时间戳与房间独立证据。
4. SceneNN 可作为第二候选，但 timestamp contract 未解决；Bonn dynamic 其他序列需先做本地历史曝光审计及许可核验，不能因为尚未下载某一个 ZIP 就称其 held-out。
