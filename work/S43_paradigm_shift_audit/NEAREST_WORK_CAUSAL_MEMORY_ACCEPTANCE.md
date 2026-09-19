# S43 最近邻检索：记忆证据的因果接受与 source-to-region 定位

- 检索日期：2026-09-08（Asia/Shanghai）
- 网络证据冻结时间：2026-09-07T16:12:00Z
- 研究候选：**固定其余内部状态，对一个已选中的记忆证据做因果接受测试，并检验其影响是否落在预先定义的几何支持区域**
- 方法约束：Supervisor-Skills 2.3 的“重要问题、隐藏假设、elephant-in-the-room、技术周期、可证伪差异”框架；deep-research 的多视角检索、逐条核验、反方搜索和证据强度校准
- 证据边界：本文只引用论文官方页面、论文原文、作者项目页或官方代码仓库。搜索结果页、博客和聚合摘要只用于发现候选，不作为结论证据。
- 当前判定：**KEEP_CONDITIONAL（保留为测量问题与实验协议候选）**。本次定向检索没有找到同时满足“运行时单条记忆源、固定其他内部状态、跨全部消费路径的一致反事实、输出区域定位、与自然失败/收益关联”五项条件的工作；这只是检索结果，**不能据此宣称新颖**。

## 1. 给新手的一句话解释

现有工作已经很会“把过去存起来、找到看起来相关的过去、把它喂给模型”，也已经有人画注意力图、做神经元干预、在参考图不可靠时开关门控。仍需验证的核心问题更基础：

> 当模型说自己用了某一帧记忆时，这一帧是否真的改变了结果，而且改变的位置是否正好是它在几何上应该负责的位置？

只看到“检索到了这帧”、注意力亮了、整体画质变好，均不能单独回答这个问题。反过来，只看到某个局部对干预敏感，也不能证明这条记忆带来了正确收益。因此候选更像一套**因果审计/测量协议**，暂时不应包装成一个新网络模块。

## 2. 冻结的研究问题

**RQ1：** 2023–2026 年哪些工作已经从“记忆被存储或检索”推进到“记忆被因果消费并在空间上定位”？

**RQ2：** 是否已有与当前候选等价的记忆证据接受/拒绝协议？

**RQ3：** 如果本次检索没有找到完全等价协议，哪个最小、可证伪的实验可以区分“真正的新测量问题”和“普通门控或消融”？

## 3. 检索方法

### 3.1 检索视角

为避免只搜索支持候选的论文，本次同时采用五个互相挑战的视角：

1. **记忆系统视角**：video/world model 中的 frame、token、point、surfel、KV 和 episodic memory。
2. **几何路由视角**：pose/FOV/epipolar/correspondence/3D point routing。
3. **因果解释视角**：causal tracing、activation patching、hidden-state intervention、direct effect。
4. **证据可靠性视角**：reference confidence、conflict gate、selective augmentation、abstention。
5. **反方评测视角**：长时状态保持、消失后重现、世界模型输出行为 benchmark，检查是否已有外部指标足以取代内部因果审计。

### 3.2 查询

完整、可机读查询保存在同目录的 nearest_work_causal_memory_acceptance_sources.json。查询覆盖以下组合：

- video/world model + long-term/spatial/addressable memory + retrieval/routing；
- diffusion/video + causal tracing/intervention/activation patching + localization；
- reference-conditioned generation + confidence/gate/reject/conflict；
- source image/source-to-region + attribution/counterfactual；
- 具体已发现论文标题 + official code/GitHub。

### 3.3 纳入与排除

**纳入：**

- 2023–2026 年的正式顶会论文或一手预印本；
- 与运行时记忆、参考证据、空间归因、因果干预或证据接受直接相关；
- 有官方论文页、arXiv、作者项目页或代码仓库可核验。

**排除：**

- 只讲语言模型长期记忆、且没有证据接受/归因方法可迁移的普通工作；
- 只做训练样本版权识别而不涉及运行时记忆源的工作；
- 只有二手解读、没有可核原文的条目；
- 名称相似但无法从一手页面确认内容的结果。

