# ICL-NUIM synthetic scope and generalization boundary

更新时间：2026-09-15 11:13（Asia/Shanghai）。

ICL-NUIM 是许可清楚、带 RGB-D 和轨迹的 synthetic benchmark。本轮选用的是单个 living-room 场景的一条轨迹（1508 个有效配对帧）。它可以用于检查：

1. 记忆选择是否在固定候选池与固定预算下改善未来深度/位置误差；
2. 选择器是否只使用过去观测与查询相机；
3. 深度、相机和时间合同是否可复现。

它不能单独支持以下结论：真实 Kinect/手机传感器泛化、跨房间泛化、动态物体鲁棒性、长期遮挡恢复，或对所有 world model 的普遍改进。单场景的 held-out test 只表示时间段未用于调参，不表示 scene-level independence。

## 与 proposal 的关系

proposal 的目标是长时程几何一致性。ICL-NUIM 可作为“几何真值可得的受控测试源”，但必须与至少一个真实 RGB-D/动态或跨场景来源分开报告。若真实来源不能通过许可、配对和时间审计，则论文只能声称 synthetic controlled evidence，不能声称真实世界泛化。

## 报告规则

- synthetic 结果单列，不能与 TUM/Bonn 等真实数据平均成一个数字。
- scene、trajectory、split、预算和候选池全部写入 manifest。
- 未来 RGB/depth/pose 只在预测和选择结果封存后打开。
- 若核心假设在 synthetic held-out 上不成立，停止 GRC-Memory 方法主张；不能用跨场景或视觉好看替代失败。
- 若 synthetic 成立但真实跨场景失败，结论限定为受控 synthetic 条件，不包装为通用方法。

证据：`ICL_SPLIT_AND_GT_ISOLATION_MANIFEST_20260915.json`、`ICL_NUIM_GATE0_DECISION.json`、`ICL_SAMPLE_DECODE_RECEIPT_20260915.json`。
