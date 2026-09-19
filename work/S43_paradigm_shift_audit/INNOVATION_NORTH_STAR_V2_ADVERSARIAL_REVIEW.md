# 创新北极星 V2 独立对抗式审查

- 审查时间：2026-09-08T17:24:58+08:00（Asia/Shanghai）
- 审查对象：`INNOVATION_NORTH_STAR_V2.md`
- 对象 SHA256：`574311ced8f5bcbf2ad21854a0f7895195bc49d4fe968012d3f33bca7b662f36`
- 审查性质：source/literature-only；独立、对抗式、结论优先
- 总体裁决：**PIVOT**
- 当前新颖性授权：**NONE（维持不变）**
- 运行边界：本轮没有运行模型，没有读取真实 C2 数据或图片，没有生成视频、评分像素或训练学生，也没有改动 V2 原文件

## 1. 一句话裁决

V2 做对了两件重要的事：它主动否决了 PC-DPM 硬共享，也拒绝把普通 stale-memory 清理包装成创新；但它保留的 `GeoCausal` 命名仍把“可观察的干预敏感性”说成“使用”，把“预冻结几何支持”说成“正确位置”，而 `Interaction-Aware Provenance Arbitration` 的方法外形又被 2026 年的直接视频路由和跨域反事实仲裁工作显著挤压。因此，**保留架构受限的测量问题，重写可识别量；方法分支继续冻结，不能以当前名字和逻辑进入创新实现。**

## 2. 分项 KEEP / PIVOT / REJECT

| 对象 | 裁决 | 审查理由 |
|---|---|---|
| 否决 PC-DPM hard sharing | **KEEP** | 两来源、两 consumer 的反例足以推翻“所有 consumer 应共享同一来源权重”这一普遍原则；V2 也正确保留了专业化可能性和强基线。 |
| 否决 generic stale-memory | **KEEP** | GaME、WorldMM、WorldCraft、Spatia、StableWorld 等已经覆盖更新、删除、刷新或抑制旧状态；普通“发现旧记忆并清掉”不能再单独成为贡献。 |
| GeoCausal 的问题动机 | **KEEP，限测量假说** | “访问/检索成功不保证可观察影响或最终收益”是值得验证的问题，但跨域已有直接 access–utilization 与逐证据干预先例；视频生成中的窄实例仍可能有价值。 |
| `Access–Use / Use–Location / Use–Benefit` 当前定义 | **PIVOT** | 三个名字均比实际可识别量更强：零输出效应不等于未使用，support 外效应不等于错位，单条自然重访参考也不自动构成反事实真值。 |
| Interaction-Aware Provenance Arbitration | **PIVOT，继续冻结** | CUE-R、CF-RAG、CoRM-RAG、CAMA 与 TetherMem 已分别覆盖逐证据交互、反事实仲裁、教师到轻量 critic、provenance 仲裁/主动恢复和视频内条件路由。剩余价值必须来自视频特有的新现象和机制，而非这些组件的联合命名。 |
| “颠覆式创新/范式转移”定位 | **REJECT TODAY** | V2 有第一性原理和自我否决，但没有验证领域大象的频率与实际痛点，没有提出技术周期使该问题现在首次可解的证据，也没有建立 Hamming 意义上的领域重要性。 |

## 3. 审查问题与检索范围

本轮冻结三个问题：

1. V2 是否真正执行 Supervisor-Skills 2.3，还是只引用了它的词汇？
2. 两条已否决路线是否否决充分；剩余测量量和方法量是否可识别、可执行？
3. 2024-01-01 至 2026-09-08 的主会和强预印本，是否已经覆盖剩余问题或方法外形？

检索从互相挑战的五个方向展开：直接视频世界记忆、动态/旧状态更新、逐证据反事实归因、来源/证据仲裁、访问与利用分解。正式会议页面、CVF/NeurIPS/ICLR/ACL/SIGIR 论文页和 arXiv 原页被优先使用；搜索摘要只作入口，不作最终发表状态证据。“未找到完全相同系统”不被解释为领域不存在。

## 4. 对 Supervisor-Skills 2.3 的逐项核验

Supervisor-Skills 2.3 给出四条思考路线，而不是一个勾选后即可授权“颠覆”的清单。V2 的符合程度如下。

### 4.1 第一性原理：部分通过

