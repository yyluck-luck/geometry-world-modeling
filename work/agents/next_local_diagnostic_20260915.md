# 下一项本机诊断草案：S103 预测几何扰动的“支持变化 vs 深度变化”分解

记录时间：2026-09-15（本文件为协议草案；以实际运行回执中的 UTC 时间为准）  
作者：root 子任务设计；不是独立方法验证。

## 为什么做这项实验

S102 已确认现有 TUM RGB-D 数据属于 `DEVELOPMENT_SEEN`，不能作为正式的 held-out
测试。S100 已封存 9 对 low-disagreement / confidence 候选、两个固定历史背景、4 个
查询目标的预测，并且发现成对收益的平均值接近零、部分 pair 在两个背景间反号。

现在需要先回答一个更具体、且不需要再次读取未来 GT 的机制问题：

> S100 中 low 与 confidence 替换产生的上下文差异，主要来自可见支持/遮挡覆盖变化，
> 还是来自相同支持上的深度数值变化？

这个问题可以用已经封存的预测深度和 renderer provenance（`source_pixel_identity`）
回答。它不能证明哪一个来源是真实三维正确的，只能解释保存的几何消费者输出发生了什么。

## 数据与边界

- 输入只读取 `work/S100_context_matched_swap/predict_01/predictions.npz`、
  `select_01/SELECTION.json`、`FREEZE.json` 和 `PROTOCOL.md`。
- `predictions.npz` 的字段是 `depth_m[36,4,224,224]` 与
  `source_pixel_identity[36,4,224,224]`；36 个 visit 按冻结顺序对应 pair、source、
  context 和 arm，映射必须从 `SELECTION.json` 重建，不能凭数组位置猜测。
- 本诊断不读取任何新的 RGB、depth GT、pose GT 或未来答案，不运行神经模型，不改变
  S100 的预测/评分文件。
- S100 的 `SCORES.json` 可作为已见结果的标签做事后描述，但不得把它称为新的测试或
  独立证据；主分析先完全不读取该文件。

## 预注册的量

对每个 `(pair, source, context, target)`，取 low arm 与 confidence arm 的成对输出。
令 `V_a` 是预测深度有限且大于零的像素集合，`I_a` 是 source identity。

1. **支持变化比例**：`support_flip = |V_low XOR V_conf| / |V_low UNION V_conf|`。
2. **来源变化比例**：在 `V_low INTERSECT V_conf` 上计算
   `identity_flip = mean(I_low != I_conf)`。identity 是 renderer 来源标识，不是真值。
3. **同来源深度差**：在共同有效且 `I_low == I_conf` 的像素上，计算
   `median_abs_delta_m`、`p90_abs_delta_m` 和相对差的中位数。
4. **总输出差**：在并集支持上报告深度差的均值、p90，以及共同有效像素的
   `relative_depth_delta`。
5. **边界/重影代理**：在共同有效支持上计算 Sobel 或 4 邻域梯度幅值的均值和
   95 分位；只作为图像输出形状变化代理，不称为几何精度。
6. **上下文一致性**：同一个 pair/target 的两个 context，分别形成
   `delta_c = depth_low_c - depth_conf_c`；在两者共同有效区域报告 delta 的 Pearson
   相关（像素不足时为 NA）及余弦相似度。另报告 changed-pixel mask 的 Jaccard。

所有分母、无效像素数、NA 原因和每个 target 的结果都写入 JSON/CSV；不能只报均值。

## 可证伪的机制判据

这不是方法验收，阈值只用于决定本地解释是否被支持：

- **支持主导解释 H_support**：在至少 2/3 个可匹配来源、且至少 3/4 查询目标中，
  `identity_flip` 或 `support_flip` 排名靠前，并且同来源深度差占总差异的比例低于 0.30。
- **深度主导解释 H_depth**：在至少 2/3 个可匹配来源、且至少 3/4 查询目标中，
  `identity_flip < 0.10`，但同来源 `p90_abs_delta_m` 占总差异比例高于 0.50。
- 若两个判据都不满足，结论为 **机制未分辨**，不挑选有利解释。
- 上下文一致性若显示 delta 方向在两个 context 中相似，只说明本覆盖下输出扰动较
  稳定；若 Jaccard/相关很低，只说明存在 context dependence。两者均不能推出未来
  误差改善或因果效应。

“至少 2/3 来源、3/4 目标”是预先固定的描述性门槛，不是统计显著性检验；pair、目标和
像素不能当作独立重复样本，不做 p 值或泛化承诺。

## 运行与输出合同

建议新目录 `work/S103_prediction_geometry_decomposition/`，不覆盖 S100。执行前先保存
输入 SHA256、代码 SHA、NumPy 版本和数组形状；运行脚本可命名为 `run.py`，只使用单线程
NumPy。阶段输出：

- `PROTOCOL.md`（本文件复制并在运行时补充实际 UTC）；
- `INPUT_MANIFEST.json`（路径、SHA、字段、visit 映射）；
- `METRICS_PER_TARGET.csv` 与 `METRICS_PER_TARGET.json`；
- `AGGREGATES.json`（按 pair、source、target 等权聚合）；
- `MECHANISM_DECISION.json`（H_support/H_depth/UNRESOLVED 及触发证据）；
- `RUN.json`、`README.md`、独立复核回执。

自动停止条件：数组形状或 visit 映射不能由冻结文件重建；出现非有限正深度处理不一致；
identity 维度被误当成真实几何标签；脚本尝试读取 GT；输入 SHA 与 S100 封存不符。

## 独立复核与科学边界

独立复核者应从 `INPUT_MANIFEST.json` 和原始 S100 文件重算至少一个 pair 的两个
context、一个 target 的全部量，并核对聚合顺序、无效值处理和 H 判据。复核者不得只读
主脚本输出复述结论。

若 H_support 或 H_depth 被触发，下一步也只能是为 held-out 数据上的正式实验提供一个
可检验的机制预测；不能据此把 GRC-Memory 记为创新、不能替代 S103/S104 的真实 RGB-D
资格门、不能声称跨场景有效。只有合法 held-out RGB-D/pose 通过 Gate0 后，才可用同一
冻结候选池和真实记忆槽位预算比较 GRC 与 recent/random/pose/coverage/utility/
confidence 基线。

