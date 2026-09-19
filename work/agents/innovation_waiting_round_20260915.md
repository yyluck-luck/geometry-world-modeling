# 创新等待轮：DLV 最小证伪卡

记录日期：2026-09-16（Asia/Shanghai）  
记录性质：远端创新文件同步后的独立候选筛选；不分析 GPU job 588321，不读取其结果。  
当前状态：`new_method_validated=false`，`novelty_authorization=NONE`，`NO_METHOD_SELECTED`。

## 1. 当前只保留一个候选

**候选：DLV（dynamic-landmark validity，动态地标有效性）。**

DLV 的窄问题是：历史观测形成的一个可寻址地标，在后来已经观察到场景变化后，是否应被标记为 `valid`、`stale` 或 `unknown`，并在后续回访中暂缓使用；决策只能使用当时已经到达的历史 RGB、几何、可见性和来源 ID。未来 RGB、深度、位姿、目标 mask 和 future-valid mask 只能在选择状态封存以后用于评分。

DLV 的可辨识预测不是“几何记忆更好”或“距离更近”，而是：

> 在相同候选池、真实 memory budget、query、consumer、随机状态和计算预算下，只有包含真实已观察场景变化的回访，地标级 validity state + abstention 才应降低未来几何尾部误差；在静态回访上不得造成超过预先固定容差的退化。

这把候选限定为“动态变化后的失效管理”，而不是泛化的几何选帧。

## 2. 它暂时能经受的最近工作威胁

这里的“经受”只表示尚有可测试的差异，不表示新颖性成立。

| 最近工作/机制 | 已覆盖的部分 | DLV 暂时保留的窄差异 |
|---|---|---|
| ReWorld：pose-indexed landmark bank、pose-nearest retrieval | 地标存储、位姿索引、近邻读取 | validity 是随已到达的跨观察一致性改变的状态；回访时可以 abstain，而不是只按 pose 取最近地标 |
| ViewRope / GIM-World：几何相关性、稀疏选择、条件 pruning | 几何相关历史选择和固定容量 | DLV 的主事件是“已观察变化使旧地标失效”，并要求静态回访负向控制；若 ranking 与 conflict/coverage 完全相同则立即淘汰 |
| Spatia / WorldStereo：显式 3D memory 与更新 | 空间记忆更新、3D 对应和回访一致性 | 不主张新的 3D memory backbone；只检验同一 consumer 中 landmark-level invalidation/abstention 的效应 |
| WorldTrace / transition memory | 可寻址压缩、转变/地标记忆 | DLV 必须证明 validity signal 比地址/transition/recent 控制多提供信息；不能把 transition gate 改名为 validity |
| MemoNav、普通 forgetting/uncertainty gate、change-point 方法 | forgetting、门控、历史变化检测 | 只有在同槽位、同 token、同显存和同 forward 预算下，且静态不退化、动态几何尾部改善，才保留 DLV 作为候选；否则降级为已知门控或评价诊断 |

因此，DLV 的最低差异必须同时出现：地标级状态转移、未来答案隔离、动态/静态配对、固定真实预算，以及未来几何评分。少一个，不能写成方法差异。

## 3. 最便宜且有决定性的证伪实验

### 3.1 适用前提

正式执行前仍需通过项目 Gate 0：至少一条有合法许可、RGB-D、内参、时间戳、位姿和可复查配对的序列；另需在同一或另一条序列中找到一个**已经在历史中被观察到的变化**，例如物体位置/占据发生改变，且变化标签不使用未来目标答案。若找不到可审计的动态变化，DLV 直接记为 `data_unidentifiable`，不以合成移动物体冒充真实证据。

### 3.2 最小规模

只使用：

- 1 个固定候选地标 `j`，1 个固定 memory budget（主值 `k=4`；不在本轮搜索更多 cap）；
- 1 个动态回访 query：历史中已出现变化，随后回到相近 pose/FoV；
- 1 个静态回访 query：同场景或同数据合同下无已观察变化的回访；
- 同一候选池、同一 consumer、同一随机状态、同一 query 相机轨迹和同一输出分辨率；
- 四个选择臂：`pose-only`（ReWorld-style）、`recent`、`conflict/coverage-only`、`DLV`。`oracle-validity` 只作上界，不进入公平排名。

