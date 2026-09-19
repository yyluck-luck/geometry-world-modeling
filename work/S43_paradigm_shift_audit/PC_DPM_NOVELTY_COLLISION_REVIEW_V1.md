# GeoCausal Memory Contract 与 PC-DPM：2024–2026 新颖性碰撞审查 V1

- 审查日期：2026-09-08（Asia/Shanghai）
- 审查对象：**GeoCausal Memory Contract** 与条件式方法候选 **Provenance-Coupled Dual-Path Memory（PC-DPM）**
- 审查性质：fresh、对抗式、source-only 文献审查；不使用尚未完成的实验结果替方法背书
- 证据范围：项目已冻结的一手文献表，加上本轮核验的论文原文、顶会官方页面与 arXiv 原文；时间窗为 2024-01-01 至 2026-09-08
- 证据限制：这是高压力的最近邻碰撞审查，不是对全部论文、专利、代码分支和未公开工作的穷尽证明；“未在已核来源中识别到”不能写成“领域中不存在”
- 当前新颖性授权：`NONE`

## 1. 裁决

| 候选 | 当前裁决 | 可保留的定位 | 不能成立的定位 |
|---|---|---|---|
| GeoCausal Memory Contract | **KEEP_AS_ARCHITECTURE_SCOPED_MEASUREMENT_HYPOTHESIS** | 面向“显式检索、稳定 source ID、全部 appearance consumer 可枚举”的视频世界模型，检验一条普通运行实际选择的来源是否可寻址、产生全路径因果影响、在预先定义的几何区域内起作用，并对独立自然重访有正或负收益 | 不能称为已建立的新 benchmark、通用世界模型定律或已证明的新发现；联合协议目前仍没有真实实验结论 |
| PC-DPM | **HIGH_COLLISION；REJECT_AS_STANDALONE_METHOD_NOVELTY_TODAY** | 一个只在观测到稳定跨路径冲突后才启用的、特定架构修复假说 | “双路径”“source token/ID”“几何 attention”“双记忆”“可信 gate”“utility teacher”“accept/reject”任何单项均已高度拥挤；当前不能称为新方法或顶会级贡献 |

本轮没有在已核来源中识别到下面这个**完整交集**：

> 对同一、稳定可追踪的运行时来源，要求所有可枚举 appearance consumer 使用同一 source 边际权重；以全路径一致干预、几何局部效应和独立自然重访 signed Benefit 产生离线教师，再只用生成前信息预测 accept / reject / re-observe。

但“没有找到完整交集”并不足以救活 PC-DPM。最强近邻已经把它拆成若干成熟部件；更严重的是，**相同 source 权重**本身存在简单数学反例。PC-DPM 要成为可投稿方法，必须先证明跨路径差异确实是错误而非功能互补，并证明共同权重比独立权重、软一致性和统一单路架构更好。

## 2. 冻结研究问题

**RQ1：** 2024–2026 的工作已经覆盖候选的哪些组件和组件组合？

**RQ2：** 哪个可操作、可证伪的差异仍未被已核近邻覆盖；最强反例是什么？

**RQ3：** 在没有自然失败、因果量和样本外收益之前，怎样表述问题才不会过度声称？

## 3. 被审候选的精确定义

### 3.1 GeoCausal Memory Contract

合同把“有记忆”拆成六个不能互相替代的阶段：

`Store → Select → Address → Influence → Localization → Benefit`

它要求研究对象具有稳定来源身份，并对普通运行已经选中的来源做同随机性、同外生条件的成对干预。干预必须覆盖该来源的全部真实 appearance consumer，重算其全部下游后代；空间效应必须相对逐像素 replay 和 matched-negative control excess 衡量，并落在干预前冻结的 source-target 几何支持；Benefit 必须相对从未进入模型的同步真实重访参考，逐 sign、target 和 replacement 报告。

因此，合同不是“注意力图”“删掉整个记忆模块”或“最终平均分变好”的别名。它试图连接来源级因果影响、几何责任与真实收益。但在当前阶段，它仍是**测量假说和否证协议**，没有真实数据证明这六阶段之间存在系统性断裂。

### 3.2 PC-DPM

PC-DPM 只有在 F10/F01 显示 slotwise latent path 与 global-mean semantic path 出现跨 scene、跨 seed 的可重复来源冲突，并且 source-level signed Benefit `B_i` 存在稳定正负差异时才允许进入方法阶段：

1. 为每个来源保留稳定 provenance ID；
2. semantic 与 latent appearance consumer 对来源采用同一组归一化边际权重；
3. 以跨路径冲突作训练期诊断；
4. 用昂贵的、来源级、全路径、几何定位 signed `B_i` 生成离线教师标签；
5. 学生只读取生成前可见的 addressability、source-target geometry、retrieval、attention prior 和 memory-trust 特征；
6. 学生输出收益区间及 accept / reject / re-observe，并用总体损失、risk–coverage、clean false rejection 和跨 scene/consumer 泛化评价。

## 4. 检索与判定方法

为主动寻找撞车，本轮从七条互相挑战的路线核验：

