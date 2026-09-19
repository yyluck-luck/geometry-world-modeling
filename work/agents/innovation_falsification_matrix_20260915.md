# SOCF / FGB-Future 审稿人拒稿压力测试矩阵

审查日期：2026-09-15（Asia/Shanghai）  
范围：基于 ViewRope/Spatia 精读卡、S99/S100/S103 结果，构造可在 SuperPod 上执行的
最小证伪检验。本文不授予新颖性，不把候选方法写成已成立结果。  
固定状态：`new_method_validated=false`，`novelty_authorization=NONE`。

## 1. 审稿人要求的“唯一可辨识预测”

SOCF 不能只预测“当前看起来几何一致”“覆盖率更高”或“相机距离更近”。这些都可能由
pose/coverage/confidence/recent 解释。唯一需要被单独检验的预测是：

> 在候选池、历史输入权限、真实 memory budget、生成器、随机状态和 query 轨迹全部固定
> 时，SOCF 的历史-only source-conflict 风险，能够预测候选替换对**未见未来 RGB-D/pose
> 损失的有符号增量**；在控制 recent、random、pose、coverage、confidence 和 utility-only
> 后，风险的 out-of-sample 预测仍有增量信息，并据此降低未来 mean/tail loss。

这里的“有符号”很关键：只预测某个候选会不会改变输出（absolute change）不够，必须区分
改变后是变好还是变坏。S103 目前只显示少量 provenance 变化和中等 context 相关，尚未
证明这条预测成立。

## 2. 与基线的唯一差异矩阵

| 选择器 | 只使用的信息 | 它自然会预测什么 | SOCF 必须额外预测什么 | 让 SOCF 失去可辨识性的观察 |
|---|---|---|---|---|
| **recent/sliding** | 时间位置、最近帧 | 新近项平均更有用 | 在同样 recency 分层内，conflict 风险仍预测 future signed gain | 控制 recency 后风险不再有增量预测力 |
| **random** | 候选池与随机种子 | 无系统方向，给出方差基线 | 在同预算下风险排序稳定超过随机，并跨轨迹复现 | 只在一条轨迹/一个 seed 超过随机 |
| **pose-distance** | 相机位姿、视角距离 | 几何邻近或视场重叠 | 在 pose/角距离分层内，source-conflict 风险仍预测未来损失方向 | 风险收益完全由 pose distance 解释 |
| **coverage/visibility** | 历史可见区域、覆盖率、遮挡 | 支持区域更多/缺失更少 | 在 coverage 相等候选对中，风险仍区分未来 signed loss | 只有 coverage 增加，future depth/pose 变差 |
| **confidence-only** | 模型 confidence 或历史不确定度 | 模型主观置信更高的项更好 | 在 confidence 分层/控制后，calibrated conflict 风险仍预测 future signed gain | 风险与 confidence 完全同秩，或 confidence 更强且 SOCF 无增量 |
| **utility-only** | development 上的当前重建/当前 consumer 代理 utility；不读 test future | 当前任务代理分数更高的项更好 | test future 中风险仍比当前 utility 更能预测有符号几何收益 | utility-only 在锁定 test 上同样或更好，或 SOCF 依赖 future utility |
| **ViewRope-like ray relevance** | ray 几何、历史帧/attention relevance | 几何相关历史帧更适合回访 | 即使 ray relevance 相同，source-conflict 风险仍预测未来深度/pose loss，并且不是只改善 LCE | SOCF 与 ray relevance 等价，或只在 LCE 改善而 RGB-D/pose 不改善 |
| **Spatia-like updatable 3D memory** | 显式点云更新、参考帧、camera path | 更新后的空间 memory 改善迭代生成 | 在相同 future query 和成本约束下，SOCF 风险排序改善真实未来状态 | 异构 backbone/预算无法公平对齐，或只报告点云/视频观感 |

“增量预测”必须在 test 上通过预先冻结的 nested 设计检查：先用 calibration 选择
strongest baseline 和拟合 SOCF 阈值，再锁定 test；对 test 只计算历史可见风险和预测，
future RGB/depth/pose 在 prediction seal 后才读取。不能在 test 上挑选最有利 baseline、
截断上限或轨迹。

## 3. SuperPod 最小样本和分层

### 3.1 最小可证伪规模

- **Calibration-only**：至少 3 条独立 development 轨迹，每条至少 3 个 query；只用于
  风险校准、阈值和确定 strongest non-SOCF baseline，不用于最终 test 结论。
- **Held-out test**：至少 10 条此前未用于选择或调参的独立轨迹，每条至少 3 个 future
  query（至少 30 个 query 单元）；统计重复单位是轨迹，不是像素。
- 每个 query 固定一条 camera trajectory，并预先标注是否包含遮挡、回访和大视角变化；
  这些分层不能事后按结果重定义。
- random 至少 5 个固定 seed；SOCF 与各 baseline 使用相同候选池、`k=2,4,8`、token/
  显存/forward/生成步数预算和随机状态。

10 条轨迹是一个最小筛查门，不足以支持复杂场景的普遍性结论；若只有 3–5 条轨迹，
结果只能标为 pilot，禁止显著性检验和 CCF/PhD 水平宣称。

### 3.2 统计检验合同

1. **主终点**：每条 test 轨迹先对其 3 个 query 取均值，再计算 SOCF 与 calibration
   选择的 strongest baseline 的 paired future capped AbsRel 差；报告 mean、median、
   worst-5%/CVaR 和 coverage，不能以像素为独立样本。
2. **方向检验**：对 10 条轨迹做预注册的 paired sign-flip/permutation test（10,000 次，
   双侧，`alpha=0.05`），同时给 trajectory bootstrap 95% BCa 区间。若两个方向检验结果
   不一致，报告不确定，不能挑有利者。
