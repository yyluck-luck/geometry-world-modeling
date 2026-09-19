# 创新北极星 V2：从“统一权重”转向“逐来源记忆责任与条件式治理”

- 冻结时间：2026-09-08T09:09:09Z（Asia/Shanghai 17:09:09）
- 状态：`METHOD_SELECTION_DEFERRED_UNTIL_P0_P3`
- 当前新颖性授权：`NONE`
- 当前新增方法运行：`0`
- 相对 V1 的关键改动：否决 PC-DPM 硬共享权重；否决“旧记忆会过时”作为独立创新；保留 GeoCausal 测量主线；把方法候选缩成需要真实现象触发的集合级、分路径治理问题
- 依据：Supervisor-Skills 2.3 的第一性原理、隐藏假设、领域大象与重要问题检查；`idea-evaluator` 的致命缺陷审查；`benchmark-paper-template` 与 `tech-paper-template` 的贡献闭环；2024–2026 顶会/预印本碰撞审查
- 证据边界：本文件只冻结研究判断，没有新增模型运行、真实评分、像素检查或方法增益

## 给新手的一句话

现在最可能让老师真正停下来看的，不是再加一个 memory 模块，而是用真实反事实证明下面这件事：

> **模型明明存到了、也选对了历史画面，最终却可能没用它、用错地方，甚至被它伤害；而常见总体分数把这些情况都算成“记忆成功”。**

这目前只是可检验假说。只有在真实生成、多个场景和严格负控上反复出现，它才会成为创新发现。

## 1. V1 中哪一项已经被主动否决

### PC-DPM 的“所有 consumer 使用相同来源权重”不再作为主方法

设 semantic 分支只需要来源 `s1` 的身份信息，latent 分支只需要来源 `s2` 的局部纹理。两条路径各自选择最合适来源时总效用可以为 2；若强迫它们使用同一组权重，总效用恒为 1。不同路径的来源权重不同，可能是合理专业化，而非错误。

因此：

- `F10 != F01` 不能单独证明 provenance 冲突；
- 路径变得一致不能替代最终真实 loss 改善；
- 硬共享、软 KL/JS、一致 source token、独立权重与统一 attention 都只能作为对照；
- 若真实数据没有证明“不一致会造成伤害”，PC-DPM 必须永久删除。

当前裁决：`PC_DPM_HARD_SHARING_REJECTED_AS_STANDALONE_NOVELTY`。

## 2. “旧记忆冲突”为什么也不能直接当创新

新增顶会碰撞进一步关闭了普通 stale-memory 故事：

- GaME（CVPR 2026）明确讨论 stale observations 破坏几何和语义一致性，并通过 keyframe management 丢弃过时观测；
- Spatia（CVPR 2026）使用可更新空间记忆；
- WorldMM（CVPR 2026）识别、删除或更新冲突/过时语义 triplet；
- WorldCraft（2026 预印本）在物体被移动后刷新自回归记忆，使其离开视野后能在更新位置重现；
- SPMEM（NeurIPS 2025）已经区分多层时空记忆。

当前裁决：`GENERIC_STALE_MEMORY_REJECTION_OR_REFRESH_IS_OCCUPIED`。动态变化仍可作为压力测试轴，但不能靠“检测并删除旧记忆”构成主创新。

## 3. 仍保留的主问题：GeoCausal Memory Accountability Gap

我们不把六层合同本身包装成贡献，而用它寻找三种现有总体指标可能漏掉的、反直觉的真实失败：

1. **Access–Use Gap**：来源已存储、已选中、也可寻址，但 matched all-path intervention 对输出没有超过 zero-edit/sham 的作用；
2. **Use–Location Gap**：来源确实改变了输出，但 excess effect 没有落在干预前冻结的 source-target 几何支持区域；
3. **Use–Benefit Gap**：来源在正确区域产生影响，却相对未进入 memory 的同步真实重访 reference 带来负 signed Benefit。

完整审计链仍是：

`Store → Select → Address → Influence → Localization → Benefit`

候选贡献不是把指标拆成六项，而是回答一个可证伪问题：

> 在 ordinary-selected、source-ID 稳定的外部视频记忆上，前三层通过是否系统性地高估后面三层；这种高估能否解释自然回访失败，并跨 scene、seed、source 与架构重复？

若普通 retrieval/access 与 reference-based 指标已经解释全部现象，GeoCausal 主线也应停止。

## 4. 可能最“惊讶”的非显然发现形态

以下必须由真实结果支持，目前都不是结论：

