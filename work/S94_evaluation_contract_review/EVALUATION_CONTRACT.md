# S94 最小评价合同：固定预算下的未来几何风险记忆选择

版本：`S94-v1`

审查记录时间：2026-09-12 17:11:57（Asia/Shanghai）

状态：`PROTOCOL_ONLY / NOT_RUN`

## 1. 研究问题与可证伪假设

研究问题是：在相同历史候选池、相同记忆槽位、相同消费者和相同总计算成本下，历史观测的几何风险能否预测**独立未来查询**的几何误差，并在已有的时间、位姿、覆盖率和置信度选择之外带来增量收益？

唯一允许的主方法假设是：

> `risk+utility` 在未见轨迹上比 `recent`、`nearest-pose`、`coverage`、`confidence-only` 和可运行的长期记忆基线更低的未来几何误差，且优势同时出现在平均误差和尾部风险中。

这不是“风险与误差有相关性”假设。相关性可以作为诊断，但不足以证明选择方法有效。

## 2. Gate0：数据资格与答案隔离

每个场景必须同时拥有：

1. 历史 RGB 与深度/几何，以及原始时间戳；
2. 未来 RGB 与深度/几何，以及原始时间戳；
3. 请求相机的内参、外参/位姿、坐标系和深度单位；
4. 可复查的文件 SHA、数据来源和使用条件；
5. 至少 6 个历史候选与 3 个未来查询。

正式确认集至少使用 **5 条相互独立的 test trajectory**，每条至少 3 个未来查询；只有 3–4 条轨迹时必须标记为 `PILOT_ONLY`，不能写跨场景确认。场景/轨迹而不是帧随机拆分：`development`、`calibration`、`test` 三组互斥。

时间约束为 `t_history < t_query`。历史候选可来自查询之前的帧；未来 RGB、未来深度、未来位姿、未来 mask、未来模型输出、未来误差和任何未来有效性标签均不得进入选择器、效用训练或阈值设定。

执行上使用两个阶段和两个目录：

- `select/` 进程只接收历史 manifest、请求相机和冻结的模型状态，输出 source IDs；
- `score/` 进程在 `select/` 输出 SHA 封存后才挂载未来答案；
- 选择器输入 manifest 与未来 manifest 使用不同 Unix 文件权限或容器挂载，运行后保存系统调用/文件访问审计；
- 若任何选择器日志、缓存或 checkpoint 读到未来路径，整个 query 作废，不只删除一个指标。

## 3. Source identity 合同

每个候选历史观测必须有稳定的 `source_id`：

```text
{dataset, scene_id, trajectory_id, frame_id, timestamp_ns, modality, file_sha256}
```

选择器输出必须保存候选排序、入选 source IDs、未入选 IDs、分数和 tie-break 规则。消费者读取的每个槽位保留 source ID；若发生融合，必须保存组成该槽位的完整 source-ID 集合及权重。

评分端至少报告：

- `selected_source_identity_match`：同一 source 是否真的进入消费者；
- `source_traceability_rate`：输出槽位可追踪到原始 source 的比例；
- `identity_collision_rate`：不同 source 被错误合并的比例。

若 traceability `< 95%` 或 identity match 不能计算，运行降级为“系统级记忆对比”，不得宣称单条记忆的几何风险效应。

## 4. 固定预算与公平比较

每个 query 预先冻结以下预算，所有方法完全相同：

|预算项|合同要求|
|---|---|
|候选池|同一历史候选 IDs 和数量|
|槽位数|固定 `k`；主合同默认 `k=4`，敏感性另跑 `k=2,8`|
|GPU/cache|保存峰值字节和 token 数；上限由最大合法基线的冻结预算决定|
|CPU/host memory|单独计数；不能把无限增长的 host key 或索引隐藏在“固定 k”后|
|选择计算|选择时间、读取字节、前向次数、FLOPs/可用近似均记录|
|消费者计算|相同 denoising steps、分辨率、噪声/RNG、模型权重、VAE、后处理|
|输出|同一查询相机、同一输出数量和同一停止条件|

GPU cache 与 host memory 必须分列。WorldTrace-Field、MemRoPE 等基线若 host 状态随历史增长，按实际峰值计入；超过冻结上限即 `OVER_BUDGET`，不可仅报告 GPU 占用。

若某方法不能在同一 `k` 或内存上限下运行，不能通过删减其状态来制造“公平”；该方法记为 `INCOMPATIBLE_BASELINE`，并在主表中保留缺失原因。

## 5. 方法与强基线

所有方法读取相同候选池，并使用相同消费者：

