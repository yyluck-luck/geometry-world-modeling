# S43 最近邻独立核验：Causal Memory Acceptance

- 核验时间：2026-09-08 00:39:57（Asia/Shanghai）
- 核验人角色：独立 citation verifier；未参与原报告结论形成
- 被核验报告：`NEAREST_WORK_CAUSAL_MEMORY_ACCEPTANCE.md`
- 被核验 sources：`nearest_work_causal_memory_acceptance_sources.json`
- 总判定：**NEEDS_CORRECTION**
- 研究路线判定：**KEEP_CONDITIONAL_AFTER_CORRECTION_AND_EXPANDED_CITATION_NETWORK_AUDIT**
- Novelty 判定：**UNRESOLVED；不得写 first、novel、no prior work 或“已经证明创新”**
- 机器可读证据：`nearest_work_independent_verification.json`

## 1. 给新手的结论

原报告的核心想法还值得做实验，但现在不能说它已经是新方法。独立核验发现两类问题：

1. 原资料中有 **5 个论文题名错误**，另有一句关于 ReMind 的关键词判断不成立；
2. 原检索遗漏了至少 **2 篇会直接收紧创新边界的近邻论文**，其中 *Vision-Language Binding in In-Context Image Generation* 已经对“参考图如何因果影响生成图”做了路径干预。

同时，核验也没有在已经检查的一手论文中发现一篇工作同时完成以下五件事：

1. 干预运行时真正被选中的一条历史记忆；
2. 固定采样、相机、检索结果和其余内部状态；
3. 在所有真实消费路径上连贯地改变同一条记忆；
4. 用干预前冻结的几何支持区和面积基线定位生成结果中的效应；
5. 证明这个局部因果量能预测自然重访失败或收益，并用于接受、拒绝或重观察。

这只能解释为：**这五项的联合协议在本次核验集合中尚未被推翻。** 它不能解释为“领域里没有人做过”，更不能解释为“创新已证明”。由于检索确实漏掉了高压力近邻，任何论文式 novelty 语句都应继续冻结。

## 2. 输入完整性

| 输入 | 期望 SHA-256 | 实测 SHA-256 | 结果 |
|---|---|---|---|
| `NEAREST_WORK_CAUSAL_MEMORY_ACCEPTANCE.md` | `98ce907c5d0eeea334d8d7bc762abe9661f7eeaf0ebe45406fabfbe74db23261` | `98ce907c5d0eeea334d8d7bc762abe9661f7eeaf0ebe45406fabfbe74db23261` | PASS |
| `nearest_work_causal_memory_acceptance_sources.json` | `a44c9a8f873fea3b667084e9e4cfc8cb22ae1bbe0ed8fa4816e4565656cea150` | `a44c9a8f873fea3b667084e9e4cfc8cb22ae1bbe0ed8fa4816e4565656cea150` | PASS |

输入与任务指定的冻结版本完全一致。本次没有修改原报告或原 sources JSON。

## 3. 核验方法与证据边界

本次逐项检查了原 sources JSON 中的 20 条一手记录。题名、年份和 venue 优先以官方 proceedings 为准；没有正式 proceedings 的 2026 工作使用 arXiv 官方记录，并明确保留“preprint”状态。机制和比较结论来自论文正文、附录、作者项目页或官方代码。搜索结果页只用于发现候选，不作为机制证据。

代码方面，重新查询了原 JSON 记录的 13 个官方公开仓库 HEAD；13 个均与冻结记录一致。HEAD 一致只证明核验时远程默认分支指向相同提交，不证明训练代码完整、权重可用或结果可复现。

对于“没有做某项方法”的判断，本报告采用有范围的写法：只说“在已检查的正文、附录或公开代码中没有识别到”。关键词没有命中、一次搜索没有结果、仓库没有链接，都不构成领域不存在某方法的证明。

## 4. 必须更正的题名与陈述

### 4.1 五个题名错误