## 4. 证据地图：最近工作分别解决到了哪里

| 层 | 最近工作 | 它们已经解决的部分 | 它们没有单独建立的部分 |
|---|---|---|---|
| 存储/选择/寻址 | VMem [1]、SPMEM [2]、WorldMem [3]、Context-as-Memory [5]、WorldTrace [8] | 用 surfel、空间点、状态、FOV 或位置编码组织历史，并为当前视图选择/寻址相关内容 | 被选中的**某一条**证据是否真的被生成器采用；影响是否落在该证据应负责的区域 |
| 消费能力 | VRAG [4]、Memory Forcing [6]、ReMind [7] | 让模型更能使用检索上下文；暴露“有上下文但不会用”或“过度依赖不足上下文”的失败 | 在一次固定随机性的推理中，隔离单一来源的总因果效应 |
| 空间归因 | DAAM [9]、I²AM [10] | 从 cross-attention 得到词到图像、参考图到生成图的空间归因图 | 注意力相关图本身不等于因果效应；没有保证其他消费路径同步变化 |
| 因果定位 | DiffQuickFix [11]、LocoGen [12]、Activation Patching 最佳实践 [13]、AGRA [14] | 用替换或扰动定位内部组件/空间 token 的直接效应，并指出干预与指标选择会改变结论 | 干预单位通常是层、隐藏状态或动作关键区域，不是运行时的一条记忆来源到视频输出区域 |
| 接受/拒绝 | Ada-RefSR [15]、Sufficient Context [16]、RECOMP [17]、CARE [18] | 参考不可靠时抑制条件、空输出检索上下文、评估上下文是否充分或可靠 | “门控”本身已经拥挤；这些工作没有证明世界模型中某条记忆的几何局部因果贡献 |
| 外部行为评测 | STEVO-Bench [19]、MemoBench [20] | 测量不可见状态演化、重现一致性、身份/运动/3D/相机等外部行为 | 外部得分不能区分模型是用了正确记忆、错误捷径，还是仅靠参数先验猜对 |

这个矩阵说明，邻近文献不是空白。VMem、SPMEM 和 WorldMem 已经占据“记忆表示与检索”主线，WorldTrace 更把问题推进到 KV 是否可寻址；VRAG、Memory Forcing 和 ReMind 则把重点移到“检索以后模型会不会用”。与此同时，I²AM 已经非常接近 source-to-region 的**空间描述**，AGRA 已经展示世界模型中的**空间因果敏感性**，Ada-RefSR 已经展示参考证据的**自适应抑制**。因此可保留的差异只能是这些部分之间仍缺少的严格连接，不能把任一单独部分说成新概念。

## 5. 最近邻逐项对照

### 5.1 记忆系统：存到、找到，不自动等于用到

VMem 用 surfel-indexed view memory 关联历史视图与三维表面，并检索重访相关帧；SPMEM 将长期空间、工作和情景记忆组合为条件信号；WorldMem 以带相机状态与时间信息的 memory unit 和 state-aware attention 处理重访 [1–3]。三者共同证明几何索引和历史条件已经是成熟设计空间，但其论文级平均消融主要回答“模块整体是否改善质量/一致性”，并不自动回答“当前输出的某一区域是否由某一条被选历史证据造成”。

Context-as-Memory 按视场重叠选择历史帧并以帧拼接条件化，WorldTrace 则指出即便内容存入 KV，训练分布之外的位置编码也可能让它无法被正确寻址 [5,8]。前者强化“选择策略已很丰富”，后者强化“能读到正确地址也是独立问题”；二者都使当前候选更应聚焦**消费证据的因果审计**，而不是再发明一种记忆容器。

### 5.2 消费能力：文献已经暴露 elephant，但还没有给出目标协议

