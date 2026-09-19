# S96 本地 RGB-D 数据盘点与最小配对资格诊断

- 记录时间（UTC）：`2026-09-12T11:43:17.838838+00:00`
- 范围：只检查项目内已有数据和来源文件；没有联网，没有加载模型，没有生成新结果。
- 目的：纠正“Gate 0 未通过”与“本地完全没有 RGB-D 数据”的混淆。

## 结论

本地确实存在可读取的 RGB + 16-bit depth + timestamp list + groundtruth pose 数据。最小配对诊断通过 **开发用途资格**，但两个序列都已经在本项目的开发/历史实验中暴露，不能作为 GRC-Memory 的未见确认集；正式 S91 仍保持 Gate 0 阻断。

相机内参使用项目已冻结的 TUM 近似值 `(fx, fy, cx, cy)=(525, 525, 319.5, 239.5)`。这是来源文档中的推荐近似，不是本轮从每帧中重新估计出的精确标定。深度解释为 uint16，除以 5000 转米，0 表示缺失。

## 最小配对诊断（每个序列一对）

### tum_fr1_xyz

- 路径：`/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/data/tum/rgbd_dataset_freiburg1_xyz`
- 暴露状态：**DEVELOPMENT_SEEN**（Used in earlier S5-S8/S14 development and historical diagnostics; not a held-out confirmation set.）
- 文件数量：RGB 798，Depth 798，GT pose 3000 行；文本表对应 RGB 798 / Depth 798 行。
- 样本 RGB：`/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/data/tum/rgbd_dataset_freiburg1_xyz/rgb/1305031102.175304.png`，[640, 480]，模式 `RGB`，类型 `uint8`。
- 样本 Depth：`/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/data/tum/rgbd_dataset_freiburg1_xyz/depth/1305031102.160407.png`，[640, 480]，模式 `I;16`，类型 `uint16`，非零比例 `0.748291`。
- RGB–Depth 时间差：`0.014896870` 秒；RGB–GT 最近时间差：`0.000496149` 秒。
- GT 行结构：8 列（timestamp + 3 平移 + 4 四元数）。
- 结果：**PASS（开发资格）**；不是未见场景验证，也没有运行模型。

### tum_fr2_desk_guard

- 路径：`/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/data/tum/fr2_desk_timestamp_guard/rgbd_dataset_freiburg2_desk`
- 暴露状态：**DEVELOPMENT_SEEN**（Used in S8/S22/S23/S27/S32/S33 and related development diagnostics; not an unseen confirmation set.）
- 文件数量：RGB 2965，Depth 2964，GT pose 20926 行；文本表对应 RGB 2965 / Depth 2964 行。
- 样本 RGB：`/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/data/tum/fr2_desk_timestamp_guard/rgbd_dataset_freiburg2_desk/rgb/1311868164.363181.png`，[640, 480]，模式 `RGB`，类型 `uint8`。
- 样本 Depth：`/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/data/tum/fr2_desk_timestamp_guard/rgbd_dataset_freiburg2_desk/depth/1311868164.373557.png`，[640, 480]，模式 `I;16`，类型 `uint16`，非零比例 `0.676237`。
- RGB–Depth 时间差：`0.010375977` 秒；RGB–GT 最近时间差：`0.000018835` 秒。
- GT 行结构：8 列（timestamp + 3 平移 + 4 四元数）。
- 结果：**PASS（开发资格）**；不是未见场景验证，也没有运行模型。

## 这对科研路线意味着什么

- 可以在本机对已有 TUM 数据做“开发诊断”：例如检查配对、深度单位、投影、指标脚本和失败案例。
- 不能用这些已经暴露的数据给 GRC-Memory 做未见场景确认、校准测试或最终论文主结果。
- 3RScan 仍是候选的新数据来源；它需要完整帧、`_info`、K、单位、pose 和许可边界的实际核验。
- 本文件没有改变主账，也没有把开发诊断写成 S91 或新方法结果。

## 可复核证据

- `docs/S8_DATA_SOURCE_REVIEW.json`
- `data/cut3r/S8_fr2desk_inputs_v2/S8_inputs.json`
- `data/cut3r/S8_fr2desk_inputs_v2/sampling_metadata.json`
- `docs/S22_RESULTS.md`
- `work/S33_scoring_preparation/manifest.json`
- `docs/S32_RESULTS.md`、`docs/S33_RESULTS.md`（fr1/fr2历史开发暴露证据）
- `results/S32_consumer_windows/fr1_xyz_j1/receipt.json`、`results/S33_pair_scale_control/fr1_xyz_j1/receipt.json`

机器可读回执：`local_pair_qualification.json`