| 候选发现 | 为什么反直觉 | 最强推翻证据 |
|---|---|---|
| 检索正确但未使用 | 论文常把 retrieval 命中视为 memory 有效 | all-path matched edit 与 same-path zero/sham 无差别 |
| 使用了但几何错位 | 3D 索引看似应保证空间责任 | effect 与预冻结 support 不相关，或 shape/camera placebo 同样显著 |
| 几何对但净收益为负 | 局部影响常被误读成帮助 | independent natural return 显示 signed Benefit 不为负，或负值不重复 |
| 单来源收益会随共同来源变号 | gate 常把 source utility 当固定属性 | F00/F10/F01/F11 与 pairwise replacement 近似可加 |
| 总体回访分数掩盖责任断裂 | 平均分可能被别处改善抵消 | source audit 与总体 loss 没有额外解释力 |

真正有冲击力的 Figure 1 应展示同一个真实样本：左侧“检索命中与总体分数通过”，中间“来源级反事实暴露未用/错位/有害”，右侧“一个只看生成前信息的治理策略修复同一区域且不损害别处”。在最后一步尚未实现前，只允许画问题示意图，不能画成方法成功图。

## 5. 条件式方法候选：Interaction-Aware Provenance Arbitration

这个名字只指方法研究空间，不代表已经提出或证明新方法。它仅在 P0–P3 全部通过后进入实现。

### 5.1 方法对象

来源效用不是固定标量，而是条件量：

`B_i(S, r, t, seed, consumer)`

其中 `S` 是共同选中的来源集合，`r` 是 replacement，`t` 是目标时刻。方法不能给某张历史图永久贴“好/坏”标签。

### 5.2 离线教师

在未用于模型输入的同步自然重访 reference 上，以 `F00/F10/F01/F11`、same-path dose-zero、sham、未选 source、已知 consumer 正控和小规模 pairwise replacement 得到：

- 每个来源对 semantic 与 latent consumer 的条件 signed Benefit；
- 来源之间的协同、冗余与破坏性交互；
- 预冻结几何 support 内外的 effect；
- 估计不确定区间，而非单次二值标签。

### 5.3 在线动作空间

学生在生成前只能读取当时可见的信息，并从下列动作中选择：

`both / semantic-only / latent-only / soft-downweight / reject / re-observe`

关键点是允许路径专业化，只在数据证明某个来源对某条路径有害时分流。`re-observe` 必须与相同 test-time compute 的普通 active sensing、coverage、uncertainty 与 reward-guided candidate search 比较。

### 5.4 为什么它仍不能声称新颖

- ClashEval 已证明错误检索证据可伤害生成式模型；
- CUE-R 已做逐证据 REMOVE/REPLACE/DUPLICATE 并指出非加性交互；
- Causal LLM Routing 已用因果目标做端到端 regret routing；
- Ada-RefSR/TetherCache 已占据可信 gate 和坏参考抑制；
- Inference-time Physics Alignment 与 AW4RE 已占据 reward 选择和主动再观察空间。

当前能保留的窄差别只有：**显式视频世界记忆中，运行时来源身份、全部 appearance consumer、预处理几何责任和独立自然重访收益的联合监督。** 这个联合差别必须靠真实新现象与强基线增量成立，文献“没有搜到完全同名工作”不构成证明。

## 6. 三层贡献路线

### Layer A：发现/测量，当前唯一主线

- 架构受限的来源级责任审计；
- 报告传统指标漏掉的 gap 频率、效应量、置信区间和失败全量；
- 先在 VMem 做深，再在第二个 stable-source 架构验证可迁移性。

### Layer B：机制，必须由 Layer A 触发

- 判断路径差异是专业化还是有害冲突；
- 用析因与几何定位检验中介关系；
- 量化单来源、pairwise 与集合级交互。

### Layer C：方法，必须胜过完整强基线

- 独立 consumer 权重；
- hard sharing；
- KL/JS soft consistency；
- per-source token、source ID、geometry attention；
- trust gate；
- unified pose-aware attention；
- 相同训练数据、参数/FLOPs 和 test-time compute 的路由/主动再观察对照。

若只能完成 Layer A 且得到跨模型的重要新发现，论文应定位为 measurement/benchmark；若 Layer B/C 也通过，才升级为 mechanism + technique。

## 7. 决定是否继续的 P0–P6

