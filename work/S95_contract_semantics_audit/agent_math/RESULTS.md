# S95 Contract Semantics Audit — independent mathematical review

审查时间：2026-09-12（实际记录时间以文件 mtime 与主账为准）  
审查范围：`work/S94_evaluation_contract_review/EVALUATION_CONTRACT.md`、`.json`、`validate_contract.py`。  
性质：**协议数学审查，不是模型实验、数据实验或新方法结果**。

## 结论

S94 的离线验证器成功，只能证明若干字段存在和三个基本布尔约束。它没有检查下面的语义，因此不能把 `S94_CONTRACT_OFFLINE_PASS` 解释成评价合同已足够严密。以下问题都可修复，不改变 S94 仍为 `PROTOCOL_ONLY / NOT_RUN` 的状态。

|问题|严重性|可复现证据|建议修复|
|---|---|---|---|
|`k=8` 与 Gate 0 的最少 6 个候选不相容|阻断敏感性|`C(6,8)=0`，见 `audit_cases.py`|把 Gate 0 候选下限提高到 8（实际建议更高），或把 `k=8`改成候选池比例/只在 `N>=8` query 报告；禁止静默补候选|
|`worst-5%` 与严格 `x>q95` 的 CVaR 未定义|阻断尾部主指标|94 个 0、5 个 1、1 个 10：top-5 均值=2.8，严格超分位尾均值=10；全相同误差时严格尾为空|预先定义有限样本 top-tail 的分数（含分位点、线性插值和 fractional tie）；建议 CVaR 用 top-5% 的积分/加权平均，空尾不允许返回 NA 而要有明确规则|
|5 条 trajectory 不能自动支撑 0.05 级确认性结论|重要统计限制|全 5 条 paired difference 都为负时双侧精确 sign p=1/16=0.0625；cluster bootstrap 仍只反映 5 个簇|合同写明 n=5 仅为最低描述性确认门；若要假设检验/稳定性主张，预注册 exact paired/randomization test 的目标、效应阈值和功效，或增加 trajectory 数|
|风险分位数的边际覆盖不能推出选择后的条件安全|重要方法限制|校准总体错误率 5% 可以与一个被选择子组的错误率 100% 同时成立；见脚本固定构造|若声称“风险上界”，冻结 subgroup/scene/selection 条件并报告 conditional risk；否则只称 marginal calibration，增加 risk-coverage 与 post-selection 分层评估|
|`q_i=Q(r_i)` 未规定残差标度/合成方式|阻断可复现性|同一误差向量在深度 m 与 mm 表示下和式从 2.1 变为 102；排序与分位数可变|为每个分量冻结单位、归一化、聚合函数、校准样本和 tie-break；跨模态向量不要直接做无量纲相加|
|“未来相机”与“未来答案”没有按信息可用时间区分|重要协议歧义|请求相机可由实验计划提前给定，也可由实际未来位姿产生；两种情况对选择器信息集不同|在 `FREEZE.json` 中记录 `camera_available_at` 和 provenance；允许预先发布的 query camera，禁止从未来帧读取的实际 pose/depth/mask/error；按可用时间而非字段名称隔离|

## 已运行的独立检查

```text
python3 work/S95_contract_semantics_audit/agent_math/audit_cases.py
S95_CONTRACT_SEMANTICS_AUDIT_PASS
```

脚本只使用 Python `Fraction`、组合数和穷举小样本，不加载模型、不读项目数据、不访问网络。它覆盖：尾部指标 ties、全相同误差、5 簇 bootstrap/sign-test、`k=8` 候选不足、边际与选择后覆盖反例、单位缩放不变性。

## 不能由本审查推出的结论

本审查没有证明 GRC-Memory 无效，也没有证明它有效；没有运行 S91，没有获取新 RGB-D/pose，没有修改 S94 主合同。它只表明：正式实验前必须把这些语义写进新合同版本或补充冻结字段，否则结果的解释空间会在看见答案后变大。

## 推荐的最小补丁顺序

1. 先修 `N >= k_max`、有限样本 CVaR/worst-tail 定义和单位/聚合规则；否则尾部表不能复核。
2. 再冻结 query camera 的可用时间与 provenance；否则无法审查未来泄漏。
3. 最后预注册 trajectory-level 的效应阈值与推断方法；把 5 条轨迹明确为下限/描述性门，不包装成充分功效证明。
