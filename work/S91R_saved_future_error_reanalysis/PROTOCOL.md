# S91R（已保存历史候选与未来深度误差回顾性复算）

## 定位

这是对已经保存的 S15B 几何候选、目标预测和传感器深度结果做一次固定公式的**回顾性 saved-data recomputation**，不是新模型实验，也不是 GRC-Memory 的验证。它只回答一个先导问题：在这一段已见 TUM fr2_desk 数据中，选择前可见的几何候选不一致/置信度，是否与后续目标深度误差有描述性关联。

S15B 的输入和目标数据已经在更早阶段暴露，因此不能称为未见测试、独立场景或确认性实验。未来目标深度仅用于最后的误差统计；风险特征只来自已保存的 proposal 文件。

## 固定输入

- `results/S15B_prefix_proposals/proposals.npz`：old/new self-z、confidence、来源身份。
- `results/S15B_consumer_predictions/target_predictions.npz`：7种已保存消费者输出、source pixel identity。
- `results/S15B_consumer_scores/evaluation_gt.npz`：4个目标深度答案。
- 只分析 `never`（旧候选）和 `all_new`（新候选）两条固定输出，避免把所有方法当新实验。

## 预注册风险特征

对每个来源像素，仅使用 proposal 中的过去可见量：

`risk_disagreement = |new_z - old_z| / (0.5 * (|new_z| + |old_z|))`。

同时报告 `risk_low_confidence = 1 / new_confidence`，但不把它作为主风险定义。正值有限、old/new均有效的像素才有 disagreement；缺失保留为 NA，不填零。

## 未来误差

对每个目标、方法和来源像素，使用保存的预测深度与目标传感器深度计算 absolute relative error `|pred-gt|/gt`。只在 source identity、预测、GT均有效处统计。统计单位是像素和目标帧，不能当作独立场景；按 source 和 target 分层报告。

## 输出和停止条件

输出 Spearman 描述性相关、固定风险五分位的未来误差均值、中高风险与低风险的差值，并报告有效计数。没有显著性、跨场景泛化或方法收益主张。

如果相关方向不稳定、只由一两个目标支配或与 confidence 相反，则不能把“低风险预测未来收益”写成成立假设。正式 GRC-Pilot 仍需 Gate 0 合格的历史—未来 RGB-D 数据、同候选池、同预算和未见场景。
