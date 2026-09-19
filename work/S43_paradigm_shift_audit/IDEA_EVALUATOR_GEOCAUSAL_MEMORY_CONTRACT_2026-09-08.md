# GeoCausal Memory Contract：想法审稿式评估

- 评估日期：2026-09-08（Asia/Shanghai）
- 评估对象：对显式检索式视频世界模型中一条普通运行实际选中、当前可寻址的记忆来源，匹配干预前外生条件与非目标初态，连贯改变该来源在全部真实消费路径中的表示，重算全部下游后代，测量输出效应的几何局部性及其对自然重访错误或收益的预测力。
- 当前证据级别：候选问题与协议；真实 C1/C2 质量和因果实验尚未完成。
- 新颖性授权：`NONE`

## 1. First impression

- **Paper type：Novel Problem / Evaluation Setting。** 目前不是已成立的 Novel Method；只有因果量显示可预测且存在 oracle headroom 后，才值得发展接受、拒绝或重新观察的方法。
- **One-sentence story：** 世界模型把历史画面存下并选中，不代表它能正确寻址、真正使用、在正确空间位置发挥作用或最终带来收益；本项目要用同一来源的全路径一致反事实，把这六件事逐项证实或推翻。

这个故事具有清楚的“隐藏假设”：许多系统把检索命中、注意力、模块消融或最终平均质量当作记忆工作的证据。候选的价值在于要求建立来源级、空间级和效用级的闭环。现阶段最诚实的定位是新的诊断任务和证据合同，而不是宣传一个更复杂的网络。

## 2. Fatal-flaws audit (early gate)

| # | Flaw | Severity | Defense |
|---|---|---|---|
| 1 | **F9：目前还没有被 C1/C2 质量评测确认的自然失败。** 如果先写 gate 或训练接受器，再去寻找能展示它的案例，问题会显得人为制造。 | MAJOR | 先完成 C1 盲评分与 C2 确认，只接受可重复的自然重访失败作为种子。若没有稳定自然失败，立即停止这个方向；不使用合成变化冒充现实问题。 |

**F1 novelty audit：当前窄表述没有被判为致命重复，但边界很脆弱。** 单组件重叠非常强；只保留“显式检索 + 稳定 source ID + 普通运行选择 + 全路径一致编辑 + 后代重算 + 干预前几何定位 + 独立 signed benefit”这一联合协议。若实验只做其中一项，F1 将升级为致命重复。

五个最接近工作的作者、年份与差异轴如下。

| 最近工作 | 作者、年份 | 已覆盖内容 | 与候选仍不同的轴 |
|---|---|---|---|
| I3DM | Jia Li et al., 2026 | 空间置信图、最大覆盖选择、3D 对齐和可靠区域注入 | 未建立普通运行单来源的全路径 post-selection effect、匹配 mask 局部富集和 signed benefit |
| WorldTrace | Xindi Wu et al., 2026 | 位置可寻址性与内容信息量分离 | Address 阶段；未建立六阶段联合合同 |
| TetherCache | Yu Meng et al., 2026 | attention+diversity 选择和 recalled K/V trusted alignment | 已覆盖选择/修复；候选必须证明几何因果量提供普通 proxy 没有的增量信息 |
| Echo-Memory | Wayne King et al., 2026 | 在匹配设置中拆分 storage、readout、recurrence，并分开 replay/return | 已否定“存了等于用了”；未做 stable single-source 的几何因果定位和 matched signed benefit |
| CUE-R | Siddharth Jain and Venkat Narayan Vedam, 2026 | 优先 actually-used evidence，做 REMOVE/REPLACE/DUPLICATE、paired utility 和协同 | 对象是 RAG 证据；论文明确把 prompt-level 结果限制为 interventional sensitivity；没有视频相机与几何支持 |

WorldKV、CaR、DensityKV、GIM-World、Matrix-Game 3.5 和 SPMEM 继续作为额外强压力与系统基线。

上述检索只能支持“已核材料中未识别到联合等价协议”，不能证明领域内绝对不存在同类工作。

## 3. Lifecycle and capability match

