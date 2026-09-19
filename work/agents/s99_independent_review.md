# S99 独立复核报告（2026-09-14）

## 结论

独立复核通过，S99 的几何重投影和评分账本可复现；科学判定仍为：

`STOP_LOW_DISAGREEMENT_ADVANTAGE_IN_THIS_SETTING`

这不是 GRC-Memory 方法验证，也不是新模型或视频生成实验。数据来自已经暴露的 S15B 单段、4 个相关目标。

## 第一阶段：读取 GT 之前的复核

独立脚本 `work/agents/s99_independent_recompute/pre_gt.py` 没有导入 `consumer.render`，只读取冻结文件、proposal、给定目标相机、选择 mask、已封存预测和历史端点。检查结果：

- 预测封存状态为 PASS，封存声明 `evaluation_gt_read=false`。
- FREEZE、预测 RUN、PREDICTION_SEAL 和全部封存文件 SHA 一致。
- 25×4 预测形状和 source-ID 形状正确，39 blocks/source 约束正确。
- `never`、`all_new` depth 与 source provenance 均逐元素等于原 S15B 端点。
- 对 target 20 的 low-disagreement 条件，独立 z-buffer 投影访问 148,928 个 source visits；depth 和 source-ID 与封存预测逐元素完全相等。
- 共 27 项预测前检查，0 项失败；此阶段未读取 GT。

## 第二阶段：读取 GT 后的独立评分

在预测前检查通过后，独立脚本读取已封存 `evaluation_gt.npz`，重新计算 25 条件×4 目标共 100 行：共同域 mean AbsRel、fractional worst-5% AbsRel、MAE、coverage、delta1_all_gt、source-ID 变化、lost/gained 计数和 pairwise signed benefit。fractional worst-5% 按误差降序，并对 5% 边界做小数权重。

结果与 S99 官方 `SCORES.json` 全部一致：

- 1,896 项独立断言通过，0 项失败。
- 100/100 行身份与指标一致，最大浮点差为 0。
- 25 条条件的 mask 选择、39 blocks/source、low/high/confidence 排序和 20 个 PCG64 随机 seed 全部独立重算一致。
- 目标聚合和最终判定一致：`STOP_LOW_DISAGREEMENT_ADVANTAGE_IN_THIS_SETTING`。

## 关键聚合结果

| 条件 | 共同域 AbsRel | 共同域 worst-5% AbsRel | coverage | delta1_all_gt |
|---|---:|---:|---:|---:|
| never | 0.079769 | 0.425196 | 0.703919 | 0.660420 |
| all_new | 0.088932 | 0.711486 | 0.721472 | 0.666288 |
| low_disagreement | 0.079561 | 0.426901 | 0.704997 | 0.661263 |
| high_disagreement | 0.081865 | 0.473196 | 0.711147 | 0.664624 |
| confidence_gain | 0.078365 | 0.429155 | 0.705474 | 0.662163 |
| random 20-seed mean | 0.079978 | 0.447109 | 0.709441 | 0.664406 |

low-disagreement 相比 random 均值只在目标 20、21、23 更低，目标 22 更高；虽然四目标等权共同 AbsRel 略低于 random，但它在四目标均不优于 `confidence_gain`。因此预设门不通过。`high_disagreement` 没有反转胜过 low-disagreement 的风险顺序，但这不能挽救 low-D 相对普通 confidence 对照的失败。

逐目标 low-D 相对 random 的共同 AbsRel 差（random−low，正值代表 low-D 更好）：

- target20：`+0.001111`，随机20次中 low-D 更好 17 次；
- target21：`+0.000328`，12 次；
- target22：`−0.000330`，7 次；
- target23：`+0.000559`，13 次。

low-D 相对 confidence_gain 在四个目标均为负：`−0.000718、−0.000874、−0.001991、−0.001199`。这说明在本设置下，低不一致度没有超过普通置信度增益排序。

## 审稿式解释

本次结果支持的最强结论是：在固定每源 39/196 个 source block、已知查询相机和几何 z-buffer 的回顾性消费者诊断中，low-disagreement 更新相对随机更新有轻微且不稳定的共同域误差差异；它没有超过 confidence_gain，因此本设置不保留低-D 排序优势主张，也不据此否决所有 GRC 方向。

不能据此声称：

- 几何不一致度已成为独立风险信号；
- 单条记忆的因果收益已被识别；
- GRC-Memory 已验证；
- 有跨场景、未见数据或视频质量提升；
- 已达到 PhD/CCF-A 水平。

source-ID 变化、可见性和 z-buffer 竞争仍是主要混杂。39 blocks/source 是几何网格改写预算，不是记忆槽数 `k`；实际比例是 19.897959%，不是精确 20%。

## 证据文件

- 预测前复核：`work/agents/s99_independent_recompute/pre_gt/PRE_GT_RESULT.json`
- 独立评分：`work/agents/s99_independent_recompute/score/SCORE_RECOMPUTE_RESULT.json`
- 独立脚本：`work/agents/s99_independent_recompute/pre_gt.py`、`score.py`
- 原始协议和结果：`work/S99_fixed_budget_risk_update/PROTOCOL.md`、`predict_01/`、`score_01/`

所有原冻结文件和原 S99 输出均未修改。
