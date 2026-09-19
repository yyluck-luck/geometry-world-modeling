# 创新审查补充：S99–S103 之后最多两个候选方向

审查时间：2026-09-15（实际运行时间以主账回执为准）  
审查身份：独立审稿式子任务，不是方法验收。  
证据入口：原 proposal、`work/S99_fixed_budget_risk_update/RESULTS.md`、
`work/S100_context_matched_swap/RESULTS.md`、`work/S103_prediction_geometry_decomposition/RESULTS.md`，
以及 `work/agents/S100_innovation_review.md`、`S100_claim_boundary.md`、
`innovation_frontier_round2.md`。

**状态固定为：** `new_method_validated=false`，`novelty_authorization=NONE`。以下是可被真实
实验推翻的候选，不是已经成立的创新点。

## 1. 证据约束

S99 已停止“低历史几何不一致度在固定改写预算下平均优于 confidence”的解释：在已见
消费者上 low-D 的平均 AbsRel 和 Delta1 均不占优。S100 的 9 对、两个背景和四个目标
产生的 mean benefit 在三个截断上接近零，部分 pair 出现背景间符号反转；这至多提示
替换偏好可能依赖上下文。S103 进一步显示，low/conf 输出的支持变化极少，差异集中在
少量 `source_pixel_identity` 变化像素，跨两个背景的差分相关约 0.604，但
`source_pixel_identity` 不是几何真值。

因此不能把“几何记忆”“上下文交互”“utility 分数”“有符号干预”“confidence gate”
重新命名为贡献。GIM-World 已有集合条件的信息引导 pruning；CUE-R 已有有符号
REMOVE/REPLACE 及多证据干预；MemoNav、WorldPlay、Spatia、MosaicMem、RELIC、Memorize
When Needed 和 Latent Spatial Memory 已覆盖多种长期/空间记忆、门控或重访机制。候选
必须在**历史输入权限、未来 RGB-D/pose 目标、固定真实记忆预算、完整消费者和来源级
干预**的联合问题上形成可检验差异。

## 2. 候选 A：稀疏遮挡竞争风险的未来效用校准（SOCF）

### 具体问题

在候选历史项加入当前 memory 之前，能否只用历史可见的投影、深度、可见性和来源边界，
预测该项在未来查询中触发的**来源竞争/遮挡替换事件**及其有符号几何收益？S103 的局部
证据给出一个窄而可推翻的机制：low/conf 的差异不是全图覆盖变化，而是少量 z-buffer
竞争像素的来源改变。SOCF 不是普通“低风险优先”，而是显式预测候选加入后会在哪些
查询区域造成 provenance conflict，并允许在预测不确定时 abstain（保留原状态）。

### 可能的实质贡献

只有在下列链条全部成立时，才可能被写成方法/问题贡献：

1. 历史-only 的 conflict 特征（投影重叠、深度 margin、可见性边界、候选来源）在
   calibration 集上校准为未来 conflict 概率或区间；
2. 这个风险在此前未见的查询上预测 source-level overwrite 与 future RGB-D/pose
   loss，优于 recent/random/pose/coverage/depth/confidence/MI-GP；
3. 在真实 memory slot `k` 和相同 token、显存、选择时间、forward 次数下，SOCF 的
   abstention/update 规则降低未来 mean 和 tail loss，且不是只降低 coverage；
4. 源级反事实（只替换一个候选，固定其它记忆、seed、轨迹和生成步数）复现预测的
   竞争区域；完整 VMem/生成消费者上的结果方向一致。

这条链条比“风险分数 + top-k”窄得多，但仍可能被 SplaTAM 风格 overlap/visibility
 gating、Spatia/MosaicMem 的空间记忆和已有不确定性选择解释掉，故不能预先称新。

### 审稿人打分（假设全部实验成功）

| 维度 | 分数/10 | 审稿判断 |
|---|---:|---|
| 新颖性潜力 | 7.0 | 具体到 future conflict + source intervention；普通几何门控本身不新 |
| 科学价值 | 8.0 | 能把 ghosting/局部 z-buffer 竞争与未来几何误差联系起来 |
| 可证伪性 | 8.5 | 历史-only 预测、abstain 收益和 source-level 反事实均可失败 |
| 工程可行性 | 5.5 | 需要真实长序列、完整消费者、多个 budget 和 GPU |
| 近邻风险 | 7.0（高风险） | overlap/visibility gating、空间记忆和 calibrated uncertainty 很接近 |
| 综合决策 | 6.8 | 仅作为候选；先做小规模资格实验，不直接开发大模型 |

### 最小真实实验与 kill criteria

在合法 `HELD_OUT_TEST` RGB-D/pose 通过 Gate0 后，冻结 `k∈{2,4,8}`、候选池、四类
输入预算和 query 轨迹；calibration 只用 development。最小运行包括：

- 至少 5 条独立轨迹、每条至少 3 个未来查询；
- recent、random（多 seed）、pose、coverage、depth、confidence、GIM-World 风格
  MI/GP 和 SOCF；所有方法相同候选池与 token/显存/forward 预算；
- 先封存选择与预测，再读取 future depth/pose/RGB 评分；报告 mean AbsRel、Delta1、
  worst-5%/CVaR、coverage、reprojection error、source overwrite rate、显存和时延；
- 对每个 source conflict 事件做单项 replace/delete replay，检查相同 seed 下事件位置与
  预测区间；至少一次独立作者重算。

预先停止条件：

