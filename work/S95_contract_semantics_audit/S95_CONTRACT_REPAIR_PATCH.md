# S95 evaluation-contract repair patch

时间：2026-09-12（Asia/Shanghai）
状态：`REPAIR_REQUIRED_BEFORE_FORMAL_RUN`

这份补丁不改变已经保存的 S94 结果；它规定正式实验使用的新合同约束。S94 的字段验证仍可通过，但不能把它解释成语义合同充分。

## 必须修复的六项语义

1. **候选池与 k**：Gate 0 改为每个 query 至少 `N >= max(k)` 个合法、可追踪候选；若采用 `k=4`主设置和`k=2,8`敏感性，则至少 `N >= 8`，不允许静默补候选。候选不足的 query 标记 `INCOMPATIBLE_FOR_K8`。
2. **有限样本尾部指标**：`worst-5%` 和 `CVaR95`统一定义为按误差从大到小排序后的 top-5% 积分平均，最后一个样本允许 fractional weight。不得使用严格 `x > q95` 作为唯一 CVaR 定义；全相同误差必须返回该误差，而不是空集/NA。
3. **轨迹级统计**：5条独立轨迹是最低描述性门，不自动构成0.05显著性证据。正式报告必须说明轨迹数、paired effect、cluster bootstrap和预注册效应阈值；如声称显著性，另给精确配对随机化/符号检验及功效限制。
4. **边际与选择后校准**：`q_i`只能称 marginal calibration，除非预先冻结 scene/trajectory/selection 条件并报告 conditional/post-selection risk-coverage。不能从总体5%错误率推出被选择子群5%错误率。
5. **风险量纲和聚合**：冻结每个风险分量单位、裁剪、归一化、聚合函数、校准样本和 tie-break。深度、像素重投影、可见性冲突不得直接无量纲相加。
6. **请求相机的信息时间**：`FREEZE.json` 必须记录 `camera_available_at`、来源和是否在选择前发布。允许预先给定的 query camera 与禁止读取未来帧得到的真实 pose/depth/mask/error 分开记录；按信息实际可用时间判断泄漏。

## 最小可证伪实验的有效性条件

正式 S91 只能在 S95 patch 通过、Gate 0 通过、未来答案隔离、source traceability 达标、统一预算冻结后运行。这个补丁不授予新颖性，不把 GRC 变成已验证方法。
