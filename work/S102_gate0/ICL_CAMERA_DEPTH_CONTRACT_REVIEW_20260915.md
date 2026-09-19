# ICL-NUIM camera/depth contract review (Gate 0 evidence)

更新时间：2026-09-15 09:52:36（Asia/Shanghai；UTC 01:52:36）。本文件把官方格式说明与官方 MATLAB 源码分开记录，目的是在正式 GRC 前冻结可审计的读取约定。它不是数据质量通过，也不是方法结果。

## 已核实的官方约定

TUM 官方格式页（<https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats>，访问 2026-09-15）说明：RGB 为 640×480、8-bit、PNG；深度为 640×480、16-bit 单通道 PNG；RGB 与 depth 已由 OpenNI 预配准、像素一一对应；16-bit 深度以 5000 缩放，5000 表示 1 m，0 表示缺失。该页还给出针孔反投影 `Z=d/5000, X=(u-cx)Z/fx, Y=(v-cy)Z/fy`，并说明轨迹文本每行是 `timestamp tx ty tz qx qy qz qw`。这些是数据格式的外部证据，仍需在本地抽样解码核对。

ICL 作者代码页（<https://www.doc.ic.ac.uk/~ahanda/VaFRIC/iclnuim.html> 与 `codes.html`）说明 ICL 有 living/office 场景和手持轨迹；作者 `getcamK.m` 使用 MATLAB 1-index 光学中心 320.5/240.5，native POV-Ray 的 `fy` 可为负；`compute3Dpositions.m` 明确将 native radial Euclidean depth 转换为相机轴向 z。`computeRT.m` 的 R/T 是由相机位置和朝向构造的 camera-to-world 变换。

## 冻结候选读取合同（待抽样验收）

| 项目 | 候选合同 | 资格状态 |
|---|---|---|
| PNG 深度 | 读取 uint16；`0` 设为 invalid；`z_m=d/5000` | 文档支持，实际像素抽样待做 |
| 坐标 | 0-index `cx=319.5, cy=239.5`；默认 K 仅在没有 ICL 专用 K 时使用 | 待确认 archive 是否 TUM-compatible |
| ICL 专用 K | `[[481.20,0,319.50],[0,-480.00,239.50],[0,0,1]]`；native 合同保留负 `fy` | 官方 ICL codes 页面支持，需在实现中显式记录 |
| 反投影 | `X=(u-cx)z/fx, Y=(v-cy)z/fy, Z=z` | 代数单测可做，物理精度未证明 |
| native `.depth` | 先 radial→z，再与 RGB 像素对齐；不能对已是 TUM PNG 的 z 再转换 | 仅适用于 native 文件 |
| pose | 轨迹文本字段按 TUM 格式读取；ICL 30 Hz 只能作为数据集帧序的相对时间 | 绝对硬件时间缺失，需写入限制 |
| GT 隔离 | 只在冻结 split 后读取未来 GT 做最终评分；选择器训练/阈值校准不读取未来 GT | Gate 0 必须证明 |

## 关键风险与停止条件

不能把“官方格式页写明 5000”直接等同于当前 tar 中每个 PNG 已被正确读取；必须在取得归档后对少量 RGB/depth/association/pose 做 dtype、尺寸、非零比例、时间顺序和数值范围检查。若文件不是 TUM-compatible PNG，切换到 native 合同并重新记录。若未来 GT 参与候选选择或校准，正式 GRC 立即停止并重建 split。单一 living-room 轨迹不构成跨场景泛化。

## 证据索引

- `official_camera_sources_20260915/getcamK.m` SHA256 `2344bc9fd0e2f3227f39b59e86694cedab7adc9742d3d4fb6ae3dffafd355d36`
- `official_camera_sources_20260915/computeRT.m` SHA256 `3a058ee67156e3c5d1f171a25e14284868ae8aa995d78764145124b07ed2bbe2`
- `official_camera_sources_20260915/compute3Dpositions.m` SHA256 `aac993838fa28732032430862e03d0ede913daad67016de8701d96473444dca1`
- `ICL_NUIM_MAPPING_MANIFEST.json`（当前配对审计）
- `ICL_NUIM_GATE0_DECISION.json`（整体仍阻断）