1. **显式/隐式世界记忆与地址化**：VMem、SPMEM、WorldMem、WorldTrace；
2. **几何检索、投影与局部注入**：I3DM、MosaicMem、Matrix-Game 3.5、WorldStereo、Spatia；
3. **双路或多路参考条件**：Phantom、Dual-Granularity Memory、WorldStereo；
4. **来源身份与多参考绑定**：Movie Weaver、PoCo；
5. **可信度、选择与自适应抑制**：Ada-RefSR、TetherCache；
6. **来源到输出的定位与因果干预**：I²AM、LocoGen、Activation Patching；
7. **逐证据效用与轻量代理**：CUE-R、Utility-Oriented Visual Evidence Selection；
8. **分层、细粒度和参考式评测**：MomentSeeker、Hi3DEval、Ref4D-VideoBench；
9. **推理期 reward 选择与主动再观察**：Inference-time Physics Alignment、AW4RE。

判定使用以下规则：

- 论文明确描述的能力记为“明确”；只有抽象相似但对象、干预或评价不同的记为“部分”；
- 论文没有报告某能力，只能写“未在已核材料中识别到”，不能据关键词缺失证明没有；
- 正式顶会论文与 2026 年预印本分开标注；预印本用于碰撞压力，不被冒充为已经同行评审的顶会论文；
- 测试通过、模块名字不同、任务域不同，都不能自动证明新颖；
- 只有能被实验推翻、且强基线无法解释的差异，才有保留价值。

## 5. 组件碰撞图

| 候选组件 | 2024–2026 最近邻 | 碰撞程度 | 审查结论 |
|---|---|---:|---|
| 显式空间记忆与来源检索 | VMem、SPMEM、WorldMem、MosaicMem、Matrix-Game 3.5 | 极高 | 存储、检索、空间索引和重访均不是新概念 |
| Address 与 Select 分离 | WorldTrace | 高 | “选中了但读不到”已经被明确提出；合同可以把它纳入审计，但不能把该分解单独当创新 |
| target-view 几何对齐与可靠区域注入 | I3DM、WorldStereo、Spatia、Matrix-Game 3.5 | 极高 | 几何支持、覆盖选择、投影、z-buffer、可靠区域 gating 已是强基线 |
| 低层细节 + 高层语义双路径 | Phantom | **直接碰撞** | Phantom 明确用 VAE 编码参考图的低层细节，用 CLIP 编码高层语义，并分别送入 MMDiT 的视频与文本分支；“latent + semantic 双路”不能称新 |
| 双记忆/多记忆互补 | Dual-Granularity Memory、WorldStereo、Matrix-Game 3.5 | 极高 | 双记忆故事已经拥挤；多条记忆路径的组合也不是新颖依据 |
| 多参考来源绑定与防混淆 | Movie Weaver、PoCo、Phantom | 高 | 每个 reference 的身份、锚定、位置编码和 association 控制已有直接工作 |
| 可信 gate、坏参考抑制、召回校准 | Ada-RefSR、TetherCache | 极高 | trust/gate/reliability 不能作为 PC-DPM 主创新 |
| source-to-region attribution | I²AM | 高 | 参考到生成区域的双向归因图已有成熟近邻；attention attribution 仍不是因果量 |
| 干预式定位 | LocoGen、Activation Patching | 高 | 替换/恢复、metric 与 corruption 选择敏感性已知；本项目只能靠更严格的来源、全路径、几何和自然收益联合定义区别 |
| 单证据 REMOVE/REPLACE/DUPLICATE 与 signed utility | CUE-R | **直接抽象碰撞** | “逐 item 干预看有益或有害”不是新问题；CUE-R 还显示证据存在非加性交互 |
| utility surrogate / 轻量学生 | Utility-Oriented Visual Evidence Selection | 高 | “昂贵 utility 作教师、轻量模型预测”本身不能称新 |
| accept/reject 与 risk–coverage | 选择性预测的成熟文献；本项目已有强基线清单 | 极高 | 评价方式必要但不是创新来源 |
| 端到端结果与准确访问分离 | MomentSeeker（NeurIPS 2025 Datasets and Benchmarks Track） | 高 | “最终任务做对不代表准确访问证据”已有直接评测逻辑；可作 Address 层诊断基线 |
| 层级/局部有效性评测 | Hi3DEval（NeurIPS 2025 Datasets and Benchmarks Track）、Ref4D-VideoBench（CVPR 2026） | 高 | object/part、参考式、多维细粒度评测已成熟；只能支持更强评价，不能单独建立 source-level 因果性 |
| reward 引导的推理期候选选择 | Inference-time Physics Alignment（CVPR 2026） | 高 | 用 reward 搜索和引导多条 denoising trajectory 已有主会近邻；PC-DPM 的 risk action 必须与此类 test-time selection 比较 |
| evidence-supported 区域与 active retrieval / exploration | AW4RE（ICLR 2026 World Models Workshop） | 概念压力高，发表层级较弱 | 支持区/非支持区和主动相机查询已经被提出；它是 workshop 工作，不能单独用来否定主会级新颖性，但必须作 re-observe 概念与系统基线 |

### 5.1 最直接的双路径碰撞：Phantom

