# S91R-C（已保存数据的增量风险与有符号未来收益控制审查）

## 目的与边界

这是对 S91R（已保存历史候选与未来深度误差回顾性复算）的**一次固定控制分析**。它只问两个问题：

1. S91R 的计数、风险分位数和有效掩码是否正确；
2. 几何 old/new 不一致度在控制新置信度、深度、局部深度边缘、confidence-mask 和相机位移后，是否仍能预测 `all_new` 相对 `never` 的**有符号未来误差变化**。

它不训练 GRC-Memory，不选择阈值，不修改原始预测或 `results.json`，也不把相关性当成方法验证。

## 固定输入和计数

使用 S91R 已封存的 `proposals.npz`、`target_predictions.npz`、`evaluation_gt.npz`，另读取已保存的 `target_camera_inputs.npz` 获得查询相机。S91R 有 2 个方法 × 4 个目标 × 4 个来源 = **32 个分层组合**；因此每个方法是 16 个组合，而不是 32 个。像素数只作为有效像素分母，不作为独立实验数。

## 固定公式

对目标像素 `u`，仅在 `never` 和 `all_new` 都有正深度且 GT 有效时配对：

\[
 e^m(u)=|\hat d^m(u)-d^*(u)|/d^*(u),\qquad
 y(u)=e^{never}(u)-e^{all\_new}(u).
\]

`y>0` 表示 `all_new` 改善，`y<0` 表示变差。风险特征使用 `never` 输出所选历史 source identity 对应的过去量：

\[
 D(u)=|z_{new}-z_{old}|/[0.5(|z_{new}|+|z_{old}|)].
\]

控制变量固定为：`1/new_confidence`、`log(new_z)`、新深度图的归一化局部梯度、`model_confidence_mask` 和 source-to-query 相机平移距离。`source_valid` 在保存数据中对四个来源全为 1，因此不作为可变控制变量。所有特征只从 proposal、source mask 和已知查询相机读取；GT 只用于最后的 `y`。

用固定的留一目标（4 个目标）交叉验证比较两个线性 ridge 预测器：

* `M0`: controls → `y`；
* `M1`: controls + `D` → `y`。

ridge `alpha=1e-3` 固定，标准化参数只从训练目标计算；不调参、不看测试目标改规则。输出每个留出目标的 MSE、R² 和 `ΔR²=R²(M1)-R²(M0)`，以及 `y` 的均值、median、改善比例和 `never/all_new` source identity 相同的比例。

## 分位数泄漏审计

S91R 原始脚本先用同时满足预测和 GT 有效的像素计算风险五分位边界。这个做法会让未来 GT 有效掩码参与风险分组。S91R-C 从每个来源全部 finite、positive old/new proposal 像素计算边界，再把固定边界应用于未来有效配对像素；同时保留原始边界作差异记录。该修正只用于审计，不回写 S91R。

## 预先固定的否决规则

* 若 `never` 与 `all_new` 的 source identity 配对比例很低，D 只表示“旧输出所选 source 的风险”，不能解释为同一记忆条目的因果效应；报告停止 GRC 方法主张。
* 若 4 个留出目标中至少 3 个没有正 `ΔR²`，或平均 `ΔR²≤0`，则没有增量预测证据。
* 若加入 D 后不能稳定超过只用 confidence、深度、边缘、mask 和 pose 的控制模型，则 disagreement 不能称为独立新信号。
* 无论控制结果如何，单段已见数据、保存预测和未来答案回顾性读取都不能证明跨场景 GRC-Memory 或新颖性。