VRAG 的出发点是直接延长上下文或朴素 RAG 可能因视频生成器有限的 in-context learning 而失效，因此显式引入全局状态条件 [4]。Memory Forcing 更直接报告：空间记忆在上下文不足时会诱导模型过度依赖并伤害新场景质量，随后通过时空混合记忆和训练策略缓解 [6]。ReMind 则加入 node-drop、噪声记忆与保护锚点等训练机制，让模型在记忆损坏时更稳健 [7]。

这些结果已经否定“只要检索正确，生成器自然会正确消费”的隐藏假设，也使“wrong memory hurts”本身不再是足够的新发现。尚待独立验证的是：在**同一运行、同一被检索集合、同一相机、同一随机噪声和同一其他内部状态**下，一条特定来源通过所有实际消费路径产生了多大总效应，这个效应是否集中在其预处理前的几何支持区，以及该测量能否预测自然重访失败。

### 5.3 定位：注意力图是线索，干预结果才接近因果证据

DAAM 和 I²AM 都从 cross-attention 聚合空间归因图；I²AM 尤其给出参考图与生成图之间的双向 attribution map，是本次检索中与 source-to-region **表面形式最接近**的工作 [9,10]。但这类图首先说明模型内部权重或特征相关性落在哪里，不能单靠图的亮区证明“移除这条来源就会使这个输出区域发生对应变化”。

DiffQuickFix 将 causal mediation/tracing 引入文生图模型，LocoGen 进一步发现定位结论会随架构和效应定义变化，并通过直接干预 cross-attention 层定位概念知识 [11,12]。Activation Patching 最佳实践也系统表明，腐化方式、恢复方式和评价指标能给出不同定位结论 [13]。这些工作不是当前候选的空白证据，反而构成严格约束：必须有 exact replay、预注册的连贯反事实、同噪声配对、预处理前 mask，且不能把单一路径替换当成总效应。

AGRA 是最强的邻接反例之一：它认为世界模型的注意力图不足以识别动作关键区域，于是对空间隐藏 token 做因果扰动，并测量机器人动作偏差 [14]。这已经覆盖“世界模型 + 空间位置 + 因果干预”，大幅缩小候选可声称的范围。它与当前协议的剩余差异在干预单位和输出：AGRA 干预隐藏空间 token 并观察动作，而当前候选要干预**运行时记忆来源**，并将效应定位到**生成视频区域**。如果后续完整检索发现 AGRA 或相关后续工作已做后一件事，当前候选应立即降级。

### 5.4 接受门控：不能把 gate 当主要创新

Ada-RefSR 在参考超分辨率中学习隐式相关性门控，抑制错位或误导性参考 [15]；Sufficient Context 将“上下文本身不充分”和“模型有充分证据却回答失败”分开，并训练引导式 abstention [16]；RECOMP 可在检索内容无益时输出空上下文 [17]；CARE 则在检索证据与参数知识冲突时评估上下文可靠性 [18]。

尽管后三者来自文本 RAG，它们已经覆盖“先评估证据、再接受/拒绝/置空/转向可靠来源”的抽象结构。因此，简单的置信度阈值、null memory、generic reference、最近邻回退或 product-of-experts 门控都应作为普通基线。只有当因果审计先证明“错误证据有可重复伤害、存在 oracle headroom、现有普通门控无法达到风险—覆盖率优势”时，才值得训练新 gate。

### 5.5 行为 benchmark：能告诉我们模型错了，但不一定告诉我们为什么

STEVO-Bench 通过观察与控制条件测量不可见状态的演化，MemoBench 将消失后重现的身份、运动、三维与相机一致性做成系统评测 [19,20]。它们使“长时记忆会失败”不再是充分贡献；当前候选只有在能解释这些自然失败、区分来源路径、或预测何时应拒绝证据时才增加价值。

## 6. Supervisor 2.3：颠覆式创新审计

### 6.1 已进入常规技术周期的内容

以下内容已有多个近邻，不能单独作为核心创新：