| Aspect | User's input | Assessment |
|---|---|---|
| Idea category | 视频世界模型的因果诊断与评测 | **Frontier Exploration / Benchmark**；若后续出现可训练接受器，才进入 Innovative Technique |
| Lifecycle | 用户未指定截稿日；领域在 2026 年更新很快 | 完整跨模型论文估计 **3–9 个月**；单模型 kill experiment 可先在约 **1–3 周**内争取完成。这是计划估计，不是已投入工时证明。 |
| Weekly effective hours | 未提供；用户要求 AI 持续自主推进 | 不能据此推断人的有效科研工时；自动化可降低工程成本，但科研判断、视觉质检和最终写作仍需人审。 |
| Hardware and skill | M3 Max 64GB，本地 MPS/CPU，无远程 GPU；用户是该方向新手 | 本地可做一个模型的小规模审计；多模型、多种子和训练型方法不适合直接全量展开。 |
| Fit | 能做窄范围 pilot，完整顶会规模存在资源与经验缺口 | **Yellow** |

## 4. Five-dimension radar

| Dimension | Score 1–10 | Evidence | Lift suggestion |
|---|---:|---|---|
| Higher | **6** | 机制上可识别“有记忆但用错”的样本，并可能改善重访质量；尚无真实生成增益。**Mechanism-based, not yet confirmed by data.** | 只有 causal score 能指导接受/重观察并降低总体 paired loss 后才上调。 |
| Faster | **3** | F00/F10/F01/F11、exact replay 和多种子都会增加推理量；当前没有加速机制。 | 先开发一次运行日志复用和最小 source pilot，报告额外推理次数、墙钟时间和峰值内存。 |
| Stronger | **8** | 将 Store、Select、Address、Consume、Localize、Benefit 分开，可在路径冲突、伪注意力和无益记忆下主动失败，理论上比平均质量/模块消融更抗混淆。**Mechanism-based, not yet confirmed by data.** | 在不同场景、来源和至少两种消费者上复现，并加入 exact-replay、单路径冲突和 dormant-pathway 反例。 |
| Cheaper | **6** | 若从已有运行日志和自动几何支持生成标签，可减少逐帧人工解释；但反事实推理本身昂贵。**Mechanism-based, not yet confirmed by data.** | 量化每个有效样本的 GPU/CPU 时间与人工标注分钟数；先验证廉价代理能否逼近完整分数。 |
| Broader | **7** | 六阶段证据合同原则上可跨具有稳定来源身份和可审计多消费路径的显式检索式视频世界模型使用，但排除没有天然全局 item 的连续/压缩记忆。**Mechanism-based, not yet confirmed by data.** | 严格限定模型家族；用第二个架构检验，不外推到隐状态不可追踪的所有世界模型。 |

论文最应强调 **Stronger、Broader、Higher**，其中 Higher 必须等实际质量或风险结果，Stronger/Broader 也必须通过跨案例验证。

## 5. Paradigm-shift probe

| Probe | Yes or No | Rationale |
|---|---|---|
| First Principles | **Yes** | 直接挑战“检索到/注意到了就等于记忆有效”的默认替代指标。 |
| Elephant in the Room | **Yes** | 重访时场景会变是该领域公开展示的核心问题，但系统平均分无法指出是哪条记忆在哪个区域造成了问题。 |
| Technology Cycle | **Yes** | 2025–2026 的显式空间/KV 记忆开始暴露 source、patch、chunk 和多路径接口，使过去难以做的来源级审计变得可实施。 |
| Hamming's Rule | **No** | 即使本问题解决，也主要改变显式检索式视频世界模型的评测与调试，尚不能声称改变整个世界模型领域。 |

**Disruptive potential：possible。** 三项为 Yes，说明它值得用最小实验检验；没有实证前不能称为颠覆式成果。

### Supervisor-Skills 2.3 对照