3. **实用门槛**：SOCF 的主预算 `k=4` 相对 strongest baseline 的 future mean AbsRel
   至少改善 1%（相对值），且 bootstrap 下界 > 0；CVaR/worst-5% 不得恶化超过 5%。
   `k=2,8` 作为锁定的敏感性结果，不能择优替换主预算。
4. **唯一性检验**：在 test 上以 baseline 分数（recency、pose、coverage、confidence、
   utility-only）为协变量，报告 SOCF 风险对 future signed gain 的 out-of-sample partial
   Spearman 相关和分层 AUROC；要求相关的 95% 轨迹 bootstrap 区间 > 0，且 AUROC 至少
   比 strongest baseline 高 0.05。若控制协变量后区间跨 0，停止“独有预测”主张。
5. **校准检验**：只在 calibration 拟合的风险区间，在 test 报名义 0.9/0.8 覆盖率和
   实际覆盖率；任一偏差超过 0.05 视为校准失败。校准通过也不等于方法收益通过。
6. 不对每个 query、像素或多个截断重复报显著性；主终点只有一个，其他指标是诊断。

## 4. 预先固定的停止条件

出现任一条件即停止相应创新主张，保留原始数据和失败回执：

- Gate0 数据、许可、RGB-D/pose/K、时间戳或 split 失败；
- selector 读取 future depth/RGB/pose/mask，或 calibration/test 身份重叠；
- memory slot、token、显存、forward、生成步数或选择时长无法公平对齐；
- SOCF 的 partial prediction 不超过 confidence/pose/coverage/utility-only，或只改善
  当前 reconstruction/coverage 而 future depth/pose 变差；
- 主预算下 mean AbsRel 未达到 1% 且 bootstrap 下界跨 0，或 tail 恶化超过 5%；
- 只有一条轨迹、一个遮挡强度、一个 seed、一个 cap 或一个异构模型得到阳性；
- source-level replay 与预测 conflict 区域 IoU < 0.5，或 replay 方向在多数轨迹不一致；
- 去掉 calibrated risk、conflict 特征或 abstention 后性能不变，或 simple overlap/visibility
  gate 达到相同结果；
- ViewRope/Spatia 只能以不同 backbone、训练数据或预算运行，无法形成公平 paired 对照。

停止后可以报告“该机制在此合同下未通过”，不能通过新增 seed、放宽阈值、改 cap、换
聚合或增加 agent 数量追求阳性。

## 5. 导致 SOCF 被淘汰的数学反例

即使几何风险 `q_i` 已经完美校准，也不保证它等于未来效用。令两个候选的历史几何风险为

\[
q_A=0.10 < q_B=0.20,
\]

但未来查询有一个关键可见区域，候选错误在该区域的代价权重分别为

\[
w_A=100,\qquad w_B=1.
\]

在其它记忆和随机状态完全相同的情况下，候选的期望未来几何损失增量为

\[
\mathbb E[\Delta L_A]=w_Aq_A=10,
\qquad
\mathbb E[\Delta L_B]=w_Bq_B=0.2.
\]

因此低风险的 A 反而比高风险的 B 更差。这里的 `w_i` 表示遮挡/重访区域对未来 RGB-D
或 pose 的影响强度；它不是事后调出来的参数，而是说明“风险概率”和“未来状态信息
价值”在数学上不是同一个量。conformal coverage、低重投影误差或 source identity 稳定
都不能自动消除这个反例。

更简单的确定性版本是：在固定背景 C 下，`L(C∪A)=0.40`、`L(C∪B)=0.10`、
`L(C)=0.20`。A 的风险分数可以低于 B，但 A 使未来损失上升，B 使损失下降。若
SOCF/ FGB-Future 的真实实验出现这一模式，且跨轨迹可重复，就必须停止“风险单调决定
记忆价值”的主张，转而把风险作为一个可能有用但不充分的 covariate。

## 6. 审稿式最终裁决规则

- **Accept as candidate（仍非已成立方法）**：Gate0、隔离、预算、独立复核全通过；SOCF
  在控制所有基线后仍有独有预测；主预算未来 mean/tail 改善达到门槛；source replay
  方向一致；跨轨迹/遮挡/回访分层不反转。
- **Borderline / evaluation-only**：风险能预测 conflict，但不能改善 future loss，或只在
  部分分层有效。此时可保留 FGB-Future 评价问题，停止 SOCF 方法主张。
- **Reject / pivot**：风险不具备增量预测、被 pose/coverage/confidence/utility-only
  完全解释、仅当前重建改善、数据/预算/隔离失败，或数学反例在真实实验中重现。此时应
  归档负结果，回到 proposal 的 failure analysis，而不是重命名为新方法。

本文件只收紧创新的可辨识条件；无论哪种结果，当前项目仍保持
`new_method_validated=false`，直到合法未见数据、完整 consumer、独立复核和公平跨场景
实验全部通过。

## 原始来源

- [ViewRope, arXiv:2602.07854](https://arxiv.org/abs/2602.07854)
- [Spatia, CVPR 2026 Open Access](https://openaccess.thecvf.com/content/CVPR2026/papers/Zhao_Spatia_Video_Generation_with_Updatable_Spatial_Memory_CVPR_2026_paper.pdf)
- [GIM-World, arXiv:2606.02436](https://arxiv.org/abs/2606.02436)
- [Geometry-as-context, CVPR 2026 Open Access](https://openaccess.thecvf.com/content/CVPR2026/html/Hu_Geometry-as-context_Modulating_Explicit_3D_in_Scene-consistent_Video_Generation_to_Geometry_Context_CVPR_2026_paper.html)