- frame/token/point/surfel/KV/episodic memory；
- pose、FOV、surfel、3D point、epipolar 或 correspondence 路由；
- 把检索帧拼接、注入 cross-attention、加入全局状态或 reference cache；
- memory dropout、noisy memory、protected anchor；
- cross-attention/importance heatmap；
- 模块开关消融和平均质量提升；
- reference confidence、null context、abstention、冲突门控；
- 消失—重现、长时状态和重访一致性 benchmark。

### 6.2 隐藏假设

1. **检索即使用**：检索日志中出现某帧，不代表生成器依赖它。
2. **注意力即因果**：亮的 attribution map 不保证去掉该来源会产生相应变化。
3. **单路径干预代表总效应**：只替换 CLIP 或只替换 latent 会制造路径冲突，不能代表真实世界中的一致来源变化。
4. **局部敏感即有益**：无 GT 的局部响应只说明敏感，不说明变得更正确。
5. **门控更安全**：门控可能只是拒绝困难样本；若不报告 clean false rejection、coverage 和总体配对损失，会形成虚假改进。
6. **整模块消融可归因到单条证据**：关闭整个 memory module 同时改变多个来源与计算路径，不能定位一条来源。
7. **一次成功可泛化**：单场景、单消费者或单编辑类型不足以支持一般性机制。

### 6.3 Elephant-in-the-room

领域常用四种代理来暗示“模型记住并用了过去”：检索 ID、注意力/KV 热图、整模块消融、平均输出指标。它们各自有价值，却没有共同保证以下闭环：

> 被选择的证据，在其他因素固定时确实改变了输出；变化出现在其几何上应负责的区域；该变化超过重放噪声；并且这种局部因果量能预测自然重访中的错误或收益。

这就是当前候选真正值得测的“大象”。但它有对称风险：一个漂亮、可重复的局部因果图也可能只是模型对颜色扰动的脆弱性。如果它不预测真实错误、不提升接受决策，或离开一个模型就消失，它仍只是诊断图，而不是 PhD/CCF-A 级贡献。

### 6.4 把问题从“再做一个模块”改写为“建立一个证据合同”

候选可暂时改写为五级合同：

1. **Store**：证据确实被写入可访问记忆；
2. **Select**：当前查询确实选择了该证据；
3. **Consume**：在固定其余状态下，连贯改变该证据会造成超过 replay 的输出变化；
4. **Localize**：变化显著集中在预处理前定义的几何支持区域，并超过 mask 面积基线；
5. **Benefit/Accept**：因果局部量能预测自然错误或收益，从而支持接受、拒绝或重观察。

前两级已被大量系统工程覆盖；第三到第五级之间的联合验证，是本次检索后仍可保留的研究问题。

## 7. 可证伪差异：必须同时满足，缺一项就降级

| 维度 | 邻近文献常见做法 | 当前候选的可证伪要求 | 失败后的解释 |
|---|---|---|---|
| 干预单位 | 整个模块、层、隐藏 token、文本概念或全部参考 | 运行时被选择的**一条真实记忆来源** | 若只能做整模块，则退化为普通消融 |
| 固定条件 | 不同采样或整套输入一起改变 | 固定 retrieval IDs、pose、K/Plücker、latents、实际 noise、RNG 和其他消费者状态 | 若 exact replay 不稳，则任何差异都不可归因 |
| 路径完整性 | 只改 CLIP、只改 latent、只看 attention | 主比较只使用跨全部真实消费路径一致的 F11；F10/F01 仅诊断路径冲突 | 若只有单路径有效，则不能称总因果效应 |
| 定位目标 | post-hoc attention 热图 | 使用 intervention 前冻结的几何支持 mask；报告内外区效应和面积基线 | 若 CI 下界不超过面积基线，则无 source-to-region 证据 |
| 有益性 | 局部变化或相似度相关 | 局部因果量必须增量预测自然重访 error/benefit | 若不预测真实失败，只能称 sensitivity |
| 接受决策 | 学一个 gate 并报过滤后得分 | 先证实 oracle headroom，再报 AURC、risk–coverage、clean false reject 与总体 paired loss | 若通用 gate 已解决，则方法创新被普通基线吸收 |
| 外推 | 单一场景或单一模型 | 至少两个场景；进入论文主张前至少两个消费者/架构 | 若只在一个消费者出现，则只能称 case study |

