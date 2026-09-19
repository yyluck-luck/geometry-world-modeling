# 创新前沿检索：S91R-C 的尾部风险与 GRC-Memory 近邻审查

- **检索时间**：2026-09-12（Asia/Shanghai；UTC 约 08:20--08:35）
- **任务**：针对 S91R-C 暴露的“局部像素改善但整体有符号收益为负、尾部失败可能主导平均值”问题，检索近年 ICML/NeurIPS/CVPR/ICCV/ICLR 原文或官方代码，覆盖风险敏感预测、selective prediction、conformal/decision-theoretic memory、tail-risk calibration。
- **证据边界**：以下是原文近邻审查，不是新颖性证明，也没有运行这些方法。S91 正式 GRC-Pilot 仍受 Gate0 RGB-D/相机/未来真值门阻断；`new_method_validated=false`，`novelty_authorization=NONE`。

## 研究问题（冻结）

1. 是否已有工作把**尾部风险或可校准风险**直接用于模型输出/选择，从而覆盖“风险约束”这一部分？
2. 是否已有工作把**历史记忆压缩/遗忘/选择**用于视觉长期任务，从而覆盖“记忆选择”这一部分？
3. 是否已有决策理论说明“预测误差较低”不等于“对未来决策有价值”，从而要求 GRC-Memory 以未来几何收益而不是当前分数验收？

## 论文一：Conformal Risk Training（NeurIPS 2025）

**原文**：Yeh, Christianson, Wierman, Yue, “Conformal Risk Training: End-to-End Optimization of Conformal Risk Control,” NeurIPS 2025 Main Conference。