1. `random-k`：至少 5 个预注册 seed，报告均值和 seed 区间；
2. `recent-k`：最近时间；
3. `nearest-pose-k`：请求相机位姿距离；
4. `coverage-k`：历史空间/视锥覆盖；
5. `pose/reprojection-only`：只用位姿或重投影误差；
6. `depth-consistency-only`：只用历史深度一致性；
7. `confidence-only`：只用已有模型置信度；
8. `utility-only`：只用过去信息的效用，不读未来答案；
9. `risk-only`：只用几何风险；
10. `risk+utility`：GRC 候选；
11. 可复用时加入 `WorldTrace-Field/Landmark`、`MemRoPE` 和 `WORLDMEM-style`，严格记录实现版本；
12. 资源允许时加入 `Fisher/EIG-proxy`，若无法运行完整 FisherRF，必须明确标成代理，不称原方法复现。

`oracle-future` 只能作为上界诊断，不能进入主排名、不能用于调阈值，也不能写成可部署方法。

## 6. 指标与统计单位

### 6.1 主几何指标

- 首选：未来物体中心/关键点的 3D 位置误差；
- 若只有深度：相机坐标系 Z 深度的 `AbsRel` 与 `MAE(m)`；深度单位、无效值和裁剪范围在 Gate0 冻结；
- 若有相机与深度：未来帧重投影误差（px）和有效覆盖率作为几何辅助指标。

### 6.2 尾部风险

同时报告：

- 所有有效像素/点的 mean `AbsRel`；
- 每个 query 的 worst-5% `AbsRel`（最高误差5%均值）；
- 每个 query 的 `CVaR95`（超过95%分位的误差均值）；
- 失败率、有效覆盖率和缺失深度率。

`worst-5%` 和 `CVaR95` 是风险指标，不是把像素当成独立样本的显著性证据。

### 6.3 聚合与置信区间

主统计单位为 `scene/trajectory/query`。先在 query 内汇总，再按 trajectory 汇总；不把几十万像素当几十万个独立实验。报告每个 query 的 paired difference（方法−baseline），再用 trajectory-level bootstrap 计算 95% CI。若 test trajectory 少于 5 条，只报告描述性区间并标记 `PILOT_ONLY`。

同时报告 risk calibration：开发/校准集的 risk–coverage 曲线、固定风险分位的未来误差趋势，以及 test 集 Spearman 仅作为辅助，不把其本身当方法收益。

## 7. 运行前冻结清单

在读取任何 test future 文件前，保存 `FREEZE.json`，至少包含：

- 数据集版本、scene/trajectory split、所有 source IDs 和 SHA；
- 模型/权重/代码 commit、消费者和 VAE 身份；
- `k`、GPU/host/token/时间预算；
- 所有 baseline 的参数、随机种子和 tie-break；
- 主要指标、无效值规则、CVaR/worst-5%定义；
- 预测方向（误差越低越好）、停止规则和缺失数据处理。

冻结后不得根据 test 结果改风险公式、阈值、分位数或可视化选择。任何改动建立新合同版本。

## 8. 停止规则

以下任一情况发生即停止 GRC 的方法主张，保留结果和失败证据：

1. Gate0 未通过、时间戳/相机/深度单位不能绑定，或 future truth 缺失；
2. 选择器访问未来答案、未来 pose/mask、生成后误差或 future-valid mask；
3. source traceability `<95%`，或同一 source 的进入消费者身份无法核对；
4. 任一方法超过 GPU/host/时间/槽位预算，且无法在冻结规则内公平修复；
5. `risk+utility` 在 5 条以上 test trajectories 上没有同时改善 mean AbsRel 与 worst-5%/CVaR95，或 paired CI 跨越零且方向不稳定；
6. 增益只出现在单一场景、单一轨迹、单一随机种子，或仅 RGB MSE 改善而几何主指标不改善；
7. 结果只来自已见/已用于调参的场景，或仅来自保存数据回顾性复算；
8. 计算成本显著增加而几何收益不超过 `coverage`、`nearest-pose`、`confidence-only`、`WorldTrace/MemRoPE` 等强基线。

停止规则触发时，允许保留为 `measurement/diagnostic` 或负结果，但不得把它命名包装成已验证的新方法。

## 9. 通过条件（仍不等于创新成立）

只有在 Gate0、答案隔离、source traceability、固定预算和独立复核均通过后，且 `risk+utility` 在至少 5 条 test trajectories 上对主要几何指标和至少一个尾部指标相对最强非 oracle 基线呈稳定 paired 改善，才可进入方法论文审查。即便通过，也还需要跨数据集、消融、机制反例和原文近邻审查；本合同不授予 `novelty_authorization`。

## S95语义审查冻结提醒（2026-09-12）

S94字段离线检查通过不代表合同语义充分。`work/S95_contract_semantics_audit/RESULTS.md`发现正式运行前必须修复：`N>=k_max`（当前k=8敏感性与原N>=6冲突）、有限样本CVaR的fractional-tail定义、5条轨迹仅描述性门、marginal与post-selection校准区分、风险分量量纲/归一化，以及请求相机的实际信息可用时间。正式S91在S95补丁通过前继续禁止。