V2 确实质疑了隐藏假设“存到并检索到，就等于记忆帮助了输出”，并回到世界模型的目的：重访时生成正确、可解释且有益的世界状态。它还用反例主动杀掉自己的 hard-sharing 方案。这比从模块名称出发找增量更符合 2.3。

但当前从“输出对某个 edit 不敏感”跳到“模型没用来源”，仍包含一个新的隐藏假设；从“影响不落在投影 support”跳到“用错地方”又包含另一个隐藏假设。第一性原理审查尚未完成，只是把旧假设换成了两个尚未证明的新假设。

### 4.2 房间里的大象：只有候选，没有证据

“检索指标掩盖生成期记忆失效”可以是极端失败或真实痛点，但 V2 没有真实 cohort、频率、用户后果或从业者证据。P0 也只问是否存在失败，没有建立它是否常见、重要、此前为何被系统性忽略。按照 2.3，这目前是 elephant hypothesis，不是已经找到的大象。

### 4.3 技术周期：缺失

V2 没有回答：为什么这个问题在 2026 年现在才可解？是 stable source ID、可重放扩散随机性、可枚举 consumer、几何投影、参考数据，还是算力/工具出现了数量级变化？没有这条桥，方案是更严格的审计协议，不是由技术代际更迭触发的新范式。

### 4.4 Hamming 重要问题：尚未建立

长期一致、可追责的世界记忆显然重要，但 V2 没有把它与本领域 10–20 个核心问题比较，也没有证据说明 source-level accountability 比可控性、交互速度、物理一致性、真实状态更新等问题更优先。它值得投入一个有上限的测量 pilot，尚不值得以“改变领域格局”的表述投入完整方法工程。

### 4.5 2.3 总结

结论是 **FOLLOWED IN SPIRIT, NOT YET PASSED AS A PARADIGM SHIFT**。第一性原理和主动否决成立；elephant、technology-cycle、Hamming 三项仍是空缺或弱证据。V2 对外表述保持 `novelty_authorization=NONE` 是正确的。

## 5. 两条否决是否充分

### 5.1 PC-DPM hard sharing：否决充分，适用范围需保持精确

V2 的反例证明了：当 semantic 和 latent consumer 所需信息互补时，普遍硬共享会严格劣于独立权重。因此，“跨路径权重不同就是错误”与“共享权重是一条通用 provenance 原理”均被推翻。

这个反例没有证明所有共享机制都无效。它不排除数据依赖的软耦合、只在检测到伤害时触发的共享、分层 token 共享或统一 attention。V2 已把 hard sharing 降为对照，并要求伤害证据，边界是正确的。

**Hard-sharing kill condition：** 若跨 consumer 差异与 held-out 自然损失、几何参考误差或负 signed utility 没有稳定关系，永久删除“冲突”主张；即使有关系，若独立权重、软一致性或统一 attention 在等预算下不差于 hard sharing，也不得恢复 hard sharing 为主方法。

### 5.2 generic stale-memory：否决充分，而且直接近邻比 V2 列出的更强

V2 对 GaME、WorldMM、WorldCraft 的核心描述经原文核验基本准确。WorldMM 的论文正文确实让 LLM 在 consolidation 中标出 outdated/conflicting triplets 并删除、修订或加入 triplet。问题不在事实准确性，而在任务范围：GaME 是在线 3DGS 映射，WorldMM 是长视频问答，只有 WorldCraft、Spatia、StableWorld 与 TetherMem 更贴近生成或交互视频。

generic stale-memory 仍应永久作为背景/压力轴，而非创新标题。

**Stale-memory kill condition：** 任何只做 age/conflict detection、drop/refresh/update/eviction 的方法，无论本项目实验是否提升，都只能与现有工作比较，不能被申报为主创新；只有 source/consumer/set 特有、现有更新方法不能解释的机制才允许进入下一轮。

## 6. 指定一手来源的精确核验