1. conflict 风险在 held-out query 上的 AUROC 不超过 confidence/coverage 中最强者，
   或 calibration 覆盖率低于预设名义覆盖率 10 个百分点以上；
2. 在任一主预算下 SOCF 的未来 mean AbsRel 不优于最强基线，且 tail/CVaR 也无补偿；
3. 收益只来自 coverage 改变、未来答案被 selector 读取、或 source ID 与真实几何误差
   不一致；
4. 去掉 conflict 特征后性能不变，或 simple overlap/visibility gate 达到同等效果；
5. 完整生成器中没有方向一致的 RGB-D/pose 改善。

任一条件触发都停止“SOCF 方法”主张，保留为失败机制诊断，不通过再加网络层或改指标
挽救。

## 3. 候选 B：固定预算未来几何效用基准（FGB-Future）

### 具体问题

建立一个可复现的**新评价问题**：在固定真实记忆预算下，历史观测级风险分数能否预测
并改善完整 world-model consumer 对未见未来 RGB-D/pose 的状态误差？重点不是再发明
一个 selector，而是把当前文献通常分开的四件事放入同一严格合同：历史-only 选择、
独立未来状态、来源级 paired intervention 和真实成本预算。

### 可能的实质贡献

若要成为 benchmark/evaluation 论文，至少需要一套公开可复核的 held-out 轨迹或合法
数据协议、统一 runner、泄漏测试、source provenance、预算账本、强基线实现、失败案例
和跨场景结果；论文主贡献应是**问题定义和评价框架**，不能把现有 GRC 公式包装成新
算法。一个 companion method（如 SOCF）只能作为可选项，不能让 benchmark 依赖某个
未验证的选择器。

该方向与 GIM-World 的固定容量/几何 pruning、Spatia 的回访一致性、WorldMM 的检索
以及各类长期空间记忆工作有明显重叠，因此差异必须落实为“未来状态效用的独立测试
合同 + 来源级干预 + 全成本公平比较”，而不能只增加数据表。

### 审稿人打分（假设 benchmark 证据完整）

| 维度 | 分数/10 | 审稿判断 |
|---|---:|---|
| 新颖性潜力 | 7.5 | 联合评价合同可能独立；单一指标或固定预算本身不新 |
| 科学价值 | 8.5 | 可直接检验“历史风险是否真的帮助未来世界状态” |
| 可证伪性 | 9.0 | 任一选择器不超过基线、跨场景不稳或泄漏即否定原主张 |
| 工程可行性 | 6.0 | 需要数据、GPU、完整 consumer 和大量审计 |
| 近邻风险 | 6.5（中高） | 许多工作已有几何 memory/回访指标，联合合同尚需原文再核 |
| 综合决策 | 7.1 | 当前两个候选中更稳妥；先形成 benchmark 规格，再决定 companion method |

### 最小真实实验与 kill criteria

Gate0 通过后，冻结至少 5 条未见轨迹、每条 3 个未来 query、development calibration、
`k=2/4/8` 和所有成本单位。最小矩阵：

1. recent/sliding、uniform、random、多 seed、pose-only、coverage、depth-only、
   confidence、GIM-World 风格 MI/GP、oracle（只作上界）以及待验证 SOCF；
2. 每个选择器只读历史，future RGB/depth/pose 在预测封存之后才可读取；
3. 同一 VMem/consumer、同一生成轨迹和随机状态；记录 wall time、GPU memory、token、
   forward 次数、失败和 I/O；
4. 报告未来 RGB-D/pose mean、tail/CVaR、回访/重投影、覆盖率、source provenance 和
   每条轨迹结果，另做遮挡、视角变化、重访和序列长度分层；
5. 不同作者从冻结 manifest 独立重算选择、至少一个完整 consumer 预测和所有聚合。

预先停止条件：

- held-out 数据、许可、RGB-D/pose/K/时间戳任一字段不合格；
- selector 读取任何未来答案，或 calibration 与 test 身份重叠；
- 主预算下所有候选都不超过 recent/random，或风险分数不比 confidence 更能预测未来
  误差；
- 只有当前重建/coverage 改善，没有未来 RGB-D/pose 或完整视频改善；
- 结果只在一个已见序列、一个截断、一个 seed 或 oracle 条件成立；
- 记忆槽位、token、GPU/CPU、选择时间或 forward 成本不相等且无法修复。

触发时，停止“GRC-Memory 方法有效”与“FGB-Future 已证明普遍规律”的主张；可以把
负结果作为一份数据/评价审计，不能靠扩大 agent 数量、改聚合或重命名继续追阳性。

## 4. 推荐顺序与当前决策

审稿式优先级：

1. **先做 FGB-Future 的数据和评价合同**：它最直接对应 proposal，也能在不承诺某个
   selector 的情况下检验问题是否成立。当前 S102 已阻断，所以只做 schema、runner、
   synthetic/no-GT 单元测试和资源清单，不能宣称性能。
2. 若 Gate0 通过，再将 SOCF 作为一个小型 companion method；先做冲突风险预测和
   source-level replay，预测失败就停止，不接入完整生成器。
3. 只有 SOCF 在 held-out 多场景、固定预算和完整 consumer 上击败强基线，才讨论论文
   方法章节；否则以 benchmark/负结果/失败机制为主，并保持 `new_method_validated=false`
   直到独立复核完成。

本审查没有授予任何新颖性授权；它只把 S103 的“稀疏 provenance 变化”转为两个窄的、
可推翻的研究候选，并明确了近邻风险、真实实验和停止规则。