这不是跨场景验证，也不够支持论文结论；它只是最快的击杀筛选。

### 3.3 先封存，再评分

在每个 query 的 future RGB-D/pose 打开前，序列化：

1. 候选地标的历史-only residual、重叠/可见性、来源 ID 和 validity state；
2. 选择或 abstention 决定；
3. 选中的 source IDs、候选池、`k`、token/显存/forward/时间账本；
4. consumer 的预测输出及其哈希。

之后才读取 future RGB、depth 和 pose，计算：

- 未来有效区域的 depth AbsRel（主）；
- 几何重投影/位姿误差（若合同允许）；
- worst-query 或固定尾部误差；
- stale-region coverage、source overwrite/provenance 改变和 abstention rate；
- 静态 query 相对于 pose-only/recent 的退化量；
- 实际 token、GPU/host memory、forward 次数和 wall time。

### 3.4 唯一关键比较

先看动态 query 的 paired 差值：

`DLV future loss - best non-DLV control future loss`

再看静态 query 的差值。若 DLV 的动态改善只伴随更低 coverage、更少 token、更少
forward 或不同候选池，则实验无效，不能解释为 validity 作用。

### 3.5 预先固定的击杀规则

任一条件成立，就停止 DLV 方法主张并保留原始回执：

1. 没有合格的真实已观察变化，或变化/validity 使用了未来 RGB-D、pose、mask 或答案；
2. DLV 与 pose/recent/conflict/coverage 的地标排序完全相同，或 source ID 无法追溯；
3. 动态 query 的未来 depth/pose 尾部误差没有改善，或改善只来自 coverage/预算差异；
4. 静态 query 相对最佳非 DLV 控制超过预注册容差而退化；
5. 去掉 state transition、abstention 或 dynamic residual 后结果不变；
6. 结果仅改善 RGB 观感/当前重建，未来几何保持不变或变差；
7. 单个地标/单个 query 的差异落在 replay 噪声范围内，无法超过预先冻结的重复运行容差。

通过这次筛选也只意味着“可以申请更大 held-out pilot”，不意味着新颖性或方法验证。

## 4. 当前判断

DLV 是本轮唯一仍有清楚可证伪边界的候选：它把现有“几何记忆/历史选择”问题进一步压缩为“已观察动态变化后的地标失效管理”，并内置静态场景不退化的负向预测。其主要风险同样清楚：validity 可能只是 conflict、visibility、recency 或 transition gate 的别名，且项目尚未完成合格动态 RGB-D/pose 数据确认。

因此下一步应先完成数据资格和一个动态/静态配对的最小真实筛选；若筛选失败，转为负诊断/评价协议，不增加网络层、不改阈值、不用 GPU smoke 结果挽救候选。当前 GPU smoke 588321 的运行状态与本候选判断无关，本文件没有读取或解释该作业输出。

## 5. 依据文件

- `work/remote_innovation_20260915/latest/INNOVATION_SCAN_20260915.md`（本地同步的远端创新检索结论）
- `work/remote_innovation_20260915/latest/INNOVATION_IDEAS_20260915.md`（本地同步的候选与近邻范围）
- `work/remote_innovation_20260915/latest/EVALUATION_AND_DATA_PLAN_20260915.md`（TUM/Bonn/ARKitScenes 数据边界与未来评分合同）
- `work/remote_innovation_20260915/latest/GATE0_TUM_QUALIFICATION_20260915.md`（TUM 数据属性复算；不代替 Gate 0 正式判定）
- `work/agents/innovation_continuous_next_20260915.md`（ReWorld 与 DLV 候选）
- `work/agents/innovation_topconf_matrix_20260915.md`、`work/agents/innovation_redteam_continuous_20260915.md`（SOCF/FGB-Future 近邻压力与停止规则）
- `work/agents/innovation_scan_final2_20260915.md`（不一致度/尾部风险候选及其淘汰条件）

本文件未运行模型、未读取未来 GT、未查看或分析 job 588321 结果，也未改变主账中的创新状态。