| 工作 | 核验后的准确含义 | 发表状态（截至 2026-09-08） | 对 V2 的约束 |
|---|---|---|---|
| [GaME](https://openaccess.thecvf.com/content/CVPR2026/html/Yugay_Gaussian_Mapping_for_Evolving_Scenes_CVPR_2026_paper.html) | 面向长期变化场景的在线 3D Gaussian mapping；持续更新 3D 表示，并用 keyframe management 丢弃会破坏几何/语义一致性的 stale observations。 | **CVPR 2026 主会**，pp. 18903–18912。 | 直接占据 evolving-map 中的旧观测删除；不是视频生成 memory arbitration。 |
| [WorldMM](https://openaccess.thecvf.com/content/CVPR2026/html/Yeo_WorldMM_Dynamic_Multimodal_Memory_Agent_for_Long_Video_Reasoning_CVPR_2026_paper.html) | 长视频 QA/推理 agent；episodic、semantic、visual 三类 memory。semantic graph consolidation 识别 overlapping/conflicting triplets，并让 LLM 决定 outdated/conflicting 的删除与修订/新增。 | **CVPR 2026 主会**，pp. 25599–25609。 | V2 第 40 行事实准确；这是 reasoning/QA 的 semantic memory，不是像素生成或几何重访。 |
| [WorldCraft](https://arxiv.org/abs/2605.25077) | 交互视频世界模型从相机导航扩展到物体轨迹操控；TASP 在轨迹条件生成后刷新自回归 memory，使移动物体离开视野后在新位置重现。 | **arXiv v1，2026-05-24；未核到同行评审主会状态。** | 与动态状态刷新直接相邻，足以否决普通 refresh 作为独立创新。 |
| [ClashEval](https://proceedings.neurips.cc/paper_files/paper/2024/hash/3aa291abc426d7a29fb08418c1244177-Abstract-Datasets_and_Benchmarks_Track.html) | 研究 RAG LLM 的内部先验与外部文本证据冲突；错误检索内容会使 LLM 覆盖正确先验并采用错误。 | **NeurIPS 2024 Datasets and Benchmarks Track**。 | V2 第 109 行应限定为“RAG LLM”，不能写成对所有生成式模型的普遍证明。 |
| [Causal LLM Routing](https://proceedings.neurips.cc/paper_files/paper/2025/hash/357774d53e5ee21c5f08ba779e3b5dd9-Abstract-Conference.html) | 根据 query 在多个 LLM 间平衡准确率与成本；只用已部署模型的 observational outcome，以 causal end-to-end regret 和代理目标学习路由。 | **NeurIPS 2025 Main Conference Track**。 | 因果 regret routing 的算法外形已占据；它不路由视频 memory sources，也不提供几何责任。 |

两处最需要注意的表述边界：

1. GaME/WorldMM 是“跨任务占据 generic stale/update”，不能当作与视频生成方法完全等价；
2. ClashEval 只证明 RAG LLM 对错误文本证据的脆弱性，不能替视频生成中的有害 source effect 提供实证结论。

## 7. V2 漏掉的 2024–2026 强碰撞

### 7.1 直接视频碰撞：TetherMem

[Tether the Subject, Release the Scene](https://arxiv.org/abs/2608.26902) 于 2026-08-27 提交 arXiv v1。它在冻结视频生成器上做 training-free、query-aware spatiotemporal memory routing：subject query 保留身份历史，scene query 降低对 subject history 和 stale background 的依赖，并按区域和 memory age 调制访问。论文还把 realized attention 与输出变化连接，并在第二个 autoregressive host 上报告 transfer。

它没有逐 source 反事实教师、稳定运行时 provenance、全部 appearance consumer 或自然重访 signed Benefit，因此不等价于 GeoCausal。可是它已直接占据：

- 视频生成中的条件式 memory routing；
- 不同 query/region 允许不同历史访问策略；
- stale background 抑制；
- frozen host 上的跨模型路由迁移。

这意味着 `Interaction-Aware Provenance Arbitration` 不能再把“分路径/分区域条件路由”作为主要新意，TetherMem 必须进入强基线和最近邻表。

### 7.2 反事实教师到轻量 critic：CoRM-RAG

[CoRM-RAG](https://arxiv.org/abs/2605.01302) 把“相关性不等于效用”定义成 Relevance–Robustness Gap；用反事实 query perturbation 产生监督，将其蒸馏为轻量 Evidence Critic，并在推理时做风险重排和 abstention。arXiv 页面关联 DOI `10.1145/3805712.3809631`，会议录记录为 **SIGIR 2026**。

它的任务是 RAG 决策，不是视频生成；但“昂贵反事实 teacher → 轻量在线风险模型 → 保留/拒绝”这一主方法外形已经是主会工作。V2 若训练学生，必须把 CoRM 式 relevance/risk critic 迁移基线纳入，而不能把 teacher–student 结构当贡献。

### 7.3 反事实证据仲裁：CF-RAG

[Counterfactual Reasoning for Retrieval-Augmented Generation](https://proceedings.iclr.cc/paper_files/paper/2026/hash/1c078897dc08d46091d0d361d9955c6b-Abstract-Conference.html) 是 **ICLR 2026 主会**。它用 counterfactual queries 找 causally relevant distinctions，并用 parallel arbitration 调和冲突证据。对象虽是文本 RAG，但“counterfactual evidence arbitration”这个宽主张已被直接占据。

### 7.4 逐 item 效用与非加性交互：CUE-R

[CUE-R](https://arxiv.org/abs/2604.05467) 是 2026-04-07 arXiv v1，尚未核到同行评审主会状态。它对单条证据做 REMOVE/REPLACE/DUPLICATE，测 correctness、grounding、confidence error 与 trace divergence；two-support ablation 明确报告 non-additive interaction。它还谨慎地把目标称为 observable operational utility，而不是隐藏机制。

CUE-R 几乎直接否决“逐来源干预 + signed utility + pairwise interaction”作为抽象新意，并给出 V2 应采用的措辞标准：在机制尚未识别前，应说操作性干预效应。

### 7.5 provenance 仲裁与主动恢复：CAMA

[Beyond Memory Majority / CAMA](https://arxiv.org/abs/2608.19701) 于 2026-08-20 提交 arXiv v1。它用 provenance priors 和 neural dependency inference 估计有效独立来源数，并学习 sequential recovery policy 去检索替代证据或追溯上游来源，在预算约束下仲裁 correlated memories。

它属于多 agent 文本 memory，不是视频；但 `provenance arbitration`、来源依赖、集合相关性和主动恢复的组合已经出现。V2 的方法名字与 CAMA 的概念距离过近，必须依靠视频特有 estimand 和新的机制发现，而不是名称或动作空间区分。

### 7.6 access 不等于 utilization：UtilMem

[UtilMem](https://arxiv.org/abs/2608.30508) 于 2026-08-31 提交 arXiv v1。它明确报告：传统 factual-memory 表现不保证 memory utilization；即使检索到相关证据，系统仍可能不能跨会话整合，或不能抵抗相似 distractor。

它没有视频生成反事实与几何定位，因此不关闭 GeoCausal 的窄测量空间；但“access success 高估 use success”这个问题结构已被明确提出，不能再作为跨领域首次发现。

### 7.7 碰撞后的剩余空间

在本轮已核材料中，仍未找到一项工作同时满足：显式视频世界 memory、ordinary-selected runtime source identity、全部可枚举 appearance consumer 的一致 intervention、预处理几何责任、未输入模型的自然回访 reference、集合条件 signed effect 与生成前策略。

这只能说明完整交集在本轮来源中未命中。它不能证明联合本身有学术新意。**若每个组件都已被占据，剩余贡献必须是一条文献不能预测的真实现象、一个可识别机制，以及相对最强组合基线的增量。**

## 8. 可识别性与偷换概念审查

### A1. CRITICAL：零输出效应不等于“未使用”

V2 将 matched all-path intervention 与 zero/sham 无差异定义为 Access–Use Gap。这个观测最多支持“在当前 edit、共同来源集合和统计功效下，未检测到可观察总效应”。它不能排除：

- 来源被内部读取，但与另一来源冗余；
- 多条路径效应互相抵消；
- 来源改变了隐藏状态，却没有越过当前输出 metric 的检测阈值；
- edit 没有破坏真正被用到的充分统计量。

反过来，发现输出变化也可能来自 off-manifold edit 或归一化/排列变化，而非语义上的“使用”。

**必须 PIVOT：** 在未完成冗余、灵敏度和 in-distribution intervention 识别前，把该量称为 `Access–Observable-Influence Gap` 或 `interventional sensitivity gap`。只有额外机制证据才能升级为 use。

**Kill condition：** 若正控可检测、两类 in-distribution edit 一致、功效足够后仍无法区分冗余/抵消与未使用，删除“Use”机制主张，只保留操作性测量。

### A2. CRITICAL：几何 support 不等于“正确影响位置”

预冻结 support 可以防止看完输出后移动 mask，却不保证 support 外影响是错误。视频生成中的正确记忆可能通过遮挡、阴影、反射、光照、关系、相机运动或全局布局在投影区域外产生合理效应。把 outside-support effect 直接称作错位，是把工程先验偷换成真值。

**必须 PIVOT：** `Use–Location Gap` 应先改成描述性的 `Support–Effect Mismatch`。只有 support 外 effect 同时提高 reference error，或违反预定义对象/几何因果关系时，才能称 harmful mislocalization。

**Kill condition：** 若 support 外 effect 对真实 reference 有益、mask 对深度/位姿/placebo 不稳健，或不同合理 support 定义给出相反结论，删除“用错位置”主张。

### A3. CRITICAL：自然重访参考不是自动成立的反事实真值

一条同步自然 return 是现实世界的一个实现，不是“同一外生噪声下、只改变 memory source”的完整 counterfactual。动态物体、光照、曝光、遮挡、相机误差和非决定性环境都可能改变 reference。把生成 loss 对这条参考的差写成来源的真实 causal Benefit，会混合 source intervention 与 reference uncertainty。

**必须 PIVOT：** 把当前量称为 `reference-conditioned signed utility`，明确它条件于 reference、edit、set、target 和噪声。静态场景可近似使用；动态场景需要状态同步/多参考/不确定区间或明确的观测模型。

**Kill condition：** 若 reference 重测/配准误差与候选 Benefit 同量级，或 utility 符号随合理 reference/metric 改变，删除 Benefit 的因果解释。

### A4. MAJOR：`B_i(S,r,t,seed,consumer)` 是干预协议效应，不是来源固有属性

V2 已承认 set、replacement、target、seed 和 consumer 条件性，这是正确修复。但它仍没有定义 estimand：remove、replace、zero、feature swap 会同时改变 token 数、归一化、顺序、注意力竞争或缓存统计。不同 intervention 估计的是不同因果问题。

**要求：** 预先区分 total effect、consumer-specific controlled effect 和 pairwise interaction；定义 treatment、baseline、共同集合、matched noise、聚合单位和 sign。主要策略 estimand 应对 seed 取期望，seed 只用于重复性/异质性，而不应让学生把随机种子当成语义风险特征。

**Kill condition：** 若 effect 的方向主要由 edit family、replacement 或 token-layout 改变决定，删除“来源效用”标签，报告 intervention sensitivity。

### A5. MAJOR：六级链不能由后选择 intervention 识别

对 ordinary-selected source 在 consumer 入口做 edit，可以研究 Select/Address 之后的响应；它不能反推出 Store 或 Select 的因果贡献。`Store → Select → Address → ...` 可以是审计清单，却不是已经识别的中介链。

**Kill condition：** 若没有对 store/write 和 selection policy 的独立随机化或有效工具变量，禁止声称识别完整六级因果链；只报告条件于已存、已选、可寻址的下游效应。

### A6. MAJOR：P0 可能造成按结果选择样本

P0 先要求找到自然失败，P1 再审计 gap。如果 P1 只在失败样本上估计 gap 频率，就会 conditioning on outcome，无法回答 V2 第 60 行“ordinary-selected 是否系统性高估”的总体问题。

**要求：** failure-enriched pilot 只能发现机制；确认性统计必须使用事先冻结的完整 ordinary cohort 和完整分母，成功与失败均保留。

**Kill condition：** 若主结果的样本进入规则依赖事后自然失败、视觉质量或 gap 大小，删除 prevalence/systematic 主张，只保留 case study。

### A7. MAJOR：`all appearance consumers` 可能不可枚举

在非线性 diffusion/transformer 中，semantic、latent、residual、self-attention、normalization、cache 和共享 hidden state 可能形成间接后代。只切两个显式接口并不证明所有 appearance 路径已被干预。

**Kill condition：** 若 source identity 在 intervention 边界之前已池化，或存在未覆盖的 source-dependent descendant，F00/F10/F01/F11 不能称 all-path；降级为“两个已枚举接口的局部析因审计”。

### A8. MAJOR：当前 P0–P6 是方向，不是可执行 preregistration

“多 scene/seed”“effect 稳定”“显著交互”“额外解释力”“跨 scene 预测”“胜过全部强基线”都没有数值阈值、样本量、独立单位、统计模型、multiplicity、等价/非劣界限或缺失处理。每个 gate 都可在看到结果后被重新解释。

**Kill condition：** 在真实数据解封前若未冻结 cohort、primary endpoint、最小效应、置信区间/检验、随机效应单位、FDR/多重比较和 fail-safe missingness，P0–P6 不得被称为 preregistered gates。

### A9. MAJOR：P3 的“显著交互”不足且可能不可负担

pairwise 是二次规模，完整集合干预是指数规模；视频生成还需跨 seed 重放。统计显著不表示可预测或可用于策略，样本大时微小交互也会显著。

**要求：** P3 必须同时要求预注册 effect floor、held-out predictive gain 相对 additive model、校准改善和 multiplicity 控制。先做稀疏/分层 interaction screen，再决定是否扩展。

**Kill condition：** 若 interaction 不提升 held-out risk/utility prediction，或成本不能在冻结预算内产生足够独立 scene 单位，删除集合治理。

### A10. MAJOR：教师标签可靠性和学生泄漏尚未封闭

held-out scene 是必要条件，但不足以阻止相邻帧、同一 trajectory、同一 source、相同 target 或同一 reference 泄漏。若 teacher utility 在重复 seed/edit 下不稳定，学生即使拟合也可能只学到场景/来源身份。

**Kill condition：** 若按 scene + trajectory + source group split 后性能消失，或 teacher test–retest reliability 低于模型可达到的最低上限，删除学生；禁止用 source ID 本身或未来 reference 派生特征作为输入。

### A11. MAJOR：`re-observe` 不是同一被动生成任务中的普通动作

re-observe 改变输入数据和相机轨迹，需要模拟器、真实采集接口或允许主动传感的 benchmark；它也有时间、动作和观测成本。若只有离线视频或固定轨迹，动作无法执行，且与 accept/reject 不是同一预算问题。

**Kill condition：** 没有可审计 observation API、动作可达性、状态同步与成本模型时，删除 `re-observe`；将 active sensing 另立任务，不与被动 memory arbitration 合并。

### A12. CRITICAL FOR METHOD NOVELTY：方法外形已高度占据

把已有部件串成“逐来源 + 交互 + provenance + arbitration”仍可能只是 novelty-by-conjunction。最强组合压力为：

- CUE-R：逐 item intervention、signed operational utility、non-additive evidence interaction；
- CoRM-RAG：反事实 supervision、轻量 Evidence Critic、风险拒绝；
- CF-RAG：causal evidence distinction、parallel arbitration；
- CAMA：provenance prior、依赖来源、集合仲裁、sequential recovery；
- TetherMem：视频生成、query/region/age 条件 memory routing、stale background 抑制；
- Causal LLM Routing：observational causal regret policy。

**Kill condition：** 若方法相对上述思想迁移基线与视频直接基线的增益，可由更多标签、更多采样、额外参数或 test-time compute 解释，永久删除 method novelty，只保留测量发现。

## 9. 对 `Interaction-Aware Provenance Arbitration` 的最终碰撞判断

### 可以保留的窄差别

目前仅能把下列联合属性当作待验证差别：

1. 同一 ordinary-selected 视频 memory source 在运行时有稳定身份；
2. 对全部真实 source-dependent appearance consumer 做一致、可重放、in-distribution intervention；
3. 影响与干预前 geometry 和独立 natural-return reference 同时对齐；
4. 在线策略只使用生成前信息，并对 set-conditioned reference utility 做跨 scene/source/trajectory 泛化；
5. 相对 TetherMem、CoRM 式 critic、source reliability、独立路径、soft consistency、统一 attention 和等算力 search 仍有增量。

### 不能保留的宽主张

- 首次发现 retrieval 不等于 utilization；
- 首次做逐来源 causal utility；
- 首次研究证据/来源非加性交互；
- 首次做 provenance arbitration；
- 首次用 counterfactual teacher 训练 lightweight gate；
- 首次在视频生成中做条件式或 stale-aware memory routing；
- 首次让策略 reject 或主动恢复证据。

因此，当前方法分支应继续标记：`METHOD_SELECTION_DEFERRED`。在 P0–P3 之前不应写实现；即使 P0–P3 通过，也要先解决 A1–A11 和新增近邻，才能进入 P4 学生阶段。

## 10. 可执行的修订方向（供下一版使用，不修改 V2）

1. 把主问题从“模型是否用了来源”改为“已存/已选/可寻址来源是否产生可重复的 source-conditioned observable influence，以及这种 influence 是否改善独立 reference utility”。
2. 把三个 gap 暂时改名为 `Access–Observable-Influence`、`Support–Effect Mismatch`、`Influence–Reference-Utility`，避免先验结论写进指标名。
3. 明确主要 estimand 对 seed 取平均，并分别报告 edit family、replacement、source set、consumer 的异质性；不把单 seed 标签交给学生。
4. 用完整 ordinary cohort 估 prevalence；失败样本只用于机制发现，不作总体分母。
5. 在解封结果前冻结数值 gates、统计模型、独立单位、power、FDR、metric sign 和缺失策略。
6. 先验证 teacher label 的重复可靠性与 intervention validity，再谈学生。
7. 把 TetherMem、CoRM-RAG/CF-RAG/CAMA 思想迁移、source-reliability gate 和统一 attention 加入强基线图。
8. 将 `re-observe` 从默认动作空间移出；只有存在主动环境和公平成本协议时再恢复。
9. 先做 Layer A 的小而完整确认性研究。若只有架构局部 bug，按修复报告处理；若跨架构出现大效应、且传统指标无法解释，再升级 mechanism。

## 11. 逐项最终 kill conditions

| ID | 被杀对象 | 触发条件 | 触发后的诚实定位 |
|---|---|---|---|
| K0 | paradigm-shift 表述 | elephant 频率、真实痛点、技术周期或领域重要性任一长期无证据 | 严格审计/渐进测量工作 |
| K1 | PC-DPM hard sharing | consumer 差异不伤害，或等预算独立/软/统一方案不差 | baseline only |
| K2 | generic stale-memory novelty | 方法主体仍是检测、删除、刷新或 age gate | occupied baseline |
| K3 | Access–Use 机制 | null effect 无法排除冗余/抵消/低功效；positive effect 依赖 edit artifact | operational sensitivity |
| K4 | Use–Location 机制 | support 外 effect 有益，或 support 定义/配准不稳定 | descriptive mismatch |
| K5 | causal Benefit | reference uncertainty/metric choice 改变符号 | reference-conditioned utility |
| K6 | systematic prevalence | cohort 按失败或效果事后选择 | case study only |
| K7 | all-path claim | 任一 source-dependent consumer/后代未覆盖 | interface-local audit |
| K8 | set-interaction method | interaction 近似可加，或不提升 held-out prediction | additive/source-wise policy |
| K9 | student | label 不可靠、group split 后失效、clean false rejection 过高 | delete online learner |
| K10 | re-observe | 无主动环境、状态同步或公平成本模型 | delete action / separate task |
| K11 | method novelty | 强组合基线解释全部增益，或增益来自额外算力/数据 | measurement paper only |
| K12 | generality | 第二个 stable-source 架构无法复现 | VMem-specific diagnostic/bug report |

## 12. Idea-evaluator 致命缺陷审查

| 维度 | 当前结论 | 说明 |
|---|---|---|
| 问题是否清楚 | **有条件通过** | 访问成功与最终 source-conditioned utility 的差距清楚；“use/location/causal Benefit”仍需降格。 |
| 新颖性 | **方法不通过，测量待定** | 宽问题和方法组件已被强近邻占据；视频特有联合现象尚无真实证据。 |
| 可证伪性 | **方向通过，执行不通过** | 有 kill 动作，但阈值、独立单位和统计标准未冻结。 |
| 因果可识别性 | **不通过** | null≠unused、support≠correct location、single natural return≠counterfactual truth。 |
| 可实现性 | **高风险** | all-consumer completeness、pairwise 成本、第二架构与 active re-observe 均未落实。 |
| 顶会潜力 | **存在但未授权** | 只有跨场景/架构的大效应新现象 + 明确机制 + 强组合基线增量，才可能形成 CCF A 级故事。 |

## 13. 审查结论

V2 不是伪创新文档：它主动杀掉两个诱人但错误/拥挤的故事，清楚标注零真实结果，并把方法置于 gate 之后。这些是应保留的研究纪律。

它也还不是可直接执行的创新北极星。最核心的三个 observable 被赋予了过强的机制含义，P0–P6 还不是数值化 preregistration，新近文献又显著压缩了 arbitration 的空间。最合理的下一版本应把 **GeoCausal 从“已命名机制”收缩成 reference-anchored interventional measurement**，把 **Interaction-Aware Provenance Arbitration 继续冻结为一个可能被数据触发的候选**。

最终裁决：**PIVOT**。保留 Layer A；拒绝当前范式转移表述；在完成可识别性修复、数值 gate 和新增近邻基线之前，不进入 Layer C。

## 14. 一手来源清单

### 指定核验来源

- Supervisor-Skills 2.3：<https://github.com/HKUSTDial/Supervisor-Skills/blob/main/handbook/02_Idea_Generation/2.3_%E8%BF%9B%E9%98%B6_%E5%A6%82%E4%BD%95%E5%81%9A%E9%A2%A0%E8%A6%86%E5%BC%8F%E5%88%9B%E6%96%B0.md>
- GaME，CVPR 2026：<https://openaccess.thecvf.com/content/CVPR2026/html/Yugay_Gaussian_Mapping_for_Evolving_Scenes_CVPR_2026_paper.html>
- WorldMM，CVPR 2026：<https://openaccess.thecvf.com/content/CVPR2026/html/Yeo_WorldMM_Dynamic_Multimodal_Memory_Agent_for_Long_Video_Reasoning_CVPR_2026_paper.html>
- WorldMM arXiv full text：<https://arxiv.org/html/2512.02425v2>
- WorldCraft，arXiv 2026：<https://arxiv.org/abs/2605.25077>
- ClashEval，NeurIPS 2024 Datasets and Benchmarks：<https://proceedings.neurips.cc/paper_files/paper/2024/hash/3aa291abc426d7a29fb08418c1244177-Abstract-Datasets_and_Benchmarks_Track.html>
- Causal LLM Routing，NeurIPS 2025 main：<https://proceedings.neurips.cc/paper_files/paper/2025/hash/357774d53e5ee21c5f08ba779e3b5dd9-Abstract-Conference.html>

### 新增关键碰撞来源

- TetherMem，arXiv 2026：<https://arxiv.org/abs/2608.26902>
- CUE-R，arXiv 2026：<https://arxiv.org/abs/2604.05467>
- Counterfactual RAG，ICLR 2026：<https://proceedings.iclr.cc/paper_files/paper/2026/hash/1c078897dc08d46091d0d361d9955c6b-Abstract-Conference.html>
- CoRM-RAG，SIGIR 2026 / arXiv：<https://arxiv.org/abs/2605.01302>
- CAMA，arXiv 2026：<https://arxiv.org/abs/2608.19701>
- UtilMem，arXiv 2026：<https://arxiv.org/abs/2608.30508>
- RAGONITE counterfactual attribution，arXiv 2024：<https://arxiv.org/abs/2412.10571>
- StableWorld，arXiv 2026：<https://arxiv.org/abs/2601.15281>

## 15. 本地输入完整性

| 本地输入 | SHA256 |
|---|---|
| `INNOVATION_NORTH_STAR_V2.md` | `574311ced8f5bcbf2ad21854a0f7895195bc49d4fe968012d3f33bca7b662f36` |
| `handbook_2_3.md` | `c4a0022cad1bfeb09301d3b78e16f2197693bd170d613e6a2be5e45c73266b59` |
| `PC_DPM_NOVELTY_COLLISION_REVIEW_V1.md` | `798a74ec021ac8d5f0d44a3be488ac31dc4859a3d23aacb7eee500dc87f122e6` |
| `CAUSAL_ATTRIBUTION_TOP_VENUE_REFRESH_2026-09-08T0846Z.md` | `a7aef61eb3f67dcb31386c232f923a7a41ba60abdca13741d59c8b456e7367f2` |
| `EVALUATION_PATTERN_TOP_VENUE_REFRESH_2026-09-08T0854Z.md` | `d2f801ef9075a2fef0368c5db425af78fc53e5969095a716188ff1b1d83a6824` |

本报告自身的最终文件 SHA256 在写入完成后由外部回执给出；不能把普通整文件哈希自指地写进被哈希文件本身。