- 官方摘要：[NeurIPS 2025 paper record](https://proceedings.neurips.cc/paper_files/paper/2025/hash/6559542f75b4452ebaaf82094c7defb7-Abstract-Conference.html)
- 官方 PDF：[Conference PDF](https://proceedings.neurips.cc/paper_files/paper/2025/file/6559542f75b4452ebaaf82094c7defb7-Paper-Conference.pdf)

### 原文实际覆盖的机制

该工作指出普通 Conformal Risk Control（CRC）主要约束有界单调损失的期望，现实任务往往关心尾部风险；因此引入可优化确定性等价风险（Optimized Certainty Equivalent, OCE），其中包含 Conditional Value-at-Risk（CVaR）等尾部风险。它还把风险控制嵌入训练/微调，避免单纯 post-hoc 校准导致平均性能下降；论文在肿瘤分类假阴性率和电池储能风险任务上报告实验。

### 与 GRC-Memory 的精确差异

| 轴 | Conformal Risk Training | GRC-Memory 候选 |
|---|---|---|
| 选择对象 | 模型参数/预测输出的风险控制 | 历史观测或记忆 item 的保留集合 |
| 风险目标 | 分类/数值输出的 OCE、CVaR 等风险 | 历史几何风险是否预测独立未来深度/重投影误差 |
| 监督位置 | 校准/训练时使用任务损失 | 记忆选择时使用历史几何证据，未来答案只用于冻结后的评价 |
| 计算预算 | 没有“固定记忆槽位”的核心设定 | 固定帧数、token、显存/host memory、推理步数 |
| 结论类型 | 风险控制保证及平均性能改进 | 需要证明风险排序带来未来几何收益 |

因此，“把 CVaR/尾部风险放进目标函数”本身不能作为 GRC 的新颖性。可保留的可能差异是：**尾部几何风险约束历史记忆选择，并在固定记忆预算下评价独立未来几何状态**。

### 最小可证伪实验（不等于建议马上运行）

在 Gate0 通过后，冻结同一候选池、同一相机/动作轨迹、同一噪声与生成步数，比较：

1. expected-risk 选择（平均 AbsRel/MSE）；
2. CVaR$_{0.9}$ 或固定上分位风险选择；
3. GRC 的校准几何风险 + 未来信息收益；
4. recent/random/coverage/confidence 强基线。

主指标预先写为：未来深度 AbsRel、重投影误差、位姿误差，以及 worst-10%/CVaR；同时报告全体 paired mean。若 CVaR 选择改善尾部但显著损害整体平均值，必须明确这是风险—效用权衡，不能直接称“更好”。

### 致命近邻与停止条件

- 若 CVaR/OCE 选择在相同预算下解释全部尾部改善，则 GRC 只能贡献几何风险定义或数据集设定，不能宣称风险敏感优化本身新。
- 若尾部改善只由场景/目标难度分层造成，或未来 validity 参与了风险分位边界计算，视为泄漏，实验无效。
- 若 GRC 的平均未来误差继续为负，而尾部指标改善不超过预注册置信区间，则停止方法主张，保留为失败分析。

## 论文二：Active, anytime-valid risk controlling prediction sets（NeurIPS 2024）

**原文**：Xu, Karampatziakis, Mineiro, NeurIPS 2024 Main Conference。

- 官方摘要：[NeurIPS 2024 paper record](https://proceedings.neurips.cc/paper_files/paper/2024/hash/6eb05d8bc6bd7bb6868c64b5802125bd-Abstract-Conference.html)
- DOI：10.52202/079017-1920

### 原文实际覆盖的机制

论文把 risk-controlling prediction sets 扩展到**顺序、适应性收集的数据**，给出 anytime-valid（所有时间点同时成立）的风险保证；同时在固定标注预算下，用选择策略决定哪些样本查询真实标签，并讨论利用 covariate-conditioned risk 提高效用。其核心是风险保证、主动查询和预算控制，不是视频世界模型记忆。

### 与 GRC-Memory 的精确差异

- 相同点：顺序到达、固定预算、风险—效用权衡，这些思想直接压缩了 GRC 的“记忆槽位预算 + 风险上界”叙事空间。
- 不同点：该工作选择的是“是否查询标签/构造预测集”，而 GRC 选择的是历史视觉观测；其保证针对预测集风险，不是未来几何真值。
- 关键警告：若 GRC 只写“在线更新风险阈值并满足预算”，审稿人会认为是把 sequential RCPS 换成 memory item，没有独立问题定义。

### 最小可证伪实验

在连续观测流上预先冻结校准集和风险预算，对每个时间步记录：

- 保留/淘汰的历史 item；
- 当前风险上界与实际未来几何损失；
- 累积预算是否超限；
- 是否发生跨时间失效（某个时间段的 CVaR/错误率爆发）。

比较 `anytime-style risk gate`、固定阈值、recent、random 和 GRC。要求至少有独立未见场景，并把“达到预算”与“未来误差改善”分开报告。若只得到边际平均风险控制而没有未来几何增益，GRC 的记忆选择贡献不成立。

### 致命近邻与停止条件

- 只有 marginal coverage/平均风险保证，没有 item-level source identity 和未来收益，不能宣称“记忆条目因果价值”。
- 若风险校准需要未来答案或按目标场景反复调阈值，属于答案泄漏。
- 若在线选择只是在预算下降低查询量，却增加 future AbsRel/CVaR，必须把结果记录为效率—质量负权衡。

## 论文三：MemoNav: Working Memory Model for Visual Navigation（CVPR 2024）

**原文**：Li et al., CVPR 2024, pp. 17913--17922。

- 官方页面：[CVF Open Access](https://openaccess.thecvf.com/content/CVPR2024/html/Li_MemoNav_Working_Memory_Model_for_Visual_Navigation_CVPR_2024_paper.html)
- 官方 PDF：[CVPR PDF](https://openaccess.thecvf.com/content/CVPR2024/papers/Li_MemoNav_Working_Memory_Model_for_Visual_Navigation_CVPR_2024_paper.pdf)
- 官方补充材料：[Supplement](https://openaccess.thecvf.com/content/CVPR2024/supplemental/Li_MemoNav_Working_Memory_CVPR_2024_supplemental.pdf)

### 原文实际覆盖的机制

MemoNav 针对图像目标导航维护三种记忆：动态更新的短期记忆（STM）、聚合全局场景表征的长期记忆（LTM），以及由图注意力融合形成的工作记忆（WM）；forgetting module 保留 STM 的 informative fraction。论文在 Gibson 和 Matterport3D 多目标导航中报告性能提升。补充材料明确指出：被遗忘节点的特征仍在地图中，因此 forgetting 并没有真正减少 memory footprint；迁移到 OOD 场景时还可能出现更多步数和撞墙。

### 与 GRC-Memory 的精确差异

| 轴 | MemoNav | GRC-Memory |
|---|---|---|
| 目标任务 | 图像目标导航成功率/路径效率 | 动态 3D/4D 世界模型未来几何状态预测 |
| 记忆机制 | learned forgetting + STM/LTM/WM + graph attention | 几何证据、校准风险和固定预算选择 |
| 风险校准 | 没有 conformal/finite-sample geometry-risk guarantee | 目标是历史几何风险上界与未来几何收益 |
| 真值类型 | 导航目标/轨迹 | 独立未来 RGB-D、相机内外参、深度/重投影真值 |
| 成本账本 | 论文承认 forgotten nodes 仍留在 map | 必须同时计 GPU cache、CPU/host memory、token、运行时间 |

MemoNav 已覆盖“历史视觉记忆 + forgetting + 工作记忆选择”这条近邻。因此“加入一个 forgetting/gating 记忆模块”不能作为独立创新。

### 最小可证伪实验

在同一 world-model 消费者和同一记忆槽位预算下，比较：

- recent/sliding window；
- random；
- MemoNav-style learned forgetting/attention（若能复现）；
- confidence-only、coverage-only、pose-distance-only；
- GRC risk-only 与 risk+future-utility。

评价必须包含未来深度 AbsRel、重投影误差、相机位姿误差和尾部 CVaR/worst-10%，另计 GPU 与 host memory。若 MemoNav-style forgetting 已达到 GRC 相同的未来几何效果，GRC 只能主张不同的 risk-calibration protocol；若只看导航成功率则不足以支撑世界状态几何结论。

### 致命近邻与停止条件

- learned gate/attention 的提升完全由容量或场景特征差异解释时，GRC 失去方法差异。
- forgotten node 仍保存在地图中，若 GRC 宣称固定显存却没有计 host memory，预算比较不公平。
- 只用同一场景的 self-revisit 或导航轨迹评分，不能替代独立未来几何真值。

## 论文四：Maximizing the Value of Predictions in Control: Accuracy Is Not Enough（NeurIPS 2025）

**原文**：Lin, Yeh, Chen, Wierman, NeurIPS 2025 Main Conference。

- 官方摘要：[NeurIPS 2025 paper record](https://proceedings.neurips.cc/paper_files/paper/2025/hash/561667a7bf603128a39cd1794bd984e9-Abstract-Conference.html)
- 官方 PDF：[Conference PDF](https://proceedings.neurips.cc/paper_files/paper/2025/file/561667a7bf603128a39cd1794bd984e9-Paper-Conference.pdf)

### 原文实际覆盖的机制

该工作提出 prediction power：预测的价值定义为使用预测相对忽略预测时带来的控制成本下降；在时变 LQR 中给出闭式表达，强调预测误差与预测对下游决策的价值可能不一致。论文进一步在一般动力学和非二次成本中给出下界。

### 与 GRC-Memory 的精确差异

这是对 GRC 目标函数最强的决策理论压力之一：

- GRC 不能只证明历史 risk 与未来深度误差相关；应证明被选择的历史在 world-model 消费后产生的**下游未来状态收益**。
- 低 AbsRel 的记忆可能对生成决策没有帮助；反之某条几何不完美但能消除遮挡歧义的记忆可能具有高 prediction power。
- 该工作研究控制策略和随机扰动，不研究视觉记忆选择或深度生成；所以它是目标定义近邻，不是直接实现近邻。

### 最小可证伪实验

对每个候选历史集合，在同一生成噪声、未来相机/动作轨迹和预算下运行 world-model，计算：

1. 只用当前观测的未来状态损失；
2. 加入该历史集合后的未来状态损失；
3. 二者差值作为 `downstream prediction value`；
4. 比较该差值与历史风险、当前重投影误差、retrieval similarity 的相关性。

要求以独立 future RGB-D/相机真值评分，并以 source-identity 配对、replay noise 方差和 matched placebo 控制。若 risk 排名只预测 pixel/AbsRel，却不能提升下游任务代价，则不能把它称为“未来信息价值最大化”。

### 致命近邻与停止条件

- 若 GRC 的 (I(Y_{future};H_S)) 只是离线相关分数，没有消费路径或下游决策变化，属于目标函数口号。
- 若所有候选的差异小于固定噪声/replay 置信区间，不能推断 item-level value。
- 若 gain 只来自更多历史 token 或更大模型容量，必须用容量匹配基线，否则结论无效。

## 跨论文综合：当前能保留的研究差异

### 已被近邻覆盖，不能单独当创新

1. “使用不确定性/置信度选择历史”；
2. “加入 forgetting/gating/attention 记忆模块”；
3. “固定预算下做 sequential risk control”；
4. “将 CVaR/OCE/conformal risk 放入目标”；
5. “预测误差不等于下游价值”的一般性说法。

### 仍可能形成可检验的问题设定

一个较窄且可证伪的组合是：

> 在显式、可寻址的历史观测记忆中，用**校准后的历史几何风险**对候选 item 做固定预算选择，并通过同一 world-model 的完整消费路径，使用独立未见 RGB-D 与相机真值评价未来几何状态；同时报告全体平均损失、worst-10%/CVaR、source-identity 增益、GPU/host memory 与推理成本。

这个组合仍然只是候选问题设定。它要比已有工作多证明三件事：

1. 风险来自历史几何证据，而不是输出不确定性或检索相似度；
2. 风险排序对独立未来几何答案有增量预测力；
3. 选择结果在固定预算和容量匹配下具有可重复的 downstream value，而不是只改善局部像素。

## 与 S91R-C 的直接连接

S91R-C 已暴露两项不可忽略的风险：

- all_new 相对 never 的有符号 AbsRel 平均改善在四个目标均为负，说明“局部更多像素改善”不能推出整体收益；
- 同一目标像素的 source identity 只有约 4.35%--5.49%，所以当前分析不能解释为某条记忆 item 的因果收益。

因此下一轮若数据门通过，必须把尾部指标和 source identity 写入冻结协议，而不是只复用原先的平均 MSE/相关系数。最便宜的区分实验应优先比较：

- mean-risk vs CVaR-risk；
- risk-only vs utility-only vs risk+utility；
- recent/random/coverage/confidence/MemoNav-style forgetting；
- 独立 future RGB-D 的全局 paired loss、CVaR、worst-10%；
- 完整消费路径的 source-level intervention 与 replay/placebo。

## 审稿式裁决

- **当前新颖性评分（仅方向，不是结果）**：风险控制/尾部校准 4/10；记忆选择 4/10；独立未来几何问题设定 6/10；完整固定预算 + source-identity + future-value 证据合同 7/10。最后一项仍没有实验证据。
- **最可能被拒的表述**：“我们提出一个结合 uncertainty、conformal 和 memory gate 的新方法。”这只是组件拼接。
- **较安全的表述**：“我们检验一个尚未被验证的研究问题：历史几何风险是否在固定记忆预算下预测独立未来几何收益，并通过 source-identity 干预和尾部风险报告区分局部改善与整体退化。”
- **当前决定**：不授权 GRC-Memory 方法主张；维持 `candidate / novelty UNKNOWN / not validated`。只有 Gate0 通过、至少多场景固定预算实验以及预注册尾部与 source-level 控制同时通过，才可重新评估。

## 检索可复查记录

本轮只采用官方会议/出版社页面和官方 PDF，未把搜索摘要当作实验结果；未运行任何论文代码，未下载论文数据。原文访问时间按本报告顶部记录，URL 已逐条保存。该报告应与 `S91R-C CONTROL_AUDIT_REPORT.md`、`S91_grc_pilot_protocol/PROTOCOL.md` 一起阅读。