## 8. 最便宜的决定性实验

### 8.1 先过四个便宜门；任何一门失败就停止昂贵实验

1. **G0：自然失败存在。** 在真实重访样本上复现 B0/C1/C2，并同步检查相机、输入质量和基础生成是否有效。若没有稳定自然失败，就没有需要解释的对象。
2. **A0：exact replay。** 完全相同输入与 RNG 重跑，测量本底差异分布。若重放不稳定，后续所有因果量都没有可信零点。
3. **A1：消费者真的有影响且与失败相关。** 用最小置零/替换检查 CLIP/记忆消费者是否改变目标输出并与自然失败有关。只影响画面但与失败无关，不足以进入定位实验。
4. **A2–A5：普通基线。** null、mean、nearest、generic reference、PoE/简单融合等先跑。若普通策略直接修复主要失败，就不应提前训练复杂 gate。

### 8.2 一次最小 F11 因果定位 pilot

对一个已经过 G0–A1 的真实来源帧，在预注册 mask 内做**低强度、外观一致、photometric-only**的可控编辑，保持相机、几何、可见支持和检索 ID 不变。固定 pose、K/Plücker、latents、实际采样 noise、RNG 与其余内部状态，运行：

- **F00**：原来源经过全部真实消费路径；
- **F10**：只改 CLIP 路径；
- **F01**：只改 replace/latent 路径；
- **F11**：同一编辑同时进入全部真实消费路径。

主因果比较只有 **F11 − F00**。F10/F01 用于发现跨路径冲突，不能当主反事实。以 A0 replay 分布为零点，测：

- 总效应是否显著超过 replay；
- mask 内效应 / 总效应；
- 定位比是否超过 mask 面积占比；
- bootstrap 或 paired-seed 置信区间；
- 至少两种低强度编辑是否给出同方向结论。

这个 pilot 的目的不是写论文结论，而是尽快杀死没有信号的方向。若通过，再扩到至少两个场景和第二个消费者，并检验定位量是否预测自然重访误差。

### 8.3 只有在 pilot 通过后才测试“接受”

构造冲突剂量 q ∈ {0, 1, half, all}，比较 mean/null/nearest/generic/PoE 和任何候选策略。训练 gate 前先做 oracle：如果知道哪条证据错误也无法获得明显收益，则不存在值得学习的 headroom。正式报告至少包括：

- AURC 或 risk–coverage；
- clean evidence 的 false rejection；
- 所有样本上的 paired loss；
- 接受率和失败覆盖，而不是只报被接受子集；
- 相对普通 gate 的额外收益。

## 9. Kill criteria

出现任一情况，应停止把该路线作为主创新，回到 baseline/recovery 或 benchmark：

1. G0 找不到稳定、可复现的真实自然失败；
2. A0 exact replay 的波动与候选效应同量级；
3. A1 显示消费者无效，或其影响与自然失败无关；
4. F11 总效应的置信下界不超过 replay；
5. source-to-region 定位的置信下界不超过 mask 面积基线；
6. 效应只存在于 F10/F01 的不一致路径，而 F11 不成立；
7. 定位量不能增量预测自然重访误差或收益；
8. null/nearest/generic/PoE 等普通基线已经解释或修复现象；
9. oracle 接受策略没有实质 headroom；
10. 结果只在一个场景、一个消费者或一种编辑中存在；
11. 后续 citation-network/作者检索找到已满足五项联合条件的同等协议；
12. 必须依赖 post-treatment mask、人工挑选样本或只汇报成功 seed 才成立。

## 10. 对三个研究问题的回答

