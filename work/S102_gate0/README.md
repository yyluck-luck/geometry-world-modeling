# 未见 RGB-D／相机配对资格审计（S102）

状态：`PREPARATION_ONLY_NOT_RUN`（2026-09-15）。没有新的数据读取或服务器运行。

## 目的

在任何 GRC、VMem 或未来误差评分前，证明候选序列具有可追溯的 RGB、depth、时间戳、内参 K、外参/pose 和深度单位，并且该序列没有用于当前方法选择。

## 每帧不可变字段

`sample_id`、`rgb_path`、`rgb_sha256`、`rgb_bytes`、`depth_path`、`depth_sha256`、`depth_bytes`、`rgb_timestamp`、`depth_timestamp`、`delta_t`、`width`、`height`、`depth_dtype`、`depth_scale`、`depth_invalid_codes`、`K_sha256`、`pose_sha256`、`coordinate_frame`、`split_label`、`permission_evidence`。

## 自动停止条件

- 缺 RGB/depth 文件、SHA 不一致或尺寸不一致；
- 时间戳来自文件名猜测，或一对多/重复配对未解释；
- K、pose 方向、坐标系或深度单位无法从原始资料核验；
- `split_label` 不是明确的 `HELD_OUT_TEST`；
- 任何未来 depth/pose 在 selector、调参或预测封存前被读取；
- 许可、场景连续性或 reference/rescan 语义未核验。

## 允许通过的最小证据

1. 原始 timestamp 配对表和固定阈值；
2. 每个序列完整 RGB-D manifest 与 SHA；
3. K、pose、分辨率、单位和坐标系原始来源；
4. 有效深度统计与无效值统计；
5. 发展/校准/测试划分证明；
6. 一组人工可读的重投影边界样例；
7. 独立复核脚本和 `GATE0_RESULT.json`。

## 与原 proposal 的关系

S102 不是 proposal 的性能实验，而是进入 Week 10–12 evaluation 的数据资格门。Gate0 失败时，只记录数据阻断，不运行正式 S91 或 GRC-Memory。