| Gate | 预注册问题 | 通过标准的性质 | Kill 动作 |
|---|---|---|---|
| P0 | 是否存在相机服从、可复现的自然回访失败 | 多 scene/seed，盲评分，像素与来源链可审计 | 没有真实失败就停止当前故事 |
| P1 | 前三层通过是否仍出现 Access–Use/Use–Location/Use–Benefit gap | matched controls 后 effect 仍稳定 | 普通指标已充分解释则停止 GeoCausal |
| P2 | consumer 差异是有害冲突还是合理专业化 | 与几何错位、负 Benefit、自然 loss 有预注册关系 | 只显示差异而无伤害就删除 conflict 主张 |
| P3 | 来源收益是否有显著集合交互 | factorial/pairwise 比单项模型有额外解释力 | 近似可加则不开发集合治理 |
| P4 | 生成前学生能否跨 scene 预测风险 | held-out scene、校准区间、clean false rejection | 只记住 scene/source 就删除学生 |
| P5 | 治理策略是否胜过全部强基线 | 相同数据、容量、采样与计算预算 | 无增量就删除方法，只保留发现 |
| P6 | 是否在第二架构重复 | stable source ID 的独立架构 | 只在 VMem 单一 bug 上成立则降级为修复报告 |

任何 gate 都禁止事后换阈值、挑样例、删除失败 seed 或新增看过测试答案的特征。

## 8. 投稿级最低证据包

### 数据与范围

- 至少多个未参与协议设计的独立真实场景；
- 静态重访、遮挡、动态变化与长时离开后返回分层；
- source、target、seed、scene 全量报告，不用帧数冒充独立样本数。

### 因果识别

- 两种 edit family；
- same-path dose-zero、exact replay、sham、未选 source negative、已知 consumer positive；
- `F00/F10/F01/F11` 及至少小规模 pairwise 交互；
- 输出 effect、几何 local excess、signed Benefit 与自然失败之间的预注册关系。

### 公平比较

- 所有 source-aware、geometry-aware、trust-aware、unified-attention 与 active-selection 强基线；
- 参数、训练样本、推理采样、相机动作、重观察次数和 wall time 对齐；
- 总体质量、局部几何、相机服从、support 外损伤、速度和内存同时报告。

### 可复现性

- 冻结 manifest、逐文件 hash、真实运行 receipt、失败保留、独立重算与独立审查；
- 区分 source-only、自测、保存数组重读、真实模型执行和人工像素审查。

## 9. 顶会碰撞后的占据地图

| 已被占据 | 在本项目中的角色 |
|---|---|
| VMem 的 surfel memory、检索与 cycle trajectory | baseline，不是创新 |
| Movie Weaver/Video Alchemist 的来源绑定 | source-aware baseline |
| WorldStereo/Geometry-as-context/Spatia 的几何条件和门控 | geometry-aware baseline |
| SPMEM/VRAG/long-context SSM 的多层或长时记忆 | memory architecture baseline |
| MomentSeeker 的 access 与 end-to-end 分离 | Address 评价先例 |
| Hi3DEval/Ref4D 的层级、局部与 reference-based 评价 | Benefit 评价强基线 |
| Finding NeMo/activation patching 的功能定位 | 干预设计先例 |
| ClashEval/CUE-R 的有害证据与非加性交互 | harm/interaction 先例 |
| Causal LLM Routing 的因果 regret 路由 | policy learning 先例 |
| GaME/WorldMM/WorldCraft/Spatia 的更新或移除过时状态 | dynamic/stale-memory baseline |

因此不能依赖任何单个模块名称。候选创新只能来自这些维度在**同一视频生成来源上的、以前未被强基线解释的非显然实证**。

## 10. 现在的最诚实结论

1. 已经有一个有潜力的创新问题：ordinary retrieval success 是否系统性高估真实 memory accountability。
2. 已经有一个可能形成方法的分支：依据集合级、分 consumer 的条件因果收益做生成前 provenance arbitration。
3. PC-DPM 硬共享版本已被数学反例和统一 attention 强基线否决；普通 stale-memory 删除也已被近邻占据。
4. 当前还没有任何真实 GeoCausal arm、方法增益或跨场景统计，创新尚未成立。
5. 下一项科学工作不是继续取名字，而是完成 C1/C2 合法 baseline cohort、冻结 S48 V6，并让 P0–P3 用真实结果决定方法是否存在。

## 11. 对外表述边界

当前允许说：

> 我们已把候选问题收窄为显式视频世界记忆的来源级责任缺口，并冻结了能否证它的真实实验链；一次对抗式文献审查主动否决了硬共享权重与普通 stale-memory 两条拥挤路线。

当前禁止说：