**RQ1 回答。** 现有工作分别推进了记忆存取与寻址 [1–8]、空间相关归因 [9–10]、组件或空间 token 的因果定位 [11–14]、证据接受/拒绝 [15–18] 和长期行为评测 [19–20]。其中 I²AM、AGRA、Ada-RefSR 和 Memory Forcing 是最具压力的邻居，因为它们分别覆盖 source-to-region 外观、世界模型空间干预、参考门控和错误空间记忆的伤害；但本次检索没有发现它们完成目标五级合同的联合验证。

**RQ2 回答。** 本次定向检索没有找到完全等价协议。这个答案的证据强度是“未检索到”，不是“领域中不存在”。在任何论文式 novelty 声明前，必须继续做前向/后向引用网络、相关作者主页、最新 workshop/arXiv 和独立研究者复核。

**RQ3 回答。** 最便宜的决定性实验不是训练 gate，而是先跑 G0→A0→A1，再用一个真实来源做成对 F00/F11 与预处理前几何 mask 的小型 pilot。该实验同时检验“是否有因果效应”和“是否在正确区域”；任一不成立就 kill。只有它通过且能预测自然错误，才进入接受/拒绝研究。

## 11. 自我反驳与局限

1. **检索漏项风险。** 2026 年论文仍在快速出现，部分项目只在作者主页或 workshop 发布；标题未使用 memory/causal/localization 关键词时可能漏检。
2. **代码不等于论文结论。** 本文记录的仓库 HEAD 只证明检索时公开仓库状态，不证明完整训练代码、权重或可复现性。
3. **跨领域类比有限。** 文本 RAG 的 abstention 证明“接受/拒绝”思想已存在，但不能直接证明视频世界模型中的几何证据问题已经解决。
4. **因果干预可能离分布。** 即使 appearance-only 编辑也可能成为异常输入，必须做强度扫描、多个编辑类型和自然错误关联。
5. **固定内部状态并非全部自然因果。** 固定随机性有利于归因，却只测局部干预下的直接效应；它不能替代长期闭环交互评价。
6. **几何 mask 可能错。** 相机或深度误差会污染“正确区域”；mask 质量必须独立审计，并在可行时报告不确定边界。
7. **统计显著不等于研究价值。** 极小但稳定的效应若不能预测失败、改变决策或跨模型复现，仍不足以形成强贡献。

## 12. 当前研究决策

**保留 P1，但把定位从“创新方法”降为“待证的因果测量合同”。**

下一步主张只能按证据逐级升级：

- 只通过 F11：可称“固定状态下观察到单来源因果敏感性”；
- 再通过几何基线：可称“观察到 source-to-region 局部性”；
- 再预测自然失败：可称“该审计量具有错误诊断价值”；
- 再优于普通接受基线并跨消费者复现：才有资格讨论通用方法贡献；
- 在完成独立最近邻复核前，任何阶段都不称“首个”或“新颖”。

## 参考文献与一手链接