[Phantom（ICCV 2025）](https://openaccess.thecvf.com/content/ICCV2025/html/Liu_Phantom_Subject-Consistent_Video_Generation_via_Cross-Modal_Alignment_ICCV_2025_paper.html) 的视觉编码器同时使用 VAE 和 CLIP。论文原文明确说明，参考图的 VAE latent 与视频 latent 合并，提供低层细节；CLIP 特征与文本特征合并，提供高层语义并补足 VAE 低层表示。它还支持单/多参考动态注入。

这与当前 VMem 假说中的“slotwise latent path + semantic path”在机制层高度相邻。Phantom 没有报告同一来源在两个分支中的边际权重必须相等，也没有 source-level signed natural-revisit Benefit 教师；这使“跨消费者 provenance 一致性”仍可被测试，却不能消除一个基本事实：**双路径互补及其联合注入已经不是新设计。**

### 5.2 最强架构反例：Matrix-Game 3.5

[Matrix-Game 3.5（2026-08-30 技术报告）](https://arxiv.org/html/2608.29910) 把 anchor、历史 context、检索 patch 和 noisy target 放进同一个 pose-aware token sequence，用一个 self-attention stack 处理，而不是为这些条件建立相互独立的 cross-attention 分支。它的 patch memory：

- 用深度、内参和位姿把历史 latent patch 提升到 3D；
- 按目标视角投影、z-buffer 和 coverage 选择构造 aligned memory canvas；
- 记录每个检索 patch 的 source frame 与原始 patch location 的 reverse mapping；
- 将 patch、context 和 dynamic reference-token memory 放入统一的 pose-aware 序列。

它已经同时覆盖“来源 provenance、几何定位、多种记忆、目标视角寻址与共享融合路线”。它没有 PC-DPM 的全路径因果教师，但它构成了更强的反问题：

> 如果把所有来源 token 放入一个统一、姿态感知的 attention 路线就能消除所谓跨消费者冲突，那么 PC-DPM 的硬共同权重只是对可避免架构不一致的修补，并不是普遍的新问题。

因此，统一序列/统一 attention 必须成为 PC-DPM 的强基线。没有这个对照，不能把“两路权重同步后变好”解释为 provenance 原理成立。

### 5.3 几何与多记忆碰撞

- [I3DM（2026 预印本 v2）](https://arxiv.org/html/2603.23413v2) 在每个候选源上估计目标视角空间置信度，做最大覆盖选择，把可靠区域的 NVS 对齐记忆注入生成器；这直接占据 geometry-aware selection、confidence 和 local injection。
- [MosaicMem（2026 预印本）](https://arxiv.org/html/2603.17117) 组合显式 patch 几何与隐式生成注意力，并使用互补的 Warped RoPE / Warped Latent 对齐；这压缩了“显式 provenance + 隐式 consumer”叙事空间。
- [WorldStereo（CVPR 2026）](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_WorldStereo_Bridging_Camera-Guided_Video_Generation_and_Scene_Reconstruction_via_3D_CVPR_2026_paper.html) 同时使用 global geometric memory 与 spatial stereo memory，分别处理相机/粗结构和对应约束的细节。
- [Spatia（CVPR 2026）](https://openaccess.thecvf.com/content/CVPR2026/papers/Zhao_Spatia_Video_Generation_with_Updatable_Spatial_Memory_CVPR_2026_paper.pdf) 使用可更新点云，并把场景投影与检索帧作为多条件输入。
- [Dual-Granularity Memory（CVPR 2026）](https://openaccess.thecvf.com/content/CVPR2026/supplemental/Wang_Dual-Granularity_Memory_for_CVPR_2026_supplemental.pdf) 已组合 chunk 内 Context Memory 与跨 segment 的 latent retrieval / cross-attention。其补充材料还把两条路径分别消融，显示多路径的互补与异构优化问题。

这些工作没有建立 PC-DPM 的 exact shared source marginal，但已经使“几何双记忆”“跨路径融合”“可靠区域注入”全部失去单独新颖性。

### 5.4 来源绑定碰撞

[Movie Weaver（CVPR 2025）](https://openaccess.thecvf.com/content/CVPR2025/html/Liang_Movie_Weaver_Tuning-Free_Multi-Concept_Video_Personalization_with_Anchored_Prompts_CVPR_2025_paper.html) 用 anchored prompts 和每个参考概念的独立表示建立多来源绑定，目标之一就是避免 identity blending。[PoCo（CVPR 2026）](https://openaccess.thecvf.com/content/CVPR2026/papers/Huang_Rethinking_Position_Embedding_as_a_Context_Controller_for_Multi-Reference_and_CVPR_2026_paper.pdf) 把位置编码作为 context controller，控制多参考关联，同时保留完整 attention。

它们说明“给每个来源稳定身份并防止跨参考混淆”已经是明确问题。PC-DPM 可测试的差异只能是：**同一来源身份在多个独立 appearance consumer 中的边际责任是否矛盾，以及这种矛盾是否具有可测负收益。**

### 5.5 可信门控与效用教师碰撞

[Ada-RefSR（ICLR 2026）](https://proceedings.iclr.cc/paper_files/paper/2026/hash/9d0947107ea92d6ce369dce7749180dd-Abstract-Conference.html) 用 Adaptive Implicit Correlation Gating 汇总参考模式并对每个输出位置自适应调节参考强度，以压制误导参考。[TetherCache（2026 预印本）](https://arxiv.org/abs/2606.13035) 以 attention 与时间多样性选择记忆，并把召回 token 对齐到可信分布。二者已经覆盖 reference trust、选择、gate、repair 和错误证据抑制。

[CUE-R（2026 预印本）](https://arxiv.org/abs/2604.05467) 对检索证据逐项做 REMOVE、REPLACE 和 DUPLICATE，并测量正确性、grounding、confidence error 与 trace divergence。它还报告两个支持证据存在非加性交互。[Utility-Oriented Visual Evidence Selection（ACL 2026）](https://aclanthology.org/2026.acl-long.1620.pdf) 用 information gain 定义视觉证据效用，再训练轻量代理进行选择。

因此，“错误来源应被拒绝”“逐来源 signed utility”“昂贵标签训练轻量 selector”都已有直接抽象近邻。PC-DPM 只能依赖视频世界模型中特有的**全消费路径 + 干预前几何责任 + 独立自然重访收益**联合定义，而不能依赖 gate 或 teacher/student 外形。

### 5.6 定位与因果干预碰撞

[I²AM（ICLR 2025）](https://proceedings.iclr.cc/paper_files/paper/2025/hash/c4a59e985de8b134328f41a47bc7dfac-Abstract-Conference.html) 聚合 diffusion step、head 和 layer，建立 reference-to-generated 与 generated-to-reference 的双向归因图，已经占据 source-to-region 描述性定位。[LocoGen（ICML 2024）](https://proceedings.mlr.press/v235/basu24b.html) 用直接干预定位生成模型中的概念控制位置；[Activation Patching 最佳实践（ICLR 2024）](https://proceedings.iclr.cc/paper_files/paper/2024/hash/06a52a54c8ee03cd86771136bc91eb1f-Abstract-Conference.html) 则显示 corruption、恢复和评价指标选择会大幅改变因果定位结论。

这三类工作意味着：一张 attention 热图、一种替换方式或一次局部响应都不够。GeoCausal 合同的可保留差异，是对运行时实际来源做全路径一致干预，并用预先冻结的 source-target geometry 与逐像素 control-excess 检验局部效应，最后连接到自然重访 signed Benefit。它依然需要真实实验确认，而不是文献差异自动赋予新颖性。

### 5.7 评测、推理期选择与主动再观察的新增压力

[MomentSeeker（NeurIPS 2025 Datasets and Benchmarks Track）](https://proceedings.neurips.cc/paper_files/paper/2025/hash/281e0b9142763f2b6c944fedb8550ba9-Abstract-Datasets_and_Benchmarks_Track.html) 明确指出，只看长视频任务的端到端表现不适合判断关键时刻是否被准确访问。它研究视频理解而非生成记忆，不能替代 GeoCausal 干预；但它给出一个已经被主会 benchmark 接受的评价原则：**end-to-end success 与 evidence access 必须分开。** 因而 Address 层只能作为候选合同中的必要诊断，不能称为新发现。

[Hi3DEval（NeurIPS 2025 Datasets and Benchmarks Track）](https://proceedings.neurips.cc/paper_files/paper/2025/hash/42ffaddcc6edc9fb05ff9f9b49fca700-Abstract-Datasets_and_Benchmarks_Track.html) 把 3D 生成评测从 object-level 扩展到 part-level、材质和多维层级有效性；[Ref4D-VideoBench（CVPR 2026 主会）](https://openaccess.thecvf.com/content/CVPR2026/html/Wei_Ref4D-VideoBench_Four-Dimensional_Reference-Based_Evaluation_of_Text-to-Video_Generative_Models_CVPR_2026_paper.html) 则使用参考视频，对生成视频做语义、运动、事件时间和世界知识四维、十二指标的细粒度评价。二者都说明“只报全局平均分不够”“应使用参考和细粒度区域/维度”已是强评测基线。它们没有对运行时已选 memory source 做全路径干预，所以不能取代 GeoCausal；但未来 Benefit 必须说明相对 Ref4D 式 reference-based metrics 的增量，并报告局部与整体有效性，不能只展示一个 source-local 分数。

[Inference-time Physics Alignment（CVPR 2026 主会）](https://openaccess.thecvf.com/content/CVPR2026/html/Yuan_Inference-time_Physics_Alignment_of_Video_Generative_Models_with_Latent_World_CVPR_2026_paper.html) 使用 latent world model 的物理 reward 搜索并引导多条候选 denoising trajectories。它不做 memory-source provenance 或 source-level causal teacher，但已经直接占据“在推理时用外部/代理 reward 选择候选生成路径”的方法空间。若 PC-DPM 的 `reject / re-observe` 最终通过额外采样或候选选择实现，必须加入相同 test-time compute 的 reward-guided trajectory selection；否则收益可能来自更多采样，而不是 provenance 机制。

[AW4RE（ICLR 2026 第 2 届 World Models Workshop）](https://openreview.net/forum?id=6cJXSaHHgV) 用 4D-informed retrieval、action-conditioned geometric support 和 generative completion支持主动相机查询，明确区分 evidence-supported 与 unsupported 区域，并把 counterfactual sensing 用于 exploration/camera-action evaluation。它与 `re-observe`、几何支持和 active retrieval 高度相邻。**发表状态必须写清：它是 ICLR workshop 论文，不是 ICLR main-conference paper。** 因而它不能单凭发表层级关闭 PC-DPM 的主会新颖空间，但它足以要求：re-observe 不能作为新动作，evidence-supported mask 不能作为新概念，主动相机选择必须与 AW4RE 式策略比较。

这四类工作主要压缩的是**评测和决策层**，不是 PC-DPM 的 exact shared-source marginal。它们最合适的角色如下：

| 工作 | 正确角色 | 不能被误用为 |
|---|---|---|
| MomentSeeker | Address/access 诊断逻辑与 benchmark 设计参照 | 视频生成 source intervention 的等价方法 |
| Hi3DEval | hierarchical、part-level validity 评价参照 | 记忆来源的因果 Localization |
| Ref4D-VideoBench | reference-based fine-grained Benefit 评价强基线 | source-level causal Benefit 本身 |
| Inference-time Physics Alignment | 等 test-time compute 的 reward-guided candidate selection 基线 | provenance coupling 的等价实现 |
| AW4RE | evidence support、active retrieval 与 re-observe 的 workshop 系统/概念基线 | ICLR 主会先例或 shared cross-consumer weight 先例 |

## 6. 联合能力矩阵

记号：`●` = 已核材料明确包含；`◐` = 部分或邻接能力；`○` = 本轮已核材料未识别到。`○` 不是领域不存在的证明。

| 工作 | 稳定来源/provenance | 目标几何支持 | 双/多 appearance consumer | 跨 consumer 同一 source 边际约束 | item 级干预 | 几何局部因果量 | signed utility / Benefit | 生成前 risk action |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **目标 GeoCausal + PC-DPM** | ● | ● | ● | ● | ● | ● | ● | ● |
| Phantom | ◐ | ○ | ● | ○ | ○ | ○ | ○ | ○ |
| Matrix-Game 3.5 | ● | ● | ● | ○（统一路线回避该约束） | ○ | ○ | ○ | ○ |
| I3DM | ◐ | ● | ◐ | ○ | ○ | ○ | ○ | ◐ |
| MosaicMem | ●（patch reverse mapping 邻近） | ● | ● | ○ | ○ | ○ | ○ | ○ |
| WorldStereo / Spatia | ◐ | ● | ● | ○ | ○ | ○ | ○ | ○ |
| Movie Weaver / PoCo | ●（reference/concept 绑定） | ◐ | ◐ | ○ | ○ | ○ | ○ | ○ |
| Ada-RefSR | ◐ | ◐ | ◐ | ○ | ○ | ○ | ◐ | ●（soft gate） |
| TetherCache | ◐ | ◐ | ● | ○ | ○ | ○ | ◐ | ● |
| I²AM | ●（reference identity） | ◐（attribution region） | ◐ | ○ | ○ | ○ | ○ | ○ |
| CUE-R | ●（evidence item） | 不适用 | ◐（usage trace） | ○ | ● | 不适用 | ● | ○ |
| Utility-Oriented Visual Evidence Selection | ●（evidence item） | ◐ | ○ | ○ | ○ | ○ | ● | ● |
| MomentSeeker | ●（video moment） | ◐（多层查询） | ○ | ○ | ○ | ○ | ○ | ○ |
| Ref4D-VideoBench | ●（reference video） | ◐（细粒度维度） | ○ | ○ | ○ | ○ | ◐（reference quality） | ○ |
| Inference-time Physics Alignment | ○ | ○ | ○ | ○ | ○ | ○ | ●（physics reward） | ●（trajectory search/steering） |
| AW4RE（workshop） | ●（retrieved evidence） | ● | ◐ | ○ | ○ | ◐（supported/unsupported） | ◐ | ●（active sensing） |

矩阵中确实没有一行覆盖目标全部列。但其正确解释是：**组合仍未被本轮文献直接等价覆盖，组件与大部分相邻组合已高度拥挤。** 只有观察到文献没有预测的非显然现象，并且强基线无法解释，完整组合才可能形成贡献。

## 7. 最强反例与致命风险

### 7.1 数学反例：不同 consumer 的最优来源权重本来就可能不同

设两个来源为 `s1, s2`，两个消费者为 semantic 与 latent；每个消费者的来源权重非负且和为 1。假设：

- semantic 只从 `s1` 得到有用信息：`u_sem(s1)=1, u_sem(s2)=0`；
- latent 只从 `s2` 得到有用信息：`u_lat(s1)=0, u_lat(s2)=1`。

独立最优权重为：

`w_sem=(1,0), w_lat=(0,1)`，总效用为 `2`。

若 PC-DPM 强制 `w_sem=w_lat=(a,1-a)`，总效用恒为：

`a + (1-a) = 1`。

共同权重直接损失一半效用。这个反例对应真实直觉：一张来源可能语义身份清楚但局部纹理/视角不可靠，另一张来源可能局部几何与纹理精确但缺少全局语义。两条路径权重不同可能是合理的专业化，而不是 provenance 断裂。

**后果：** F10/F01 响应不一致不能推出“最佳权重应相同”。要先证明不一致与失败具有稳定中介关系，再比较硬共享、软一致性、独立权重和统一 attention。若硬共享只减少路径差异却恶化总体 loss，它必须被否决。

### 7.2 架构反例：统一单路可能比同步两路更直接

Matrix-Game 3.5 把多种来源放入一个 pose-aware self-attention 序列。若容量匹配的统一路线在相同预算下达到或超过 PC-DPM，说明跨路径冲突来自当前实现的分支分裂，PC-DPM 只是局部补丁。

**必须对照：** 当前两路独立权重、硬共享权重、KL/JS 软一致性、per-source token 但不共享权重、Matrix-style 统一 attention，以及参数/FLOPs/训练数据匹配版本。

### 7.3 非加性交互：`B_i` 不是来源的固定属性

CUE-R 的 two-support ablation 已显示多条证据可非加性互动。对视频记忆同样可能出现：

- **冗余**：删除任一来源几乎无损，删两条才失败；
- **协同**：两个视角共同才能约束纹理或遮挡；
- **冲突**：一个来源只有在另一个来源存在时才有害；
- **replacement 依赖**：`B_i` 随替换来源、相机、target、seed 和其他选中集合变化。

因此 `B_i` 应写成条件量 `B_i(S, r, t, seed)`，不能当成来源的永久标签。若训练学生时把一次 single-item replacement 的符号当作固定监督，标签可能不可识别。至少需要 pairwise/factorial 检查、replacement 分层和不确定区间；若交互占主导，accept/reject 必须是集合级决策。

### 7.4 provenance 单位未必稳定

在 frame、patch、surfel、aligned canvas、summary token 和压缩 KV 间，什么叫“同一来源”并不天然一致。一个 target cell 可能由多个历史 patch 经 z-buffer/融合而来，一个 semantic token 又可能是多来源池化结果。若 provenance 在进入 consumer 前已经合并，强制相同 frame-level 权重无法恢复真实责任。

**后果：** 候选必须预先声明最小可干预单位、合并规则和 source-to-token conservation。它目前不能外推到隐式、连续或不可枚举记忆。

### 7.5 因果教师可能学习干预伪影

若 all-path edit 改变编码分布、token 数量、归一化统计或缓存布局，学生可能学习“某类来源容易产生替换伪影”，而不是自然使用风险。必须有 zero-edit、matched unselected source、多个 edit family、剂量稳健性和独立自然 return reference。只有 `B_i` 对这些设计选择稳健，才配作为教师。

## 8. 唯一可保留的可证伪差异

本轮认为可保留、但尚未成立的最窄差异是：

> 在具有稳定 source ID 且至少包含两个独立加权 appearance consumer 的显式检索式视频世界模型中，检验同一已选来源的跨消费者责任是否出现可重复、与自然重访错误相关的矛盾；若矛盾成立，再检验由全路径干预、预处理前几何支持和独立真实重访 signed Benefit 监督的来源一致性策略，是否在容量匹配的 source-aware、geometry-aware、trust-gated 与统一单路基线上提供样本外增量。

这里真正要验证的不是“我们会同步权重”，而是以下连续命题：

1. **存在性：** 普通运行自然产生稳定的跨路径 source conflict；
2. **错误性：** conflict 不是两条路径合理互补，而是与几何错位或负 Benefit 关联；
3. **可干预性：** 调整跨路径责任会减少错误，而不是只让内部指标更一致；
4. **增量性：** 效果超过 source tokens、geometry attention、普通 gate、trusted alignment、统一 attention 与单一 proxy；
5. **可迁移性：** 至少在第二个 scene 和第二种 consumer/架构成立。

任何一个命题失败，都应缩小或删除 PC-DPM，而不是换一个名字继续声称方法新颖。

## 9. 决定性实验与 kill rules

| 假说 | 决定实验 | 需要超过的对照 | Kill 条件 |
|---|---|---|---|
| H1：存在真实跨路径 conflict | 对自然失败中的同一已选 source 做 F10/F01，多 scene/seed/sign/target 重复 | exact replay、zero-edit、matched unselected source | conflict 不稳定、只在单 seed/source，或与 replay/sham 同量级 |
| H2：conflict 是错误而非互补 | conflict 对几何 local excess、independent natural-return `B_i` 与总体 loss 有预注册关联 | attention、pose overlap、retrieval、source quality、addressability | 普通 proxy 解释全部结果，或 conflict 与 Benefit 无关 |
| H3：共同 provenance 约束改善结果 | 比较独立、硬共享、软一致性、per-source token 与统一单路 | Phantom-style dual path、Matrix-style unified path、I3DM/WorldStereo geometry injection | 硬/软约束不优于容量匹配基线，或只改善内部一致性 |
| H4：因果教师有增量 | scene-held-out 训练学生，报告总体 loss、AURC、coverage、clean false rejection | Ada-RefSR/TetherCache式 gate；pose/retrieval/attention 单阈值；Ref4D式参考指标；同 test-time compute 的 reward-guided trajectory selection；oracle | 教师标签不稳、学生无样本外增量、clean false rejection 过高 |
| H5：来源效用可逐项预测 | 做 replacement 分层及至少小规模 pairwise/factorial 干预 | 单项模型与集合级模型 | 强交互使 single-source `B_i` 无法泛化 |
| H6：机制不是 VMem 私有实现 bug | 在第二个具有 stable source ID 的架构复验 | 统一路线或不同 consumer 设计 | 只在当前 global-mean semantic 实现存在 |
| H7：re-observe 是 provenance-aware 决策 | 在固定预算下比较 reject、额外候选、主动相机再观察 | Inference-time Physics Alignment 式候选搜索；AW4RE 式 active sensing；随机/coverage/uncertainty 策略 | 优势只来自更多 test-time compute，或普通 active retrieval 同样有效 |

建议优先级是 H1 → H2 → H3。H1/H2 未过，不应训练学生；H3 未过，不应保留 PC-DPM。H4/H5/H6 是论文级方法主张所需，而不是当前本地 pilot 的已有结果。

## 10. 不过度声称的新问题表述

### 中文版本

> 我们研究一类受限但可审计的问题：在具有稳定来源身份和多个独立 appearance-conditioning 分支的显式检索式视频世界模型中，同一条已选历史证据是否会在不同分支中承担相互矛盾的因果责任；这种矛盾是否落在其预先定义的几何支持区域，并能预测独立自然重访中的正负收益。只有当上述现象真实存在时，我们才评估来源一致性约束是否优于已有的来源绑定、几何路由、可信门控和统一注意力基线。

### English version

> We study an architecture-scoped question in explicit-retrieval video world models with stable source identities and multiple independently weighted appearance-conditioning branches: whether the same selected historical source acquires inconsistent causal responsibility across branches, whether that inconsistency is localized to its pre-defined geometric support, and whether it predicts signed utility on an independent natural revisit. Only if this phenomenon is observed do we test whether a provenance-consistency constraint improves over source-aware binding, geometry-aware routing, trust gating, and unified-attention baselines.

这段表述刻意不使用 `first`、`novel`、`unprecedented`、`general world model principle` 或“已经改善”。它把问题限定在可审计架构，把方法置于现象之后，并明确最强邻近基线。

## 11. RQ 回答

### RQ1：哪些部分已经被覆盖？

几乎所有单组件和大部分两两组合都已被覆盖：Phantom 覆盖 VAE/CLIP 低层-高层双路径；Movie Weaver/PoCo 覆盖多参考来源绑定；I3DM、MosaicMem、WorldStereo、Spatia 和 Matrix-Game 3.5 覆盖几何选择、对齐、局部注入和多记忆；Ada-RefSR/TetherCache 覆盖可靠性 gate 与 trusted alignment；I²AM/LocoGen/Activation Patching 覆盖空间归因和因果定位；CUE-R/Utility Visual Evidence 覆盖逐证据干预效用与轻量代理。

### RQ2：剩余差异与最强反例是什么？

剩余差异只是一项高条件性的联合命题：**同一 runtime source 在所有可枚举 appearance consumer 上的责任一致性，与来源级、几何局部、全路径 signed Benefit 教师的结合。** 最强反例有两个：Matrix-Game 3.5 的统一 attention 架构可能直接消除需要修补的分支不一致；不同 consumer 的信息职责本来可能不同，硬共享权重在简单两来源例子中可将最优效用从 2 降为 1。

### RQ3：怎样安全表述？

把 GeoCausal 定位为架构受限的测量问题，把 PC-DPM 定位为只有观测到跨路径错误后才测试的修复假说。当前允许说“完整联合协议未在已核来源中被直接识别，且已冻结可证伪差异”；不允许说“已证明创新”“已提出有效方法”或“达到 CCF A/PhD 水平”。

## 12. 已做与未做

### 已做

- 复核冻结候选的六阶段合同、PC-DPM 触发条件、共同权重、因果教师与风险动作；
- 按记忆、几何、双路径、来源绑定、门控、因果定位、utility、分层评测、推理期 reward 与主动再观察九个对抗方向检索；
- 核验 2024–2026 顶会官方页及相关 2026 arXiv 原文；
- 明确正式顶会与预印本的状态；
- 构造数学反例、统一路线反例、非加性交互反例与 provenance 不可识别风险；
- 给出可执行强基线和逐项 kill rules；
- 形成中英文、不会过度声称的新问题表述。

### 未做

- 没有声称穷尽所有论文、专利、workshop、在投稿和未公开系统；
- 没有运行任何模型，也没有使用真实 C1/C2 数据；
- 没有验证自然失败、跨路径 conflict、因果 Localization 或 signed Benefit；
- 没有证明共同权重、软一致性或学生 gate 能改善任何指标；
- 没有授予 novelty、method 或投稿级结论。

## 13. 经核一手来源

### 正式会议论文

1. [VMem: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory（ICCV 2025）](https://openaccess.thecvf.com/content/ICCV2025/html/Li_VMem_Consistent_Interactive_Video_Scene_Generation_with_Surfel-Indexed_View_Memory_ICCV_2025_paper.html)
2. [SPMEM: Multi-Level Spatial-Temporal Memory for Video World Models（NeurIPS 2025）](https://proceedings.neurips.cc/paper_files/paper/2025/hash/467655d26fcc207bca08915dc91964c6-Abstract-Conference.html)
3. [WorldMem（NeurIPS 2025）](https://proceedings.neurips.cc/paper_files/paper/2025/hash/470629a47e2d65ce0606c40055df5d26-Abstract-Conference.html)
4. [Phantom: Subject-Consistent Video Generation via Cross-Modal Alignment（ICCV 2025）](https://openaccess.thecvf.com/content/ICCV2025/html/Liu_Phantom_Subject-Consistent_Video_Generation_via_Cross-Modal_Alignment_ICCV_2025_paper.html)
5. [Movie Weaver: Tuning-Free Multi-Concept Video Personalization with Anchored Prompts（CVPR 2025）](https://openaccess.thecvf.com/content/CVPR2025/html/Liang_Movie_Weaver_Tuning-Free_Multi-Concept_Video_Personalization_with_Anchored_Prompts_CVPR_2025_paper.html)
6. [WorldStereo: Bridging Camera-Guided Video Generation and Scene Reconstruction via 3D Memory（CVPR 2026）](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_WorldStereo_Bridging_Camera-Guided_Video_Generation_and_Scene_Reconstruction_via_3D_CVPR_2026_paper.html)
7. [Spatia: Video Generation with Updatable Spatial Memory（CVPR 2026）](https://openaccess.thecvf.com/content/CVPR2026/papers/Zhao_Spatia_Video_Generation_with_Updatable_Spatial_Memory_CVPR_2026_paper.pdf)
8. [Dual-Granularity Memory for Efficient Video Generation（CVPR 2026）](https://openaccess.thecvf.com/content/CVPR2026/supplemental/Wang_Dual-Granularity_Memory_for_CVPR_2026_supplemental.pdf)
9. [PoCo: Rethinking Position Embedding as a Context Controller for Multi-Reference Generation（CVPR 2026）](https://openaccess.thecvf.com/content/CVPR2026/papers/Huang_Rethinking_Position_Embedding_as_a_Context_Controller_for_Multi-Reference_and_CVPR_2026_paper.pdf)
10. [Trust but Verify: Ada-RefSR（ICLR 2026）](https://proceedings.iclr.cc/paper_files/paper/2026/hash/9d0947107ea92d6ce369dce7749180dd-Abstract-Conference.html)
11. [I²AM: Interpreting Image-to-Image Latent Diffusion Models via Bi-Attribution Maps（ICLR 2025）](https://proceedings.iclr.cc/paper_files/paper/2025/hash/c4a59e985de8b134328f41a47bc7dfac-Abstract-Conference.html)
12. [Locating and Editing Factual Associations in Text-to-Image Generative Models（LocoGen, ICML 2024）](https://proceedings.mlr.press/v235/basu24b.html)
13. [Is This the Subspace You Are Looking for? An Interpretability Illusion for Subspace Activation Patching（ICLR 2024）](https://proceedings.iclr.cc/paper_files/paper/2024/hash/06a52a54c8ee03cd86771136bc91eb1f-Abstract-Conference.html)
14. [Utility-Oriented Visual Evidence Selection for Multimodal LLMs（ACL 2026）](https://aclanthology.org/2026.acl-long.1620.pdf)
15. [MomentSeeker: A Task-Oriented Benchmark for Long-Video Moment Retrieval（NeurIPS 2025 Datasets and Benchmarks Track）](https://proceedings.neurips.cc/paper_files/paper/2025/hash/281e0b9142763f2b6c944fedb8550ba9-Abstract-Datasets_and_Benchmarks_Track.html)
16. [Hi3DEval: Advancing 3D Generation Evaluation with Hierarchical Validity（NeurIPS 2025 Datasets and Benchmarks Track）](https://proceedings.neurips.cc/paper_files/paper/2025/hash/42ffaddcc6edc9fb05ff9f9b49fca700-Abstract-Datasets_and_Benchmarks_Track.html)
17. [Ref4D-VideoBench: Four-Dimensional Reference-Based Evaluation of Text-to-Video Generative Models（CVPR 2026）](https://openaccess.thecvf.com/content/CVPR2026/html/Wei_Ref4D-VideoBench_Four-Dimensional_Reference-Based_Evaluation_of_Text-to-Video_Generative_Models_CVPR_2026_paper.html)
18. [Inference-time Physics Alignment of Video Generative Models with Latent World Models（CVPR 2026）](https://openaccess.thecvf.com/content/CVPR2026/html/Yuan_Inference-time_Physics_Alignment_of_Video_Generative_Models_with_Latent_World_CVPR_2026_paper.html)

### 2026 一手预印本/技术报告

19. [Matrix-Game 3.5](https://arxiv.org/html/2608.29910)
20. [MosaicMem](https://arxiv.org/html/2603.17117)
21. [I3DM v2](https://arxiv.org/html/2603.23413v2)
22. [WorldTrace](https://arxiv.org/abs/2608.07408)
23. [TetherCache](https://arxiv.org/abs/2606.13035)
24. [Echo-Memory](https://arxiv.org/abs/2606.09803)
25. [CUE-R](https://arxiv.org/abs/2604.05467)

### Workshop 论文（不得写成主会论文）

26. [AW4RE: Active World-Model with 4D-informed Retrieval for Exploration and Awareness（ICLR 2026, 2nd Workshop on World Models）](https://openreview.net/forum?id=6cJXSaHHgV)

## 14. 最终结论

GeoCausal Memory Contract 仍值得作为一个**受限、严格、可失败的测量问题**继续做最小实验，因为已核文献尚未直接给出“普通运行实际来源 + 全路径干预 + 干预前几何局部性 + 独立自然重访 signed Benefit”的完整闭环。这个空隙目前只是待验证的问题空间，不是新颖性证明。

PC-DPM 当前不能作为 standalone novelty。它最核心的硬共同权重存在功能互补反例，且可能被统一 attention 架构更直接地替代。只有自然数据先证明跨路径来源冲突稳定存在、冲突确实有害、共同或软 provenance 约束在严格强基线上带来样本外收益，并在第二架构成立，PC-DPM 才有资格重新接受新颖性审查。
