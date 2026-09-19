# S82 组件输出核验计划

本计划在新四历史输出出现前制定。不同作者检查器为 `check_geometry_outputs.py`；不导入 CUT3R、Torch 或图像解码器，不加载模型、不调用前向。准备阶段只运行人工 pose 例子，不打开新输出。

核验目的限于：既定四历史原始 heads 档案是否完整、身份及元数据是否对应、保存的官方解码位姿与独立公式是否一致。通过不意味着几何质量、相机米制、可渲染性、生成收益或创新通过。

## 冻结检查范围

1. 显式传入执行目录、合同路径及 root 已读的精确合同 SHA；记录执行/监督回执 SHA。核四 ID `[12,13,18,19]`、输入已记 hash/size、解码顺序、输出行和生成槽 `[19,18,13,12]`，不读取四张原图重新验证像素。
2. 核一次模型加载、一次四帧 recurrent 调用、四个 heads、四次图像解码、eval/fresh-state，optimizer/render/generation 为 0；这些依赖实际回执与另行源审，不称独立重跑模型。
3. 每个输出 NPZ 文件 hash/size、全部字段的 shape/dtype/body hash/finiteness 与回执相符。四 head 必须恰六键，点图与 rgb `[1,384,512,3]`、两置信图 `[1,384,512]`、pose `[1,7]`，均 float32。预测相机档案应为四 ID int64、四个 float32 4×4矩阵。预处理档案必须恰四 ID、归一化 images float32 `[4,3,384,512]`、由归一化反变换的 rgb01 float32 `[4,384,512,3]`、四个 float64 3×3坐标/K元数据。范围分别为 [-1,1]/[0,1]，反变换逐值一致，四坐标矩阵与已核合同精确相符。最终作者 schema 没有独立 true_shape 数组：空间维度和 receipt 的 processed_wh 双重核，不新增该字段。本核不读取原图作二次解码。
4. 从各 raw pose 的平移和 wxyz 四元数独立在 float64 归一化后构建旋转矩阵，对比 `PREDICTED_CAMERAS.npz` 与回执中官方 helper 输出；二者自身存储应数值全等。独立公式比较 `atol=2e-6, rtol=2e-6`，与 float32 官方计算区别相容。齐次行应精确 `[0,0,0,1]`；`R.T@R` 对单位阵及 `det(R)` 对 1 使用 `atol=5e-6, rtol=0`。这是数值表示/刚体解码容差，不是任务性能阈值。零四元数不能解码，保留失败。

各字段仅记录 min/max 范围，不按 confidence、深度正负、覆盖或误差删除点。无 GT、无目标 RGB/depth、无筛选，不检验 self/cross 必须刚体相等，不把两点图/预测相机称作已对齐 TUM 世界。

## 执行方式与停止条件

先运行 `--selftest --report GEOMETRY_OUTPUT_CHECKER_SYNTHETIC.json`，仅含五个人工有效 pose 与零四元数拒绝例。其通过只验证检查器的基本公式，不代表对未来真实档案完成核验。

root 完成精确脚本/合同前审并授权读取已完成输出后，才运行真实输出核验：必须显式给 `--execution`、`--contract`、`--contract-sha256`、新的 `--report`。默认不自动读取任何执行目录，也不覆盖已有检查回执。遇字段、hash、解码或执行状态不一致即保存 FAILED，不修原数据、不重跑前向。此检查器先按作者已落盘的接口起草；待作者合同冻结后对照精确 schema 再确认，修改版本及人工检查保留。

最终接口更新：合同 SHA `cb60e53793942e9356eb1935544f490dc4a86be3be330bfdb2fe5abf285b0f46`。RGB 身份 hash-read 为 4 条；checkpoint 只继承已验 SHA 并核 size/mtime，不能要求它出现在新 full-hash 列表。四 RGB 各有 hash+PIL 共两次文件 open，checkpoint 为扫描+load 两次 open；与一次 model load 分开。前版检查器/计划/人工回执保存在 `output_checker_archive_v1/`。
