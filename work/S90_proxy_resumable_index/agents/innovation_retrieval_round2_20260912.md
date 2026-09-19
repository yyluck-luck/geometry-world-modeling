# 英文原文检索 Round 2：未来几何效用与风险校准近邻

检索时间：2026-09-12 06:58:48 UTC。范围限定为论文原文、正式会议/期刊页面或作者论文页面；没有运行模型。下面的“未见”表示本次核读范围内没有找到，不是证明文献空白。

## 1. 最接近的已核原文

### R2M-Bench（arXiv:2608.27328v1，2026-08-27，预印本，未核到正式会议接收）

原文：[arXiv HTML](https://arxiv.org/html/2608.27328)。论文第 3 节构造 100 个场景和三种离开—返回轨迹；第 4.1–4.3 节把返回帧与同一 rollout 内的 gap-matched non-revisit pair、short-range pair 比较，定义 MemoryGain 和 Normalized Memory Ratio。第 4.4 节包含 local geometric correspondence；第 5 节报告 300 个实例、7 个 world models，并做 motion/confound 诊断。原文还明确指出 MemoryGain 是行为层面的相对测量，不能解释为内部 memory 的因果估计；NMR 在动态范围很小时可能不稳定。

与 GRC 的关系：

- **已覆盖的部分**：未来/重访一致性不能只用绝对相似度评价；必须用同一 rollout 的匹配对照，控制慢运动、保守渲染和一般时间稳定性。
- **尚未覆盖的差异**：R2M-Bench 是 model-level benchmark，不选择历史记忆，也不为每一条历史给出可部署风险；它的局部几何指标是评价维度，不是 risk-calibrated selector。
- **对 GRC 的直接压力**：GRC 不能只报告未来 RGB/几何绝对误差；至少要增加 gap-matched temporal baseline，报告 revisit-specific geometric gain，并说明收益是否只是模型整体稳定性。

### WorldPack（arXiv:2512.02473；arXiv 当前标注 Published in TMLR 09/2026）

原文：[arXiv HTML](https://arxiv.org/html/2512.02473)。第 1–2 节把空间检索和压缩合并；第 4.2 节使用 3D spatial relevance 做动态压缩率分配：与当前视角重叠高的帧保留高分辨率，较不相关帧压缩但不完全删除。第 5–6 节在 LoopNav/Minecraft 的长期空间一致性和空间推理上与强基线比较；第 7 节讨论限制。

与 GRC 的关系：

- **已覆盖的部分**：固定上下文预算下利用空间相关性分配记忆容量；“几何选择 + 固定预算”本身不能作为新贡献。
- **尚未覆盖的差异**：WorldPack 的选择/压缩分数来自当前视角的空间相关性，论文并未把每条历史的校准风险与独立未来几何误差建立选择条件保证。
- **必须击败的基线**：WorldPack 风格的空间重叠/几何相关性分配，不能只和随机或最近帧比较。若 GRC 只是在其分数上加一个风险项而没有未来 signed utility 增量，很可能被审稿人判为重命名或组合。

### GIM-World（arXiv:2606.02436v1，2026-06-01，预印本；本轮重新核读原文）

原文：[arXiv HTML](https://arxiv.org/html/2606.02436v1)。第 3.3 节用 camera-queryable geometry supervision，把几何信息压进固定大小 memory；第 3.4 节明确给出固定预算子集目标 `I(S; H\\S)`，并用 pose-time GP posterior variance 与 greedy pruning。第 4 节在 MIND 上报告 memory、action 和 3D geometry 指标。

与 GRC 的关系：

- **已覆盖的部分**：几何监督、固定预算、信息增益/子模贪心和跨视角几何一致性已经是公开设计空间。
- **尚未覆盖的差异**：GIM 目标是从历史中保留能解释其余历史的 subset；它不是对“未来查询几何损失”的风险校准，也没有逐条历史的 deployment-time conformal 语义。
- **必须击败的基线**：GIM 的 GP/MI pruning 或同等 pose-time coverage 代理；否则不能称 GRC 的 future utility 新颖。

### CAP（JMLR 26(287), 2025；跨领域统计近邻）

原文：[JMLR 页面](https://www.jmlr.org/papers/v26/24-0452.html)。CAP（Calibration after Adaptive Pick）研究先选择样本、再对被选样本提供 prediction interval 的 post-selection calibration，并讨论 online temporal multiplicity、selection-conditional coverage 和 distribution shift 下的长期 FCR 控制。

与 GRC 的关系：

- **已覆盖的部分**：一旦选择规则会影响校准样本，不能把普通 split conformal/CRC 的保证直接搬到自适应选择后；“策略级风险”比“每条记忆的 q 值”更接近正确对象。
- **尚未覆盖的差异**：CAP 不是视频记忆或几何预测方法；它没有证明跨视角、动态场景的交换性，也没有 world-model future-position loss。
- **对 GRC 的直接压力**：如果 GRC 使用 conformal 名称，必须明确 adaptive-pick 后校准单位、交换性/漂移假设和边际还是 selection-conditional 保证；否则只能称经验 risk score。

## 2. 本轮检索后的判断

目前没有在上述原文中找到“对历史记忆逐项计算经校准的几何风险，并在固定消费预算下证明它改善未见未来位置误差”的完整方法。这个结果只能叫**当前核读范围内未见完整组合**；它不授权新颖性，也没有排除未检索工作、同期预印本或等价表述。R2M-Bench 使评价协议压力更高，WorldPack/GIM 使几何固定预算选择的组件压力更高，CAP 使风险保证的统计条件压力更高。

## 3. 仍可保留的三个候选变体（均未授权 novelty claim）

### 变体 A：Relative Future Geometric Utility Selector

把 GRC 的未来目标改成 R2M 风格的相对未来几何收益，而不是绝对误差：

`MG_geo = score(revisit pair) - score(gap-matched non-revisit pair)`，再以独立未来深度/位置真值定义 signed utility。

**实质差异**：R2M-Bench只评价完整模型；此变体在相同候选池中学习/选择历史，并把相对重访收益作为 selector 的目标。它只有在 risk+utility 比 WorldPack/GIM/coverage/距离基线提供额外未来收益时才有意义。

**必须击败**：absolute future loss、同一 rollout gap-matched baseline、最近时间、相机距离、覆盖贪心、WorldPack/GIM 风格空间相关性。

**可证伪预测**：在未调参的重访/遮挡后查询上，risk+utility 的相对几何收益稳定高于 utility-only 和 coverage；若仅在慢运动或低动态范围序列有效，停止方法主张。

### 变体 B：Adaptive-Pick Geometry Risk Calibration

不再宣称每条历史 `q_i` 是未来误差上界，而是把完整选择策略 `π_φ` 作为校准对象；借鉴 CAP 的 adaptive-pick 语义，在独立查询上校准“被策略选中后”的未来几何损失或区间覆盖。

**实质差异**：相对 CRC 的新增点只能是视频重访、几何误差和选择后条件；不是把 conformal 分位数写进公式。需要处理临近帧的依赖、场景/时间漂移和未来查询选择。

**必须击败**：split conformal、已有 CRC、CAP 式 selection calibration 的直接适配、未校准 risk-only 和 utility-only。所有方法使用相同 calibration/test split 和同一候选池。

**可证伪预测**：在冻结策略族和预先规定的损失下，选择后风险覆盖达到目标区间，同时不牺牲超过 `δ` 的未来几何效用；若只能得到边际平均控制、不能得到选择后控制，必须收窄主张。

### 变体 C：Fixed-Budget Risk–Utility Pareto Memory

把风险项改成可测的 Pareto 曲线：固定候选池、固定历史槽位和总消费预算，逐步改变允许风险，报告未来几何误差—覆盖—成本的前沿，而不预设 `Σq_i` 或 `1−1/e` 定理。

**实质差异**：WorldPack/GIM 已有几何相关性和固定预算；潜在差异只在于用独立未来真值定义 risk/utility 前沿，并显示风险阈值是否提供跨场景可迁移的选择规律。

**必须击败**：WorldPack 几何相关压缩、GIM GP/MI pruning、VMem surfel-indexed retrieval、最近/覆盖/随机和同成本 utility-only。

**可证伪预测**：在相同总计算成本下，Pareto 曲线在至少一个未见场景族上严格优于空间覆盖基线；若优势仅来自更多特征计算或额外未来信息，停止。

## 4. 推荐的近期动作

先完成 Gate 0 数据资格和 Gate 1 2×2 机制诊断。取得合格历史—未来配对后，优先实现变体 A 的**评估协议**，不先训练新模型：先固定风险分数、候选池、`k`、同成本 baseline 和相对未来几何指标，再做一次小型 selection pilot。只有 A 的风险—signed utility 关系成立，才考虑 B 的 selection-conditional calibration；C 可作为统一效率/风险曲线的报告方式。

如果没有未来真值、相对重访对照或固定成本，三个变体都应保持 UNKNOWN，不能通过公式或名称升级为创新。