| ID | 原记录 | 一手来源核实后的正确题名 | 状态 |
|---|---|---|---|
| AGRA | *Making Foresight Actionable: Repurposing Representation Alignment for Causally Grounded Video World Models* | [*Making Foresight Actionable: Repurposing Representation Alignment in World Action Models*](https://arxiv.org/abs/2606.12217) | NEEDS_CORRECTION |
| Ada-RefSR | *Trust but Verify: Adaptive Conditioning for Reference-Based Image Super-Resolution* | [*Trust but Verify: Adaptive Conditioning for Reference-Based Diffusion Super-Resolution via Implicit Reference Correlation Modeling*](https://proceedings.iclr.cc/paper_files/paper/2026/hash/9d0947107ea92d6ce369dce7749180dd-Abstract-Conference.html) | NEEDS_CORRECTION |
| ReMind | *Teaching Video Generators to Remember: Training-Time Memory for Long-Horizon World Simulation* | [*Teaching Video Generators to Remember: Eliciting Dynamic Memory for Out-of-Sight State Evolution*](https://arxiv.org/abs/2605.25333) | NEEDS_CORRECTION |
| RECOMP | *RECOMP: Improving Retrieval-Augmented LMs with Compression and Selective Augmentation* | [*RECOMP: Improving Retrieval-Augmented LMs with Context Compression and Selective Augmentation*](https://proceedings.iclr.cc/paper_files/paper/2024/hash/bda88ed2892f5e61c9a9bf215c566913-Abstract-Conference.html) | NEEDS_CORRECTION |
| CARE | *CARE: Context-Aware Retrieval Enhancement for Countering Retrieval-Augmented Generation Failures* | [*Conflict-Aware Soft Prompting for Retrieval-Augmented Generation*](https://aclanthology.org/2025.emnlp-main.1371/)；CARE 指 Conflict-Aware REtrieval-Augmented Generation | NEEDS_CORRECTION |

年份和 venue 没有在这五条中发现对应的硬错误：AGRA、ReMind 是 2026 arXiv preprint，Ada-RefSR 是 ICLR 2026，RECOMP 是 ICLR 2024，CARE 是 EMNLP 2025。

### 4.2 ReMind 的负面关键词结论不能保留

原 JSON 写道：

> keyword checks of the arXiv HTML did not find counterfactual, causal, accept or reject terminology.

这句话按字面是错误的，官方全文含有 causal video generation 相关表述。即使全文完全没有这些单词，关键词缺失也不能证明方法缺失。可替换为：

> 对 ReMind 方法与附录的核验没有识别到“固定其他状态，对一条被选运行时记忆做干预，并估计生成区域总因果效应”的协议。ReMind 的已验证贡献是损坏记忆训练、保护锚点、检索以及 attention/KV-importance 类诊断。

ReMind 比原报告写得更接近“可靠证据选择”：它让模型面对可靠性不同的候选记忆，使用历史锚点，并讨论旧但可靠的证据何时应压过损坏的近期上下文。因此不能把它概括成单纯的 memory dropout。

## 5. 六篇指定重点论文的独立结论

### 5.1 VMem：Store/Select 很强，单来源因果效应未建立

[VMem，ICCV 2025](https://openaccess.thecvf.com/content/ICCV2025/html/Li_VMem_Consistent_Interactive_Video_Scene_Generation_with_Surfel-Indexed_View_Memory_ICCV_2025_paper.html) 将历史视图 ID 锚定到三维 surfel；针对查询相机渲染可见证据，通过频率投票选择历史视图，再把它们作为 novel-view generator 的条件，生成后继续写回记忆。原报告对存储、几何索引、选择和条件化机制的描述成立。

论文的模块实验和整体指标能说明 VMem 系统是否改善一致性，但不等同于“在同一推理状态中，只连贯改变一条被选历史视图，然后把总效应定位到该视图的几何支持区”。因此原报告的边界结论成立，但必须写成对该论文证据范围的阅读，不能写成领域不存在这种协议。

官方代码 HEAD 复核为 `39291e4f272f6b4f270691d930926ab5930f942e`，与原 JSON 一致。

### 5.2 SPMEM：三类记忆已覆盖系统设计，未做 per-source causal audit

[Video World Models with Long-term Spatial Memory，NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/467655d26fcc207bca08915dc91964c6-Abstract-Conference.html) 使用近期帧形成 working memory，以几何约束的静态点云形成 spatial memory，并以稀疏历史帧形成 episodic memory，再把这些记忆作为条件注入。原报告的机制与 venue 判断成立。

论文的组件消融没有隔离一条被选 memory source 的固定状态因果效应，也没有把这一效应与输出几何支持做面积控制比较。另一个小的术语提醒是：公开项目和仓库使用 SPMEM 名称，但正式论文题名本身是 *Video World Models with Long-term Spatial Memory*；引用论文时应优先用正式题名。

官方代码 HEAD 复核为 `89e1f70e7d8b4087b87306f958406cf9e4b2b2a7`，与原 JSON 一致。

### 5.3 Memory Forcing：已经证明错误空间上下文可能伤害生成

[Memory Forcing，arXiv 2025](https://arxiv.org/abs/2510.03198) 明确报告：模型过度依赖不足的 spatial context 时，新场景生成质量会下降。它使用 Hybrid Training 区分探索时的 temporal memory 与重访时的 spatial memory，并包含 Chained Forward Training、geometry-indexed memory 和 Point-to-Frame retrieval。

因此，“错误或不足的空间记忆会伤害生成”本身不是当前候选的新发现；“训练或上下文构造应随探索/重访情形变化”也已有直接近邻。尚未在该论文中识别到的是：对一次查询中的一条实际记忆做固定状态、全消费路径一致的干预，再将其因果效应定位并转为单样本接受决定。

### 5.4 I²AM：已经有 reference-to-region、mask 和随机区域基线，但不是因果干预

[I²AM，ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/c4a59e985de8b134328f41a47bc7dfac-Abstract-Conference.html) 聚合 diffusion steps、attention heads 和 layers 的 cross-attention，构造 reference-to-generated 与 generated-to-reference 双向 attribution map。SRAM 还能从一个选定的生成 patch 反查 reference patches。

原报告将它描述成 reference-to-generated attribution 基本正确，但低估了它的评测压力：论文已经用预存 task mask 做内外区评价，也用 object box 和随机 10–30% 区域做比较，还用 attention map 诊断并训练 refined model。由此，以下内容均不能单独称为当前候选的新意：

- 画 reference-to-output 热图；
- 用一个事先存在的 mask 评价热图；
- 计算区域内外差异；
- 加随机区域基线；
- 用 attribution map 辅助下游改进。

I²AM 仍没有在固定状态下删除或替换一个 reference，也没有估计该 reference 的总因果效应。可守住的差异只能是“来源干预产生的因果效应 + 干预前几何 support + 面积控制 + 自然失败预测”的联合。

官方代码 HEAD 复核为 `7c3e19ca3606f45a82439765b3f8fe0769d52215`，与原 JSON 一致。

### 5.5 AGRA：已经有世界模型空间因果干预、mask、内外敏感性和任务收益

[AGRA，arXiv 2026](https://arxiv.org/abs/2606.12217) 认为 attention 不足以说明因果影响，随后对 world-model hidden spatial token 做 zero、mean、shuffle 和 complement-swap 干预，以动作向量的欧氏偏差形成空间热图。它还使用人工标注的 hand-object interaction mask，对 interaction token 和 background token 计算 matched sensitivity ratio，并报告真实机器人成功率和 OOD 泛化。

原报告所说“干预对象是隐藏空间 token，结果是动作偏差，而不是一条运行时记忆到生成视频区域”是准确边界。但 AGRA 的能力应完整描述：它已经覆盖因果干预、区域 mask、内外对照和任务收益，不能再把这四个元素中的任何一个单独当作新意。

真正剩余的差异是：被干预对象必须是一次推理中实际选择的历史记忆项；结果必须是生成视频中的局部效应；support 必须由该记忆的几何关系在干预前定义；重放状态必须严格冻结；局部因果分数还应预测自然重访失败。

AGRA 官方项目页在核验时没有显示代码链接。这只是页面观察，不能据此声称代码不存在。

### 5.6 Ada-RefSR：在线、逐位置、错误参考抑制已经做过

[Ada-RefSR，ICLR 2026](https://proceedings.iclr.cc/paper_files/paper/2026/hash/9d0947107ea92d6ce369dce7749180dd-Abstract-Conference.html) 通过 learnable summary tokens 聚合 reference keys，再为每个 low-quality/output token 计算隐式相关性，经 sigmoid 得到 soft gate 并调制 reference-attention 输出。训练中含无关 HQ–reference pair；实验覆盖匹配比例、blur、affine transform 和 unrelated reference，并将 AICG 与无 gate、全局 gate 和其他 spatial gate 比较。

这使“单参考来源 + 在线空间门控 + 错误参考抑制 + 下游鲁棒性”成为已有能力。原报告说 generic confidence gate 不足以支撑 novelty 是对的，但 Ada-RefSR 的邻近程度应上调。

它仍不是历史 world memory 的 causal audit：没有固定状态来源干预、episodic item、几何产生的 pre-treatment support、abstain/re-observe 动作，也没有证明 per-example causal score 能预测自然重访失败。

官方代码 HEAD 复核为 `2d3d882db0d75dd77bf4c41c98c731be9520a275`，与原 JSON 一致。

## 6. 原检索遗漏的高压力近邻

### 6.1 最高压力遗漏：Vision-Language Binding in In-Context Image Generation

[*Vision-Language Binding in In-Context Image Generation*，arXiv 2026](https://arxiv.org/abs/2605.24624) 是本次独立核验发现的最重要漏项。它研究 FLUX.2 中 reference image 到 generated image 的因果路径，使用 T2I Lens、Attention Knockout 和 I2I-to-I2I Patching，区分 reference→text→image 与 direct reference→image 两条路径，并通过跨运行激活替换观察输出属性变化。

这篇论文直接覆盖了“参考来源、生成结果、因果干预、不同消费路径分析”，明显比只画 attention map 更接近候选。它仍没有从已检查材料中完成目标五项联合协议：对象不是视频世界模型中被选中的历史记忆项；分别分析路径不等于将同一来源在所有真实路径上连贯改变成一个总效应 estimand；没有干预前的三维几何支持和面积基线；也没有把分数链接到自然重访失败或收益。

因为它在原报告冻结日前已经公开，遗漏属于检索覆盖缺陷。它必须加入 closest-neighbor 表，并继续检查其前向、后向引用和作者后续工作。

### 6.2 高压力遗漏：MosaicMem

[*MosaicMem: Hybrid Spatial Memory for Controllable Video World Models*，arXiv 2026](https://arxiv.org/abs/2603.17117) 将 patch 提升到三维空间以支持定位和定向检索，提供 patch-and-compose 接口，并支持基于记忆的场景编辑。

它直接压缩了“patch/source 经过几何关系路由到局部区域”的设计空间。已检查的一手材料没有建立固定状态的单来源因果效应或自然失败驱动的接受分数，因此没有直接击穿五项联合协议；但任何关于几何局部记忆路由或 patch 级控制的新意表述都必须引用并对比它。

### 6.3 还应补入系统近邻表的两篇工作

- [*Compression and Retrieval: Implicit Memory Retrieval for Video World Models*](https://arxiv.org/abs/2606.23105)：attention-driven、viewpoint-conditioned implicit retrieval 与 context compression，进一步占据 Select/Consume 设计空间。
- [*DreamX-World 1.0: A General-Purpose Interactive World Model*](https://arxiv.org/abs/2606.16993)：camera-geometry memory retrieval、memory-conditioned scene persistence，以及对不完美 memory latent 的鲁棒机制，应该进入系统基线与相关工作审计。

这两篇属于系统近邻补充；前两篇属于会改变 closest-neighbor 结论强度的材料遗漏。

## 7. 全部 20 条原记录的结果

| 原记录 | 题名/年份/venue | 机制概括 | 原比较边界 | 独立结果 |
|---|---|---|---|---|
| VMem | 正确 | 正确 | 有范围地成立 | PASS |
| SPMEM paper | 正确；SPMEM 是项目简称 | 正确 | 有范围地成立 | PASS_WITH_NOTE |
| WorldMem | 正确 | 正确 | 有范围地成立 | PASS |
| VRAG | 正确 | 正确 | 成立 | PASS |
| Context-as-Memory | 正确；venue 来自作者项目页 | 正确 | 有范围地成立 | PASS_WITH_NOTE |
| Memory Forcing | 正确 | 正确，但已有探索/重访的情形自适应 | 有范围地成立 | PASS_WITH_SCOPE_NOTE |
| ReMind | **题名错误** | 方向正确但低估可靠性训练与诊断 | **关键词句错误** | NEEDS_CORRECTION |
| WorldTrace | 正确 | 正确 | 成立 | PASS |
| DAAM | 正确 | 正确 | 成立 | PASS |
| I²AM | 正确 | 正确但漏掉 mask、随机框基线和 refinement | 因果边界成立 | PASS_WITH_MATERIAL_OMISSION |
| DiffQuickFix | 正确 | 正确 | 成立 | PASS |
| LocoGen | 正确 | 正确 | 成立 | PASS |
| Activation Patching | 正确 | 正确 | 成立 | PASS |
| AGRA | **题名错误** | 正确但漏掉多种干预、mask、sensitivity ratio 和任务评测 | 核心边界成立 | NEEDS_CORRECTION |
| Ada-RefSR | **题名不完整** | 正确但低估逐 output-token 在线门控与鲁棒性实验 | 核心边界成立 | NEEDS_CORRECTION |
| Sufficient Context | 正确 | 正确 | 成立 | PASS |
| RECOMP | **题名漏 Context** | 正确 | 成立 | NEEDS_CORRECTION |
| CARE | **题名与缩写解释错误** | 基本正确 | 成立 | NEEDS_CORRECTION |
| STEVO-Bench | 正确 | 正确 | 成立 | PASS |
| MemoBench | 正确；谨慎保留 arXiv 状态是对的 | 正确 | 成立 | PASS |

更细的逐条机制、URL、状态和代码 HEAD 保存在机器可读 JSON 中。

## 8. 五项联合 gap 的压力测试

这里的“是/否”严格按整项要求判断。例如，一篇工作使用三维几何做检索，不等于它已经用几何 support 定位**因果输出效应**。

| 工作 | C1 单个运行时记忆项干预 | C2 其余状态严格固定 | C3 所有真实消费路径连贯改变 | C4 生成效应对 pre-treatment 几何 support/面积基线 | C5 预测自然失败或收益 |
|---|---|---|---|---|---|
| VMem | 否 | 否 | 否 | 否；几何用于检索与条件化 | 部分；系统级收益 |
| SPMEM | 否 | 否 | 否 | 否；几何用于记忆表示 | 部分；组件级收益 |
| Memory Forcing | 否 | 否 | 否 | 否 | 部分；情形级伤害与收益 |
| ReMind | 否 | 否 | 否 | 否 | 部分；可靠性训练与 importance 诊断 |
| I²AM | 否；没有来源干预 | 否 | 否 | 部分；非因果 mask 与随机框定位 | 部分；数据集诊断与 refinement |
| AGRA | 否；对象是 hidden token | 部分；受控 token 干预 | 否 | 部分；人工动作 mask，结果是 action deviation | 部分；任务级收益 |
| Ada-RefSR | 否；gate 不是因果干预 | 否 | 否 | 部分；逐位置 gate，不是几何因果效应 | 部分；错配鲁棒性与数据集收益 |
| Vision-Language Binding | 部分；外部 reference 的因果路径 | 部分；有 patching 控制但不是目标 replay contract | 否；多路径拆解不等于全路径统一干预 | 否 | 否；未链接自然重访失败 |
| MosaicMem | 否；没有因果来源干预 | 否 | 否 | 部分；三维 patch 路由和编辑接口 | 部分；系统级控制 |

在这组一手材料中，没有任何一行五项全为“是”。因此，目标联合协议没有被当前核验集合直接击穿。但由于本次已经证明原检索会漏掉强近邻，这个矩阵只能支持一个受限结论：

> 在已经逐篇核验的材料中，尚未识别到五项联合协议。该结论不证明领域不存在等价工作，也不支持 novelty 声明。

## 9. 对原报告核心判断的裁决

### PASS 的部分

- 把候选降为“待证的因果测量合同”，而不是直接称为创新网络模块，是正确的证据纪律。
- VMem、SPMEM、WorldMem 等已经占据 Store/Select；Memory Forcing、ReMind 等已经占据记忆消费训练与错误记忆鲁棒性；generic gate/abstention 已非常拥挤，这一总体地图成立。
- “注意力图不自动等于因果”“整模块消融不等于单来源效应”“固定重放是因果比较前提”“局部敏感不等于有益”的方法论判断成立。
- 原报告明确写出“搜索未发现不等于新颖”，这一边界必须保留。

### NEEDS_CORRECTION 的部分

- 五个错误题名必须在 Markdown 和 JSON 中统一修正。
- ReMind 的关键词负面句必须删除并换成方法级、有范围的判断。
- I²AM、AGRA、Ada-RefSR 的机制描述必须补全，否则会让目标协议看起来比实际更远离近邻。
- closest-neighbor 集合必须加入 Vision-Language Binding 和 MosaicMem；更广系统表应补入 Implicit Memory Retrieval 和 DreamX-World。
- “最强近邻只有 I²AM、AGRA、Ada-RefSR、Memory Forcing”这一检索结论已过时；Vision-Language Binding 至少应进入最高压力组。

## 10. 可以继续做什么，不能写什么

当前可继续做的最小实验仍然是原报告设计的 fixed-state F00/F11 pilot，但必须吸收近邻压力：

1. **从历史记忆项开始。** 干预单位必须是运行时实际选择的一条 history item，避免退化成 AGRA 式 hidden-token localization 或一般模块消融。
2. **一次性改全路径。** 同一来源的 CLIP、latent、replace 或其他真实消费表示必须连贯变化；分路径实验只做诊断。
3. **先冻结几何 support。** 在看干预结果之前，根据相机、深度或 correspondence 产生 support；同时报告面积基线，超越 I²AM 的随机区域比较。
4. **固定 exact replay。** 记录实际 noise、RNG、pose、K/Plücker、retrieval IDs、latents 和其他消费者状态；先用 A0 量出 replay 本底。
5. **链接自然失败。** 不能只证明区域会动；因果局部量必须预测真实重访 error/benefit，才能超过 AGRA 的受控敏感性与任务级评测。
6. **gate 放到最后。** Ada-RefSR 已覆盖在线逐位置参考 gate；只有在 causal score 有增量预测力、普通 gate 失败且 oracle 有 headroom 时，才值得训练接受模型。

当前可以使用的表述：

> 我们正在测试一个尚未被当前核验集合直接覆盖的联合协议：对被选历史记忆项做严格重放下的全路径干预，将生成效应与干预前几何支持比较，并检验该量能否预测自然重访失败。

当前不能使用的表述：

- “这是首个 causal memory acceptance 方法”；
- “过去工作没有做 source-to-region”；
- “过去工作没有用 mask、因果干预或在线门控”；
- “检索没有发现等价论文，所以方法是新颖的”；
- “已经达到 CCF-A/PhD 创新水平”。

## 11. 最终独立判定

**原报告不能按 PASS 接受，判定为 NEEDS_CORRECTION。** 原因不是候选已被某篇论文完全覆盖，而是资料中存在可验证的书目错误、一个不成立的负面关键词陈述、最近邻能力描述偏弱，以及实质性检索漏项。

五项联合合同在本次核验材料中仍未被直接满足，所以路线可以有条件保留。它现在的正确身份是一个待实验证伪、待扩展引用网络继续压缩的研究假设。完成更正与扩展检索之前，不授权任何 novelty 或优先权声明。

## 12. 一手来源索引

### 指定重点与最高压力近邻

- [VMem，ICCV 2025](https://openaccess.thecvf.com/content/ICCV2025/html/Li_VMem_Consistent_Interactive_Video_Scene_Generation_with_Surfel-Indexed_View_Memory_ICCV_2025_paper.html)
- [Video World Models with Long-term Spatial Memory，NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/467655d26fcc207bca08915dc91964c6-Abstract-Conference.html)
- [Memory Forcing，arXiv 2025](https://arxiv.org/abs/2510.03198)
- [I²AM，ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/c4a59e985de8b134328f41a47bc7dfac-Abstract-Conference.html)
- [AGRA，arXiv 2026](https://arxiv.org/abs/2606.12217)
- [Ada-RefSR，ICLR 2026](https://proceedings.iclr.cc/paper_files/paper/2026/hash/9d0947107ea92d6ce369dce7749180dd-Abstract-Conference.html)
- [ReMind，arXiv 2026](https://arxiv.org/abs/2605.25333)
- [Vision-Language Binding in In-Context Image Generation，arXiv 2026](https://arxiv.org/abs/2605.24624)
- [MosaicMem，arXiv 2026](https://arxiv.org/abs/2603.17117)

### 原 20 条记录中的其余一手来源

- [WorldMem，NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/470629a47e2d65ce0606c40055df5d26-Abstract-Conference.html)
- [Learning World Models for Interactive Video Generation，NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/e32310c3acb058d563a6a9e54d0e9000-Abstract-Conference.html)
- [Context as Memory，作者项目页](https://context-as-memory.github.io/)
- [Addressable Memory for Video World Models，arXiv 2026](https://arxiv.org/abs/2608.07408)
- [What the DAAM，ACL 2023](https://aclanthology.org/2023.acl-long.310/)
- [Localizing and Editing Knowledge in Text-to-Image Generative Models，ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/4bfcebedf7a2967c410b64670f27f904-Abstract-Conference.html)
- [On Mechanistic Knowledge Localization in Text-to-Image Generative Models，ICML 2024](https://proceedings.mlr.press/v235/basu24b.html)
- [Towards Best Practices of Activation Patching in Language Models，ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/06a52a54c8ee03cd86771136bc91eb1f-Abstract-Conference.html)
- [Sufficient Context，ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/33dffa2e3d2ab74a783d1a8c292f66d9-Abstract-Conference.html)
- [RECOMP，ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/bda88ed2892f5e61c9a9bf215c566913-Abstract-Conference.html)
- [CARE，EMNLP 2025](https://aclanthology.org/2025.emnlp-main.1371/)
- [STEVO-Bench，arXiv 2026](https://arxiv.org/abs/2603.13215)
- [MemoBench，arXiv 2026](https://arxiv.org/abs/2606.27537)

### 新增系统近邻

- [Compression and Retrieval: Implicit Memory Retrieval for Video World Models，arXiv 2026](https://arxiv.org/abs/2606.23105)
- [DreamX-World 1.0，arXiv 2026](https://arxiv.org/abs/2606.16993)
