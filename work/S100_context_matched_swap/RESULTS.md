# S100 固定上下文成对替换结果

## 实验名称

固定背景下低几何不一致度候选与 confidence 候选的成对替换（已见 S15B 几何消费者诊断）。这是机制诊断，不是 VMem 新模型训练或完整视频生成。

## 运行事实

- 运行前审查：`work/agents/S100_final_prerun.md`，结论 `S100_FINAL_PRERUN_PASS`。
- 冻结后选择：9 对，来源 0/1/3；来源 2 在冻结 caliper 下无合格配对。
- 每对 2 个固定背景、2 个替换臂、4 个未来查询；共 144 次主重渲染，0 次新增神经推理。
- 预测先封存（`predict_01/SEAL.json`），之后才读取已见 GT 并评分。

## 主要结果

定义 `B = capped_loss(low) - capped_loss(confidence)`，正数表示低不一致度替换较好。跨来源、配对、背景和目标的冻结聚合平均值为：

| 全 GT 截断上限 | 平均 B |
|---:|---:|
| 0.5 | -0.00000228936 |
| 1.0 | +0.000000121567 |
| 2.0 | +0.00000735581 |

36 个 pair-target 组合中有 8 个在两个背景之间发生符号反转；该计数在三个截断上限均为 8。平均值接近零并随截断上限改变符号，因此不能解释为稳定、实用的选择收益。

## 允许的科学结论

在这个已见场景、保存几何消费者、近似改变量匹配和有限背景下，替换收益会随其它历史块的上下文变化；这是值得继续检验的局部机制线索。

## 明确不能说

不能说已经证明“低几何风险记忆”优于 confidence，不能说发现了可泛化的记忆交互或因果效应，不能说 GRC-Memory、完整 world model、跨场景性能或 PhD/CCF-A 水平已经成立。当前 `new_method_validated=false`、`novelty_authorization=NONE`。正式 S91 仍等待合法未见 RGB-D/pose 数据和真实记忆槽位预算。

## 原始证据

`PROTOCOL.md`、`FREEZE.json`、`select_01/SELECTION.json`、`predict_01/SEAL.json`、`score_01/SCORES.json`、`work/agents/S100_claim_boundary.md`。