[1] [VMem: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory, ICCV 2025](https://openaccess.thecvf.com/content/ICCV2025/html/Li_VMem_Consistent_Interactive_Video_Scene_Generation_with_Surfel-Indexed_View_Memory_ICCV_2025_paper.html). [Official code](https://github.com/runjiali-rl/vmem).

[2] [Video World Models with Long-term Spatial Memory, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/467655d26fcc207bca08915dc91964c6-Abstract-Conference.html). [Official code](https://github.com/spmem/spmem).

[3] [WorldMem: Long-term Consistent World Simulation with Memory, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/470629a47e2d65ce0606c40055df5d26-Abstract-Conference.html). [Official code](https://github.com/xizaoqu/WorldMem).

[4] [Learning World Models for Interactive Video Generation, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/e32310c3acb058d563a6a9e54d0e9000-Abstract-Conference.html). [Official code](https://github.com/yeyutaihan/vrag).

[5] [Context as Memory: Scene-Consistent Interactive Long Video Generation with Memory Retrieval, SIGGRAPH Asia 2025 project page](https://context-as-memory.github.io/). [arXiv](https://arxiv.org/abs/2506.03141).

[6] [Memory Forcing: Spatio-Temporal Memory for Consistent Scene Generation on Minecraft, arXiv 2025](https://arxiv.org/abs/2510.03198). [Author project page](https://junchao-cs.github.io/MemoryForcing-demo/).

[7] [Teaching Video Generators to Remember: Training-Time Memory for Long-Horizon World Simulation, arXiv 2026](https://arxiv.org/abs/2605.25333). [Official code](https://github.com/Applied-Intuition-Open-Source/ReMind).

[8] [Addressable Memory for Video World Models, arXiv 2026](https://arxiv.org/abs/2608.07408).

[9] [What the DAAM: Interpreting Stable Diffusion Using Cross Attention, ACL 2023](https://aclanthology.org/2023.acl-long.310/). [Official code](https://github.com/castorini/daam).

[10] [I²AM: Interpreting Image-to-Image Latent Diffusion Models via Bi-Attribution Maps, ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/c4a59e985de8b134328f41a47bc7dfac-Abstract-Conference.html). [Official code](https://github.com/qkrwnstj306/I2AM).

[11] [Localizing and Editing Knowledge in Text-to-Image Generative Models, ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/4bfcebedf7a2967c410b64670f27f904-Abstract-Conference.html). [Official code](https://github.com/samyadeepbasu/DiffQuickFix).

[12] [On Mechanistic Knowledge Localization in Text-to-Image Generative Models, ICML 2024](https://proceedings.mlr.press/v235/basu24b.html). [Official code](https://github.com/samyadeepbasu/LocoGen).

[13] [Towards Best Practices of Activation Patching in Language Models: Metrics and Methods, ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/06a52a54c8ee03cd86771136bc91eb1f-Abstract-Conference.html).

[14] [Making Foresight Actionable: Repurposing Representation Alignment for Causally Grounded Video World Models, arXiv 2026](https://arxiv.org/abs/2606.12217).

[15] [Trust but Verify: Adaptive Conditioning for Reference-Based Image Super-Resolution, ICLR 2026](https://proceedings.iclr.cc/paper_files/paper/2026/hash/9d0947107ea92d6ce369dce7749180dd-Abstract-Conference.html). [Official code](https://github.com/vivoCameraResearch/AdaRefSR).

[16] [Sufficient Context: A New Lens on Retrieval Augmented Generation Systems, ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/33dffa2e3d2ab74a783d1a8c292f66d9-Abstract-Conference.html). [Official code](https://github.com/hljoren/sufficientcontext).

[17] [RECOMP: Improving Retrieval-Augmented LMs with Compression and Selective Augmentation, ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/bda88ed2892f5e61c9a9bf215c566913-Abstract-Conference.html).

[18] [CARE: Context-Aware Retrieval Enhancement for Countering Retrieval-Augmented Generation Failures, EMNLP 2025](https://aclanthology.org/2025.emnlp-main.1371/).

[19] [Out of Sight, Out of Mind? Evaluating State Evolution in Video World Models, arXiv 2026](https://arxiv.org/abs/2603.13215). [Official code](https://github.com/jhanliufu-personal/STEVO-Bench).

[20] [MemoBench: Benchmarking World Modeling in Dynamically Changing Environments, arXiv 2026](https://arxiv.org/abs/2606.27537). [Official code](https://github.com/MemoBench-Team/MemoBench). The author project page labels the work “ECCV 2026”; this audit uses the verifiable arXiv status rather than treating the project-page label as proceedings evidence.

## 复核要求

在把本文任何“未发现”句子写进论文前，至少由另一名研究者独立完成：

1. I²AM、AGRA、Ada-RefSR、Memory Forcing、VMem、SPMEM 的前向与后向引用网络；
2. 这些论文作者 2025–2026 年主页与最新 arXiv；
3. “runtime memory source intervention”“reference-to-output causal attribution”“memory acceptance world model”同义词扩展；
4. 对候选 closest paper 的正文、附录和代码做全文搜索，而不是只读摘要；
5. 将新证据追加到 sources JSON，并重新运行 kill criterion。