| 2.3 原则 | 本项目的具体落实 | 当前缺口 |
|---|---|---|
| 第一性原理 | 回到“记忆的目的应是让自然重访更正确”，不把存储量、检索命中或注意力当最终目标。 | 尚未证明新的因果量比普通指标更接近自然收益。 |
| 房间里的大象 | 正面研究“系统明明存了也选了，重访仍会变”的失败，而不是只在平均分上刷小幅提升。 | C1/C2 自然失败仍待盲评分确认。 |
| 技术周期 | 利用新一代显式 memory/KV 系统提供的 source、patch、chunk 与多路径接口，做以前难以进行的来源级审计。 | 必须证明这些接口足够完整，不遗漏隐式旁路。 |
| Hamming 重要问题 | 保留“世界模型如何知道自己的记忆在何时、何地值得信任”作为长期问题。 | 当前 pilot 只能回答一个模型的一小段，不能外推整个领域。 |

遵循 2.3 不等于强行宣称颠覆。当前执行策略是：用渐进路线完成真实 baseline 和统计闭环，用高风险路线测试六阶段问题；任何 kill 条件触发就如实降级。

## 6. Feasibility

| Risk | Level | Mitigation |
|---|---|---|
| Compute | **High** | 本机可运行已有 VMem 小样本，但四格反事实、多种子、跨场景会快速放大成本。先做一个自然失败、一个来源、A0 与 F00/F11；只有两道早期门通过才扩展 F10/F01 与多样本。 |
| Data | **Medium** | 已有生成链和真实 RGB-D 代理，但尚无确认的自然重访失败集合，也没有人类质量标注。先从盲评分 C1/C2 中冻结种子，再决定是否需要小规模双人标注。 |
| Engineering | **High** | 必须覆盖 CLIP、replace/latent 及其他真实消费路径，保持 source ID 和几何不变，并避免冻结下游中介；任一路径遗漏都会破坏主张。使用路径清单、同源哈希、exact replay 和 F10/F01 冲突诊断。 |
| Timeline | **High** | 相邻工作在 2026 年密集出现，新颖窗口可能迅速收窄。每完成一个 kill gate 就刷新近邻检索；不在单模型结果前写大规模方法。 |

## 7. Verdict

**Accept with Revisions — worth pursuing, pending the validation experiment.**

它值得继续，因为问题清楚、可以被一组低成本实验推翻，并且联合证据链在已核一手材料中仍有区别。但它还不是可投稿创新：F9 的 MAJOR 问题必须由真实生成失败解决；F1 的脆弱边界必须由非显然实证规律和最近工作对照守住，不能靠写作解决。

Top three actions to take first:

1. 完成 C1 盲评分和 C2 独立确认，冻结至少一个可重复的自然重访失败；若没有，停止该方向。
2. 对该失败做 A0 exact replay 和 source-coherent `F11−F00`；只固定干预前外生条件与非目标初态，重算目标来源全部后代。若效应不超过 replay，本想法失败。
3. 若因果门通过，再检验干预前 geometry support 的局部性及对自然错误的样本外增量预测，并与 attention、pose overlap、retrieval score、WorldTrace 式 addressability 修复、TetherCache 式修复和简单 gate 比较。

## 一手来源

- [SPMEM / NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/467655d26fcc207bca08915dc91964c6-Abstract-Conference.html)
- [WorldModelBench / NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/4ec03ed08a3fcb59e1c815b5598beff1-Abstract-Datasets_and_Benchmarks_Track.html)
- [Long-Context State-Space Video World Models / ICCV 2025](https://openaccess.thecvf.com/content/ICCV2025/html/Po_Long-Context_State-Space_Video_World_Models_ICCV_2025_paper.html)
- [WorldTrace](https://arxiv.org/abs/2608.07408)
- [WorldKV](https://arxiv.org/abs/2605.22718)
- [CaR](https://arxiv.org/abs/2606.23105)
- [DensityKV](https://arxiv.org/abs/2608.27922)
- [GIM-World](https://arxiv.org/abs/2606.02436)
- [Matrix-Game 3.5](https://arxiv.org/abs/2608.29910)
- [Echo-Memory](https://arxiv.org/abs/2606.09803)
- [TetherCache](https://arxiv.org/abs/2606.13035)
- [CUE-R](https://arxiv.org/abs/2604.05467)
- [Is This the Subspace You Are Looking for? / ICLR 2024](https://openreview.net/forum?id=Ebt7JgMHv1)
- [SelectiveNet / ICML 2019](https://proceedings.mlr.press/v97/geifman19a)