- 已证明新的 memory failure；
- 已提出有效的新方法；
- 首次发现有害记忆；
- S48 已运行；
- 已达到 PhD/CCF A 水平；
- 保证老师惊讶或保证录用。

## 12. 一手来源

- Supervisor-Skills 2.3：<https://github.com/HKUSTDial/Supervisor-Skills/blob/main/handbook/02_Idea_Generation/2.3_%E8%BF%9B%E9%98%B6_%E5%A6%82%E4%BD%95%E5%81%9A%E9%A2%A0%E8%A6%86%E5%BC%8F%E5%88%9B%E6%96%B0.md>
- VMem（ICCV 2025）：<https://openaccess.thecvf.com/content/ICCV2025/html/Li_VMem_Consistent_Interactive_Video_Scene_Generation_with_Surfel-Indexed_View_Memory_ICCV_2025_paper.html>
- SPMEM（NeurIPS 2025）：<https://proceedings.neurips.cc/paper_files/paper/2025/hash/467655d26fcc207bca08915dc91964c6-Abstract-Conference.html>
- Long-Context State-Space Video World Models（ICCV 2025）：<https://openaccess.thecvf.com/content/ICCV2025/html/Po_Long-Context_State-Space_Video_World_Models_ICCV_2025_paper.html>
- Movie Weaver（CVPR 2025）：<https://openaccess.thecvf.com/content/CVPR2025/papers/Liang_Movie_Weaver_Tuning-Free_Multi-Concept_Video_Personalization_with_Anchored_Prompts_CVPR_2025_paper.pdf>
- Geometry-as-context（CVPR 2026）：<https://openaccess.thecvf.com/content/CVPR2026/html/Hu_Geometry-as-context_Modulating_Explicit_3D_in_Scene-consistent_Video_Generation_to_Geometry_CVPR_2026_paper.html>
- WorldStereo（CVPR 2026）：<https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_WorldStereo_Bridging_Camera-Guided_Video_Generation_and_Scene_Reconstruction_via_3D_CVPR_2026_paper.html>
- Spatia（CVPR 2026）：<https://openaccess.thecvf.com/content/CVPR2026/papers/Zhao_Spatia_Video_Generation_with_Updatable_Spatial_Memory_CVPR_2026_paper.pdf>
- MomentSeeker（NeurIPS 2025）：<https://proceedings.neurips.cc/paper_files/paper/2025/hash/281e0b9142763f2b6c944fedb8550ba9-Abstract-Datasets_and_Benchmarks_Track.html>
- Hi3DEval（NeurIPS 2025）：<https://proceedings.neurips.cc/paper_files/paper/2025/hash/42ffaddcc6edc9fb05ff9f9b49fca700-Abstract-Datasets_and_Benchmarks_Track.html>
- Ref4D-VideoBench（CVPR 2026）：<https://openaccess.thecvf.com/content/CVPR2026/html/Wei_Ref4D-VideoBench_Four-Dimensional_Reference-Based_Evaluation_of_Text-to-Video_Generative_Models_CVPR_2026_paper.html>
- Finding NeMo（NeurIPS 2024）：<https://proceedings.neurips.cc/paper_files/paper/2024/hash/a102dd5931da01e1b40205490513304c-Abstract-Conference.html>
- ClashEval（NeurIPS 2024）：<https://proceedings.neurips.cc/paper_files/paper/2024/hash/3aa291abc426d7a29fb08418c1244177-Abstract-Datasets_and_Benchmarks_Track.html>
- Causal LLM Routing（NeurIPS 2025）：<https://proceedings.neurips.cc/paper_files/paper/2025/hash/357774d53e5ee21c5f08ba779e3b5dd9-Abstract-Conference.html>
- Inference-time Physics Alignment（CVPR 2026）：<https://openaccess.thecvf.com/content/CVPR2026/html/Yuan_Inference-time_Physics_Alignment_of_Video_Generative_Models_with_Latent_World_CVPR_2026_paper.html>
- WorldMM（CVPR 2026）：<https://openaccess.thecvf.com/content/CVPR2026/papers/Yeo_WorldMM_Dynamic_Multimodal_Memory_Agent_for_Long_Video_Reasoning_CVPR_2026_paper.pdf>
- GaME（CVPR 2026）：<https://openaccess.thecvf.com/content/CVPR2026/html/Yugay_Gaussian_Mapping_for_Evolving_Scenes_CVPR_2026_paper.html>
- WorldCraft（2026 预印本）：<https://arxiv.org/abs/2605.25077>
- AW4RE（ICLR 2026 workshop）：<https://openreview.net/forum?id=6cJXSaHHgV>

