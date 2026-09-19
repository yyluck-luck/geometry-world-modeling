# S91R（已保存历史候选与未来深度误差回顾性复算）结果

## 一句话结论

在一个已经暴露过的 TUM `fr2_desk` 单段中，保存的 old/new 几何候选相对不一致度与后续目标深度的绝对相对误差呈**正向描述性相关**。这支持“风险值得继续测量”这个假设，但不能证明 GRC-Memory、不能证明跨场景泛化，也不能称为新实验的确认结果。

## 实际运行

- 运行时间：以本次 `run_s91r.py` 运行回执和主研究日志为准。
- 输入：已保存的 `proposals.npz`、`target_predictions.npz`、`evaluation_gt.npz`。
- 没有新模型调用、没有联网、没有改变历史预测、没有读取新的图片或深度。
- 仅分析 `never` 与 `all_new` 两个已经保存的消费者输出。
- 独立复算 `verify_s91r.py` 对 32 个 method×target×source 组合逐项重算，全部通过 `S91R_INDEPENDENT_RECOMPUTE_PASS 32 True`。

## 主要数值

`risk_disagreement = |new_z-old_z| / (0.5(|new_z|+|old_z|))`，只使用提案阶段保存的 old/new 几何；未来误差是保存的目标深度上的 `|prediction-GT|/GT`。

- `never`：32 个有效来源组合的 Spearman 相关均为正；范围约 **0.088–0.633**。
- `all_new`：32 个有效来源组合的 Spearman 相关均为正；范围约 **0.154–0.497**。
- 固定过去风险五分位后，高风险组未来误差均值高于低风险组的组合占多数，但差异受来源、目标、覆盖率和同一场景结构影响。
- 低置信度特征也常与误差正相关，说明 disagreement 可能不是独立的新信号；正式 GRC 必须和 confidence-only、coverage、pose-distance、recent 等基线做增量比较。

## 审稿式解释

这个结果可以支持的最强表述是：

> 在一个已暴露的单段数据上，过去可见的 old/new 几何不一致度与未来深度误差存在稳定的描述性正相关，值得在严格未见场景上继续检验。

不能支持的表述包括：

- GRC-Memory 已经有效；
- 低风险记忆一定改善未来世界状态；
- 已经完成跨场景实验；
- 已经证明新颖性、理论保证或 PhD/CCF-A 水平。

## 下一步

1. 将该结果作为 GRC-Pilot 的先导信号和风险特征设计依据，不修改正式 Gate 0 合同。
2. Gate 0 通过后，用同候选池、同 `k`、同消费预算比较 `recent/random/pose-distance/coverage/utility-only/confidence-only/risk-only/risk+utility`。
3. 如果 risk+utility 在未见场景没有超出 confidence-only 或 coverage，停止 GRC 方法主张，保留这个负结果。
